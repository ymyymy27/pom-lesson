# 第1课：第一个 Agent — 环境搭建与核心概念

## 1. Agno 是什么？

### 一句话解释

**Agno 就是「智能体开发框架」** —— 用 Python 把大模型、工具、记忆、会话打包成可运行的 Agent，并能一键升级为 API 服务。

### 类比理解

| 日常概念 | Agno 概念 |
|---------|----------|
| 员工 | **Agent**（单智能体） |
| 项目组 | **Team**（多智能体协作） |
| 流水线 | **Workflow**（固定流程编排） |
| 公司前台 + 档案室 | **AgentOS**（API 服务 + 会话存储） |

### 解决了什么问题？

```
没有框架：
  自己拼 OpenAI SDK + 工具调用 + 历史记录 + FastAPI...
  代码分散、难调试、难复用

有了 Agno：
  Agent(...) + tools=[...] + db=SqliteDb(...)
  20 行脚本 → 生产级 API，内置 Tracing 和 UI
```

### Agno 核心组件

```
Agno
├── Agent      单智能体
├── Team       多智能体
├── Workflow   流程编排
├── Tools      工具（文件、搜索、自定义函数…）
├── Knowledge  RAG 知识库
├── Memory     跨会话记忆
└── AgentOS    FastAPI 运行时
```

---

## 2. 环境搭建

### 2.1 安装 uv（推荐）

Agno 官方推荐使用 [uv](https://docs.astral.sh/uv/) 管理 Python 环境。

```powershell
# Windows：用 pip 安装 uv
pip install uv
```

### 2.2 创建项目环境

```powershell
cd learn-agno\practice

# 创建 Python 3.12 虚拟环境
uv venv --python 3.12

# 激活（PowerShell）
.venv\Scripts\Activate.ps1

# 安装依赖
uv pip install -r requirements.txt
```

### 2.3 配置 API Key

以 OpenAI 为例（文档示例使用 `openai:gpt-5.5`，可按账号权限改为 `gpt-4o` 等）：

```powershell
$env:OPENAI_API_KEY="sk-你的密钥"
```

> 没有 OpenAI Key？可在 [platform.openai.com](https://platform.openai.com/api-keys) 申请，或改用 Ollama 等本地模型（见第2课扩展）。

### 2.4 验证安装

```powershell
python -c "import agno; print(agno.__version__)"
```

---

## 3. 第一个 Agent：Sorting Hat

官方示例：扫描文件夹，分析内容并提议整理方案。

### 3.1 代码结构

打开 `practice/sorting_hat.py`：

```python
from pathlib import Path
from agno.agent import Agent
from agno.tools.workspace import Workspace

folder = Path(__file__).parent

sorting_hat = Agent(
    name="Sorting Hat",
    model="openai:gpt-4o",
    tools=[Workspace(root=str(folder), allowed=["read", "list", "search"])],
    instructions=(
        "Walk the folder, figure out what's there, and propose a clean organization. "
        "Decide the categories yourself. Return a tidy summary, a category breakdown, "
        "and a folder tree."
    ),
    markdown=True,
)

sorting_hat.print_response(f"Inventory and organize {folder}", stream=True)
```

### 3.2 逐行理解

| 代码 | 含义 |
|------|------|
| `Agent(...)` | 创建智能体实例 |
| `name` | Agent 名称，用于日志和 UI 显示 |
| `model="openai:gpt-4o"` | 指定 LLM：`provider:model_id` |
| `tools=[Workspace(...)]` | 给 Agent 文件读写能力 |
| `allowed=["read", "list", "search"]` | 限制工具权限（只读） |
| `instructions` | 系统级行为指令 |
| `markdown=True` | 输出格式化为 Markdown |
| `print_response(..., stream=True)` | 流式打印回复 |

### 3.3 运行

```powershell
python sorting_hat.py
```

预期：Agent 会列出 `practice/` 目录下的文件，给出分类建议和目录树。

---

## 4. Agent 运行模式

### 4.1 三种调用方式

```python
# 1. 开发调试：直接打印
agent.print_response("问题", stream=True)

# 2. 获取完整响应对象
response = agent.run("问题")
print(response.content)

# 3. 异步（Web 服务中常用）
response = await agent.arun("问题")
```

### 4.2 stream 参数

| 值 | 效果 |
|----|------|
| `stream=True` | 逐 token 输出，适合终端/UI |
| `stream=False` | 等待完整响应后一次性返回 |

---

## 5. model 字符串格式

```
provider:model_id
```

| 示例 | 说明 |
|------|------|
| `openai:gpt-4o` | OpenAI GPT-4o |
| `openai:gpt-4o-mini` | 更便宜、更快 |
| `anthropic:claude-sonnet-4-20250514` | Anthropic Claude |
| `ollama:llama3.2` | 本地 Ollama |

对应环境变量：`OPENAI_API_KEY`、`ANTHROPIC_API_KEY` 等。

---

## 6. Workspace 工具权限

```python
Workspace(root=".", allowed=["read", "list", "search"])
```

| 权限 | 能力 |
|------|------|
| `read` | 读取文件内容 |
| `list` | 列出目录 |
| `search` | 搜索文件 |
| `write` | 写入/修改文件（慎用） |

**安全建议：** 开发阶段先用只读权限，确认 Agent 行为后再开放 `write`。

---

## 动手练习

### 练习 1：修改 instructions

把 instructions 改成中文，要求 Agent 用中文回复，并限制最多 3 个分类。

### 练习 2：限制权限

去掉 `search` 权限，只保留 `read` 和 `list`，观察 Agent 行为变化。

### 练习 3：换目录

把 `folder` 改成你电脑上的某个小文件夹（如桌面某个项目），重新运行。

---

## 验收标准

- [ ] 虚拟环境创建成功，`import agno` 无报错
- [ ] API Key 配置正确
- [ ] `sorting_hat.py` 能流式输出整理方案
- [ ] 能解释 `Agent` 五个核心参数：`name`、`model`、`tools`、`instructions`、`markdown`

---

## 下一课预告

第2课学习 **Tools 自定义工具** 和 **Structured Output 结构化输出**，让 Agent 返回可解析的 JSON 数据。

**延伸阅读：**

- [Build Your First Agent](https://docs.agno.com/first-agent)
- [What are Agents?](https://docs.agno.com/agents/overview)
- [Building Agents](https://docs.agno.com/agents/building-agents)
