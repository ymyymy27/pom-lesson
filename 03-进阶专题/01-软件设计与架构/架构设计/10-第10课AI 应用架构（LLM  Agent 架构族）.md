> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第10课：AI 应用架构（LLM / Agent 架构族）

> **本课覆盖谱系 · AI 应用族**：RAG → Agent 循环 → 编排器-工作者 → 多智能体 → LLM 网关  
> AI 架构是经典风格的组合：管道 × 事件驱动 × 微内核 × 状态机  
> 上一课：[`09-第9课数据网格前端架构与对等集成.md`](09-第9课数据网格前端架构与对等集成.md) · 下一课：[`04-第4课架构决策与演进.md`](04-第4课架构决策与演进.md)

---

## 1. RAG 管道架构

### 1.1 原理

RAG（检索增强生成）的本质：**模型不知道的知识，用检索补上；模型不用重训，知识随时更新。**

它由两条管道组成：

```
离线摄取管道（Pipe-and-Filter）：
文档 → 解析 → 切块 → Embedding → 写入向量库

在线问答管道：
问题 → 检索（向量 + 关键词 + 重排）→ 组装上下文 → LLM 生成 → 输出
```

关键架构决策：

| 决策 | 选项 | 权衡 |
|---|---|---|
| 摄取同步还是异步 | 同步 / 异步任务队列 | 大文档必须异步（30s+ 解析） |
| 检索粒度 | 段落 / 小 chunk / 父子分块 | 越小越准，越大上下文越全 |
| 检索方式 | 纯向量 / 混合（BM25+向量） / 重排 | 混合更稳，重排加延迟 |
| 生成上下文 | 全量塞入 / 摘要 / 分层检索 | 塞得多 = 贵且慢 |
| 多租户隔离 | tenant_id 贯穿索引与查询 | 数据边界 = 安全边界 |

### 1.2 代码分析

```python
class IngestionPipeline:
    """离线摄取管道：每个过滤器可独立替换"""
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def run(self, doc_bytes: bytes) -> str:
        text = self.parse(doc_bytes)          # F1: 解析（PDF/Word）
        chunks = self.split(text)             # F2: 切块
        vectors = self.embed(chunks)          # F3: Embedding
        return self.vector_store.add(vectors) # F4: 索引

class RetrievalService:
    """在线问答：检索与生成分离，可独立扩展/替换模型"""
    def __init__(self, vector_store, reranker, llm):
        self.vector_store = vector_store
        self.reranker = reranker
        self.llm = llm

    def answer(self, question: str, tenant_id: str) -> dict:
        candidates = self.vector_store.search(
            question, tenant_id=tenant_id, top_k=50)
        top = self.reranker.rerank(question, candidates)[:5]  # 重排
        context = "\n".join(c.text for c in top)
        answer = self.llm.generate(question, context)
        return {"answer": answer, "sources": [c.id for c in top]}  # 可溯源
```

### 1.3 实战解析

**架构要点：**

1. **摄取与问答分离**——摄取可异步、可重跑；问答延迟只由在线管道决定；
2. **LLM 走代理**——限流、缓存、Fallback（见第 5 节）；
3. **答案必须可溯源**——返回引用 chunk，这是企业级 RAG 的底线；
4. **先检索后生成，检索质量决定上限**——烂检索给再强的模型也是烂答案。

**何时升级：** 单库检索 → 多路召回（向量 + 关键词 + 知识图谱）→ 多级缓存 → Agent 化检索（工具调用）。

---

## 2. 单 Agent 编排架构（Agent Loop）

### 2.1 原理

单个 Agent 的本质是一个**带工具和记忆的状态机主循环**：

```
┌──────────────────────────────────────┐
│            Agent 主循环               │
│                                      │
│  用户输入 → 规划 → 调用LLM → 需要工具？ │
│              ▲          │      │      │
│              │          │      ▼      │
│              │          │  执行工具    │
│              └──────────┴── 记录结果    │
│                                      │
│  （状态：thinking / tool_calling / done）│
└──────────────────────────────────────┘
```

架构组件：

| 组件 | 职责 | 对应经典模式 |
|---|---|---|
| 主循环 | 规划-行动-观察-反思 | 模板方法 |
| 工具注册表 | 暴露可调用工具 | 微内核/插件 |
| 记忆（短期/长期） | 上下文与知识 | 状态 + 备忘录 |
| 生命周期 | 状态流转与广播 | 状态 + 观察者 |
| Guardrails | 输入输出安全 | 责任链 |

