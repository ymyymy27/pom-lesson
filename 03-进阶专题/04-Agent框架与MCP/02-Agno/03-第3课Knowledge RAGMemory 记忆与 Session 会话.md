> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第3课：Knowledge RAG、Memory 记忆与 Session 会话

## 1. 三个概念的区别

| 概念 | 作用 | 类比 |
|------|------|------|
| **Knowledge** | 外部文档检索（RAG） | 图书馆 |
| **Memory** | 跨会话记住用户偏好 | 长期记忆 |
| **Session (db)** | 单次对话的历史记录 | 聊天记录 |

```
Knowledge  →  「这份文档里写了什么？」
Memory     →  「用户上次说他喜欢简洁风格」
Session    →  「本轮对话前面说了什么？」
```

---

## 2. Session 会话存储

### 2.1 为什么需要 db？

没有 `db` 时，每次 `run()` 都是全新对话。加上 `SqliteDb` 后，同一 `session_id` 下的对话会连续。

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

agent = Agent(
    model="openai:gpt-4o",
    db=SqliteDb(db_file="chat.db"),
    add_history_to_context=True,
    num_history_runs=5,
)

# 同一 session 内多轮对话
agent.print_response("我叫小明", session_id="user-001")
agent.print_response("我叫什么？", session_id="user-001")  # 应能回答「小明」
```

### 2.2 关键参数

| 参数 | 作用 |
|------|------|
| `db=SqliteDb(...)` | 持久化会话到 SQLite |
| `add_history_to_context=True` | 把历史注入当前 prompt |
| `num_history_runs=5` | 最多带入最近 5 轮 |
| `session_id` | 区分不同用户/会话 |

---

## 3. Memory 跨会话记忆

### 3.1 Agentic Memory

开启后，Agent 会自动调用 `update_user_memory` 工具，把重要信息写入长期记忆。

```python
agent = Agent(
    model="openai:gpt-4o",
    db=SqliteDb(db_file="agent.db"),
    enable_agentic_memory=True,
    add_history_to_context=True,
)

agent.print_response("我是 Python 开发者，偏好简洁代码", user_id="alice")
# 关闭程序后重新运行，同一 user_id 下 Agent 仍可能记住偏好
agent.print_response("帮我写个函数", user_id="alice")
```

### 3.2 user_id vs session_id

| ID | 用途 |
|----|------|
| `session_id` | 一次连续对话（如一个聊天窗口） |
| `user_id` | 同一用户跨多个 session 的身份 |

---

## 4. Knowledge RAG 知识库

### 4.1 基本流程

```
文档 → 切分 → 向量化 → 存入向量库 → 用户提问 → 检索相关片段 → LLM 回答
```

### 4.2 最小 Knowledge 示例

```python
from pathlib import Path
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.lancedb import LanceDb, SearchType

knowledge = Knowledge(
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="agno_docs",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

# 加载本地文档
knowledge.add_content(path=Path("docs"))

agent = Agent(
    model="openai:gpt-4o",
    knowledge=knowledge,
    search_knowledge=True,   # 允许 Agent 检索知识库
    db=SqliteDb(db_file="rag.db"),
    instructions="基于知识库回答，不知道就说不知道。",
)
```

### 4.3 search_knowledge

| 值 | 行为 |
|----|------|
| `True` | Agent 可主动搜索知识库（Agentic RAG） |
| `False` | 不自动检索（需手动配置 retrieval） |

---

## 5. 示例代码：knowledge_agent.py

本课示例使用 **本地 Markdown 文件 + 简化 RAG**，避免额外向量库依赖过多。

运行前在 `practice/docs/` 下已有示例文档 `agno_intro.md`。

```powershell
python knowledge_agent.py
```

示例演示：

1. `SqliteDb` 会话持久化
2. `enable_agentic_memory` 记忆
3. 基于本地文档回答问题

---

## 6. 数据库后端选择

| 后端 | 场景 |
|------|------|
| `SqliteDb` | 本地开发、单机 |
| `PostgresDb` | 生产、多实例 |
| `InMemory` | 测试、无持久化 |

```python
from agno.db.sqlite import SqliteDb
db = SqliteDb(db_file="agent.db")
```

---

## 7. 三者组合使用

```python
agent = Agent(
    model="openai:gpt-4o",
    knowledge=knowledge,
    search_knowledge=True,
    db=SqliteDb(db_file="app.db"),
    enable_agentic_memory=True,
    add_history_to_context=True,
    num_history_runs=3,
)
```

典型问答流程：

1. **Session**：带上最近 3 轮对话上下文
2. **Knowledge**：检索文档相关段落
3. **Memory**：注入用户长期偏好
4. **LLM**：综合生成回答

---

## 动手练习

### 练习 1：Session 连续性

用同一 `session_id` 连续问 3 个问题，其中第 3 个依赖第 1 个的答案。

### 练习 2：Memory 测试

第一次告诉 Agent 你的编程语言偏好，重启脚本后用同一 `user_id` 再问「我该用什么风格写代码？」。

### 练习 3：扩展知识库

在 `practice/docs/` 添加你自己的笔记，让 Agent 基于新文档回答。

---

## 验收标准

- [ ] 能解释 Knowledge / Memory / Session 的区别
- [ ] 使用 `SqliteDb` 实现多轮对话
- [ ] `knowledge_agent.py` 能基于本地文档回答
- [ ] 理解 `user_id` 与 `session_id` 的用途

---

## 下一课预告

第4课学习 **Team 多智能体** 和 **Workflow 流程编排**。

**延伸阅读：**

- [Agent with Knowledge](https://docs.agno.com/agents/usage/agent-with-knowledge)
- [Agent with Memory](https://docs.agno.com/agents/usage/agent-with-memory)
- [Agent with Storage](https://docs.agno.com/agents/usage/agent-with-storage)
- [Database Overview](https://docs.agno.com/database/overview)
