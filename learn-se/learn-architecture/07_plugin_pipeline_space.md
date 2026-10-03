# 第7课：微内核、管道与空间型架构

> **本课覆盖谱系 · 微内核族 + 管道族 + 空间型**：微内核 → 管道-过滤器 → 空间型 → 批处理 ETL  
> 上一课：[`03_event_driven_and_data.md`](03_event_driven_and_data.md) · 下一课：[`08_serverless_streaming_mesh.md`](08_serverless_streaming_mesh.md)

---

## 1. 微内核架构（Microkernel / Plugin Architecture）

### 1.1 原理

核心思想一句话：**核心系统最小化，能力全部由插件扩展。**

```
┌─────────────────────────────────────────┐
│              Core System                 │
│  - 插件注册表 / 生命周期管理              │
│  - 公共服务（配置、日志、认证）           │
│  - 扩展点契约（SPI）                      │
└───────┬──────────┬──────────┬──────────┘
        ▼          ▼          ▼
   Plugin A    Plugin B    Plugin C
   （能力）     （能力）     （能力）
```

三个关键角色：

| 角色 | 职责 |
|---|---|
| Core | 只做"必须集中"的事：启动、注册、调度、公共服务 |
| 扩展点（Extension Point） | 核心定义的接口契约，插件的"插槽" |
| Plugin | 实现扩展点，提供一项能力 |

隔离的变化：**能力集合**。加能力 = 加插件，核心零改动——这是 OCP（开闭原则）在架构级的体现。

关键纪律：

1. **核心不知道任何具体插件**——只认识扩展点接口；
2. **插件之间不直接通信**——通过核心的公共服务或事件；
3. **契约先行**——扩展点设计决定架构上限，契约错了全盘皆输。

### 1.2 代码分析

```python
from abc import ABC, abstractmethod

# 核心定义的扩展点（SPI）
class Plugin(ABC):
    name: str
    @abstractmethod
    def register(self, app: "CoreApp") -> None: ...
    @abstractmethod
    def run(self, ctx: dict) -> dict: ...

# 核心：只做注册与调度，不认识任何具体插件
class CoreApp:
    def __init__(self):
        self._plugins: dict[str, Plugin] = {}
        self.services: dict[str, object] = {}   # 公共服务注册表

    def load_plugin(self, plugin: Plugin) -> None:
        plugin.register(self)                    # 插件自己挂载服务
        self._plugins[plugin.name] = plugin

    def execute(self, name: str, ctx: dict) -> dict:
        if name not in self._plugins:
            raise KeyError(f"unknown plugin: {name}")
        return self._plugins[name].run(ctx)      # 按名调度

# 插件：实现扩展点
class AuditPlugin(Plugin):
    name = "audit"
    def register(self, app: CoreApp) -> None:
        app.services["audit"] = self             # 向核心注册公共服务
    def run(self, ctx: dict) -> dict:
        ctx["audited"] = True
        return ctx

# 使用：核心代码从不 import 具体插件
app = CoreApp()
app.load_plugin(AuditPlugin())
app.execute("audit", {"user": "alice"})
```

读代码只看两个点：

1. **CoreApp 里没有任何 AuditPlugin 的引用**——它只依赖 `Plugin` 接口；
2. 插件通过 `register(app)` 把自己挂进核心的公共服务——插件的"接线"由插件自己完成。

### 1.3 实战解析

**现实例子：**

| 系统 | 核心 | 插件 |
|---|---|---|
| VS Code | 编辑器壳 | 语言服务器、主题、LSP 客户端 |
| Jupyter | 内核管理 | Python/R/Julia kernel |
| Postgres | 数据库核心 | 扩展（pgvector 等） |
| LangChain | Chain/Agent 核心 | 模型、工具、检索器注册表 |
| 你正在用的 Codex | 平台 | skills / plugins / MCP servers |

**何时用：**

