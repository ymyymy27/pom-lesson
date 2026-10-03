# 第 05 节：OAuth2 第三方登录

## 一、OAuth2 是什么？

OAuth2 是一种 **授权协议**，允许用户通过第三方平台（GitHub、Google、微信）登录你的应用，而不需要在你的应用中注册账号。

### 1.1 OAuth2 授权流程

```
1. 用户点击"GitHub 登录"按钮
   ↓
2. 前端跳转到 GitHub 授权页面
   https://github.com/login/oauth/authorize?client_id=xxx&redirect_uri=xxx&scope=user:email
   ↓
3. 用户在 GitHub 上确认授权
   ↓
4. GitHub 回调你的应用，带上 authorization_code
   https://yourapp.com/callback?code=abc123
   ↓
5. 你的后端用 code 向 GitHub 换取 access_token
   POST https://github.com/login/oauth/access_token
   ↓
6. 用 access_token 获取用户信息
   GET https://api.github.com/user
   ↓
7. 在你的数据库中创建/关联用户，返回 JWT Token
```

### 1.2 核心概念

| 概念 | 说明 |
|------|------|
| **Client ID** | 你的应用在第三方平台注册后获得的 ID |
| **Client Secret** | 应用密钥（绝对不能暴露到前端！） |
| **Authorization Code** | 临时授权码（一次性使用） |
| **Access Token** | 访问令牌（用于获取用户信息） |
| **Redirect URI** | 授权完成后的回调地址 |
| **Scope** | 请求的权限范围（如 email、profile） |

---

## 二、使用 django-allauth

`django-allauth` 是 Django 生态中最流行的认证库，支持 50+ 社交平台登录。

### 2.1 安装

```bash
pip install django-allauth
```

### 2.2 配置

```python
# config/settings.py
INSTALLED_APPS = [
    'django.contrib.sites',          # allauth 依赖
    ...
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.github',   # GitHub
    'allauth.socialaccount.providers.google',   # Google
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# allauth 配置
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'optional'

SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'APP': {
            'client_id': 'your-github-client-id',
            'secret': 'your-github-client-secret',
        },
        'SCOPE': ['user:email'],
    },
    'google': {
        'APP': {
            'client_id': 'your-google-client-id',
            'secret': 'your-google-client-secret',
        },
        'SCOPE': ['profile', 'email'],
    },
}
```

### 2.3 获取 Client ID

**GitHub：**
1. 访问 https://github.com/settings/developers
2. 点击 "New OAuth App"
3. 填写信息：
   - Application name: TaskFlow
   - Homepage URL: http://localhost:3000
   - Authorization callback URL: http://localhost:8000/accounts/github/login/callback/
4. 获取 Client ID 和 Client Secret

**Google：**
1. 访问 https://console.cloud.google.com/apis/credentials
2. 创建 OAuth 2.0 Client ID
3. 设置 Authorized redirect URIs: http://localhost:8000/accounts/google/login/callback/

---

## 三、前后端分离中的 OAuth2

前后端分离架构中，OAuth2 流程稍有不同：

```
1. 前端引导用户跳转到 GitHub 授权页
2. 用户授权后，GitHub 将 code 回调到前端
3. 前端将 code 发送给后端 API
4. 后端用 code 向 GitHub 换取用户信息
5. 后端创建/关联用户，返回 JWT Token 给前端
```

### 3.1 后端 API

```python
# apps/users/views.py
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()

class GitHubLoginView(APIView):
    """GitHub OAuth2 登录"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'error': '缺少 authorization code'}, status=400)
        
        # 1. 用 code 换取 access_token
        token_response = requests.post(
            'https://github.com/login/oauth/access_token',
            data={
                'client_id': settings.GITHUB_CLIENT_ID,
                'client_secret': settings.GITHUB_CLIENT_SECRET,
                'code': code,
            },
            headers={'Accept': 'application/json'},
        )
        access_token = token_response.json().get('access_token')
        
        if not access_token:
            return Response({'error': 'GitHub 授权失败'}, status=400)
        
        # 2. 用 access_token 获取用户信息
        user_response = requests.get(
            'https://api.github.com/user',
            headers={'Authorization': f'Bearer {access_token}'},
        )
        github_user = user_response.json()
        
        # 获取邮箱
        email_response = requests.get(
            'https://api.github.com/user/emails',
            headers={'Authorization': f'Bearer {access_token}'},
        )
        emails = email_response.json()
        primary_email = next(
            (e['email'] for e in emails if e['primary']),
            github_user.get('email')
        )
        
        # 3. 创建或关联用户
        user, created = User.objects.get_or_create(
            email=primary_email,
            defaults={
                'username': github_user['login'],
            }
        )
        
        # 4. 返回 JWT Token
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'is_new_user': created,
        })
```

### 3.2 前端调用流程

```javascript
// 1. 跳转到 GitHub 授权页
const GITHUB_CLIENT_ID = 'your-client-id';
const REDIRECT_URI = 'http://localhost:3000/auth/github/callback';
window.location.href = 
  `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${REDIRECT_URI}&scope=user:email`;

// 2. 回调页面获取 code，发送给后端
// URL: http://localhost:3000/auth/github/callback?code=abc123
const code = new URLSearchParams(window.location.search).get('code');
const response = await fetch('/api/v1/auth/github/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ code }),
});
const data = await response.json();
// 保存 Token，跳转到主页
```

---

## 四、安全注意事项

- **Client Secret** 只能存在后端，绝不能暴露到前端
- 使用 **HTTPS** 传输 Token
- **state 参数** 防止 CSRF 攻击（授权请求时带随机 state，回调时验证一致性）
- **redirect_uri** 严格限制为你的域名
- 第三方 Token 不要直接存储，只提取需要的用户信息

---

## 五、练习

1. 在 GitHub 上创建 OAuth App，获取 Client ID 和 Secret
2. 实现 `GitHubLoginView`：接收 code，返回 JWT Token
3. 理解 OAuth2 授权码模式的完整流程，画出时序图
4. （可选）集成 django-allauth，支持 GitHub 登录

## 阶段总结

至此，第 05 阶段全部完成。你已经掌握：

- ✅ 自定义 User 模型和 Profile
- ✅ JWT 认证（SimpleJWT）
- ✅ 注册、登录、登出、修改密码 API
- ✅ DRF 权限系统（内置权限、自定义权限、对象级权限）
- ✅ OAuth2 第三方登录原理

**下一阶段** → 第 06 阶段：Celery 异步任务 & Redis 缓存
