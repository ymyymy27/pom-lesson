# 第6课：消息队列与系统集成

> **阶段 D · 消息与集成深化** · 覆盖谱系：Kafka/RabbitMQ / API Gateway / BFF / Saga  
> 与 [`03_event_driven_and_data.md`](03_event_driven_and_data.md) §3 消息驱动互补——本课侧重选型与集成实战  
> 上一课：[`04_architecture_decisions.md`](04_architecture_decisions.md) · 下一课：[`05_architecture_case_studies.md`](05_architecture_case_studies.md)

## 1. 何时需要消息队列

```
同步 HTTP 调用的问题：
  - 下游慢 → 上游阻塞
  - 下游挂 → 上游失败
  - 峰值流量 → 系统过载

消息队列解耦：
  生产者 → Queue → 消费者（异步、削峰、重试）
```

| 场景 | 推荐 |
|------|------|
| 异步通知 | RabbitMQ / SQS |
| 事件溯源 / 日志 | Kafka |
| 简单任务队列 | Redis + Celery（TaskFlow 已用） |
| 流处理 | Kafka / Pulsar |

---

## 2. Kafka vs RabbitMQ

| 维度 | Kafka | RabbitMQ |
|------|-------|----------|
| 模型 | 日志（持久化、可回放） | 队列（消费即删） |
| 吞吐 | 极高 | 高 |
| 顺序 | 分区内有序 | 队列有序 |
| 适用 | 事件流、CDC、Analytics | 任务分发、RPC 替代 |
| 复杂度 | 高 | 中 |

---

## 3. 集成模式

### API Gateway

```
Client → API Gateway → 路由到各微服务
              ↓
         认证、限流、日志、路由
```

工具：Kong、AWS API Gateway、Nginx + Lua

### BFF（Backend for Frontend）

```
Mobile App → Mobile BFF → 微服务
Web App    → Web BFF    → 微服务

BFF 聚合多个后端调用，返回前端友好的 DTO
```

### Saga（分布式事务）

```
转账 Saga：
  1. 扣款服务 → 成功 → 2. 入账服务 → 成功 → 完成
                    ↓ 失败
              补偿：退款

编排：中央协调器
编舞：各服务监听事件自行响应
```

---

## 4. TaskFlow 消息设计示例

```python
# 事件 Schema（Published Language）
{
  "event_type": "task.assigned",
  "version": "1.0",
  "timestamp": "2026-07-30T10:00:00Z",
  "data": {
    "task_id": "task_abc",
    "assignee_id": "user_42",
    "project_id": "proj_xyz"
  }
}

# Celery 任务（当前 TaskFlow 栈）
@shared_task(bind=True, max_retries=3)
def send_assignment_notification(self, task_id, assignee_id):
    try:
        notify_user(assignee_id, task_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

---

## 5. 动手练习

1. 为 TaskFlow「任务分配 → 通知 → 活动日志」画异步消息流
2. 对比 Celery+Redis vs Kafka 在 TaskFlow 规模的选型
3. 设计 `task.assigned` 事件的 Schema 和版本策略
4. 写 ADR：「是否引入 Kafka？」

---

## 6. 自检清单

- [ ] 能解释 MQ 解决的三个核心问题
- [ ] 能对比 Kafka 与 RabbitMQ
- [ ] 理解 API Gateway 与 BFF 的分工
- [ ] 知道 Saga 的编排 vs 编舞模式

---

**下一课** → [`05_architecture_case_studies.md`](05_architecture_case_studies.md)

---

# 深入篇：消息与集成的底层逻辑

## 1. 消息队列的真正价值：不止"削峰填谷"

削峰只是表面。MQ 的三大深层价值：

1. **时间解耦**——生产者不等消费者，任务可以"排队等做"；
2. **故障隔离**——下游挂了，消息在队列里躺着，恢复后继续消费（不丢不阻塞）；
3. **流量整形**——消费速率可控，保护下游（数据库、第三方 API）不被峰值打爆。

**判断是否该上 MQ 的问题**：

```
"这个动作需要立即完成吗？"
  不需要 → 可以考虑异步
