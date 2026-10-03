# 第2课：架构师的安全设计

## 1. OWASP Top 10（2021）架构视角

| # | 风险 | 架构层缓解 |
|---|------|-----------|
| A01 | Broken Access Control | RBAC + 资源级授权 + 自动化测试 |
| A02 | Cryptographic Failures | TLS 1.3、加密 at-rest、密钥管理 |
| A03 | Injection | 参数化查询、ORM、输入校验、WAF |
| A04 | Insecure Design | 威胁建模、安全 ADR、安全评审 |
| A05 | Security Misconfiguration | IaC 扫描、Hardening 基线、最小权限 |
| A06 | Vulnerable Components | Dependabot、SBOM、镜像扫描 |
| A07 | Auth Failures | MFA、强密码策略、Session 管理 |
| A08 | Software Integrity Failures | 签名验证、CI/CD 安全、供应链 |
| A09 | Logging Failures | 审计日志、SIEM、告警 |
| A10 | SSRF | URL 白名单、网络隔离、metadata 保护 |

---

## 2. 数据加密

### 传输中（In Transit）

```
客户端 ←── TLS 1.3 ──→ LB ←── TLS ──→ Service ←── TLS ──→ DB

强制 HTTPS（HSTS）
内部服务间：mTLS 或 Service Mesh
禁止：明文 HTTP 传输密码、Token、PII
```

### 静态（At Rest）

```
数据库加密：
  云厂商透明加密（AWS RDS encryption）
  应用层字段加密（PII、信用卡号）

文件存储：
  S3 SSE-S3 / SSE-KMS
  敏感附件额外应用层加密

密钥管理：
  数据密钥（DEK）加密数据
  主密钥（KEK）在 KMS/Vault 中管理 DEK
```

### 什么时候应用层加密？

```
✅ 极敏感字段：SSN、信用卡、医疗记录
✅ 合规要求：即使 DBA 也不能看明文
✅ 多租户强隔离

❌ 普通业务字段（增加复杂度，搜索困难）
```

---

## 3. 输入校验与输出编码

### 输入校验（永远不要信任客户端）

```python
from pydantic import BaseModel, Field, validator

class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    priority: str = Field("medium", pattern="^(low|medium|high)$")

    @validator("title")
    def sanitize_title(cls, v):
        return v.strip()
```

### 防 SQL 注入

```python
# ❌ 拼接 SQL
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")

# ✅ 参数化
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# ✅ ORM
User.objects.filter(email=email)
```

### 防 XSS

```
Stored XSS：用户输入存入 DB → 展示给其他用户
  缓解：输出 HTML 编码、CSP Header

Reflected XSS：恶意 URL 参数反射到页面
  缓解：编码 + CSP

Content-Security-Policy:
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
```

---

## 4. 审计日志

### 必须记录的事件

```
认证：登录成功/失败、登出、密码修改、MFA 变更
授权：权限变更、角色分配
数据：敏感数据访问、批量导出、删除
管理：配置变更、API Key 创建/撤销
```

### 日志格式

```json
{
  "timestamp": "2026-07-30T10:00:00Z",
  "event": "task.deleted",
  "actor": { "user_id": "user_abc", "ip": "1.2.3.4" },
  "resource": { "type": "task", "id": "task_xyz", "project_id": "proj_123" },
  "result": "success",
  "request_id": "req_789"
}
```

**注意：** 日志中不记录密码、Token、完整信用卡号。

---

## 5. 安全架构评审 Checklist

```
认证：
  □ 所有 API 默认需认证（除公开 endpoint）？
  □ Token 有过期机制？
  □ 支持 MFA（至少管理员）？
  □ 密码策略足够强？

授权：
  □ 每个操作有资源级权限检查？
  □ 防 IDOR（不能通过改 ID 访问他人数据）？
  □ 最小权限原则？
  □ 管理员操作有额外审计？

数据：
  □ 传输全链路 TLS？
  □ 敏感数据 at-rest 加密？
  □ PII 有脱敏/匿名化策略？
  □ 备份加密且访问受控？

输入：
  □ 所有外部输入有校验？
  □ SQL 参数化 / ORM？
  □ 文件上传有类型/大小限制？
  □ SSRF 防护（URL 白名单）？

基础设施：
  □ Secret 不在代码/镜像中？
  □ 最小权限 IAM？
  □ 网络隔离（Public/Private Subnet）？
  □ WAF / DDoS 防护？

运维：
  □ 依赖漏洞扫描（CI）？
  □ 安全事件响应流程？
  □ 审计日志保留 ≥ 90 天？
  □ 定期渗透测试？
```

---

## 6. 供应链安全

```
依赖管理：
  pip/npm audit、Dependabot、Snyk
  锁定版本（requirements.lock / package-lock.json）

容器安全：
  最小基础镜像（distroless/alpine）
  镜像扫描（Trivy、Grype）
  非 root 运行

CI/CD 安全：
  Secret 通过 CI 变量注入
  Pipeline 权限最小化
  签名镜像（cosign）
  保护 main 分支（Require Review + CI pass）
```

---

## 7. TaskFlow 安全设计示例

| 威胁 | 场景 | 缓解 |
|------|------|------|
| IDOR | 改 task_id 看他人任务 | project membership 检查 |
| XSS | 任务标题含 `<script>` | 输出编码 + CSP |
| CSRF | 伪造删除请求 | SameSite Cookie + CSRF Token |
| 暴力破解 | 撞库登录 | 限流 + 账户锁定 + MFA |
| 数据泄露 | DB 备份被盗 | at-rest 加密 + 备份访问控制 |
| Token 泄露 | XSS 偷 JWT | 短过期 + HttpOnly Refresh + CSP |
| 文件上传 | 上传恶意文件 | 类型白名单 + 病毒扫描 + 独立域名 |
| SSRF | Webhook URL 指向内网 | URL 白名单 + 网络隔离 |

---

## 8. 安全 Incident 响应

```
发现安全事件
    ↓
 containment（隔离：撤销 Token、封 IP、下线服务）
    ↓
 eradication（清除：修漏洞、轮换密钥）
    ↓
 recovery（恢复：验证修复、逐步上线）
    ↓
 lessons learned（Postmortem + 改进）

与 learn-reliability/02_incident_response.md 流程一致
安全事件通常是 P0/P1
```

---

## 9. 动手练习

1. 用 STRIDE 对 TaskFlow「文件附件上传」做威胁建模
2. 填写安全架构评审 Checklist（针对自己的项目）
3. 设计 TaskFlow 审计日志 schema（至少 10 种 event）
4. 为一个 OWASP Top 10 风险写安全 ADR

---

## 10. 自检清单

- [ ] 了解 OWASP Top 10 及架构层缓解
- [ ] 能设计传输加密和静态加密策略
- [ ] 知道输入校验和输出编码的原则
- [ ] 会用安全架构评审 Checklist
- [ ] 理解供应链安全基本实践
- [ ] 能设计审计日志格式

---

**恭喜完成安全架构模块！** → 返回 [`README.md`](README.md) 或继续 [`projects/capstone_taskflow.md`](../projects/capstone_taskflow.md)
