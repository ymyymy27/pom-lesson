# 第9课：数据网格、前端架构与对等集成

> **本课覆盖谱系 · 数据族 + 前端族 + 集成族**：数据网格 → MVC/MVP/MVVM/微前端 → ESB → P2P  
> 上一课：[`08_serverless_streaming_mesh.md`](08_serverless_streaming_mesh.md) · 下一课：[`10_ai_agent_architectures.md`](10_ai_agent_architectures.md)

---

## 1. 数据网格（Data Mesh）

### 1.1 原理

核心思想一句话：**把微服务的思路用到数据上——数据按领域分权自治，平台负责治理。**

传统数据平台（集中式数据仓库/数据湖）的问题：

```
一个中央数据团队 + 一个中央平台
  → 业务团队等数据团队排期（瓶颈）
  → 数据团队不懂业务语义（质量差）
  → 一张中央表谁都改（混乱）
```

数据网格的四个原则：

| 原则 | 含义 |
|---|---|
| 领域所有权 | 数据归业务领域团队所有（像微服务归团队所有） |
| 数据即产品 | 每个数据域要像产品一样：有文档、SLA、可发现 |
| 自助平台 | 平台团队提供工具链（摄取/转换/血缘），不替业务做数据 |
| 联邦治理 | 全局标准（命名、安全、合规）由联邦制定，执行分散 |

```
┌──────────────────────────────────────────────┐
│             Data Platform（平台团队）           │
│  工具：摄取、转换、血缘、目录、安全             │
└──────┬──────────────┬──────────────┬─────────┘
       ▼              ▼              ▼
  ┌─────────┐   ┌─────────┐   ┌─────────┐
  │ 订单数据域 │   │ 用户数据域 │   │ 支付数据域 │
  │（订单团队） │   │（用户团队） │   │（支付团队） │
  └─────────┘   └─────────┘   └─────────┘
   数据即产品：文档 + SLA + 可发现 + 可消费
```

隔离的变化：**数据的所有权与生产方式**。每个域独立演进，平台只提供"道路"不提供"货物"。

### 1.2 代码分析（概念）

```python
# 数据域 = 一个可独立发布的"数据产品"（概念骨架）
@dataclass
class DataProduct:
    domain: str            # 所属领域（订单/用户/支付）
    name: str
    owner_team: str        # 谁负责（域所有权）
    schema_version: str    # 契约版本（数据即产品）
    sla: dict              # 新鲜度/可用性承诺

    def publish(self) -> None:
        # 注册到数据目录（可发现性）
        catalog.register(self)

    def serve(self) -> Stream:
        # 通过事件流/API 对外提供（数据可消费）
        return topic_stream(self.domain, self.name)

# 联邦治理：全局标准，不碰业务数据
def validate_contract(product: DataProduct) -> bool:
    return (product.schema_version in supported_versions
            and "owner_team" in product.__dict__)
```

### 1.3 实战解析

**何时用：**

- 组织有多个业务域，数据需求远超中央团队产能；
- 需要"数据民主化"——每个团队自己生产、消费自己的数据产品；
- AI 场景：特征平台、RAG 知识库按域治理（每个业务域自己维护文档数据域）。

**何时别用：**

- 组织小、数据域单一——数据网格的治理成本是负担；
- 没有清晰的领域边界。

**代价：**

- 治理纪律要求高（没有联邦标准就是数据混乱）；
- 平台工具链建设成本大；
- "数据即产品"的 SLA 维护很重。

**与数据中台的区别：** 中台 = 集中式共享能力（中央团队）；数据网格 = 去中心化
（域自治 + 平台赋能）。中台适合"复用为主"，网格适合"规模化自治"。

---

## 2. 前端架构：MVC / MVP / MVVM 与微前端

### 2.1 原理

前端架构的核心问题永远是同一个：**界面（View）、状态（Model）、交互逻辑（Controller/Presenter/ViewModel）如何分离，依赖方向如何定。**

