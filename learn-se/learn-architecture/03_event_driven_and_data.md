# 第3课：事件驱动与数据架构

> **本课覆盖谱系 · 事件/消息族 + 数据族**：EDA → 消息驱动 → 事件溯源 → CQRS → CAP → 数据扩展  
> 上一课：[`02_microservices_and_distributed.md`](02_microservices_and_distributed.md) · 下一课：[`07_plugin_pipeline_space.md`](07_plugin_pipeline_space.md)

## 1. 事件驱动架构（EDA）

### 定义
系统组件通过**事件**进行异步通信：一个组件产生事件，其他组件订阅并响应。

```
Producer                Event Bus / Broker              Consumers
   │                         │                             │
   │── OrderCreated ───────▷│──────────▷ Inventory Svc   │
   │                         │──────────▷ Notification Svc│
   │                         │──────────▷ Analytics Svc   │
   │                         │                             │
```

### vs 请求-响应

| | 请求-响应 | 事件驱动 |
|---|---------|---------|
| 耦合 | 调用方需知道被调用方 | 发布者不知消费者 |
| 时序 | 同步等待 | 异步处理 |
| 扩展 | 加消费者需改调用方 | 加消费者只需订阅 |
| 一致性 | 强一致 | 最终一致 |

### 适用场景

- 订单创建 → 通知、库存、积分、分析（多下游）
- 用户行为追踪
- 数据同步管道
- 实时仪表盘

---

## 2. 事件模式

### 2.1 Event Notification（事件通知）

```
OrderSvc: "订单 #123 已创建"（只通知，不含详细数据）
InventorySvc: 收到后调用 OrderSvc API 获取详情
```

**特点：** 轻量事件，消费者自行拉取详情。

### 2.2 Event-Carried State Transfer（事件携带状态）

```
OrderSvc: "订单 #123 已创建 {user_id, items, total, ...}"（完整数据）
InventorySvc: 直接从事件获取所需信息，无需回调
```

**特点：** 减少回调，但事件体较大，需注意 schema 演进。

> Event Sourcing 的完整精讲见下文 **§4**；此处仅作模式对比。

---

## 3. 消息驱动架构（Message-Driven）

### 3.1 原理

核心思想：**组件通过消息队列传递「任务/命令」，生产者不等消费者处理完。**

```
Producer ──▶ [ Queue ] ──▶ Consumer A
                │
                └──▶ Consumer B（Topic 模式时）
```

**拆的维度**：通信——把同步调用变成异步投递，实现时间解耦和削峰。

### 3.2 消息驱动 vs 事件驱动

| 维度 | 消息驱动 | 事件驱动（EDA） |
|------|---------|----------------|
| 语义 | 「请做这件事」（命令/任务） | 「这件事已发生」（过去式事实） |
| 典型载体 | RabbitMQ Queue、Celery | Kafka Topic、Domain Event |
| 消费者 | 通常一个任务一个消费者 | 多个订阅者各自响应 |
| 状态归属 | 消息是传递手段，状态在各服务 | 事件本身可能是事实来源（ES） |
| 例子 | `SendEmail(task_id)` | `OrderCreated` |

**实践**：两者常混用——命令走 Queue（任务队列），事实走 Topic（事件总线）。详见 [`06_messaging_and_integration.md`](06_messaging_and_integration.md) 的选型与集成实战。

### 3.3 何时用消息驱动

- 异步通知、邮件/短信、报表生成
- 削峰填谷（秒杀下单先入队）
- 需要重试和死信队列的后台任务
- **不必用**：需要即时同步响应的核心读路径

---

## 4. 事件溯源（Event Sourcing）精讲

### 4.1 原理

**不存储当前状态，只存储导致状态变化的事件流；当前状态 = 从头重放事件。**

```
传统：accounts 表 → {id: 1, balance: 800}
事件溯源：account_events 表 → [
  {type: "AccountCreated", balance: 0},
  {type: "MoneyDeposited", amount: 1000},
  {type: "MoneyWithdrawn", amount: 200}
]
当前余额 = fold(events) → 800
```

**拆的维度**：数据——把「状态快照」换成「不可变事件账本」。

### 4.2 代码骨架

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class AccountCreated:
    account_id: str

@dataclass
class MoneyDeposited:
    amount: int

@dataclass
class MoneyWithdrawn:
    amount: int

Event = AccountCreated | MoneyDeposited | MoneyWithdrawn

