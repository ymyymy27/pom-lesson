# 安全架构全景

## 1. 安全架构是什么？

### 一句话解释

**安全不是功能上线后的补丁，而是架构设计的一等公民** —— 在系统设计阶段就识别威胁、选择防护。

### CIA 三要素

```
Confidentiality（机密性）— 只有授权者能访问数据
Integrity（完整性）    — 数据不被未授权篡改
Availability（可用性）  — 授权用户能正常使用（与可靠性交叉）
```

### 安全左移（Shift Left）

```
❌ 传统：开发 → 测试 → 上线 → 安全团队渗透测试 → 紧急修
✅ 左移：需求阶段威胁建模 → 设计阶段安全评审 → 开发阶段 SAST → CI 安全扫描
```

---

## 2. 威胁建模（STRIDE）

| 威胁 | 含义 | 示例 | 缓解 |
|------|------|------|------|
| **S**poofing | 伪造身份 | 冒充 admin 调用 API | 强认证、MFA |
| **T**ampering | 篡改数据 | 修改 HTTP 请求中的 price | HTTPS、签名、校验 |
| **R**epudiation | 否认操作 | 用户否认下过单 | 审计日志 |
| **I**nformation Disclosure | 信息泄露 | IDOR 看到他人订单 | 授权检查、加密 |
| **D**enial of Service | 拒绝服务 | DDoS、资源耗尽 | 限流、WAF、CDN |
| **E**levation of Privilege | 权限提升 | 普通用户变 admin | RBAC、最小权限 |

### 威胁建模流程

```
1. 画数据流图（DFD）：组件 + 数据流向 + 信任边界
2. 每个组件/数据流上应用 STRIDE
3. 评估风险（概率 × 影响）
4. 选择缓解措施
5. 记录到 ADR / 安全设计文档
```

---

## 3. 安全架构层次

```
┌─────────────────────────────────────────┐
│  L4 组织与流程：安全培训、Incident Response│
├─────────────────────────────────────────┤
│  L3 应用安全：认证、授权、输入校验、CSRF  │
├─────────────────────────────────────────┤
│  L2 数据安全：加密、脱敏、备份、访问审计  │
├─────────────────────────────────────────┤
│  L1 基础设施：网络隔离、WAF、DDoS 防护   │
├─────────────────────────────────────────┤
│  L0 物理/云：数据中心、IAM、VPC、Security Group│
└─────────────────────────────────────────┘
```

---

## 4. 认证 vs 授权

```
认证（Authentication）— 你是谁？
  登录、JWT、OAuth2、API Key、MFA

授权（Authorization）— 你能做什么？
  RBAC、ABAC、资源级权限、Scope

常见错误：认证通过 = 放行一切
正确做法：每个请求都检查 认证 + 授权
```

---

## 5. 常见攻击面

| 攻击面 | 威胁 | 架构层缓解 |
|--------|------|-----------|
| API | 注入、越权、枚举 | 输入校验、RBAC、Rate Limit |
| Web | XSS、CSRF、Clickjacking | CSP、SameSite Cookie、Token |
| 数据 | 泄露、勒索 | 加密 at-rest/in-transit、备份 |
| 依赖 | 供应链攻击 | SBOM、Dependabot、镜像扫描 |
| 内部 |  insider threat | 最小权限、审计、零信任 |
| 配置 | 默认密码、公开 Bucket | IaC 扫描、Secret 管理 |

---

## 6. 零信任（Zero Trust）原则

```
旧模型：内网 = 可信，外网 = 不可信
新模型：永不信任，始终验证

实践：
  - 每个服务间调用也要认证（mTLS / Service Token）
  - 最小权限 IAM
  - 网络微隔离（Micro-segmentation）
  - 持续验证，非一次登录永久信任
```

---

## 7. 密钥与 Secret 管理

```
❌ 密钥硬编码在代码 / 提交到 Git
❌ .env 文件上传到仓库
❌ 所有环境共用同一密钥

✅ Secret Manager（AWS SM、Vault、K8s Secrets）
✅ 环境隔离（dev/staging/prod 不同密钥）
✅ 自动轮换
✅ CI 中注入，不持久化在镜像里
```

---

## 8. 安全与架构决策

安全相关的 ADR 示例：

```markdown
# ADR-007: 采用 JWT + Refresh Token 认证方案

## 背景
TaskFlow 需要支持 Web + Mobile + API 集成

## 决策
Access Token（JWT, 15min）+ Refresh Token（HttpOnly Cookie, 7d）

## 考虑的选项
- Session Cookie：简单但不适合 Mobile/API
- JWT only：无法撤销，泄露风险大
- OAuth2 PKCE：适合第三方登录

## 后果
- 正面：无状态、跨端一致
- 负面：需要 Token 撤销机制（黑名单/短过期）
- 风险：XSS 窃取 Token → 配合 CSP + HttpOnly
```

---

## 9. 学习路线

```
00_security_overview.md（本文）
        ↓
01_auth_and_access_control.md — 认证与授权
        ↓
02_security_for_architects.md — OWASP 与架构评审
        ↓
learn-api-design/ — API 层安全实践
```

---

## 10. 自检清单

- [ ] 能解释 CIA 三要素
- [ ] 会用 STRIDE 做基础威胁建模
- [ ] 区分认证与授权
- [ ] 知道安全左移的含义
- [ ] 了解 Secret 管理最佳实践

---

**下一课** → [01_auth_and_access_control.md](01_auth_and_access_control.md)