| 风格 | 结构 | 依赖方向 | 特点 |
|---|---|---|---|
| MVC | Model + View + Controller | View 读 Model，Controller 改 Model | 经典，但 View 和 Model 容易纠缠 |
| MVP | Presenter 持有 View 接口 | View 完全被动，Presenter 驱动 | 可测试性最好（View 可 mock） |
| MVVM | ViewModel 暴露状态绑定 | View 绑定 ViewModel，双向绑定 | 前端主流（React/Vue 状态驱动） |

现代前端（React/Vue）本质是 **MVVM 的声明式版本**：

```
数据（State）→ 渲染函数 → UI
      ↑                      │
      └── 事件（onClick）────┘
UI 是状态的函数：UI = f(state)
```

**微前端**：多个前端团队独立开发、独立部署，最终在壳应用里组合。

```
┌──────────────────────────────────────┐
│          Shell（壳应用）               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │ 商品团队  │ │ 订单团队  │ │ 支付团队  │ │
│  │ 独立构建  │ │ 独立构建  │ │ 独立构建  │ │
│  └─────────┘ └─────────┘ └─────────┘ │
└──────────────────────────────────────┘
路由级/微件级组合，运行时加载
```

### 2.2 代码分析

```python
# MVVM 思想的最小骨架：状态 → 视图，事件 → 改状态
class ViewModel:
    def __init__(self):
        self.state = {"count": 0}
        self.listeners = []

    def subscribe(self, render):
        self.listeners.append(render)

    def increment(self):
        self.state["count"] += 1
        for render in self.listeners:      # 状态变了，通知视图重渲染
            render(self.state)

# 视图是纯函数（React 式）：UI = f(state)
def render(state):
    return f'<button>{state["count"]}</button>'

vm = ViewModel()
vm.subscribe(render)
vm.increment()   # 自动重新渲染
```

```python
# 微前端概念：壳应用按路由加载子应用
def mount_micro_frontend(route: str) -> None:
    apps = {
        "/catalog": load_module("catalog_app"),
        "/orders":  load_module("orders_app"),
    }
    apps[route].mount("#root")   # 独立构建的模块运行时挂载
```

### 2.3 实战解析

**MVVM 何时用：** 复杂交互界面、状态驱动 UI——现代前端框架默认选择；
**MVP 何时用：** 需要把 View 完全 mock 掉的强测试场景（桌面端、金融终端）。

```python
# MVP 最小骨架：View 被动，Presenter 驱动
class OrderView(Protocol):
    def show_total(self, amount: str) -> None: ...

class OrderPresenter:
    def __init__(self, view: OrderView, repo: OrderRepo):
        self.view = view
        self.repo = repo

    def on_load(self, order_id: str) -> None:
        order = self.repo.get(order_id)
        self.view.show_total(f"¥{order.total:.2f}")  # Presenter 决定展示什么
```

**微前端何时用：** 多个团队维护一个大前端、各团队技术栈不同、需要独立发版；
**微前端何时别用：** 小团队、单一技术栈——运行时组合的复杂度 > 收益。

**代价：** 微前端的样式/依赖隔离、共享状态、性能（多框架加载）都是坑。

---

## 3. 企业集成总线（Hub-and-Spoke / EAI）

### 3.1 原理

核心思想一句话：**所有系统都接入一个中心总线，由总线负责协议转换与消息路由。**

```
┌────────┐   ┌────────┐   ┌────────┐
│ ERP     │   │ CRM     │   │ 自研系统 │
└───┬────┘   └───┬────┘   └───┬────┘
    └──────┬─────┴─────┬──────┘
        ┌──▼───────────▼──┐
        │    ESB 总线      │  ← 协议转换、路由、编排、监控
        └──┬───────────┬──┘
    ┌──────┴─────┬─────┴──────┐
┌───▼────┐   ┌───▼────┐   ┌───▼────┐
│ 数据仓库 │   │ 消息系统 │   │ 外部伙伴 │
└────────┘   └────────┘   └────────┘
```

隔离的变化：**系统间的协议与格式差异**。接入新系统 = 接总线，老系统不动。

### 3.2 实战解析

**何时用：**