@dataclass
class Account:
    account_id: str
    balance: int = 0
    version: int = 0

    def apply(self, event: Event) -> None:
        match event:
            case AccountCreated():
                self.balance = 0
            case MoneyDeposited(amount=a):
                self.balance += a
            case MoneyWithdrawn(amount=a):
                if self.balance < a:
                    raise ValueError("insufficient funds")
                self.balance -= a
        self.version += 1

def rebuild(events: List[Event]) -> Account:
    account = Account(account_id="acc-1")
    for e in events:
        account.apply(e)
    return account

# 修正错误 = 追加补偿事件，绝不改历史
events = [AccountCreated("acc-1"), MoneyDeposited(1000), MoneyWithdrawn(200)]
assert rebuild(events).balance == 800
```

### 4.3 与 CQRS 的搭配

```
写路径：Command → 聚合校验 → append 事件到 Event Store
读路径：Projection Worker 订阅事件 → 更新读模型（SQL/ES/Redis）
查询：直接查读模型，不重放全量事件
```

### 4.4 何时用 / 何时别用

| 适合 | 不适合 |
|------|--------|
| 金融流水、审计追溯 | 普通 CRUD 商品库 |
| 需要「时间旅行」调试 | 团队无事件建模经验 |
| 局部聚合（订单状态机） | 全系统一刀切 ES |

**代价**：事件 schema 演进、投影延迟、存储膨胀、调试心智成本高。

---

## 5. 消息队列

### 核心概念

| 概念 | 说明 |
|------|------|
| Producer | 消息发送方 |
| Consumer | 消息接收方 |
| Queue | 点对点（一条消息一个消费者） |
| Topic | 发布/订阅（一条消息多个消费者） |
| Broker | 消息中间件（Kafka, RabbitMQ, Redis Streams） |

### 选型对比

| | RabbitMQ | Kafka | Redis Streams |
|---|---------|-------|--------------|
| 模型 | Queue + Exchange | Log（持久化流） | Stream |
| 吞吐量 | 中 | 极高 | 高 |
| 顺序 | Queue 内有序 | Partition 内有序 | Stream 内有序 |
| 回溯 | 消费后删除 | 可回溯任意 offset | 可回溯 |
| 场景 | 任务队列、RPC | 大数据管道、日志 | 轻量事件、实时 |

### 消息可靠性

```
At-most-once:  可能丢消息，不会重复
At-least-once: 不会丢，可能重复（需幂等消费）
Exactly-once:  精确一次（最难，Kafka 事务）
```

**实践建议：** 大多数系统用 **At-least-once + 幂等消费**。

```python
# 幂等消费示例
def handle_order_created(event):
    if already_processed(event.id):
        return  # 重复消息，跳过
    process(event)
    mark_processed(event.id)
```

---

## 6. CQRS（Command Query Responsibility Segregation）

### 定义
**读写分离** — 写模型和读模型分开优化。

```
         Commands                    Queries
            │                           │
            ▼                           ▼
    ┌──────────────┐           ┌──────────────┐
    │  Write Model │── events─▷│  Read Model  │
    │  (Normalized)│           │ (Denormalized)│
    │  PostgreSQL  │           │  Elasticsearch│
    └──────────────┘           └──────────────┘
```

### 为什么？

| 问题 | CQRS 解决 |
|------|----------|
| 读写负载差异大 | 读库独立扩展 |
| 复杂查询影响写入 | 读模型预聚合 |
| 不同读视图 | 多个读模型投影 |

### 示例

```
写：PlaceOrder → Order Aggregate → 存 PostgreSQL
     ↓ 发布 OrderCreated 事件
读：OrderCreated → 更新 OrderListView（Redis/ES）
     前端查询 OrderListView → 快速列表展示
```

**注意：** CQRS 增加复杂度，读写差异不大时不需要。

---

## 7. 数据一致性

### CAP 定理

分布式系统最多同时满足以下三项中的两项：

- **C** (Consistency) — 所有节点看到相同数据
- **A** (Availability) — 每个请求都能得到响应
- **P** (Partition tolerance) — 网络分区时系统仍运行

```
        C
       / \
      /   \
     / CA \        ← 传统单机数据库（非分布式）
    /       \
   /  CP     \     ← MongoDB, HBase（分区时牺牲可用性）
  /           \
 A ────────── P
     AP              ← Cassandra, DynamoDB（分区时牺牲一致性）
