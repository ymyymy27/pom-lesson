# 第3课：协作工作流

## 1. Git 工作流概览

不同团队规模和使用场景，选择不同的 Git 工作流。

```
                Git 工作流光谱
  简单 ◀────────────────────────────▶ 复杂

  GitHub Flow    Git Flow    GitLab Flow    Trunk-Based
  (小团队)      (发布驱动)   (环境驱动)      (大团队/CD)
```

---

## 2. GitHub Flow

### 流程

```
main ──────●────────●────────●────── (始终可部署)
            \      /          \
             ●────●            ●──── (PR + Review + CI)
           feature/login    fix/bug-123
```

### 步骤

1. 从 `main` 创建分支
2. 提交改动，推送到远程
3. 创建 Pull Request (PR)
4. Code Review + CI 通过
5. 合并到 `main`
6. 自动部署

### 规则

- `main` 始终可部署
- 分支生命短（1–3 天）
- 所有改动通过 PR
- CI 必须通过才能合并

**适合：** 持续部署的 Web 应用、小中型团队。

---

## 3. Git Flow

### 分支模型

```
main     ──────●─────────────────●────────── (生产版本)
                \               /
release  ────────●─────●───────●
                  \   /       /
develop  ──●──●──●──●──●──●──●──●── (集成分支)
            \    /      \    /
feature    ──●──●        ●──●
                         \  /
hotfix   ──────────────────●── (紧急修复)
```

