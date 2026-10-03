# CrewAI 多 Agent 协作

> stage-09 补充课 — 多 Agent 框架对比  
> 前置：[`learn-langgraph/`](../learn-langgraph/)、[`08-agent-evaluation-and-harness.md`](../08-agent-evaluation-and-harness.md)

## 1. 多 Agent 框架对比（2026）

| 框架 | 模型 | 适用 | 2026 状态 |
|------|------|------|-----------|
| **LangGraph** | 图状态机 | 复杂流程、合规、Human-in-the-Loop | 生产首选 |
| **CrewAI** | 角色化团队 | 快速原型、研究/内容生成 | 活跃 |
| **AutoGen** | 对话式 | 实验、对话 Agent | ⚠️ 维护模式 |
| **Agno** | Agent OS | 服务化、Team/Workflow | 见 learn-agno |

---

## 2. CrewAI 核心概念

```
Crew = 一组 Agent 协作完成目标
Agent = 有 role、goal、backstory 的 LLM 实体
Task = Agent 要执行的具体任务
Process = sequential / hierarchical 执行顺序
Tool = Agent 可用工具
```

---

## 3. 最小示例

```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role="Research Analyst",
    goal="收集 TaskFlow 竞品信息",
    backstory="你是有 10 年经验的产品分析师",
    verbose=True,
)

writer = Agent(
    role="Content Writer",
    goal="撰写竞品分析报告",
    backstory="你擅长结构化商业写作",
    verbose=True,
)

research_task = Task(
    description="调研 3 个任务管理工具的定价和功能",
    expected_output="竞品功能对比表（Markdown）",
    agent=researcher,
)

write_task = Task(
    description="基于调研结果写 500 字分析报告",
    expected_output="Markdown 报告",
    agent=writer,
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,
)

result = crew.kickoff()
print(result)
```

---

## 4. 何时用 CrewAI vs LangGraph

| 选 CrewAI | 选 LangGraph |
|-----------|--------------|
| 快速 Demo / POC | 生产级 Agent |
| 角色扮演式协作 | 精确状态控制 |
| 内容生成流水线 | 需要 Checkpoint/回滚 |
| 小团队实验 | 金融/合规场景 |

---

## 5. 生产注意事项

- CrewAI 适合原型，上线前评估 LangGraph 迁移
- 必须设置 Token 预算和步数上限
- 集成 Eval：检查 `expected_output` 是否达成
- 工具权限最小化（见 OWASP Agentic AI 安全）

---

## 6. 动手练习

1. 用 CrewAI 创建「研究员 + 写手」完成一篇短文
2. 同一任务用 LangGraph 实现，对比代码结构
3. 为 Crew 添加 Web Search Tool 并限制调用次数

---

## 参考

- [CrewAI 文档](https://docs.crewai.com/)
- 安装：`pip install crewai crewai-tools`
