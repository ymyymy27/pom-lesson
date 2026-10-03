# 第5课：平台工程与 AI 辅助开发

> 2025–2026 行业趋势补充课  
> 前置：[`02_devops_and_cicd.md`](02_devops_and_cicd.md)

## 1. 平台工程是什么？

### 一句话解释

**平台工程（Platform Engineering）是构建内部开发者平台（IDP），让产品团队自助使用标准化基础设施、CI/CD 和工具链** —— 把「每个团队自己搭一套」变成「平台团队搭一次、全员复用」。

### 与 DevOps 的关系

```
DevOps          →  文化 + 实践：开发运维协作
Platform Eng    →  产品化落地：IDP 作为内部产品
```

| 维度 | DevOps | 平台工程 |
|------|--------|----------|
| 焦点 | 流程与文化 | 内部平台产品 |
| 交付物 | 流水线、自动化 | 自助门户、Golden Path |
| 用户 | 开发 + 运维 | 开发者（内部客户） |
| 2026 驱动力 | 持续交付 | **消化 AI 加速产出的代码洪峰** |

> Gartner 预测：2026 年底约 80% 软件工程组织将拥有专职平台工程团队。

---

## 2. 内部开发者平台（IDP）核心能力

```
┌─────────────────────────────────────────────────────────┐
│                    Internal Developer Platform             │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│  环境自助    │  CI/CD 模板  │  可观测性    │  安全与合规      │
│  dev/staging│  构建/测试/部署│  日志/指标/追踪│  密钥/策略/审计  │
├─────────────┴─────────────┴─────────────┴─────────────────┤
│              Golden Path（推荐默认路径）                    │
│   「新建微服务」→ 模板脚手架 → 自动注册监控 → 一键部署       │
└─────────────────────────────────────────────────────────┘
```

### Golden Path 示例（TaskFlow）

```yaml
# 平台提供的 service-template
name: task-service
template: python-fastapi-v1
includes:
  - dockerfile
  - github-actions-ci
  - prometheus-metrics
  - opentelemetry-tracing
  - rbac-policy
```

开发者只需填业务逻辑，基础设施由平台模板保证一致。

---

## 3. 为什么 2026 平台成熟度决定 AI 成功率

Perforce 2026 平台工程报告显示：

| 指标 | 平台成熟组织 | 平台不成熟组织 |
|------|-------------|---------------|
| 认为平台对 AI 成功关键 | 73% | 44% |
| AI 工作流完全自治 | 44% | 26% |
| 对 AI 输出高置信度 | 81% | 48% |
| 治理自动化成熟 | 79% | 14% |

**结论：** AI 编码 Agent 让代码产出加速，但 CI/CD、测试、部署、审计若跟不上，瓶颈会从「写代码」转移到「验证与上线」。平台工程是 AI 时代的「泄洪道」。

---

## 4. AI 辅助开发生态（2025–2026）

### 工具光谱

```
代码补全          →  Copilot、Cursor Tab
对话式辅助        →  ChatGPT、Claude Code
自主 Agent        →  多文件修改、测试、PR
多 Agent 编排     →  规划 Agent + 编码 Agent + Review Agent
```

### 工程师的新角色

| 旧模式 | 新模式 |
|--------|--------|
| 手写每一行 | **定义意图 + 审查 diff** |
| 调试语法错误 | **调试系统行为与边界条件** |
| 个人生产力 | **团队 Golden Path + AI 治理** |

### Delegation Gap（委派鸿沟）

行业观察：约 60% 开发者使用 AI 辅助，但不足 20% 将完整任务委派给 Agent。原因往往是：

- 缺少自动化测试门禁
- 缺少可回滚的部署路径
- 缺少对 AI 生成代码的安全扫描

→ 这三项正是平台工程要解决的。

---

## 5. Policy-as-Code 与 AI 治理

平台团队 increasingly 将治理编码为软件：

```python
# 示例：PR 合并门禁策略（伪代码）
merge_policy = {
    "required_checks": ["unit_tests", "sast_scan", "dependency_audit"],
    "ai_generated_code": {
        "require_human_review": True,
        "block_secrets_in_diff": True,
        "max_files_without_tests": 5,
    },
}
```

**2026 最佳实践：**

1. AI 生成的 PR 必须过与传统代码相同（或更严）的 CI 门禁
2. 审计日志记录：哪些变更是 AI 辅助产生
3. 密钥/PII 扫描集成到 PR 阶段
4. 平台提供「AI-safe 沙箱环境」供 Agent 试跑

---

## 6. Team Topologies 与平台团队

| 团队类型 | 职责 | 与平台关系 |
|----------|------|-----------|
| Stream-aligned | 交付业务功能 | IDP 的主要用户 |
| Platform | 提供 IDP 能力 | 服务 Stream 团队 |
| Enabling | 临时赋能、培训 | 推广 Golden Path |
| Complicated-subsystem | 算法/内核等专家域 | 平台集成其能力 |

```
        Stream Team A ──┐
        Stream Team B ──┼──→ Platform Team ──→ IDP
        Stream Team C ──┘         │
                                  ↓
                          CI/CD · K8s · Observability
```

---

## 7. 动手练习

1. **盘点现状**：列出你当前项目的「每个新服务需要手动配置的事项」
2. **设计 Golden Path**：选 TaskFlow 的一个新微服务，列出平台应提供的 5 项默认能力
3. **AI 门禁设计**：写 3 条 PR 策略，确保 AI 辅助代码不会绕过质量检查
4. **ADR 草稿**：「我们是否引入 IDP？」—— 列出 3 个支持理由和 2 个风险

---

## 8. 自检清单

- [ ] 能解释平台工程与 DevOps 的区别
- [ ] 能描述 IDP 的四类核心能力
- [ ] 理解为何 AI 加速开发使平台工程变得不可回避
- [ ] 能列举 AI 辅助开发的 3 层成熟度
- [ ] 知道 Policy-as-Code 在 AI 治理中的作用

---

## 参考

- [State of DevOps Report: Platform Engineering 2026](https://www.puppet.com/resources/2026-state-of-platform-engineering) — Puppet/Perforce
- 《Team Topologies》— Skelton & Pais
- 《Accelerate》— Forsgren, Humble, Kim
