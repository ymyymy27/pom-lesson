> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第1课：OWASP Top 10 与安全编码

## 1. OWASP Top 10（2021）

| # | 漏洞 | 说明 | 防御 |
|---|------|------|------|
| A01 | 访问控制失效 | 越权访问他人数据 | RBAC、资源级权限检查 |
| A02 | 加密失败 | 明文传输/存储敏感数据 | TLS、AES、bcrypt |
| A03 | 注入 | SQL/命令/OS 注入 | 参数化查询、输入验证 |
| A04 | 不安全设计 | 架构层面缺少安全控制 | 威胁建模、安全 Review |
| A05 | 安全配置错误 | 默认密码、多余端口 | 配置审查、最小暴露 |
| A06 | 易受攻击组件 | 过时的依赖库 | 依赖扫描、及时升级 |
| A07 | 认证失败 | 弱密码、Session 固定 | MFA、Rate Limit |
| A08 | 数据完整性失败 | 不安全的反序列化 | 签名验证、白名单 |
| A09 | 日志监控失败 | 攻击发生无感知 | 集中日志、告警 |
| A10 | SSRF | 服务端伪造请求 | URL 白名单、网络隔离 |

---

## 2. 注入攻击与防御

### SQL 注入

```python
# ❌ 危险
query = f"SELECT * FROM users WHERE name = '{user_input}'"
# 输入：' OR '1'='1 → 返回所有用户

# ✅ 参数化查询
query = "SELECT * FROM users WHERE name = %s"
cursor.execute(query, (user_input,))

# ✅ ORM（Django/SQLAlchemy 默认参数化）
User.objects.filter(name=user_input)
```

### 命令注入

```python
# ❌ 危险
os.system(f"ping {host}")

# ✅ 使用库代替 shell
import subprocess
subprocess.run(["ping", "-c", "4", host], check=True)
```

---

## 3. XSS（跨站脚本）

### 三种类型

| 类型 | 存储 | 触发 |
|------|------|------|
| 存储型 | 数据库 | 其他用户访问页面 |
| 反射型 | URL 参数 | 受害者点击链接 |
| DOM 型 | 不经过服务器 | JS 直接操作 DOM |

### 防御

```python
# 后端：输出转义
from markupsafe import escape
return f"<p>{escape(user_comment)}</p>"

# 前端：避免 innerHTML
element.textContent = userInput  # ✅
element.innerHTML = userInput  # ❌

# CSP（Content Security Policy）Header
Content-Security-Policy: default-src 'self'; script-src 'self'
```

---

## 4. 敏感数据处理

```python
# 密码：永远 hash，不存明文
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# 验证
bcrypt.checkpw(password.encode(), hashed)

# API Key / Token：环境变量，不进 Git
import os
API_KEY = os.environ["API_KEY"]  # ✅
API_KEY = "sk-1234567890"         # ❌

# 日志：脱敏
logger.info(f"User {user_id} paid {mask_card(card_number)}")
# 输出：User 42 paid **** **** **** 1234
```

---

## 5. 依赖安全

```bash
# Python 依赖扫描
pip install pip-audit safety
pip-audit
safety check

# CI 中集成
# .github/workflows/security.yml
- name: Dependency audit
  run: pip-audit --strict
```

---

## 6. 安全编码 Checklist

```
输入：
  □ 所有用户输入都验证类型、长度、格式
  □ 使用参数化查询，禁止拼接 SQL
  □ 文件上传限制类型和大小

输出：
  □ HTML 输出转义
  □ 设置 CSP Header
  □ API 响应不包含堆栈信息

认证：
  □ 密码 bcrypt/argon2 hash
  □ Session 安全（HttpOnly、Secure、SameSite）
  □ 登录 Rate Limit

授权：
  □ 每个 API 都检查权限
  □ 资源级访问控制（不能改别人的数据）

配置：
  □ Debug 模式生产关闭
  □ 默认密码已修改
  □ 不必要的端口已关闭
  □ 密钥在环境变量/Secret Manager 中
```

---

## 7. 动手练习

1. 找出以下代码的安全问题并修复：
```python
@app.route("/search")
def search():
    q = request.args.get("q")
    results = db.execute(f"SELECT * FROM products WHERE name LIKE '%{q}%'")
    return render_template("results.html", query=q, results=results)
```

2. 为你的项目运行 `pip-audit`，处理发现的漏洞
3. 填写安全编码 Checklist，评估当前项目

---

## 附录：架构师安全设计（合并自原 02_security_for_architects）

### 安全架构评审 Checklist

```
认证：□ HTTPS □ JWT 短过期 □ Refresh Token HttpOnly □ MFA（管理员）
授权：□ 资源级权限 □ 防 IDOR □ 最小权限 □ 管理员操作审计
数据：□ 全链路 TLS □ at-rest 加密 □ PII 脱敏 □ 备份访问受控
输入：□ 参数化查询 □ 文件上传限制 □ SSRF 防护
基础设施：□ Secret 不在代码中 □ 最小权限 IAM □ 网络隔离 □ WAF
运维：□ 依赖扫描 □ 事件响应流程 □ 审计日志 ≥ 90 天
```

### 供应链安全

```
依赖：pip-audit / Dependabot / 锁定版本
容器：最小镜像、Trivy 扫描、非 root 运行
CI/CD：Secret 通过变量注入、保护 main 分支、cosign 签名镜像
```

### TaskFlow 威胁缓解示例

| 威胁 | 缓解 |
|------|------|
| IDOR | project membership 检查 |
| XSS | 输出编码 + CSP |
| Token 泄露 | 短过期 + HttpOnly Refresh |
| SSRF（Webhook） | URL 白名单 + 网络隔离 |

### 安全事件响应

```
发现 → containment（撤销 Token/封 IP）
     → eradication（修漏洞/轮换密钥）
     → recovery（验证修复/逐步上线）
     → lessons learned（Postmortem）
```

详见 [`learn-reliability/02_incident_response.md`](<../../02-部署与工程运维/可靠性/02-第2课故障响应与 Postmortem.md>)

---

**下一课** → [02_auth_and_identity.md](02-第2课认证授权与身份管理.md)