"失败后怎么办？"
  可以重试 → 队列天然支持重试
"谁来做都行吗？"
  是 → 队列（点对点）分发
"多个下游都要吗？"
  是 → 主题（发布订阅）
```

## 2. Kafka vs RabbitMQ 的深层差异：日志 vs 队列

不是"两个 MQ 选哪个"，而是**两种完全不同的数据模型**：

| | RabbitMQ（队列） | Kafka（日志） |
|---|---|---|
| 本质 | 消息被消费后删除 | 事件永久追加，可重放 |
| 消费 | 一条消息给一个消费者 | 每个消费者组各自读全部 |
| 回溯 | 不支持 | 任意 offset 重放 |
| 削峰 | 好（消息即删） | 好（但消息会积压） |
| 审计/重算 | 不适合 | 天生适合 |

**选型本质**：

```
要"任务分发"（谁抢到谁做，做完即弃）→ RabbitMQ/SQS
要"事实记录"（事件流、可重放、多消费者）→ Kafka
要"轻量事件"（进程内/小规模）→ Redis Pub/Sub / Streams
```

一个经典误区：把 Kafka 当"大号任务队列"用——每条消息只消费一次，
却付出了日志系统的持久化和分区成本。**模型选错了，怎么调都别扭。**

## 3. Saga 的深层：编排与编舞的代码骨架

### 编排式（中央协调器）

```python
class OrderSaga:                       # 中央协调器
    def run(self, order_id):
        try:
            self.create_order(order_id)          # 1
            self.reserve_inventory(order_id)     # 2
            self.charge_payment(order_id)        # 3
        except PaymentError:
            self.compensate_inventory(order_id)  # 补偿 2
            self.compensate_order(order_id)      # 补偿 1
```

**优点**：流程集中可读、易测试；**缺点**：协调器是中心（可能变上帝组件）。

### 编舞式（事件驱动）

```python
class InventoryService:
    def on_order_created(self, event):           # 听事件自行反应
        try:
            self.reserve(event.order_id)
            publish("inventory.reserved", event)
        except StockError:
            publish("inventory.failed", event)

class PaymentService:
    def on_inventory_reserved(self, event):
        ...
```

**优点**：无中心、自治；**缺点**：流程散落，要靠事件契约约束。

**选择**：流程稳定、需要强控 → 编排；团队自治、流程会演进 → 编舞。

## 4. 集成模式的深层：EIP 的三个家族

企业集成模式（EIP）几十种模式，本质是三个家族：

```
1. 消息路由（谁该收到）：
   Content-Based Router（按内容路由）
   Message Filter（过滤）
   Recipient List（广播给指定列表）
   Splitter / Aggregator（拆分与聚合）

2. 消息转换（格式怎么变）：
   Message Translator（协议翻译）
   Enricher（补充数据）
   Normalizer（统一格式）

3. 端点适配（系统怎么接）：
   Channel Adapter（把系统接上通道）
   Messaging Gateway（业务代码的简单门面）
   Message Dispatcher（分发）
```

对应到设计模式：路由 ≈ 策略/责任链；转换 ≈ 适配器/装饰器；
端点 ≈ 门面/适配器。**架构模式就是设计模式在"消息世界"的投影。**

## 5. 实战：TaskFlow 该用什么（结合你的项目）

```
TaskFlow 规模（单团队、小流量）：
  异步通知 → Celery + Redis（够用）
  事件审计 → 先写事件表（PostgreSQL），未来量大了再上 Kafka
  集成外部 → API 网关层统一出口

触发升级 Kafka 的信号：
  □ 事件消费方 > 3 个独立服务
  □ 需要重放历史事件（修 bug 重算）
  □ 事件吞吐 > 1000/s
```

**核心纪律**：先记录事件（事件表/日志），再决定用什么系统承载。
**记录是免费的，迁移是便宜的；架构选型要留"记录"这个退路。**