- 核心稳定、能力需要开放给第三方或并行团队；
- 能力需要热插拔（运行时启停）；
- 希望"平台"化——核心成为生态底座。

**代价：**

- 扩展点契约设计极难，错了要付出跨版本兼容的代价；
- 插件即代码——安全风险（恶意插件 = 任意代码执行）；
- 插件版本冲突、依赖地狱；
- 调试要跨核心与插件边界。

**与微服务的区别：** 插件和核心在**同一个进程**内共享内存与调用；
微服务是**独立进程**通过网络通信。插件更快，但隔离更弱。

---

## 2. 管道-过滤器架构（Pipe-and-Filter）

### 2.1 原理

核心思想一句话：**数据流经一串过滤器，每个过滤器只做一件事，管道负责搬运。**

```
输入 → [F1 清洗] → [F2 切分] → [F3 转换] → [F4 输出] → 结果
         管道       管道       管道       管道
```

四条铁律：

1. **过滤器不知道上下游是谁**——只认输入/输出数据格式；
2. **管道不加工数据**——只负责传递；
3. **过滤器可复用、可测试、可并行**——每个都是纯函数最好；
4. **顺序决定语义**——换顺序就是换行为。

隔离的变化：**处理步骤**。加一步 = 往管道里插一个过滤器，两端无感。

### 2.2 代码分析

```python
from typing import Callable, TypeVar

T = TypeVar("T")
Filter = Callable[[T], T]

def pipeline(data: T, *filters: Filter) -> T:
    for f in filters:          # 串行流过每个过滤器
        data = f(data)
    return data

# 三个可独立测试的过滤器
def normalize(text: str) -> str:
    return text.strip().lower()

def split_sentences(text: str) -> list[str]:
    return [s for s in text.split("。") if s]

def count_sentences(sentences: list[str]) -> int:
    return len(sentences)

# 组合成管道：复用任意过滤器，任意换顺序
result = pipeline("  你好。世界。", normalize, split_sentences, count_sentences)
print(result)  # 2
```

**批处理 / ETL 是管道的"定时批量"版本**：Extract（抽取）→ Transform（转换）→ Load（加载），
本质就是三个大过滤器串成管道。流式处理是管道的"持续"版本（见第 8 课 Kappa）。

### 2.3 实战解析

**现实例子：**

| 系统 | 管道 |
|---|---|
| Unix | `grep foo access.log \| sort \| uniq -c` |
| HTTP 中间件 | 请求依次穿过 CORS → 认证 → 限流 → 业务 |
| ETL | 抽取 → 清洗 → 转换 → 装载 |
| RAG 摄取 | 解析 → 切块 → Embedding → 写入向量库 |
| LLM 调用前后处理 | 输入规范化 → 调用模型 → 输出格式化 → 校验 |

**何时用：**

- 处理步骤顺序稳定、每步可独立理解；
- 需要复用步骤（不同管道共享过滤器）；
- 每步要单独测试、单独监控、单独并行。

**代价：**

- 数据格式契约是隐藏的耦合——F2 的输出必须是 F3 的输入；
- 调试要定位"卡在第几级"（管道日志很重要）；
- 跨进程/跨机器实现时，每级传递有序列化与网络开销；
- 不适合强交互流程（每步需要上下文决策时，管道太"直"）。

---

## 3. 空间型架构（Space-Based Architecture）

### 3.1 原理

核心思想一句话：**以空间换时间——把状态放进内存网格，靠多副本处理单元线性扩展。**

传统 Web 架构的瓶颈：所有请求最终打到**一个中心数据库**，加再多应用服务器，
数据库还是单点。空间型架构把"中心存储"干掉：

```
                ┌──────────────────────────────────┐
                │        Processing Unit × N       │
                │  ┌────────┐  ┌────────┐          │
 请求 ──负载均衡─▶│  │ 内存    │  │ 内存    │ ...      │
                │  │ 数据网格 │  │ 数据网格 │          │
                │  └────────┘  └────────┘          │
                │   数据复制同步（最终一致）           │
                └──────────────────────────────────┘
```

