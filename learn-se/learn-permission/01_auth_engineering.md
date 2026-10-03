# 第1课：认证工程：登录、会话与 Token

## 1. 一句话解释

认证是确认"你是谁"的过程，工程上要解决三个问题：凭据怎么安全存储、身份怎么在请求间传递、会话怎么管理（过期、刷新、撤销）。

## 2. 类比

机场安检：

```
出示证件（凭据）→ 安检确认身份（验证）→ 盖章登机牌（会话凭证）→ 之后登机只查登机牌
```

登机牌会过期，丢了可以作废重办——对应 Token 的过期与撤销。

## 3. 核心知识

### 3.1 认证 vs 授权

```
认证（Authentication）：你是谁？ → 登录
授权（Authorization）：你能做什么？ → 权限检查（第2课）
```

### 3.2 凭据安全存储

- 密码绝不存明文，也不存可逆加密
- 使用自适应哈希算法：Argon2、bcrypt、scrypt（自带盐）
- 登录接口要做限流/失败锁定，防止暴力破解

```python
# 伪代码：以 bcrypt 为例
import bcrypt

hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
ok = bcrypt.checkpw(password.encode(), hashed)
```

### 3.3 Session vs JWT

| 维度 | Session | JWT |
|------|---------|-----|
| 存储 | 服务端（Redis/DB） | 客户端（Header/Cookie） |
| 扩展 | 需要共享 Session Store | 无状态，水平扩展容易 |
| 撤销 | 立即（删 Session） | 困难（需黑名单或短过期） |
| 失效 | 服务端可控 | 只能等过期，除非额外机制 |
| 适用 | 传统 Web、强管控后台 | SPA、移动端、微服务 |

常见做法是**两者结合**：Access Token（JWT，短，15-30 分钟）+ Refresh Token（服务端可撤销，长，7-30 天）。

### 3.4 登录流程

```
客户端 → POST /auth/login（用户名 + 密码）
服务端 → 校验凭据
服务端 → 签发 Access Token（15 分钟） + Refresh Token（7 天，可撤销）
客户端 → 请求携带 Access Token
服务端 → 中间件校验签名、过期时间、签发方 → 注入当前用户
Access Token 过期 → 用 Refresh Token 换新（轮换，旧 Refresh 作废）
```

### 3.5 企业级扩展

| 方案 | 解决什么 | 何时引入 |
|------|----------|----------|
| OAuth2 / OIDC | 第三方登录、授权第三方访问 | 有外部账号体系或开放平台时 |
| SSO（单点登录） | 多系统一次登录 | 企业内部多系统 |
| MFA（多因素认证） | 弱密码风险 | 管理后台、高权限操作 |

## 4. 常见坑

- JWT 密钥泄露，或使用 `alg: none` 绕过签名
- Payload 放敏感信息（Base64 可读，不是加密）
- 只有 Access Token 没有刷新机制，体验差或无法续期
- Token 存 localStorage，被 XSS 直接偷走（优先 HttpOnly Cookie 或内存）
- 没有 `jti`/黑名单/版本号，Token 一旦泄露无法撤销

## 5. 动手练习

设计一个认证中间件伪代码：解析 Token、校验、注入当前用户与租户。

```python
def auth_middleware(request, next):
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    payload = verify_jwt(token, secret=SECRET, issuer="multitask", audience="web")
    if payload.get("type") != "access":
        raise Unauthorized("必须使用 Access Token")
    request.user_id = payload["sub"]
    request.tenant_id = payload.get("tenant_id")
    return next(request)
```

追问：如果要求"用户改密码后所有旧 Token 立即失效"，你会怎么做？

提示：在用户表加 `password_version`，登录时写进 JWT；中间件每次比对当前版本，不匹配即拒绝。

## 6. 自检清单

- [ ] 能说出 Session 与 JWT 各自的优缺点和适用场景
- [ ] 知道 Refresh Token 为什么必须可撤销，以及轮换的意义
- [ ] 能解释为什么 JWT Payload 不能放密码等敏感信息