### 2.2 代码分析

```python
class Tool(ABC):
    name: str
    @abstractmethod
    def run(self, **kwargs) -> str: ...

class Agent:
    def __init__(self, llm, tools: list[Tool], memory):
        self.tools = {t.name: t for t in tools}
        self.memory = memory
        self.llm = llm

    def run(self, user_input: str) -> str:
        self.memory.add_user(user_input)
        for _ in range(10):                          # 主循环（有限步）
            response = self.llm.call(self.memory.messages(), self.tool_schemas())
            if response.tool_call:
                result = self.tools[response.tool_call.name].run(**response.tool_call.args)
                self.memory.add_tool(result)         # 观察 → 下一轮
            else:
                return response.content
        raise TimeoutError("agent loop limit")
```

### 2.3 实战解析

**三个最容易失控的点：**

1. **循环失控**——必须限制步数、超时、token 预算；
2. **工具安全**——工具即权限，工具列表要最小化，工具调用要审计（命令模式）；
3. **状态恢复**——长任务要检查点（备忘录），失败从安全点重试。

**架构倾向：** 能单 Agent 解决就别多 Agent——每个 Agent 是成本、延迟和失控面。

---

## 3. 编排器-工作者架构（Orchestrator-Worker）

### 3.1 原理

一个中心调度者拆解任务，多个专业工作者各自执行：

```
                ┌──────────────┐
                │  Orchestrator │ ← 拆解、分配、汇总
                └──────┬───────┘
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌─────────┐  ┌─────────┐  ┌─────────┐
    │ Researcher│  │  Coder  │  │ Reviewer │ ← 专业工作者
    └─────────┘  └─────────┘  └─────────┘
        结果回传 → Orchestrator 判断下一步
```

对应经典模式：**中介者 + 模板方法**。编排器是中介者（集中协调），
每个工作者是模板方法的子类（共享主循环骨架，实现自己的规划/执行）。

### 3.2 实战解析

**何时用：**

- 任务天然可分解（研究报告：检索 + 分析 + 写作 + 审查）；
- 每个子任务需要不同的工具/提示词/模型；
- 需要清晰的进度汇报与人工介入点。

**关键设计：**

1. **契约先行**——工作者之间不直接通信，只和编排器交换结构化结果（JSON schema）；
2. **失败隔离**——一个工作者失败不影响其他，编排器决定重试/降级/终止；
3. **成本控制**——编排器决定"哪些子任务值得用 LLM"，简单的子任务用代码完成。

---

## 4. 多智能体协作架构（Multi-Agent）

### 4.1 原理

多个 Agent 之间**直接通信**或**通过共享黑板/消息总线**协作。两种主流形态：

```
黑板模式（共享状态）：
  Agent A 写 → 黑板（共享内存/数据库）→ Agent B 读
  （解耦最强，适合异步协作，如 LangGraph 的共享状态）

消息模式（Agent 间直接发消息）：
  Agent A ──消息──▶ Agent B ──消息──▶ Agent C
  （流程明确，适合流水线协作，如 OpenAI Agents SDK 的 Handoffs）
```

和编排器-工作者的区别：

| | 编排器-工作者 | 多智能体协作 |
|---|---|---|
| 谁决策 | 中心编排器 | 每个 Agent 自主决策 |
| 通信 | 都找编排器 | Agent 之间直接/黑板 |
| 适用 | 任务可预先拆解 | 动态协商、分工不明 |
| 失控风险 | 低 | 高（要设护栏） |

### 4.2 实战解析

**何时别用多智能体（大多数时候）：**

- 单一 LLM + 工具调用能解决 → 别拆；
- 团队没有能力监控多 Agent 的 token 成本与失控；
- 任务边界不清晰 → 多 Agent 变成"多个糊涂虫开会"。

**必须用时：**

- 角色需要隔离的知识/权限（如审查 Agent 不能用写代码 Agent 的工具）；
- 任务天然需要多角色轮转（辩论、审查、专家咨询）。

---

## 5. LLM 网关 / 模型路由架构

### 5.1 原理