| 分支 | 用途 | 从哪创建 | 合并到哪 |
|------|------|---------|---------|
| main | 生产代码 | — | — |
| develop | 集成开发 | main | — |
| feature/* | 新功能 | develop | develop |
| release/* | 发布准备 | develop | main + develop |
| hotfix/* | 紧急修复 | main | main + develop |

**适合：** 有明确发布周期的项目（如移动端 App、企业软件）。

**缺点：** 复杂，长期分支合并痛苦。很多团队已简化或弃用。

---

## 4. Trunk-Based Development

### 核心

```
main/trunk ──●──●──●──●──●──●──●── (所有人直接/短分支合入)
              \ /  \ /  \ /
               ●    ●    ●         (短生命周期分支，< 1 天)
```

### 规则

- 所有开发基于 trunk（main）
- 分支生命 < 1 天
- Feature Flag 控制未完成的功能
- 频繁集成（至少每天）

**适合：** 大团队、持续部署、Google/Facebook 风格。

**关键配套：** 强大的 CI、Feature Flag、良好的测试覆盖。

---

## 5. 工作流选型

| 场景 | 推荐 |
|------|------|
| SaaS Web 应用 + CD | GitHub Flow 或 Trunk-Based |
| 移动端 App（审核发布） | Git Flow 或 GitLab Flow |
| 开源项目 | GitHub Flow + Fork |
| 大团队 + 微服务 | Trunk-Based + Feature Flag |
| 个人/学习项目 | GitHub Flow（最简单） |

---

## 6. Code Review 最佳实践

### 6.1 PR 规范

```markdown
## 改动说明
修复用户登录时 Token 过期未刷新的问题。

## 改动类型
- [x] Bug 修复
- [ ] 新功能
- [ ] 重构

## 测试
- [x] 新增单元测试 test_token_refresh
- [x] 本地手动验证登录流程

## 截图（UI 改动时）
[before/after]

## 关联 Issue
Closes #123
```

### 6.2 Review 关注点

**必须改（Blocker）：**
- 逻辑 Bug
- 安全漏洞
- 无测试的关键路径
- 破坏性变更无文档

**建议改（Non-blocker）：**
- 命名改进
- 更简洁的实现
- 额外测试覆盖

### 6.3 Review 礼仪

**审查者：**
```
❌ 「这代码写得太烂了」
✅ 「这里的错误处理可以考虑捕获 ConnectionError 并重试」

❌ 「为什么不用 X？」
✅ 「考虑过用 X 吗？优点是...，缺点是...」
```

**提交者：**
- 不要 force push 已有人 Review 的分支（除非协商）
- 逐条回复 Review 意见
- 小 PR 更容易 Review（< 400 行）

---

## 7. 结对编程（Pair Programming）

### 两种角色

| 角色 | 职责 |
|------|------|
| Driver（驾驶员） | 写代码 |
| Navigator（导航员） | 思考方向、审查、查文档 |

**定期交换角色**（如每 25 分钟 Pomodoro）。

### 模式

| 模式 | 说明 |
|------|------|
| 传统结对 | 两人一台电脑 |
| 远程结对 | VS Code Live Share, Tuple |
| 强结对 | 所有代码都结对（Extreme Programming） |
| 轻结对 | 复杂任务结对，简单任务 solo |

### 收益与成本

| 收益 | 成本 |
|------|------|
| 即时 Review | 两人时间 |
| 知识共享 | 需要默契 |
| 减少 Bug | 不一定适合所有任务 |
| 新人快速成长 | |

**适合结对：** 复杂逻辑、新技术探索、Bug 排查、新人 onboarding  
**不适合：** 简单 CRUD、需要深度专注的设计思考

---

## 8. 异步协作

### 8.1 文档驱动

```
设计讨论 → 写设计文档 → 异步 Review → 确认后开始编码
```

**工具：** Notion, Confluence, GitHub Wiki, ADR

### 8.2 有效沟通

| 场景 | 方式 |
|------|------|
| 紧急问题 | 即时消息 / 电话 |
| 技术讨论 | PR Comment / Issue |
| 决策记录 | ADR / 设计文档 |
| 进度同步 | Daily Standup / 看板 |
| 知识分享 | Wiki / Tech Talk |

### 8.3 远程协作要点

- 重叠工作时间（至少 2–4 小时）
- 书面优先（减少「口头说了但忘了」）
- 视频开启建立信任（可选但推荐）
- 时区标注：`2026-07-30 14:00 UTC+8`

---

## 9. 分支命名规范

```
feature/user-authentication
fix/login-token-expiry
hotfix/payment-crash
refactor/extract-user-service
docs/api-reference-update
chore/upgrade-dependencies
```

**格式：** `{type}/{short-description}`

---

## 10. 动手练习

### 练习 1：模拟 PR Review

Review 以下代码片段，列出至少 3 条意见：

```python
def get_users(status):
    users = []
    conn = sqlite3.connect('db.sqlite')
    if status == 'active':
        rows = conn.execute("SELECT * FROM users WHERE status='active'")
    elif status == 'inactive':
        rows = conn.execute("SELECT * FROM users WHERE status='inactive'")
    else:
        rows = conn.execute("SELECT * FROM users")
    for row in rows:
        users.append({'id': row[0], 'name': row[1]})
    return users
```

<details>
<summary>参考答案</summary>

1. SQL 注入风险 — 应使用参数化查询
2. 重复代码 — 三个分支结构相同，可合并
3. 数据库连接未关闭 — 应使用 context manager
4. `SELECT *` — 应指定需要的列
5. 魔法索引 `row[0]`, `row[1]` — 应用命名元组或 ORM
6. 无错误处理

</details>

### 练习 2：选择工作流

| 团队 | 项目 | 发布频率 | 推荐工作流 |
|------|------|---------|-----------|
| 3 人 | SaaS | 每天多次 | ? |
| 20 人 | 银行系统 | 每季度 | ? |
| 1 人 | 个人博客 | 随时 | ? |

<details>
<summary>参考答案</summary>

1. GitHub Flow 或 Trunk-Based
2. Git Flow（严格 release 流程 + 合规）
3. GitHub Flow（最简单）

</details>

---

## 11. 自检清单

- [ ] 能描述 GitHub Flow 和 Git Flow 的流程
- [ ] 能根据场景选择合适的工作流
- [ ] 知道 Code Review 的关注点和礼仪
- [ ] 理解结对编程的角色和适用场景
- [ ] 知道分支命名规范

---

## 12. 延伸阅读

- 关联：`learn-tools/learn-git/05_git_workflow.md` — Git 实操
- GitHub Flow 原文：guides.github.com/introduction/flow
- 下一课：`04_technical_debt_and_estimation.md`