```

**现实：** 网络分区必然发生 → 实际在 **CP** 和 **AP** 之间选择。

### BASE 理论

- **BA** (Basically Available) — 基本可用
- **S** (Soft state) — 软状态（允许短暂不一致）
- **E** (Eventually consistent) — 最终一致

**微服务和事件驱动的主流选择：** 接受最终一致性，通过 Saga/补偿保证业务正确。

---

## 8. 数据库架构模式

### 6.1 Database per Service

```
User Svc → User DB (PostgreSQL)
Order Svc → Order DB (PostgreSQL)
Search Svc → Search Index (Elasticsearch)
Analytics → Data Warehouse (BigQuery)
```

**规则：** 服务不能直接访问其他服务的数据库，只能通过 API 或事件。

### 6.2 读写分离

```
         Writes
            │
            ▼
      ┌──────────┐
      │  Master  │
      └────┬─────┘
           │ replication
     ┌─────┴─────┐
     ▼           ▼
  Replica 1   Replica 2
     ▲           ▲
     └─────┬─────┘
         Reads
```

### 6.3 分片（Sharding）

```
user_id % 4 = 0 → Shard 0
user_id % 4 = 1 → Shard 1
user_id % 4 = 2 → Shard 2
user_id % 4 = 3 → Shard 3
```

**挑战：** 跨分片查询、重新分片（re-sharding）。

### 6.4 缓存策略

| 模式 | 说明 | 风险 |
|------|------|------|
| Cache-Aside | 应用管缓存，miss 时读 DB | 缓存穿透/击穿 |
| Read-Through | 缓存层自动读 DB | 缓存层复杂 |
| Write-Through | 写时同步更新缓存 | 写延迟 |
| Write-Behind | 异步写 DB | 可能丢数据 |

```python
# Cache-Aside 典型流程
def get_user(user_id):
    user = cache.get(f"user:{user_id}")
    if user is None:
        user = db.query(user_id)
        cache.set(f"user:{user_id}", user, ttl=3600)
    return user
```

---

## 9. 事件驱动 + 微服务 完整示例

```
用户下单流程（事件驱动）：

1. [Order Svc]  接收 CreateOrder 命令
2. [Order Svc]  保存订单，发布 OrderCreated 事件
3. [Inventory Svc] 订阅 → 扣减库存 → 发布 InventoryReserved / Failed
4. [Payment Svc]  订阅 InventoryReserved → 扣款 → 发布 PaymentCompleted / Failed
5. [Order Svc]  订阅 PaymentCompleted → 更新订单状态为 Paid
6. [Notification Svc] 订阅 OrderCreated/Paid → 发邮件
7. [Analytics Svc] 订阅所有事件 → 写入数据仓库
```

**每个服务独立部署、独立数据库、通过事件协作。**

---

## 10. 动手练习

### 练习 1：选型

以下场景选 REST 同步、消息队列还是 Event Sourcing？

1. 用户注册后发欢迎邮件
2. 银行转账
3. 电商订单创建通知 5 个子系统
4. 需要查看账户任意历史时刻余额

<details>
<summary>参考答案</summary>

1. **消息队列** — 异步，注册不需等邮件
2. **REST + Saga** — 需要强一致和即时反馈（或 Saga + 事件）
3. **消息队列/事件驱动** — 一对多解耦
4. **Event Sourcing** — 天然支持时间旅行

</details>

### 练习 2：设计读模型

电商「商品搜索页」需要：名称、价格、评分、库存状态、缩略图。  
写模型在 PostgreSQL（规范化），如何设计 CQRS 读模型？

---

## 11. 自检清单

- [ ] 能区分消息驱动与事件驱动的语义差异
- [ ] 能解释事件溯源「状态=重放」的原理

- [ ] 能解释事件驱动 vs 请求-响应的区别
- [ ] 知道 Event Sourcing 的核心思想和适用场景
- [ ] 理解 CQRS 读写分离的价值
- [ ] 能解释 CAP 定理和 BASE 理论
- [ ] 知道 Database per Service 原则
- [ ] 了解常见缓存策略

---

## 12. 延伸阅读

- 《Designing Data-Intensive Applications》— Martin Kleppmann（DDIA，必读）
- 《Enterprise Integration Patterns》— Hohpe & Woolf
- 下一课：[`07_plugin_pipeline_space.md`](07_plugin_pipeline_space.md)
- 消息集成深化：[`06_messaging_and_integration.md`](06_messaging_and_integration.md)（阶段 D）

---

# 深入篇：事件驱动与数据架构的底层逻辑

## 1. 事件驱动 vs 请求-响应的本质差异

不是"同步 vs 异步"这么简单，而是**谁拥有真相**：

```
请求-响应：服务 A 调 B，B 的状态只有 B 知道，A 只能"问"
事件驱动：状态变化本身就是事实，广播给所有关心的人
```

事件驱动的真正收益：

1. **时间解耦**——发布者不等消费者（消息先落队列）；
2. **空间解耦**——发布者不知道消费者是谁、有几个；
3. **可重放**——事件流是"事实的账本"，可以重新消费（修 bug 后重算）。

代价也很明确：**一致性从"强"变"最终"**——业务必须能容忍"订单已创建但库存还没扣"的窗口。

## 2. 三种事件模式的选型（进阶）

| 模式 | 事件里带什么 | 何时用 |
|---|---|---|
| Event Notification | 只带"发生了"（ID） | 消费者要现查详情、事件很小 |
| Event-Carried State Transfer | 带完整数据 | 消费者不想回查、数据变化频繁 |
| Event Sourcing | 事件就是事实（状态=重放） | 需要审计/时间旅行/完整历史 |

**演进路径**：大部分系统从 Notification 开始；下游回查太频繁 → 升级为
Carried State；出现"要历史、要审计"需求 → 局部使用 Event Sourcing
（比如订单状态、账户流水），别全系统溯源。

## 3. 事件溯源（ES）的深层原理

核心不变量：**事件是只追加（append-only）的，永不修改、永不删除。**

```
状态 = fold(事件流)    当前状态是事件的投影（projection）
修复错误 = 追加修正事件，而不是修改历史
时间旅行 = 重放到任意 offset
```

三个实战要点：

1. **事件是产品**——schema 要版本化，消费方要兼容旧版本；
2. **投影（Read Model）与 CQRS 天然搭配**——事件流是写模型，
   各种投影是读模型；
3. **别全系统 ES**——只在"需要审计/历史"的聚合上用，
   一般业务（比如商品库存）用普通状态存储即可。

## 4. CAP 的深层：不是"三选二"，是"分区时的选择"

CAP 常被误解为"三选二"。准确理解：

1. **分区（P）不可避免**——网络一定会断；
2. 分区发生时，你只能在"一致性"和"可用性"之间选；
3. 没有分区时，C 和 A 可以同时满足。

所以真正的决策是：**网络分区时，你是拒绝响应（CP）还是返回旧数据（AP）？**

```
CP（MongoDB、HBase）：宁可不可用，不可给错答案
  → 金融、库存扣减、余额