三个核心组件：

| 组件 | 职责 |
|---|---|
| Processing Unit | 无状态应用 + 本地内存数据副本 |
| Data Grid | 分布式内存缓存/复制（如 Hazelcast、Redis Cluster） |
| Virtual Middleware | 消息路由、数据复制、请求路由（如 Apache Zookeeper） |

**本质**：每个处理单元自带"数据分身"，请求落到哪个单元都能就地处理；
数据靠**异步复制**保持一致——牺牲强一致，换线性扩展。

### 3.2 代码分析（概念骨架）

```python
class DataGrid:
    """内存数据网格：本单元的数据副本（示意）"""
    def __init__(self):
        self._data: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._data.get(key)

    def set(self, key: str, value: str) -> None:
        self._data[key] = value
        self.replicate(key, value)      # 异步复制给其他单元

    def replicate(self, key: str, value: str) -> None:
        # 真实实现：通过消息中间件广播 (key, value, version)
        pass

class ProcessingUnit:
    """无状态处理单元：本地内存网格 + 业务逻辑"""
    def __init__(self, grid: DataGrid):
        self.grid = grid

    def handle_session(self, session_id: str) -> str:
        session = self.grid.get(session_id)
        if session is None:
            session = self.load_from_grid(session_id)   # 从网格/持久层加载
        return session
```

读代码只看一个点：**处理单元不直接打数据库**，先查本地内存网格；
命中就零网络开销，未命中才下沉。这就是"以空间换时间"。

### 3.3 实战解析

**现实例子：**

- 股票/期货高频交易系统（行情数据全在内存）；
- 秒杀/抢购系统（库存预热进内存网格，防数据库被打爆）；
- 游戏服务器（房间、玩家状态在内存，按房间路由）；
- 在线协作编辑器（文档状态在内存网格 + 复制）。

**何时用：**

- 高并发、低延迟、需要近乎线性扩展；
- 数据规模能进内存（或热数据能进）；
- 业务能容忍最终一致。

**代价：**

- 数据一致性工程复杂（版本冲突、复制延迟、脑裂）；
- 启动需要"预热"（从持久层加载数据到网格）；
- 不是所有数据都能放内存（冷数据仍要落库）；
- 运维心智高——业界用得少，属于"特定高并发场景的重武器"。

**与分片的区别：** 分片 = 每份数据**只属于一个**节点（有中心路由）；
空间型 = 每份数据在**多个**节点有副本（无中心、就地处理）。

---

## 4. 批处理 / ETL 架构（Batch Processing）

### 4.1 原理

核心思想：**按固定周期（小时/天）批量搬运、清洗、聚合数据**，与实时流式相对。

```
┌─────────┐    Extract     ┌─────────┐    Transform    ┌─────────┐    Load     ┌─────────┐
│ 业务 OLTP │ ──────────▶ │  暂存区   │ ─────────────▶ │ 清洗/聚合 │ ────────▶ │ 数仓/报表 │
│ (MySQL)  │   全量/增量    │ (S3/HDFS)│   SQL/Spark    │  作业     │   批量写入  │ (BigQuery)│
└─────────┘               └─────────┘                 └─────────┘             └─────────┘
        ↑ 定时调度（Airflow / cron / 云 Data Pipeline）
```

**拆的维度**：通信 + 数据——用**时间窗口**换**吞吐与简单性**。

### 4.2 与流式的关系

| | 批处理 / ETL | 流式（见 `08` Kappa） |
|---|-------------|---------------------|
| 延迟 | 分钟～天 | 秒～毫秒 |
| 复杂度 | 低（SQL 聚合成熟） | 高（状态、窗口、乱序） |
| 成本模型 | 定时跑大作业 | 常驻消费者 |
| 典型工具 | Airflow、dbt、Spark Batch | Flink、Kafka Streams |

