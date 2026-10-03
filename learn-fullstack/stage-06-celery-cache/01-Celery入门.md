# 第 01 节：Celery 入门

## 一、为什么需要异步任务？

Web 应用中有些操作耗时较长，不适合在请求-响应周期内同步完成：

```
同步处理（阻塞用户）：
用户点击"发送邮件" → 等待邮件发送（3秒）→ 返回响应
用户体验：点击后卡住 3 秒

异步处理（不阻塞用户）：
用户点击"发送邮件" → 立即返回"已提交" → 后台发送邮件
用户体验：点击后立刻得到反馈
```

### 1.1 适合异步处理的场景

- **发送邮件/短信通知** — 调用第三方 API 耗时
- **生成报表/导出文件** — 大量数据处理
- **图片/视频处理** — 缩略图生成、视频转码
- **数据同步** — 与第三方系统同步数据
- **定时任务** — 每日统计、定期清理

---

## 二、Celery 架构

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Django   │ ──→ │  Broker   │ ──→ │  Worker  │
│  (生产者) │     │  (Redis)  │     │  (消费者) │
│  发送任务 │     │  消息队列  │     │  执行任务 │
└──────────┘     └──────────┘     └──────────┘
                                        │
                                        ↓
                                  ┌──────────┐
                                  │  Backend  │
                                  │  (Redis)  │
                                  │  存储结果  │
                                  └──────────┘
```

| 组件 | 说明 | TaskFlow 中使用 |
|------|------|----------------|
| **Producer（生产者）** | Django 应用，发送任务 | Django 视图 |
| **Broker（消息中间件）** | 消息队列，存储待执行的任务 | Redis |
| **Worker（工作进程）** | 从 Broker 获取任务并执行 | Celery Worker |
| **Backend（结果后端）** | 存储任务执行结果 | Redis |

---

## 三、安装与配置

### 3.1 安装

```bash
pip install celery redis django-celery-beat django-celery-results
```

### 3.2 Celery 配置文件

```python
# config/celery.py
import os
from celery import Celery

# 设置 Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 创建 Celery 应用
app = Celery('taskflow')

# 从 Django settings 中读取配置（以 CELERY_ 开头的配置项）
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现各应用中的 tasks.py
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

### 3.3 注册 Celery

```python
# config/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### 3.4 Django Settings 配置

```python
# config/settings.py

INSTALLED_APPS = [
    ...
    'django_celery_beat',       # 定时任务管理
    'django_celery_results',    # 任务结果存储
]

# ==================== Celery 配置 ====================
CELERY_BROKER_URL = 'redis://localhost:6379/0'          # Broker：Redis 数据库 0
CELERY_RESULT_BACKEND = 'django-db'                      # 结果存储到 Django 数据库
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_ENABLE_UTC = True

# 任务配置
CELERY_TASK_TRACK_STARTED = True          # 跟踪任务开始状态
CELERY_TASK_TIME_LIMIT = 300              # 任务硬超时（秒）
CELERY_TASK_SOFT_TIME_LIMIT = 240         # 任务软超时（秒）
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100   # Worker 执行 100 个任务后重启（防内存泄漏）

# Beat 定时任务
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

### 3.5 迁移

```bash
python manage.py migrate
```

---

## 四、编写第一个任务

```python
# apps/tasks/tasks.py
from celery import shared_task
import logging
import time

logger = logging.getLogger(__name__)

@shared_task
def add(x, y):
    """最简单的异步任务"""
    time.sleep(2)  # 模拟耗时操作
    return x + y

@shared_task(bind=True, max_retries=3)
def send_task_notification(self, task_id):
    """发送任务通知"""
    try:
        from apps.tasks.models import Task
        task = Task.objects.select_related('assignee').get(pk=task_id)
        
        if task.assignee and task.assignee.email:
            # 模拟发送邮件
            logger.info(f"发送通知给 {task.assignee.email}: 任务 '{task.title}' 已分配给你")
            # send_email(task.assignee.email, ...)
            
        return {'status': 'sent', 'task_id': task_id}
    
    except Exception as exc:
        logger.error(f"发送通知失败: {exc}")
        # 重试：2^retry_count 秒后重试
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

---

## 五、启动 Worker

```bash
# 启动 Celery Worker
celery -A config worker --loglevel=info

# Windows 上需要加 --pool=solo（Windows 不支持 fork）
celery -A config worker --loglevel=info --pool=solo

# 指定并发数
celery -A config worker --loglevel=info --concurrency=4
```

---

## 六、调用任务

```python
# 在 Django Shell 或视图中调用
from apps.tasks.tasks import add, send_task_notification

# 方式1：异步调用（推荐）
result = add.delay(4, 6)
print(result.id)         # 任务 ID
print(result.status)     # PENDING / STARTED / SUCCESS / FAILURE
print(result.get(timeout=10))  # 等待结果：10

# 方式2：apply_async（更多控制）
result = add.apply_async(
    args=[4, 6],
    countdown=10,         # 10 秒后执行
    expires=60,           # 60 秒后过期
    queue='default',      # 指定队列
)

# 方式3：同步调用（测试用）
result = add(4, 6)       # 直接调用，不走 Celery

# 在视图中使用
class TaskViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        task = serializer.save(creator=self.request.user)
        # 异步发送通知
        if task.assignee:
            send_task_notification.delay(task.id)
```

---

## 七、练习

1. 按照上面的步骤配置 Celery + Redis
2. 创建一个简单的 `add` 任务，启动 Worker 测试
3. 创建 `send_task_notification` 任务，在任务创建时异步发送通知
4. 在 Django Shell 中测试异步调用和结果获取
5. 观察 Worker 日志，理解任务的生命周期
