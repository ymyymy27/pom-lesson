# 第11课：Agno 工程化接入 — 图谱工具、Hybrid RAG 与生产部署

> 前置：第 8–10 课 · [`learn-agno`](../../learn-agno/) Agno 框架基础  
> 本课侧重**知识图谱侧**如何工程化接入 Agno；Agno 语法详见 [`learn-agno/00_agno_syntax.md`](../../learn-agno/00_agno_syntax.md)

---

## 1. 为什么用 Agno 接入知识图谱？

Agno 原生面向 **Agent + Knowledge + AgentOS 服务化**，知识图谱不是内置存储，而是通过 **Tools / 自定义 Toolkit** 接入。与第 9 课 LangChain 示例相比，Agno 路径更适合：

| 场景 | Agno 优势 |
|------|-----------|
| 快速把图谱封装为 Agent 工具 | `@tool` / `Toolkit` 模式简洁 |
| 向量 + 图谱 Hybrid RAG | `Knowledge` + 自定义 `knowledge_retriever` |
| 多 Agent 分工（检索 / 推理 / 审核） | `Team` / `Workflow` 内置 |
| 生产 API | `AgentOS` 一键暴露 REST + Tracing |

**集成全景：**

```
用户问题
    ↓
Agno Agent / Team
    ├─ Knowledge（向量库）─────── 语义相似文档
    ├─ GraphToolkit（Neo4j）──── 关系 / 多跳事实
    └─ Memory / Session ──────── 用户偏好与对话历史
    ↓
AgentOS API（可选）→ Nginx → 监控 / 限流
```

**与 learn-agno 的分工：**

| 主题 | 权威来源 |
|------|----------|
| Agent / Team / Workflow / AgentOS 语法 | [`learn-agno`](../../learn-agno/) |
| Schema、抽取、Neo4j 建模、Graph API | 本课程第 1–8 课 |
| Hybrid RAG 架构原理 | [`stage-08-rag/06-graph-rag.md`](../stage-08-rag/06-graph-rag.md) |
| **图谱 + Agno 工程化接入** | **本课** |

---

## 2. 三种接入模式

### 2.1 模式 A：内置 Neo4jTools（快速验证）