**Lambda 架构**（`08` §2）：批 + 流双轨——批算历史全量，流算增量，查询时合并。Kappa 则主张「只有流，批是流的特例」。

### 4.3 代码骨架（概念）

```python
# 简化 ETL 管道：Extract → Transform → Load
def extract(source_db, watermark: str) -> list[dict]:
    return source_db.query("SELECT * FROM orders WHERE updated_at > %s", watermark)

def transform(rows: list[dict]) -> list[dict]:
    return [
        {"order_id": r["id"], "amount_usd": r["amount_cents"] / 100, "day": r["created_at"][:10]}
        for r in rows
    ]

def load(warehouse, rows: list[dict], run_id: str) -> None:
    warehouse.upsert("fact_orders", rows, idempotency_key=run_id)

def etl_job(watermark: str, run_id: str) -> str:
    rows = transform(extract(oltp, watermark))
    load(warehouse, rows, run_id)
    return max(r["updated_at"] for r in rows)  # 新 watermark
```

### 4.4 何时用 / 何时别用

- **用**：日报/月报、数仓建模、离线 ML 特征、成本敏感的大批量迁移
- **别用**：实时风控、实时大屏、用户期望秒级更新的场景
- **代价**：数据新鲜度差、失败重跑需幂等设计、与 OLTP 库争抢资源（应用只读副本）

---

## 5. 动手练习

1. **插件槽设计**：为一个「Markdown 渲染器」设计 3 个扩展点（语法扩展、输出格式、主题），画出 Core + Plugin 关系图。
2. **管道组合**：把 RAG 摄取拆成 4 个 Filter（解析 → 分块 → 向量化 → 入库），说明哪些 Filter 可并行、哪些必须串行。
3. **批 vs 流**：电商「每日 GMV 报表」用批还是流？「库存扣减」呢？各写一句理由。

---

## 6. 自检清单

- [ ] 能说出微内核架构的三角色（核心/扩展点/插件）和铁律
- [ ] 能手写一个插件注册 + 调度的最小骨架
- [ ] 能解释管道-过滤器的四条铁律
- [ ] 能说出 RAG 摄取管道由哪几个过滤器组成
- [ ] 能解释空间型架构"以空间换时间"的含义
- [ ] 能区分批处理 ETL 与流式处理的延迟与复杂度权衡
- [ ] 能说出 Lambda 与 Kappa 在批流关系上的分歧（预习 `08`）

**下一课** → [`08_serverless_streaming_mesh.md`](08_serverless_streaming_mesh.md)

---

## 7. 延伸阅读

- 《Software Architecture Patterns》— Mark Richards（微内核、管道章节）
- 《Designing Data-Intensive Applications》— 第 10–12 章（批处理 vs 流处理）
- 关联：`learn-data-systems/03_batch_and_stream_processing.md`

---

# 深入篇：插件与管道族的底层逻辑

## 1. 微内核的深层：OCP 在架构级的落地

扩展点设计是微内核的 **唯一不可逆决策**。改扩展点 = 改核心契约 = 所有插件跟着改。
好的扩展点：**稳定、窄、面向能力**（`render`、`export`），而非面向实现（`MarkdownRendererV2`）。

## 2. 管道的深层：Unix 哲学在系统级

「只做一件事，做好；通过管道组合」——Filter 必须 **无共享可变状态**，否则并行和测试都会崩。
RAG、CI/CD、日志处理都是同一套管道思维。

## 3. 空间型的深层：复制 vs 分片

空间型用 **多副本 + 本地处理** 消除中心路由；代价是冲突解决和脑裂。
只在「读多写少、延迟敏感、数据能进内存」时值得上。

## 4. 批处理的深层：用延迟换正确与简单

批处理的力量在于 **幂等重跑**——同一 `run_id` 覆盖写入，失败就整批重跑。
流式则要处理 **乱序、重复、迟到数据**；别在不需要实时的地方付流式的复杂度税。
