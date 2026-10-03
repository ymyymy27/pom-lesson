# 第3课：威胁建模与安全测试

## 1. 威胁建模流程

```
1. 画数据流图（DFD）
   标注：外部实体、进程、数据存储、数据流

2. 识别威胁（STRIDE 逐类检查）
   每个组件、每条数据流都问：
   - 能被伪造吗？（Spoofing）
   - 能被篡改吗？（Tampering）
   - 能被否认吗？（Repudiation）
   - 会泄露吗？（Info Disclosure）
   - 能被拒绝吗？（DoS）
   - 能被提权吗？（Elevation）

3. 评估风险（概率 × 影响）
4. 制定缓解措施
5. 验证措施有效性
```

### TaskFlow 威胁建模示例

```
威胁：用户 A 通过修改 task_id 访问用户 B 的任务
  STRIDE：Elevation of Privilege
  风险：高（数据泄露）
  缓解：API 层检查 task.project.members 包含 current_user
  验证：编写越权访问测试用例

威胁：攻击者暴力破解登录
  STRIDE：Spoofing
  风险：中
  缓解：Rate Limit（5 次/分钟）+ 账户锁定 + MFA
  验证：自动化测试 Rate Limit 生效
```

---

## 2. 安全测试

### SAST（Static Application Security Testing）

```
分析源代码，不运行程序

工具：
  Python: Bandit, Semgrep
  JS/TS: ESLint security plugins
  通用: SonarQube, CodeQL

集成到 CI：
  - 每次 PR 自动扫描
  - 高危漏洞阻止合并
```

```bash
# Bandit 示例
pip install bandit
bandit -r ./app -ll  # 只报告 medium 及以上
```

### DAST（Dynamic Application Security Testing）

```
对运行中的应用发送攻击 payload

工具：OWASP ZAP, Burp Suite

场景：
  - Staging 环境定期扫描
  - 发版前的安全回归
```

### 渗透测试

```
人工模拟攻击者，全面评估安全性

范围：
  - 网络层（端口扫描、防火墙）
  - 应用层（OWASP Top 10）
  - 社会工程（钓鱼测试，可选）

频率：至少每年一次，重大变更后
```

---

## 3. 安全审计日志

```python
@dataclass
class AuditLog:
    timestamp: datetime
    user_id: int
    action: str          # "task.delete", "user.login"
    resource_type: str   # "task", "user"
    resource_id: str
    ip_address: str
    user_agent: str
    result: str          # "success" / "denied"
    details: dict        # 变更前后值

# 必须记录的操作：
# - 登录/登出（成功和失败）
# - 权限变更
# - 敏感数据访问
# - 数据修改和删除
# - 配置变更
# - 管理员操作
```

---

## 4. 密钥管理

```
❌ 密钥硬编码在代码/Git 中
❌ 所有环境用同一个密钥
❌ 密钥永不过期

✅ Secret Manager（AWS Secrets Manager / Vault / K8s Secret）
✅ 环境隔离（dev/staging/prod 不同密钥）
✅ 定期轮换（90 天）
✅ 最小权限（App 只能读自己的 Secret）
```

---

## 5. 动手练习

1. 用 STRIDE 为 TaskFlow 的「文件上传」功能做威胁建模
2. 运行 Bandit 扫描一个 Python 项目，修复发现的问题
3. 设计 AuditLog  schema，列出 TaskFlow 必须记录的 10 种操作

---

## 6. 自检清单

- [ ] 会用 STRIDE 识别威胁
- [ ] 理解 SAST vs DAST 的区别和用途
- [ ] 知道安全审计日志应记录什么
- [ ] 理解密钥管理的最佳实践

---

**下一模块** → [learn-api-design/](../learn-api-design/)：API 设计