- 大量异构遗留系统要互联（SAP、Oracle、自研）；
- 需要中心化监控与审计的集成场景（金融、制造）。

**何时别用：**

- 系统少——总线成为单点故障和瓶颈；
- 现代微服务场景——总线会变成"分布式单体"（所有流量过中心）。

**代价：** 总线本身是单点、性能瓶颈、变成"上帝组件"；
现代替代是事件驱动 + 消息队列（去中心化集成）。

---

## 4. 点对点架构（Peer-to-Peer / P2P）

### 4.1 原理

核心思想一句话：**没有中心服务器——每个节点既是客户端又是服务端。**

```
中心化：所有请求打向中心
        C1 ─┐
        C2 ─┼─▶ Server（单点/瓶颈）
        C3 ─┘

去中心化：节点互相服务
        N1 ⇄ N2
        ⇅    ⇅
        N3 ⇄ N4
        每个节点都存数据、都提供服务
```

两种形态：

| 形态 | 说明 |
|---|---|
| 结构化 P2P | 用分布式哈希表（DHT）精确定位数据在哪个节点（Chord/Kademlia） |
| 非结构化 P2P | 泛洪传播，适合搜索场景（早期 Gnutella） |

### 4.2 实战解析

**现实例子：** BitTorrent（文件分片 + 节点互传）、区块链（账本副本全节点）、
WebRTC 实时通信（浏览器直连）。

**何时用：**

- 海量节点共享资源（文件、带宽、算力）；
- 抗审查/抗单点故障；
- 低延迟直连（WebRTC 视频通话）。

**代价：**

- 一致性极难（无中心权威）；
- 节点可信度问题（防作弊、防污染）；
- 监管与运维困难。

**AI 相关：** 联邦学习本质是"数据不出本地 + 模型参数聚合"的 P2P/半中心化思路；
去中心化推理网络（节点贡献 GPU）是 P2P 在新领域的新应用。

---

## 5. 动手练习

1. 为「订单域」设计一个 Data Product 契约（owner、schema 版本、SLA 字段）。
2. 用表格对比 MVC / MVP / MVVM 在你熟悉的前端框架中各对应什么层。
3. 画 SOA 的 Hub-Spoke 与 P2P 拓扑对比图，各写一条适用场景。

---

## 6. 自检清单

- [ ] 能说出数据网格四原则（域所有权/数据即产品/自助平台/联邦治理）
- [ ] 能区分数据网格与数据中台
- [ ] 能说出 MVC / MVP / MVVM 的依赖方向差异
- [ ] 理解"UI = f(state)"的现代前端本质
- [ ] 知道企业总线为何会被事件驱动替代
- [ ] 能说出 P2P 的代价（一致性/可信度）

**下一课** → [`10_ai_agent_architectures.md`](10_ai_agent_architectures.md)

---

## 7. 延伸阅读

- 《Data Mesh》— Zhamak Dehghani
- 《Micro Frontends in Action》
- 关联：`learn-fullstack/` 前端分层实践

---

# 深入篇：数据、前端与集成的底层逻辑

## 1. 数据网格的深层：组织问题，不是工具问题

没有域团队 ownership，买再多数据平台也只是「中央团队换个名字」。
数据网格成功的标志是：**业务团队能自助发布和消费数据产品**，平台只提供 paved road。

## 2. 前端架构的深层：UI = f(state)

MVC/MVP/MVVM 的本质分歧是 **谁持有状态、谁驱动更新**。
React/Vue 的声明式渲染 = MVVM；微前端则是 **部署边界** 问题，与 MVVM 正交。

## 3. ESB vs 事件驱动的深层

ESB 把 **智能管道**（编排、转换）放在中心；现代集成主张 **dumb pipe + 智能端点**。
遗留 ESB 不必一夜拆掉——绞杀者模式（`04`）逐步旁路新流量即可。

## 4. P2P 的深层：用一致性换去中心

没有权威节点，就要在协议层解决 **发现、信任、冲突**——区块链和 BitTorrent 是两种典型答案。
联邦学习是 P2P 思想在 AI 数据隐私场景的应用。
