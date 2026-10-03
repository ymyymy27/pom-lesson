# 第 03 节：Web 安全

## 一、常见攻击类型

| 攻击 | 全称 | 简要说明 |
|------|------|---------|
| **XSS** | Cross-Site Scripting | 注入恶意脚本到页面 |
| **CSRF** | Cross-Site Request Forgery | 伪造用户请求 |
| **SQL 注入** | SQL Injection | 通过输入操纵 SQL 查询 |
| **SSRF** | Server-Side Request Forgery | 利用服务端发起内部请求 |
| **暴力破解** | Brute Force | 穷举密码 |
| **敏感信息泄露** | Information Disclosure | 暴露密钥、堆栈信息 |

---

## 二、XSS（跨站脚本攻击）

攻击者注入恶意 JavaScript，在其他用户的浏览器中执行。

```
存储型 XSS：恶意脚本存入数据库（如评论 <script>alert('XSS')</script>）
反射型 XSS：恶意脚本在 URL 参数中传递
DOM 型 XSS：前端直接操作不安全的用户输入
```

### 2.1 防护

**后端：**

```python
# Django 模板自动转义（默认开启）
# {{ user_input }} 会自动转义 HTML 特殊字符

# DRF 序列化器中过滤
import bleach

class CommentSerializer(serializers.ModelSerializer):
    def validate_content(self, value):
        # 只允许安全的 HTML 标签
        return bleach.clean(value, tags=['p', 'b', 'i', 'a', 'br'], strip=True)
```

**前端：**

```tsx
// ✅ React 默认转义（安全）
<p>{userInput}</p>  // <script> 会被转义为文本

// ❌ dangerouslySetInnerHTML（危险，避免使用）
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// 如果必须渲染 HTML，使用 DOMPurify 消毒
import DOMPurify from 'dompurify';

function SafeHTML({ html }: { html: string }) {
    const clean = DOMPurify.sanitize(html);
    return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}
```

---

## 三、CSRF（跨站请求伪造）

攻击者诱骗用户访问恶意页面，在用户不知情的情况下向目标站点发送请求。

### 3.1 防护

```python
# Django CSRF 保护（默认开启）
# 使用 JWT 认证时，CSRF 风险降低（Token 不会被自动发送）

# 如果前端使用 Cookie 传递 Token：
CSRF_COOKIE_HTTPONLY = False  # 前端需要读取 CSRF Cookie
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

# 前端发送请求时携带 CSRF Token
import axios from 'axios';

function getCsrfToken(): string {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

api.defaults.headers.common['X-CSRFToken'] = getCsrfToken();
```

**JWT 方案天然防 CSRF：**
- JWT 存在 `localStorage` 或内存中
- 需要手动添加到请求头 `Authorization: Bearer xxx`
- 恶意网站无法读取你的 localStorage

---

## 四、SQL 注入

攻击者通过输入构造恶意 SQL 语句。

```python
# ❌ 拼接 SQL（极度危险）
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
# 输入: ' OR '1'='1 → 返回所有用户

# ✅ Django ORM 自动参数化（安全）
User.objects.filter(username=username)

# ✅ 原生 SQL 使用参数化查询
cursor.execute("SELECT * FROM users WHERE username = %s", [username])

# ✅ DRF 的 filter 参数也是安全的
# ?status=pending → ORM filter → 参数化查询
```

---

## 五、安全配置

### 5.1 Django 安全设置

```python
# config/settings.py（生产环境）

# HTTPS
SECURE_SSL_REDIRECT = True              # HTTP 重定向到 HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookie 安全
SESSION_COOKIE_SECURE = True            # Cookie 仅通过 HTTPS 发送
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True           # JS 不能读取 Session Cookie
CSRF_COOKIE_HTTPONLY = True

# 安全头
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'               # 禁止 iframe 嵌入
SECURE_HSTS_SECONDS = 31536000          # HSTS 1 年
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# 密码验证
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 隐藏 Django 版本
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
```

### 5.2 Nginx 安全头

```nginx
# 安全响应头
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

# 隐藏 Nginx 版本
server_tokens off;
```

---

## 六、API 安全

### 6.1 请求限流

```python
# config/settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',     # 匿名用户 30 次/分钟
        'user': '100/minute',    # 认证用户 100 次/分钟
        'login': '5/minute',     # 登录接口更严格
    },
}

# 自定义限流
from rest_framework.throttling import SimpleRateThrottle

class LoginRateThrottle(SimpleRateThrottle):
    scope = 'login'
    
    def get_cache_key(self, request, view):
        # 基于 IP 限流
        return self.get_ident(request)

class LoginView(APIView):
    throttle_classes = [LoginRateThrottle]
```

### 6.2 输入验证

```python
# 始终在序列化器中验证
class TaskSerializer(serializers.ModelSerializer):
    def validate_title(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError('标题至少 2 个字符')
        return value.strip()
    
    def validate_priority(self, value):
        if not 0 <= value <= 10:
            raise serializers.ValidationError('优先级必须在 0-10 之间')
        return value
```

### 6.3 敏感信息保护

```python
# ❌ 绝对不要做的事
SECRET_KEY = 'hardcoded-in-code'  # 不要硬编码密钥
print(user.password)              # 不要打印密码

# ✅ 使用环境变量
SECRET_KEY = os.getenv('SECRET_KEY')

# ✅ 序列化器排除敏感字段
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar']
        # 永远不包含 password
        
# ✅ 生产环境关闭 DEBUG
DEBUG = False  # 不暴露堆栈信息
```

---

## 七、安全检查清单

```
✅ 后端
  □ DEBUG = False（生产环境）
  □ SECRET_KEY 使用环境变量，足够随机
  □ ALLOWED_HOSTS 限制域名
  □ CORS 只允许你的前端域名
  □ HTTPS + HSTS
  □ Cookie Secure / HttpOnly / SameSite
  □ API 限流
  □ 输入验证和数据清洗
  □ 使用 ORM，不拼接 SQL
  □ 密码使用 Django 内置哈希（bcrypt）

✅ 前端
  □ 不信任用户输入，避免 dangerouslySetInnerHTML
  □ Token 存储安全（不放入 URL）
  □ 环境变量不含敏感信息（VITE_ 前缀变量会暴露到前端）
  □ HTTPS 下运行

✅ 基础设施
  □ 服务器防火墙
  □ SSH 密钥认证，禁用密码登录
  □ 数据库不暴露到公网
  □ Redis 设置密码
  □ Docker 使用非 root 用户
  □ 定期更新依赖（安全补丁）
```

---

## 八、练习

1. 运行 `python manage.py check --deploy`，修复所有安全警告
2. 配置 Django 安全设置（HTTPS、Cookie、安全头）
3. 为登录接口配置请求限流（5 次/分钟）
4. 检查所有序列化器，确保不暴露密码等敏感字段
5. 在 Nginx 中配置安全响应头
6. 对照安全检查清单逐项检查项目
