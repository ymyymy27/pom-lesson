> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Agno 语法结构参考

> 本文档系统梳理 Agno 的四层结构：**Agent**、**Team**、**Workflow**、**AgentOS**。建议配合 `01-第1课第一个 Agent — 环境搭建与核心概念.md` 一起阅读。

---

## 1. 整体架构：四层结构的关系

```
┌─────────────────────────────────────────────────────────────┐
│  1. Agent              →  单智能体（模型 + 指令 + 工具）      │
│     Agent(name, model, tools, instructions, ...)            │
├─────────────────────────────────────────────────────────────┤
│  2. Team               →  多智能体协作                         │
│     Team(members=[agent_a, agent_b], mode=...)              │
├─────────────────────────────────────────────────────────────┤
│  3. Workflow           →  确定性流程编排                     │
│     Workflow(steps=[Step(...), Parallel(...), Loop(...)])   │
├─────────────────────────────────────────────────────────────┤
│  4. AgentOS            →  FastAPI 运行时（API + 会话 + UI） │
│     AgentOS(agents=[...], teams=[...], workflows=[...])     │
└─────────────────────────────────────────────────────────────┘
```

**演进路径：**

```
脚本 Agent  →  加 Tools/Knowledge  →  Team/Workflow  →  AgentOS 服务
```

---

## 2. Agent 语法结构

### 2.1 最小 Agent

```python
from agno.agent import Agent

agent = Agent(
    name="MyAgent",
    model="openai:gpt-4o",       # 格式: provider:model_id
    instructions="你是一个助手。",
)

agent.print_response("你好", stream=True)
```

### 2.2 常用参数

| 参数 | 作用 | 示例 |
|------|------|------|
| `name` | Agent 名称 | `"Sorting Hat"` |
| `model` | LLM 模型 | `"openai:gpt-4o"` |
| `instructions` | 系统指令 | `"只回答中文"` |
| `tools` | 工具列表 | `[Workspace(".")]` |
| `markdown` | 输出 Markdown | `True` |
| `db` | 会话存储 | `SqliteDb(db_file="app.db")` |
| `enable_agentic_memory` | 跨会话记忆 | `True` |
| `add_history_to_context` | 注入历史对话 | `True` |
| `num_history_runs` | 历史轮数 | `3` |
| `response_model` | 结构化输出 | `MyPydanticModel` |
| `knowledge` | 知识库 | `Knowledge(...)` |

### 2.3 运行方式

```python
# 方式1：直接打印（开发调试）
agent.print_response("问题", stream=True)

# 方式2：获取 RunOutput 对象
response = agent.run("问题")
print(response.content)

# 方式3：异步
response = await agent.arun("问题")
```

---

## 3. Tools 语法结构

### 3.1 内置工具

```python
from agno.tools.workspace import Workspace

tools = [
    Workspace(root=".", allowed=["read", "list", "search"]),
]
```

### 3.2 自定义函数工具

```python
def get_weather(city: str) -> str:
    """获取城市天气"""
    return f"{city}: 晴, 25°C"

agent = Agent(
    model="openai:gpt-4o",
    tools=[get_weather],   # 函数 docstring 会成为工具描述
)
```

### 3.3 常用内置工具（按需 import）

| 工具 | 用途 |
|------|------|
| `Workspace` | 读写本地文件 |
| `DuckDuckGoTools` | 网页搜索 |
| `YFinanceTools` | 金融数据 |
| `MCPTools` | 接入 MCP 服务器 |

---

## 4. Team 语法结构

```python
from agno.agent import Agent
from agno.team import Team

researcher = Agent(name="Researcher", model="openai:gpt-4o", ...)
writer = Agent(name="Writer", model="openai:gpt-4o", ...)

team = Team(
    name="Research Team",
    members=[researcher, writer],
    instructions="Researcher 负责调研，Writer 负责写报告。",
)

team.print_response("分析 Python 异步编程趋势", stream=True)
```

---

## 5. Workflow 语法结构

```python
from agno.workflow import Workflow, Step

workflow = Workflow(
    name="Research Pipeline",
    steps=[
        Step(name="collect", agent=collector),
        Step(name="analyze", agent=analyst),
        Step(name="write", agent=writer),
    ],
)

workflow.print_response("研究 Agno 框架", stream=True)
```

### 5.1 常见步骤类型

| 步骤 | 作用 |
|------|------|
| `Step` | 单步执行 |
| `Parallel` | 并行执行 |
| `Loop` | 循环 |
| `Router` | 条件路由 |
| `Condition` | 分支判断 |

---

## 6. AgentOS 语法结构

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.os import AgentOS

agent = Agent(
    name="Workbench",
    model="openai:gpt-4o",
    db=SqliteDb(db_file="workbench.db"),
)

agent_os = AgentOS(agents=[agent], tracing=True)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="workbench:app", reload=True)
    # → http://localhost:7777/docs
```

### 6.1 AgentOS 注册内容

```python
AgentOS(
    agents=[agent1, agent2],
    teams=[team1],
    workflows=[workflow1],
    tracing=True,
)
```

---

## 7. 模型 Provider 格式

```
provider:model_id
```

| Provider | 示例 |
|----------|------|
| OpenAI | `openai:gpt-4o` |
| Anthropic | `anthropic:claude-sonnet-4-20250514` |
| Google | `google:gemini-2.0-flash` |
| Ollama（本地） | `ollama:llama3.2` |

环境变量通常按 provider 命名，如 `OPENAI_API_KEY`、`ANTHROPIC_API_KEY`。

---

## 8. 数据库（Session Storage）

```python
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="agent.db")
```

| 后端 | 适用场景 |
|------|----------|
| `SqliteDb` | 本地开发、单机部署 |
| `PostgresDb` | 生产环境 |
| `MongoDb` | 文档型存储需求 |

---

## 9. 常用 import 速查

```python
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow, Step
from agno.os import AgentOS
from agno.db.sqlite import SqliteDb
from agno.tools.workspace import Workspace
from agno.knowledge.knowledge import Knowledge
from pydantic import BaseModel, Field
```

---

## 10. 官方文档导航

| 主题 | 链接 |
|------|------|
| 第一个 Agent | https://docs.agno.com/first-agent |
| Agent 构建 | https://docs.agno.com/agents/building-agents |
| AgentOS | https://docs.agno.com/agent-os/introduction |
| 示例合集 | https://docs.agno.com/examples/basics/overview |
| 完整索引 | https://docs.agno.com/llms.txt |