LLM 调用是所有流量的咽喉。网关把"调用模型"这个动作统一治理：

```
应用 → LLM Gateway
         ├── 路由（按任务/成本/延迟选模型）
         ├── 限流（Token Bucket / 配额）
         ├── 缓存（相同请求直接返回）
         ├── 重试 + Fallback（主模型挂了换备用）
         ├── 审计（谁调了什么、花了多少钱）
         └── 语义缓存 / Prompt 版本管理
```

对应经典模式：**代理 + 装饰器 + 适配器 + 门面**全家桶。

### 5.2 代码分析

```python
class LLMGateway:
    """统一模型入口：路由 + 缓存 + Fallback"""
    def __init__(self, providers: dict[str, ChatModel], cache):
        self.providers = providers
        self.cache = cache

    def chat(self, request: ChatRequest) -> str:
        cached = self.cache.get(request.key())
        if cached:
            return cached                        # 缓存代理

        for provider in self.route(request):     # 按策略选模型（策略）
            try:
                result = provider.chat(request)  # 适配器统一接口
                self.cache.set(request.key(), result)
                return result
            except ProviderError:
                continue                          # Fallback 到下一个
        raise AllProvidersFailed()
```

### 5.3 实战解析

**什么时候必须上网关：**

- 多模型混用（主模型 + 便宜模型 + 本地模型）；
- 需要成本可见（每租户 token 用量、费用分摊）；
- 需要 Failover（供应商故障不能拖垮业务）；
- 需要缓存/限流保护后端配额。

**企业级加分项：** 语义缓存（相似问题复用答案）、Prompt 版本管理、
灰度切换模型（新模型 10% 流量试跑）、敏感内容审计。

---

## 6. AI 架构选型速查

| 需求 | 架构 |
|---|---|
| 知识问答、可溯源 | RAG 管道 |
| 单任务自动完成 | 单 Agent 循环 |
| 任务可拆解、需专业分工 | 编排器-工作者 |
| 角色需隔离权限/多角色协商 | 多智能体（慎用） |
| 多模型/成本治理 | LLM 网关 |
| 文档异步摄取 | 消息队列 + Worker（管道） |
| Agent 全流程可观测 | 事件流 + 检查点 |

---

## 7. 动手练习

1. 为一个「内部文档问答」画出 RAG 离线与在线两条管道，标出每个 Filter。
2. 设计一个 Agent 主循环：列出 Plan → Act → Observe → Reflect 各步可能调用的工具。
3. 说明什么场景用「编排器-工作者」、什么场景**不该**上多智能体。

---

## 8. 自检清单

- [ ] 能画出 RAG 的离线/在线两条管道
- [ ] 能说出 Agent 主循环的四个环节和对应模式
- [ ] 能区分编排器-工作者与多智能体
- [ ] 知道多智能体什么时候不该用
- [ ] 能列出 LLM 网关的六项职责
- [ ] 能在经典架构风格与 AI 架构之间互相翻译

**下一课** → [`04-第4课架构决策与演进.md`](04-第4课架构决策与演进.md)（阶段 D · 架构决策）

---

## 9. 延伸阅读

- `02-方向选修/02-AI应用/参考资料/05-AI工程化/` — AI 工程实践
- Anthropic / OpenAI Agent 设计指南
- 关联：`05-第5课架构案例实战.md` 案例 4（RAG 平台）

---

# 深入篇：AI 架构与经典风格的映射

## 1. RAG = 管道-过滤器 + 检索适配器

摄取链是 `07` 的管道；向量库是 Driven Adapter；LLM 是最后一个 Filter。
换 embedding 模型 = 换 Filter，不动整体拓扑。

## 2. Agent Loop = 状态机 + 工具端口

Agent 核心是 **有状态的循环**——与无状态 FaaS 相反，需要检查点、会话存储。
工具调用接口 = 六边形的 Port；每个 Tool 是 Adapter。

## 3. 多智能体的深层：默认别用

多 Agent 的协调成本 > 大多数业务收益。优先 **编排器-工作者**；
只有角色权限、协商流程确实需要隔离时才考虑多 Agent。

## 4. LLM 网关 = API 网关 + 模型路由

与 `02`/`06` 的 API Gateway 同构：认证、限流、路由、聚合、Fallback——
只是把 upstream 从微服务换成 LLM 供应商。