Agno 提供 [`Neo4jTools`](https://docs.agno.com/tools/toolkits/database/neo4j)，适合**开发期探索**和 Schema 熟悉：

```python
from agno.agent import Agent
from agno.tools.neo4j import Neo4jTools

agent = Agent(
    name="Graph Explorer",
    model="openai:gpt-4o",
    tools=[Neo4jTools(
        enable_run_cypher=True,
        enable_get_schema=True,
        enable_list_labels=True,
    )],
    instructions=[
        "你是组织架构图谱助手，只读查询 Neo4j。",
        "优先用 get_schema 了解结构，再写参数化 Cypher。",
        "禁止 CREATE / DELETE / SET 等写操作。",
    ],
)
```

**适用：** POC、数据分析师自助查图。  
**局限：** Agent 直接写 Cypher，易超深遍历、难做业务语义封装、NL2Cypher 安全风险高。

### 2.2 模式 B：GraphRepository Toolkit（生产推荐）

复用第 8 课 `GraphRepository`，把**业务语义**封装为有限工具集，而非暴露任意 Cypher：

```python
from agno.tools import Toolkit

class OrgGraphToolkit(Toolkit):
    def __init__(self, repo):
        super().__init__(name="org_graph")
        self.repo = repo
        self.register(self.search_people)
        self.register(self.get_person_projects)
        self.register(self.get_neighbors)

    def search_people(self, name: str, limit: int = 5) -> str:
        """按姓名模糊搜索在职员工。适用于「找张三」「谁叫李四」类问题。"""
        results = self.repo.search_people(name, limit=limit)
        return str(results) if results else "未找到匹配人员。"

    def get_person_projects(self, person_id: str) -> str:
        """获取某员工的部门与参与项目。person_id 来自 search_people 结果。"""
        data = self.repo.get_person_with_projects(person_id)
        return str(data) if data else "人员不存在。"

    def get_neighbors(self, entity_id: str, limit: int = 20) -> str:
        """获取实体一度邻居及关系类型。适用于汇报链、部门归属。"""
        return str(self.repo.get_neighbors(entity_id, limit=limit))
```

**设计原则：**

- 每个工具对应**一个业务意图**，描述里写清「何时调用」
- 返回 JSON 字符串或结构化文本，便于 LLM 引用
- 内部 Cypher 已参数化、带 `LIMIT`，Agent 无法任意扩查询

完整可运行示例见 `practice/agno_graph_agent.py`。

### 2.3 模式 C：Hybrid — Knowledge + Graph Toolkit

向量库负责文档语义，图谱负责关系事实，与第 9 课 Hybrid RAG 对齐：

```python
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.chroma import ChromaDb
from agno.vectordb.search import SearchType

knowledge = Knowledge(
    vector_db=ChromaDb(
        collection="org_docs",
        path="tmp/chromadb",
        persistent_client=True,
        search_type=SearchType.hybrid,
    ),
)

agent = Agent(
    model="openai:gpt-4o",
    knowledge=knowledge,
    search_knowledge=True,          # Agentic RAG：Agent 决定何时搜文档
    tools=[OrgGraphToolkit(repo)],  # 关系类问题走图谱
    instructions=[
        "人员、部门、项目、汇报关系 → 优先调用 org_graph 工具。",
        "制度、流程、文档内容 → 搜索 knowledge。",
        "两者都有时用图谱事实校验文档描述。",
    ],
)
```

**路由策略（三选一）：**

| 策略 | 实现 | 适用 |
|------|------|------|
| Prompt 路由 | `instructions` 描述分工 | 简单场景、工具少 |
| 关键词预路由 | 第 9 课 `route_query()` 决定先调哪个 | 延迟敏感 |
| 自定义 retriever | `knowledge_retriever=` 注入图谱上下文 | 需统一检索入口 |

### 2.4 模式 D：LightRAG — 文档自动构图 + Agno 编排

[LightRAG](https://github.com/HKUDS/LightRAG) 在 `insert()` 时**自动**切分文档、抽取实体关系、建图并向量化；查询时内置 `local / global / hybrid / mix` 等模式。与第 2–8 课「先 Schema、再 ETL 入 Neo4j」的路径互补：

| 维度 | 手工 Neo4j 图谱（模式 B） | LightRAG |
|------|---------------------------|----------|
| 构图 | Schema YAML + 流水线 | `insert()` 自动抽图 |
| 存储 | 自管 Neo4j / Graph API | 默认 NetworkX 文件，可配 `Neo4JStorage` |
| 检索 | 自定义 Cypher / Toolkit | `QueryParam(mode=...)` 内置 Hybrid |
| 适用 | 组织主数据、强治理 | 文档库、研报、制度库快速上线 |

**推荐架构（生产）：LightRAG Server + Agno AgentOS 分离部署**

```
文档上传 ──→ LightRAG Server (:9621)
                 ├─ insert / scan  （建图 + 向量）
                 └─ /query         （Graph RAG 检索 + 生成）

用户 ──→ Agno AgentOS (:7777)
              └─ LightRAGToolkit  ──HTTP──→ /query
              └─ OrgGraphToolkit  ──Bolt──→ Neo4j（可选，结构化主数据）
```

官方建议：业务集成优先走 [LightRAG Server REST API](https://github.com/HKUDS/LightRAG/blob/main/docs/LightRAG-API-Server.md)；嵌入式 Core 适合研究或单机 demo。

#### 方式 1：HTTP Toolkit（生产推荐）

LightRAG Server 启动后，用 Agno 工具调 `/query`：

```python
import os
import httpx
from agno.tools import Toolkit

LIGHTRAG_URL = os.getenv("LIGHTRAG_URL", "http://localhost:9621")
LIGHTRAG_API_KEY = os.getenv("LIGHTRAG_API_KEY", "")

class LightRAGToolkit(Toolkit):
    def __init__(self):
        super().__init__(name="lightrag")
        self.register(self.query_hybrid)
        self.register(self.query_local)
        self.register(self.query_global)
        self.register(self.query_mix)
        self.register(self.get_retrieval_context)

    def _post_query(self, question: str, mode: str, only_context: bool = False) -> str:
        payload = {
            "query": question,
            "mode": mode,
            "include_references": True,
            "include_chunk_content": only_context,
        }
        headers = {}
        if LIGHTRAG_API_KEY:
            headers["X-API-Key"] = LIGHTRAG_API_KEY
        r = httpx.post(f"{LIGHTRAG_URL}/query", json=payload, headers=headers, timeout=60.0)
        r.raise_for_status()
        data = r.json()
        if only_context:
            refs = data.get("references", [])
            return str(refs)[:4000]
        return data.get("response", str(data))

    def query_hybrid(self, question: str) -> str:
        """文档库混合检索（默认首选）。局部实体 + 全局主题，适合 80% 文档问答。"""
        return self._post_query(question, mode="hybrid")

    def query_local(self, question: str) -> str:
        """围绕具体实体/概念的局部检索。适合「张三的职责是什么」类点名问题。"""
        return self._post_query(question, mode="local")

    def query_global(self, question: str) -> str:
        """跨文档全局主题归纳。适合「公司有哪些业务线」类宏观问题。"""
        return self._post_query(question, mode="global")

    def query_mix(self, question: str) -> str:
        """图谱 + 向量深度融合，适合多跳、复杂推理问题。"""
        return self._post_query(question, mode="mix")

    def get_retrieval_context(self, question: str) -> str:
        """只返回检索到的文档片段与引用，不生成最终答案。供 Agent 自行综合。"""
        return self._post_query(question, mode="mix", only_context=True)
```

```python
from agno.agent import Agent

agent = Agent(
    name="DocGraphAgent",
    model="openai:gpt-4o",
    tools=[LightRAGToolkit()],
    tool_call_limit=3,
    instructions=[
        "制度、流程、文档内容 → 使用 lightrag 工具。",
        "默认用 query_hybrid；具体人/项目用 query_local；宏观总结用 query_global；复杂多跳用 query_mix。",
        "需要自行组织答案、对比多个来源时用 get_retrieval_context。",
    ],
)
```

可运行示例：`practice/agno_lightrag_agent.py`（需先启动 LightRAG Server）。

#### 方式 2：嵌入式 Core + Toolkit

单机 demo 或需要与 Agno 同进程时，直接嵌入 `LightRAG` 实例（**必须** `await initialize_storages()`）：

```python
import asyncio
import os
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed

WORKING_DIR = "./lightrag_storage"
_rag: LightRAG | None = None

async def get_lightrag() -> LightRAG:
    global _rag
    if _rag is None:
        rag = LightRAG(
            working_dir=WORKING_DIR,
            embedding_func=openai_embed,
            llm_model_func=gpt_4o_mini_complete,
            # 与现有 Neo4j 共用时可开启：
            # graph_storage="Neo4JStorage",
            addon_params={"language": "Simplified Chinese"},
        )
        await rag.initialize_storages()
        _rag = rag
    return _rag

def query_lightrag(question: str, mode: str = "hybrid") -> str:
    """查询 LightRAG 文档知识库。mode: local|global|hybrid|mix|naive。"""

    async def _run():
        rag = await get_lightrag()
        return await rag.aquery(question, param=QueryParam(mode=mode))

    return asyncio.run(_run())
```

```python
# 入库（流水线脚本，非 Agent 实时调用）
async def ingest_docs(paths: list[str]):
    rag = await get_lightrag()
    for p in paths:
        with open(p, encoding="utf-8") as f:
            await rag.ainsert(f.read(), file_paths=p)
    await rag.finalize_storages()
```

注意：Agno 工具函数是**同步**的，嵌入式需用 `asyncio.run()` 包一层；高并发生产环境更推荐方式 1 独立服务。

#### 方式 3：作为 Agno 的 knowledge_retriever

若希望 Agno 统一走 `search_knowledge` 入口，但检索引擎换成 LightRAG，可自定义 retriever：

```python
async def lightrag_knowledge_retriever(agent, query: str, num_documents: int = 5, **kwargs) -> str:
    rag = await get_lightrag()
    return await rag.aquery(
        query,
        param=QueryParam(mode="mix", only_need_context=True, chunk_top_k=num_documents),
    )

agent = Agent(
    model="openai:gpt-4o",
    knowledge=knowledge_placeholder,   # 仅占位，实际检索由 retriever 完成
    search_knowledge=True,
    knowledge_retriever=lightrag_knowledge_retriever,
    instructions="基于检索到的文档片段回答，标注引用来源。",
)
```

这样 **LightRAG 只负责检索**，最终生成由 Agno Agent 的模型与 instructions 控制，便于统一 Prompt 与安全策略。

#### 方式 4：LightRAG + 手工 Neo4j 双库（企业常见）

```
LightRAG          → 非结构化文档（制度 PDF、Wiki、邮件）
OrgGraphToolkit   → 结构化主数据（HR、项目、汇报链）
Agno Agent        → 按问题类型选工具，必要时交叉验证
```

```python
agent = Agent(
    tools=[LightRAGToolkit(), OrgGraphToolkit(repo)],
    instructions=[
        "人员、部门、项目、汇报关系 → org_graph。",
        "制度、流程、文档原文 → lightrag。",
        "两者都涉及时，以 org_graph 结构化事实为准，lightrag 作补充说明。",
    ],
)
```

#### LightRAG 查询模式选型

| mode | 检索侧重 | 典型问题 |
|------|----------|----------|
| `naive` | 纯向量 | 基线对比 |
| `local` | 实体邻域 | 「订单系统的后端负责人是谁？」 |
| `global` | 社区/主题摘要 | 「研发部主要关注哪些技术方向？」 |
| `hybrid` | local + global | **默认首选** |
| `mix` | 图 + 向量 + 关键词 | 复杂多跳 |
| `bypass` | 不检索，直答 LLM | 闲聊 |

#### LightRAG 接入优化要点

```
□ 入库与查询分离：insert/scan 走离线 Pipeline，Agent 只读 query
□ 控制 QueryParam.top_k / max_total_tokens，防止 context 爆炸
□ enable_rerank 默认 true，无 rerank 模型时在 Server 侧关闭
□ 多租户用 workspace 或独立 LightRAG 实例隔离语料
□ Agent 侧 tool_call_limit=2~3，避免同一问题多次 query_mix
□ 生产：LightRAG Server + API Key；Agno AgentOS 分进程部署
```

完整嵌入式示例见 `practice/agno_lightrag_embedded.py`。

---

## 3. 深度优化：框架调用与使用技巧

### 3.1 工具粒度：少而精

```
❌ 一个 mega 工具 query_graph(question) — Agent 黑盒，难 debug
❌ 暴露 run_cypher — NL2Cypher 风险、性能不可控

✅ search_people / get_person_projects / get_subgraph
   — 3–6 个语义清晰的只读工具
```

工具 `description` 是 Agent 的「路由表」，务必包含：

- **适用问题类型**（例：「汇报链」「参与项目」）
- **前置依赖**（例：「需先 search_people 获取 person_id」）
- **不适用场景**（例：「不要用于查文档全文」）

### 3.2 Context 预算控制

图谱子图膨胀是 Hybrid Agent 的头号性能杀手：

```python
MAX_SUBGRAPH_NODES = 30
MAX_TOOL_RESULT_CHARS = 4000

def get_subgraph_limited(self, entity_id: str, depth: int = 2) -> str:
    depth = min(depth, 2)  # 硬上限
    data = self.repo.get_neighbors(entity_id, limit=MAX_SUBGRAPH_NODES)
    text = str(data)
    return text[:MAX_TOOL_RESULT_CHARS] + ("..." if len(text) > MAX_TOOL_RESULT_CHARS else "")
```

Agent 侧可配合：

```python
Agent(
    ...,
    tool_call_limit=5,           # 限制单轮工具调用次数
    num_history_runs=3,          # 控制历史 token
)
```

### 3.3 缓存热点查询

组织架构查询重复率高，在 Toolkit 与 Neo4j 之间加 Redis：

```python
import json
import hashlib

def cached_search(repo, redis, name: str, ttl: int = 300) -> list:
    key = f"kg:search:{hashlib.md5(name.encode()).hexdigest()}"
    hit = redis.get(key)
    if hit:
        return json.loads(hit)
    results = repo.search_people(name)
    redis.setex(key, ttl, json.dumps(results, ensure_ascii=False))
    return results
```

Pipeline 发布新图谱版本时，`FLUSHDB` 或按 `kg:version` 前缀失效。

### 3.4 结构化输出减少幻觉

对「列出张三的所有项目及负责人」类问题，要求 Pydantic 输出：

```python
from pydantic import BaseModel, Field

class ProjectFact(BaseModel):
    project_name: str
    role: str | None = None
    owner: str | None = None

class PersonProjectsAnswer(BaseModel):
    person_name: str
    projects: list[ProjectFact]
    sources: list[str] = Field(description="引用的 tool 名称")

agent = Agent(
    tools=[OrgGraphToolkit(repo)],
    response_model=PersonProjectsAnswer,
    instructions="必须基于工具返回填写 projects，不得编造。",
)
```

### 3.5 Team 分工模式

复杂问答可拆为多 Agent（见 [`learn-agno/04_team_workflow.md`](../../learn-agno/04_team_workflow.md)）：

```
Router Agent     → 判断 graph / vector / both
Graph Agent        → 仅挂载 OrgGraphToolkit
Doc Agent          → 仅挂载 Knowledge
Synthesizer Agent  → 合并事实，标注来源
```

```python
from agno.team import Team

graph_agent = Agent(name="Graph Specialist", tools=[OrgGraphToolkit(repo)], ...)
doc_agent = Agent(name="Doc Specialist", knowledge=knowledge, search_knowledge=True, ...)

team = Team(
    name="Org QA Team",
    members=[graph_agent, doc_agent],
    instructions="关系事实以 Graph Specialist 为准，文档细节以 Doc Specialist 为准。",
)
```

### 3.6 Workflow 确定性编排

对**固定流程**（如「查人 → 扩子图 → 生成摘要」），用 Workflow 比纯 Agent 更稳：

```python
from agno.workflow import Workflow, Step

# 伪代码：先 search，再 get_projects，最后 LLM 总结
workflow = Workflow(
    name="person_briefing",
    steps=[
        Step(name="search", agent=search_agent),
        Step(name="enrich", agent=graph_agent),
        Step(name="summarize", agent=summary_agent),
    ],
)
```

适用：合规审计、固定报表；灵活对话仍用单 Agent + Tools。

### 3.7 安全：图谱工具的硬性约束

```
□ 生产禁用 Neo4jTools 的 enable_run_cypher（或只读账号 + 语句白名单）
□ Graph API / Toolkit 使用只读 Neo4j 用户
□ 工具层禁止 MERGE / DELETE / SET
□ AgentOS 开启认证（API Key / JWT），见 learn-agno 第 6 课
□ 审计日志记录 tool_name + 参数（脱敏 PII）
```

只读 Neo4j 用户示例：

```cypher
CREATE USER kg_reader SET PASSWORD 'xxx' CHANGE NOT REQUIRED;
GRANT MATCH {*} ON GRAPH neo4j TO kg_reader;
```

---

## 4. AgentOS 工程化部署

### 4.1 最小服务结构

将图谱 Agent 注册到 AgentOS，与第 10 课 Graph API 并存：

```
                    ┌─────────────────┐
  用户 / 前端 ──────→│  Nginx (TLS)    │
                    └────────┬────────┘
                             ↓
              ┌──────────────┴──────────────┐
              ↓                             ↓
     ┌─────────────────┐          ┌─────────────────┐
     │  AgentOS :7777   │          │  Graph API :8000 │
     │  (Agno Agent)    │          │  (FastAPI 只读)   │
     └────────┬─────────┘          └────────┬─────────┘
              │                             │
              └──────────────┬──────────────┘
                             ↓
                    ┌─────────────────┐
                    │  Neo4j :7687     │
                    └─────────────────┘
```

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.os import AgentOS

org_agent = Agent(
    name="OrgGraphAgent",
    model="openai:gpt-4o",
    tools=[OrgGraphToolkit(repo)],
    db=SqliteDb(db_file="org_agent.db"),
    add_history_to_context=True,
    num_history_runs=3,
    tracing=True,
)

agent_os = AgentOS(agents=[org_agent], tracing=True)
app = agent_os.get_app()
```

运行示例见 `practice/agno_graph_agentos.py`。

### 4.2 环境变量与配置

```bash
# .env — 与 practice/.env.example 对齐
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=kg_reader          # 生产用只读账号
NEO4J_PASSWORD=***
OPENAI_API_KEY=sk-...
AGNO_DB_URL=sqlite:///org_agent.db   # 或 PostgresDb
KG_ENV=production
```

**禁止**在 Agent `instructions` 或代码中硬编码连接串；Toolkit 从 `os.getenv` 读取。

### 4.3 Docker Compose 扩展

在现有 `practice/docker-compose.yml` 基础上，增加 AgentOS 服务（示意）：

```yaml
  agentos:
    build: .
    ports:
      - "7777:7777"
    environment:
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: changeme
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      neo4j:
        condition: service_healthy
```

生产建议：Neo4j、AgentOS、向量库分网络域；AgentOS 不暴露 Bolt 端口。

### 4.4 可观测性

| 层级 | 手段 |
|------|------|
| AgentOS | `tracing=True`，连接 os.agno.com 或导出 OpenTelemetry |
| 工具层 | 记录 `tool_name`、`latency_ms`、`result_size` |
| Neo4j | 慢查询日志、`PROFILE` 定期审查 |
| 业务 | 黄金 QA 集自动回归（见第 9 课 eval_cases） |

```python
import time
import logging

log = logging.getLogger("kg.tools")

def search_people(self, name: str, limit: int = 5) -> str:
    t0 = time.perf_counter()
    results = self.repo.search_people(name, limit=limit)
    log.info("search_people name=%s hits=%d ms=%.1f", name, len(results), (time.perf_counter()-t0)*1000)
    return str(results)
```

### 4.5 性能 SLA 参考

| 路径 | 目标 P95 |
|------|-----------|
| Agent 单轮（无工具） | < 3 s |
| search_people 工具 | < 150 ms |
| get_subgraph depth=2 | < 800 ms |
| Hybrid（向量 + 图谱 + 生成） | < 8 s |

超时策略：工具内部设 Neo4j `transaction_timeout`；Agent 层 `tool_call_limit` 防止无限循环。

---

## 5. 与 Graph API 的协作方式

| 方式 | 说明 |
|------|------|
| **直连 Neo4j** | Toolkit 内嵌 `GraphRepository`，延迟最低 |
| **调 Graph API** | Agent 通过 `HttpTools` 调 `/v1/persons/search`，便于独立扩缩容 |
| **MCP 暴露图谱** | 将 Graph API 封装为 MCP Server，Agno Agent 当 MCP Client（跨语言） |

HTTP 调用示例：

```python
import httpx

def search_via_api(name: str) -> str:
    """通过 Graph REST API 搜索人员（适用于 Agent 与 Neo4j 网络隔离）。"""
    r = httpx.get("http://graph-api:8000/v1/persons/search", params={"q": name}, timeout=5.0)
    r.raise_for_status()
    return str(r.json())
```

---

## 6. 常见问题与排错

| 现象 | 原因 | 处理 |
|------|------|------|
| Agent 从不调用图谱工具 | `description` 不清晰 | 重写工具说明，加负面示例 |
| 回答与图谱不一致 | 未强制基于工具 | `response_model` + instructions「不得编造」 |
| Context 超限 | 子图过大 | 降 depth、截断、摘要后再注入 |
| Cypher 超时 | NL2Cypher 深遍历 | 改用 GraphRepository 语义工具 |
| 重复调用同一工具 | 无 Session 记忆 | `add_history_to_context=True` |
| 部署后 503 | Neo4j 未就绪 | `depends_on` healthcheck + AgentOS `/health` |

---

## 7. 工程化 Checklist

```
接入设计
□ 选定模式 A/B/C，生产默认 B 或 C
□ Toolkit 工具数 ≤ 6，均有清晰 description
□ 只读 Neo4j 账号 / 禁用任意 Cypher

性能
□ 子图 depth ≤ 2，节点数 LIMIT
□ 热点查询 Redis 缓存 + 版本失效
□ tool_call_limit 与 transaction_timeout

Hybrid
□ 向量与图谱 entity id 对齐（第 9 课）
□ Prompt 或 Router 明确 graph vs vector 分工

部署
□ AgentOS tracing + 工具 latency 日志
□ 环境变量外置，密钥不进 Git
□ docker-compose / K8s healthcheck

质量
□ 黄金集含多跳关系题（第 9 课 eval_cases）
□ 对比纯 RAG vs Hybrid 准确率
```

---

## 8. 动手练习

1. 启动 Neo4j 并 `python seed_demo_graph.py`，运行 `practice/agno_graph_agent.py`，问：「张三参与哪些项目？负责人是谁？」
2. 把 `Neo4jTools` 与 `OrgGraphToolkit` 各跑一遍，对比延迟、准确性与可解释性
3. 在 `instructions` 中写清路由规则，设计 5 个问题：3 个应走图谱、2 个应走 Knowledge
4. 为 `OrgGraphToolkit.search_people` 添加 Redis 缓存（可用内存 dict 模拟）
5. 启动 `agno_graph_agentos.py`，用 Swagger `/docs` 发一条会话请求
6. 列出你的项目适合「模式 B」还是「模式 C」，并说明理由
7. 启动 LightRAG Server，运行 `agno_lightrag_agent.py`，对比 `query_local` vs `query_global` 的回答差异
8. （可选）运行 `agno_lightrag_embedded.py`，理解嵌入式 `initialize_storages()` 与 `asyncio.run` 包装

---

## 9. 自检清单

- [ ] 能说出 Neo4jTools vs GraphRepository Toolkit 的适用场景
- [ ] 会设计 3–6 个语义清晰的只读图谱工具
- [ ] 理解 Hybrid 下 Knowledge 与 Graph Toolkit 的分工
- [ ] 掌握 context 预算、缓存、tool_call_limit 等优化手段
- [ ] 能将图谱 Agent 注册到 AgentOS 并配置环境变量
- [ ] 完成工程化 Checklist 自评
- [ ] 能说出 LightRAG HTTP Toolkit vs 嵌入式 Core 的选型
- [ ] 会根据问题类型选择 local / global / hybrid / mix

---

## 参考

- [Agno Neo4jTools](https://docs.agno.com/tools/toolkits/database/neo4j)
- [Agno Knowledge Overview](https://docs.agno.com/knowledge/overview)
- [Agno AgentOS](https://docs.agno.com/agent-os/introduction)
- [`learn-agno`](../../learn-agno/) — Agno 框架系统课程
- [`09_integration_rag_llm.md`](09_integration_rag_llm.md) — Hybrid RAG 原理
- [`10_deployment_and_operations.md`](10_deployment_and_operations.md) — 图谱运维基线
- [LightRAG GitHub](https://github.com/HKUDS/LightRAG) · [LightRAG API Server](https://github.com/HKUDS/LightRAG/blob/main/docs/LightRAG-API-Server.md) · [Programming With Core](https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md)