AP（Cassandra、DynamoDB）：宁可旧数据，不可不响应
  → 购物车、点赞、评论、推荐
```

**一致性的光谱**（比"强/最终"更细）：

```
强一致 → 线性一致 → 顺序一致 → 最终一致
（越左越安全，越右越可用；业务目标决定你在哪）
```

## 5. 数据扩展三板斧的深层适用

| 方案 | 解决什么 | 代价 | 什么时候用 |
|---|---|---|---|
| 读写分离 | 读 QPS 高 | 复制延迟（读旧数据） | 读多写少、报表查询重 |
| 分片 | 单库容量/写 QPS 到顶 | 跨分片查询、再分片难 | 数据量巨大、写扩展 |
| 缓存 | 热点读 | 穿透/击穿/雪崩/一致 | 读多、重复读多 |

**优先级**：先缓存 → 再读写分离 → 最后分片。
分片是"不可逆手术"（再分片极痛），能拖就拖，拖不住才做。

**缓存三大坑的防御**：

```
穿透：查了不存在的数据 → 布隆过滤器/空值缓存
击穿：热点 key 过期 → 互斥锁重建/逻辑过期
雪崩：大批 key 同时过期 → 过期时间加随机偏移
```

## 6. 综合实战：订单事件流的正确姿势

```
CreateOrder 命令 → Order 聚合校验 → 写入订单表
  → 发布 OrderCreated（Carried State，带完整订单）
      → Inventory 订阅：扣库存，成功发 InventoryReserved / 失败发 Failed
      → Payment 订阅 Reserved：扣款，发 PaymentCompleted / Failed
      → Order 订阅 Completed：更新状态 Paid
      → Notification 订阅 Created/Paid：发通知
      → Analytics 订阅一切：进数仓

失败处理：Inventory 失败 → 发补偿事件 → Order 标记失败
幂等：每个事件带 event_id，消费者按 event_id 去重
审计：订单事件流进 Event Sourcing 存储，可重放
```

**核心纪律**：

- 事件是过去式名词（OrderCreated），不是命令（CreateOrder）；
- 一个事件一个 owner（只有 Order 服务能发 OrderCreated）；
- 消费者幂等——消息至少投递一次，消费必须能去重。
