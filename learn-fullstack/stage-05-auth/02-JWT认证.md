# 第 02 节：JWT 认证

## 一、认证方式对比

| 方式 | 原理 | 适用场景 | 前后端分离 |
|------|------|---------|-----------|
| **Session** | 服务端存储会话，Cookie 传递 Session ID | 传统 Web | ❌ 不适合 |
| **Token** | 服务端存储 Token，请求头传递 | 简单 API | ✅ |
| **JWT** | 无状态，Token 自包含用户信息 | 前后端分离 | ✅ 推荐 |

### 1.1 JWT 是什么？

JWT（JSON Web Token）是一种 **自包含的** Token 格式，服务端不需要存储 Token，只需要验证签名。

```
JWT = Header.Payload.Signature

eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.     ← Header（算法+类型）
eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6InpoYW5n... ← Payload（用户数据+过期时间）
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c  ← Signature（签名验证）
```

### 1.2 JWT 认证流程

```
1. 用户发送 邮箱+密码 → POST /api/v1/auth/login/
2. 服务端验证通过 → 返回 access_token + refresh_token
3. 前端存储 Token → localStorage 或内存
4. 后续请求携带 → Authorization: Bearer <access_token>
5. access_token 过期 → 用 refresh_token 换新的 access_token
6. refresh_token 过期 → 需要重新登录
```

---

## 二、安装 SimpleJWT

```bash
pip install djangorestframework-simplejwt
```

### 2.1 配置 settings.py

```python
# config/settings.py
from datetime import timedelta

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),    # access_token 有效期
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),       # refresh_token 有效期
    'ROTATE_REFRESH_TOKENS': True,                      # 刷新时返回新的 refresh_token
    'BLACKLIST_AFTER_ROTATION': True,                   # 旧 refresh_token 加入黑名单
    'AUTH_HEADER_TYPES': ('Bearer',),                   # 请求头格式: Bearer xxx
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_OBTAIN_SERIALIZER': 'apps.users.serializers.CustomTokenObtainPairSerializer',
}
```

### 2.2 配置 URL

```python
# apps/users/urls.py
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

app_name = 'users'

urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token-verify'),
]
```

### 2.3 使用

```bash
# 1. 获取 Token
POST /api/v1/auth/login/
{"email": "user@example.com", "password": "mypassword"}

# 响应：
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGci...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}

# 2. 携带 Token 访问 API
GET /api/v1/tasks/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGci...

# 3. access_token 过期后，用 refresh_token 刷新
POST /api/v1/auth/refresh/
{"refresh": "eyJ0eXAiOiJKV1QiLCJhbGci..."}

# 响应：
{"access": "eyJ0eXAi...(新的access_token)"}

# 4. 验证 Token 是否有效
POST /api/v1/auth/verify/
{"token": "eyJ0eXAi..."}
```

---

## 三、自定义 Token 返回内容

默认只返回 `access` 和 `refresh`，我们可以自定义返回用户信息。

```python
# apps/users/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """自定义登录返回：Token + 用户信息"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # 在返回数据中附加用户信息
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'avatar': self.user.avatar.url if self.user.avatar else None,
            'is_staff': self.user.is_staff,
        }
        
        return data
```

```json
// 登录响应
{
    "access": "eyJ0eXAi...",
    "refresh": "eyJ0eXAi...",
    "user": {
        "id": 1,
        "username": "zhangsan",
        "email": "zs@example.com",
        "avatar": null,
        "is_staff": false
    }
}
```

---

## 四、Token 黑名单（登出）

```python
# config/settings.py
INSTALLED_APPS = [
    ...
    'rest_framework_simplejwt.token_blacklist',  # 添加黑名单应用
]
# 然后运行 python manage.py migrate
```

```python
# apps/users/views.py
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()  # 将 refresh_token 加入黑名单
            return Response({'message': '登出成功'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': '无效的 Token'}, status=status.HTTP_400_BAD_REQUEST)
```

---

## 五、前端如何使用 JWT

```
1. 登录成功 → 将 access_token 和 refresh_token 存储
   - access_token → 内存 / sessionStorage（更安全）
   - refresh_token → httpOnly Cookie（最安全）或 localStorage

2. 每个 API 请求 → 在 Header 中携带 access_token
   Authorization: Bearer <access_token>

3. 收到 401 响应 → 用 refresh_token 刷新
   POST /api/v1/auth/refresh/ {"refresh": "xxx"}

4. refresh_token 也过期 → 跳转登录页
```

---

## 六、练习

1. 安装 SimpleJWT，配置 settings.py 和 URL
2. 用 API 测试登录，获取 Token
3. 携带 Token 访问受保护的 API
4. 自定义 `TokenObtainPairSerializer`，登录时返回用户信息
5. 实现登出 API（Token 黑名单）
6. 测试 Token 过期后的刷新流程
