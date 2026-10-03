> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 03 节：WebSocket 实时通知

## 一、为什么需要 WebSocket？

HTTP 是 **请求-响应** 模式，服务端不能主动推送数据给客户端。WebSocket 提供 **全双工** 通信：

```
HTTP：  客户端 → 请求 → 服务端 → 响应（单向，每次都要请求）
WS：    客户端 ←→ 服务端（双向，服务端可主动推送）
```

适用场景：实时通知、聊天消息、任务状态变更推送、协作编辑。

---

## 二、Django Channels

Django Channels 扩展了 Django，支持 WebSocket、长轮询等异步协议。

### 2.1 安装

```bash
pip install channels channels-redis
```

### 2.2 配置

```python
# config/settings.py
INSTALLED_APPS = [
    'daphne',          # ASGI 服务器（放在最前面）
    'django.contrib.admin',
    ...
    'channels',
]

# ASGI 应用
ASGI_APPLICATION = 'config.asgi.application'

# Channel Layers（使用 Redis）
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}
```

```python
# config/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

from apps.notifications.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

### 2.3 WebSocket Consumer

```python
# apps/notifications/consumers.py
import json
from channels.generic.websocket import AsyncJsonWebSocketConsumer

class NotificationConsumer(AsyncJsonWebSocketConsumer):
    """用户通知 WebSocket"""
    
    async def connect(self):
        self.user = self.scope['user']
        
        if self.user.is_anonymous:
            await self.close()
            return
        
        # 加入用户专属的通知频道
        self.room_name = f'user_{self.user.id}_notifications'
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()
        
        # 发送欢迎消息
        await self.send_json({
            'type': 'connected',
            'message': f'已连接通知服务',
        })
    
    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)
    
    async def receive_json(self, content):
        """接收客户端消息（如已读通知）"""
        msg_type = content.get('type')
        if msg_type == 'mark_read':
            notification_id = content.get('notification_id')
            # 标记通知为已读...
    
    # ===== 以下是服务端推送方法 =====
    
    async def notification_message(self, event):
        """推送通知给客户端"""
        await self.send_json({
            'type': 'notification',
            'data': event['data'],
        })
    
    async def task_updated(self, event):
        """任务状态更新推送"""
        await self.send_json({
            'type': 'task_updated',
            'data': event['data'],
        })
```

### 2.4 路由

```python
# apps/notifications/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
]
```

### 2.5 从后端推送消息

```python
# apps/tasks/signals.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_notification(user_id, data):
    """向指定用户推送通知"""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'user_{user_id}_notifications',
        {
            'type': 'notification_message',
            'data': data,
        }
    )

# 在信号中使用
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender='tasks.Task')
def notify_task_update(sender, instance, created, **kwargs):
    if instance.assignee_id:
        send_notification(instance.assignee_id, {
            'title': '任务更新' if not created else '新任务',
            'message': f'任务 "{instance.title}" {"已分配给你" if created else "已更新"}',
            'task_id': instance.id,
        })
```

---

## 三、前端 WebSocket

### 3.1 WebSocket Hook

```tsx
// src/hooks/useWebSocket.ts
import { useEffect, useRef, useCallback, useState } from 'react';
import useAuthStore from '@/store/useAuthStore';

interface UseWebSocketOptions {
    onMessage?: (data: any) => void;
    reconnectInterval?: number;
    maxRetries?: number;
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
    const { onMessage, reconnectInterval = 3000, maxRetries = 5 } = options;
    const wsRef = useRef<WebSocket | null>(null);
    const retriesRef = useRef(0);
    const [isConnected, setIsConnected] = useState(false);
    const token = useAuthStore((s) => s.token);
    
    const connect = useCallback(() => {
        if (!token) return;
        
        const wsUrl = `${url}?token=${token}`;
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            setIsConnected(true);
            retriesRef.current = 0;
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onMessage?.(data);
        };
        
        ws.onclose = () => {
            setIsConnected(false);
            // 自动重连
            if (retriesRef.current < maxRetries) {
                retriesRef.current += 1;
                setTimeout(connect, reconnectInterval);
            }
        };
        
        ws.onerror = () => {
            ws.close();
        };
        
        wsRef.current = ws;
    }, [url, token, onMessage, reconnectInterval, maxRetries]);
    
    useEffect(() => {
        connect();
        return () => {
            wsRef.current?.close();
        };
    }, [connect]);
    
    const send = useCallback((data: any) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(data));
        }
    }, []);
    
    return { isConnected, send };
}
```

### 3.2 在组件中使用

```tsx
function App() {
    const { isAuthenticated } = useAuth();
    
    const { isConnected } = useWebSocket(
        `ws://localhost:8000/ws/notifications/`,
        {
            onMessage: (data) => {
                if (data.type === 'notification') {
                    // 显示通知 toast
                    toast.info(data.data.message);
                }
                if (data.type === 'task_updated') {
                    // 刷新任务列表
                    queryClient.invalidateQueries({ queryKey: ['tasks'] });
                }
            },
        }
    );
    
    return (
        <div>
            {isConnected && <span className="text-green-500 text-xs">● 实时连接</span>}
            <Routes>...</Routes>
        </div>
    );
}
```

---

## 四、练习

1. 安装 Django Channels + Redis，配置 ASGI
2. 创建 `NotificationConsumer`，实现连接/断开/接收/推送
3. 在任务创建/更新时通过 Channel Layer 推送通知
4. 实现前端 `useWebSocket` Hook，自动重连
5. 在 App 中连接 WebSocket，收到通知时显示 Toast
