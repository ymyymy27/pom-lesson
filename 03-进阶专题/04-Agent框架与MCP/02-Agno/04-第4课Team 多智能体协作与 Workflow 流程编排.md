> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第4课：Team 多智能体协作与 Workflow 流程编排

## 1. 何时用 Agent / Team / Workflow？

| 模式 | 适用场景 | 特点 |
|------|----------|------|
| **Agent** | 单一任务、一个角色 | 简单、快速 |
| **Team** | 需要分工、讨论、多角度 | LLM 协调多个 Agent |
| **Workflow** | 步骤固定、要并行/分支/循环 | 确定性流程，可预测 |

```
写一篇文章：
  Agent     → 一个「全能写手」搞定
  Team      → 调研员 + 写手 + 编辑 协作
  Workflow  → 1.采集 → 2.分析 → 3.写作 → 4.审核（固定流水线）
```

---

## 2. Team 多智能体

### 2.1 基本结构

```python
from agno.agent import Agent
from agno.team import Team

researcher = Agent(
    name="Researcher",
    model="openai:gpt-4o",
    instructions="负责搜集信息、列出要点，不写最终报告。",
)

writer = Agent(
    name="Writer",
    model="openai:gpt-4o",
    instructions="根据调研结果写简洁的中文报告。",
)

team = Team(
    name="Research Team",
    members=[researcher, writer],
    instructions="Researcher 先调研，Writer 再写报告。用中文输出。",
)

team.print_response("介绍 Agno 框架的核心特性", stream=True)
```

### 2.2 Team 工作流程

```
用户问题 → Team Leader（协调者）→ 分配给成员 Agent → 汇总结果 → 返回用户
```

Team 内部由模型决定调用哪个成员、何时切换，适合 **角色清晰、需要协作** 的任务。

### 2.3 设计成员 Agent 的技巧

| 原则 | 说明 |
|------|------|
| 职责单一 | 每个 Agent 只做一件事 |
| instructions 互斥 | 明确「谁做什么、不做什么」 |
| 统一语言 | Team instructions 指定输出语言 |

---

## 3. Workflow 流程编排

### 3.1 顺序 Workflow

步骤固定、按序执行：

```python
from agno.workflow import Workflow, Step

workflow = Workflow(
    name="Research Pipeline",
    steps=[
        Step(name="research", agent=researcher),
        Step(name="write", agent=writer),
    ],
)

workflow.print_response("写一份 Agno 学习路线", stream=True)
```

### 3.2 常见步骤类型

| 步骤 | 用途 | 示例 |
|------|------|------|
| `Step` | 单步执行 | 调用一个 Agent |
| `Parallel` | 并行 | 多路调研同时进行 |
| `Loop` | 循环 | 反复修改直到满意 |
| `Router` | 路由 | 按条件走不同分支 |
| `Condition` | 条件 | if/else 逻辑 |

### 3.3 Workflow vs Team

| 对比 | Team | Workflow |
|------|------|----------|
| 流程控制 | LLM 动态协调 | 开发者预定义 |
| 可预测性 | 较低 | 较高 |
| 适用 | 开放讨论、创意 | ETL、审批流、固定 pipeline |

---

## 4. 示例代码：research_team.py

`practice/research_team.py` 演示 **Team 模式**：

- `Researcher`：列出 Agno 核心概念
- `Writer`：整理成结构化 Markdown 报告

运行：

```powershell
python research_team.py
```

---

## 5. 进阶：带 Session 的 Team

```python
from agno.db.sqlite import SqliteDb

team = Team(
    name="Research Team",
    members=[researcher, writer],
    db=SqliteDb(db_file="team.db"),
    add_history_to_context=True,
)

team.print_response("继续上次的话题", session_id="session-001", stream=True)
```

Team 和 Agent 一样支持 `db`、`session_id`、Tracing 等。

---

## 6. Human-in-the-Loop（了解）

生产环境中，敏感操作（发邮件、删文件）可要求人工确认：

- [Human-in-the-Loop 示例](https://docs.agno.com/examples/basics/human-in-the-loop)
- Workflow 中支持 `confirmation` 步骤

本课程暂不展开，AgentOS 阶段可继续学习。

---

## 7. 架构示意

```
                    ┌─────────────┐
                    │   用户输入   │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
      ┌─────────┐    ┌──────────┐   ┌───────────┐
      │  Agent  │    │   Team   │   │ Workflow  │
      └────┬────┘    └────┬─────┘   └─────┬─────┘
           │              │               │
           └──────────────┼───────────────┘
                          ▼
                   ┌─────────────┐
                   │ Tools / KB  │
                   └─────────────┘
```

---

## 动手练习

### 练习 1：三角色 Team

增加 `Editor` Agent，负责润色 Writer 的输出。

### 练习 2：顺序 Workflow

把 Team 改成 Workflow：Step(research) → Step(write)，对比输出差异。

### 练习 3：分工 instructions

故意让两个 Agent instructions 冲突，观察 Team 协调行为，再修正 instructions。

---

## 验收标准

- [ ] 能创建含 2+ 成员的 Team 并运行
- [ ] 能解释 Team 与 Workflow 的选型差异
- [ ] `research_team.py` 输出完整报告
- [ ] 能写出带 `Step` 的简单 Workflow

---

## 下一课预告

第5课将 Agent 部署为 **AgentOS 服务**：REST API、Tracing、Web UI、Docker 入门。

**延伸阅读：**

- [Multi-Agent Team 示例](https://docs.agno.com/examples/basics/multi-agent-team)
- [Sequential Workflow 示例](https://docs.agno.com/examples/basics/sequential-workflow)
- [Workflow Examples](https://docs.agno.com/examples/agent-os/workflow/overview)
