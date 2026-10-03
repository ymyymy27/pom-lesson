> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第5课：AgentOS 服务化 — API、Tracing 与 UI

## 1. 从脚本到服务

### 为什么需要 AgentOS？

```
脚本模式：
  python agent.py  →  跑完就结束，无法多用户、无 API、难监控

AgentOS 模式：
  python workbench.py  →  http://localhost:7777
  ├── REST API（/docs）
  ├── Session 隔离
  ├── Tracing 追踪
  └── 连接 os.agno.com UI
```

**AgentOS = FastAPI + Agno 运行时**，把 Agent / Team / Workflow 暴露为生产 API。

---

## 2. 最小 AgentOS 服务

### 2.1 workbench.py 结构

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.os import AgentOS
from agno.tools.workspace import Workspace

workbench = Agent(
    name="Workbench",
    model="openai:gpt-4o",
    db=SqliteDb(db_file="workbench.db"),
    tools=[Workspace(".")],
    enable_agentic_memory=True,
    add_history_to_context=True,
    num_history_runs=3,
)

agent_os = AgentOS(agents=[workbench], tracing=True)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="workbench:app", reload=True)
```

### 2.2 安装与运行

```powershell
cd 03-进阶专题\04-Agent框架与MCP\02-Agno\practice
uv pip install -r requirements-os.txt
$env:OPENAI_API_KEY="sk-你的密钥"
python workbench.py
```

服务启动后：

| 地址 | 用途 |
|------|------|
| http://localhost:7777 | API 根路径 |
| http://localhost:7777/docs | Swagger API 文档 |

---

## 3. AgentOS 核心能力

### 3.1 注册多个组件

```python
agent_os = AgentOS(
    agents=[agent1, agent2],
    teams=[team1],
    workflows=[workflow1],
    tracing=True,
)
```

### 3.2 Session 与 Memory

服务模式下 Session 自动通过 API 的 `session_id` 传递，数据存在 `workbench.db`。

### 3.3 Tracing

`tracing=True` 开启后，每次 Run 的工具调用、LLM 请求可在 UI 或 API 中查看，便于调试。

---

## 4. 连接 AgentOS UI

1. 打开 [https://os.agno.com](https://os.agno.com) 并登录
2. 点击 **Connect OS**
3. 选择 **Local**，URL 填 `http://localhost:7777`
4. 命名如「Local AgentOS」，点击 **Connect**
5. 在 **Chat** 中测试：`Categorize the files in your working dir`
6. 在 **Sessions** / **Traces** 查看历史与调用链

> Session 数据在本地 SQLite，不会上传到 Agno 云端（官方说明）。

---

## 5. API 调用示例

在 `/docs` 页面可交互测试，或用 curl：

```powershell
# 查看已注册的 Agent 列表（路径以 /docs 为准）
curl http://localhost:7777/v1/agents
```

具体端点以当前版本 Swagger 文档为准，常见操作：

| 操作 | 说明 |
|------|------|
| 创建 Run | 向指定 Agent 发送消息 |
| 列出 Sessions | 查看会话历史 |
| 列出 Traces | 查看调用追踪 |

官方参考：[Using the API](https://docs.agno.com/agent-os/using-the-api)

---

## 6. 注册 Team 和 Workflow

```python
agent_os = AgentOS(
    agents=[workbench],
    teams=[research_team],
    workflows=[pipeline],
    tracing=True,
)
```

API 会分别暴露 agents / teams / workflows 端点，客户端可按需调用。

---

## 7. 生产部署入门

### 7.1 环境变量

```powershell
$env:OPENAI_API_KEY="..."
# 生产环境用 .env 或密钥管理服务，勿提交到 Git
```

### 7.2 Docker 部署（扩展）

官方提供 Docker 模板：

- [AgentOS on Docker](https://docs.agno.com/deploy/templates/docker/deploy)
- 结合你 `learn-docker` 课程知识部署

### 7.3 安全

多用户场景需配置 JWT / RBAC：

- [Security Overview](https://docs.agno.com/agent-os/security/overview)
- [JWT Middleware](https://docs.agno.com/agent-os/middleware/jwt)

---

## 8. MCP 与外部集成（了解）

AgentOS 可挂载 MCP 工具、作为 MCP Server 对外提供能力：

- [MCPTools within AgentOS](https://docs.agno.com/agent-os/mcp/tools)
- [AgentOS as MCP Server](https://docs.agno.com/agent-os/mcp/mcp)

适合与 Cursor、Claude Desktop 等 MCP 客户端集成。

---

## 9. 课程总结

```
第1课  Agent 基础          sorting_hat.py
第2课  Tools + 结构化输出   tools_agent.py
第3课  RAG + Memory         knowledge_agent.py
第4课  Team + Workflow      research_team.py
第5课  AgentOS 服务         workbench.py
```

你已具备：

- 编写单 Agent 与多 Agent 系统
- 使用工具、知识库、记忆
- 将 Agent 发布为本地 API 服务
- 用 UI 调试和查看 Traces

---

## 动手练习

### 练习 1：UI 联调

启动 `workbench.py`，在 os.agno.com 完成连接并发送 3 条有上下文的消息。

### 练习 2：注册 Team

把第4课的 `research_team` 注册进 AgentOS，在 API 文档中找到 Team 相关端点。

### 练习 3：Tracing 分析

在 Traces 中查看一次 Run 的 tool call 链路，记录 LLM 调用了哪些工具。

---

## 验收标准

- [ ] `workbench.py` 在 7777 端口正常运行
- [ ] 能打开 `/docs` 并理解主要 API
- [ ] 成功连接 os.agno.com 并完成一次 Chat
- [ ] 能在 Traces 中查看一次完整调用链

---

## 继续学习

| 方向 | 文档 |
|------|------|
| 与 Coding Agent 集成 | [Coding Agents](https://docs.agno.com/coding-agents) |
| Agent 质量评估 | [Evals](https://docs.agno.com/evals/overview) |
| Slack / Telegram 接入 | [Interfaces](https://docs.agno.com/agent-os/interfaces/overview) |
| 云平台部署 | [Deploy Templates](https://docs.agno.com/deploy/introduction) |
| Agno CLI | [CLI Overview](https://docs.agno.com/cli/overview) |

**官方第一个 Agent 教程：** [Build Your First Agent](https://docs.agno.com/first-agent)
