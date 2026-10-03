# 第3课：战术模式与应用层

## 1. 分层架构在 DDD 中的体现

```
┌─────────────────────────────────────────┐
│  用户界面层 UI / API                     │  ← HTTP、CLI
├─────────────────────────────────────────┤
│  应用层 Application                      │  ← 用例编排，无业务规则
├─────────────────────────────────────────┤
│  领域层 Domain                           │  ← 实体、聚合、领域服务
├─────────────────────────────────────────┤
│  基础设施层 Infrastructure               │  ← DB、消息队列、外部 API
└─────────────────────────────────────────┘

依赖方向：UI → Application → Domain ← Infrastructure
                              ↑
                    Domain 不依赖任何外层
```

---

## 2. Repository（仓储）

### 作用
**聚合的持久化抽象**，领域层定义接口，基础设施层实现。

```python
# domain/repositories.py
class OrderRepository(ABC):
    @abstractmethod
    def get(self, order_id: str) -> Order | None: ...

    @abstractmethod
    def save(self, order: Order) -> None: ...


# infrastructure/sql_order_repo.py
class SqlOrderRepository(OrderRepository):
    def __init__(self, session):
        self._session = session

    def get(self, order_id: str) -> Order | None:
        row = self._session.query(OrderModel).get(order_id)
        return self._to_domain(row) if row else None

    def save(self, order: Order) -> None:
        row = self._to_model(order)
        self._session.merge(row)
        self._session.commit()
```

### 规则

- **一个聚合一个 Repository** — 不为 LineItem 单独建 Repository
- **只 load/save 聚合根** — `get(order_id)`, `save(order)`
- **领域层不感知 SQL/ORM** — 映射在 infrastructure

---

## 3. Domain Event（领域事件）

### 作用
聚合内发生**业务上重要的事**，通知其他上下文或触发副作用。

```python
@dataclass(frozen=True)
class OrderSubmitted:
    order_id: str
    customer_id: str
    total: Money
    occurred_at: datetime = field(default_factory=datetime.utcnow)


class Order:
    def submit(self):
        # ... 业务逻辑 ...
        self._events.append(OrderSubmitted(...))

    def collect_events(self) -> list:
        events, self._events = self._events, []
        return events
```

### 发布流程

```
1. 聚合根产生事件 → collect_events()
2. 应用服务 save 聚合后发布事件
3. 事件总线分发给本上下文处理器 + 其他上下文
```

```python
class SubmitOrderHandler:
    def __init__(self, repo: OrderRepository, event_bus: EventBus):
        self._repo = repo
        self._bus = event_bus

    def handle(self, cmd: SubmitOrderCommand):
        order = self._repo.get(cmd.order_id)
        if not order:
            raise NotFoundError()
        order.submit()
        self._repo.save(order)
        for event in order.collect_events():
            self._bus.publish(event)
```

### 命名规范

- 过去式：`OrderSubmitted`, `PaymentCompleted`, `TaskAssigned`
- 含必要数据，避免消费者回调查库

---

## 4. Application Service（应用服务）

### 职责
- **编排**用例流程（load → 调用领域 → save → 发事件）
- **不包含**业务规则（规则在聚合里）
- 处理事务边界

```python
@dataclass
class PlaceOrderCommand:
    customer_id: str
    items: list[tuple[str, int, Money]]  # product_id, qty, price


class PlaceOrderHandler:
    def __init__(self, order_repo: OrderRepository, id_generator, event_bus):
        self._repo = order_repo
        self._ids = id_generator
        self._bus = event_bus

    def handle(self, cmd: PlaceOrderCommand) -> str:
        order = Order(self._ids.next(), cmd.customer_id)
        for product_id, qty, price in cmd.items:
            order.add_item(product_id, qty, price)
        order.submit()

        self._repo.save(order)
        for event in order.collect_events():
            self._bus.publish(event)
        return order.id
```

### 应用服务 vs 领域服务

| | 应用服务 | 领域服务 |
|---|---------|---------|
| 层 | Application | Domain |
| 内容 | 编排、事务 | 跨聚合的领域逻辑 |
| 示例 | PlaceOrderHandler | PricingService.calculate_discount() |
| 状态 | 无状态 | 无状态 |

**领域服务：** 当逻辑不属于任何单一聚合时使用。

```python
class TransferService:  # 领域服务
    """转账涉及两个 Account 聚合，不属于单一聚合"""
    def transfer(self, from_acc: Account, to_acc: Account, amount: Money):
        from_acc.withdraw(amount)
        to_acc.deposit(amount)
```

---

## 5. CQRS 在 DDD 中的位置

```
Commands（写）                    Queries（读）
     │                                │
     ▼                                ▼
Application Service            Query Service
     │                                │
     ▼                                ▼
Domain + Repository            Read Model（可非规范化）
     │                                │
     ▼                                ▼
Write DB                       Read DB / Cache / ES
```

**简单项目：** 读写共用模型即可  
**复杂读场景：** 单独建读模型，由 Domain Event 投影更新

---

## 6. 工厂（Factory）

当聚合创建逻辑复杂时，用工厂封装。

```python
class OrderFactory:
    @staticmethod
    def create_from_cart(cart: Cart, customer_id: str) -> Order:
        order = Order(generate_id(), customer_id)
        for item in cart.items:
            order.add_item(item.product_id, item.quantity, item.price)
        return order
```

**vs 构造函数：** 简单创建用 `__init__`；多步骤/多来源用 Factory。

---

## 7. 规格模式（Specification）

封装可组合的业务规则，用于查询或验证。

```python
class OrderSpecification(ABC):
    @abstractmethod
    def is_satisfied_by(self, order: Order) -> bool: ...

class LargeOrderSpec(OrderSpecification):
    def __init__(self, threshold: Money):
        self._threshold = threshold

    def is_satisfied_by(self, order: Order) -> bool:
        return order.total.amount >= self._threshold.amount

class VIPCustomerSpec(OrderSpecification):
    def is_satisfied_by(self, order: Order) -> bool:
        return order.customer.is_vip

# 组合
def eligible_for_free_shipping(order: Order) -> bool:
    return LargeOrderSpec(threshold).is_satisfied_by(order) or \
           VIPCustomerSpec().is_satisfied_by(order)
```

---

## 8. 完整用例串联

```
HTTP POST /orders
    ↓
PlaceOrderController
    ↓
PlaceOrderHandler（应用服务）
    ├── OrderFactory.create_from_cart()
    ├── order.submit()（聚合 + 不变量 + 事件）
    ├── OrderRepository.save()
    └── EventBus.publish(OrderSubmitted)
            ↓
    ┌───────┴───────┐
    ▼               ▼
InventoryHandler  NotificationHandler
（其他上下文）      （本上下文）
```

---

## 9. 动手练习

### 练习 1：实现 CancelOrder 用例

写出 Application Service 伪代码：加载订单 → 调用 `order.cancel()` → 保存 → 发布 `OrderCancelled` 事件。

### 练习 2：设计读模型

`OrderSubmitted` 事件后，Notification 上下文需要发邮件。它需要哪些字段？是否应回调 Order API？

<details>
<summary>参考答案</summary>

事件应含：`order_id`, `customer_id`, `customer_email`, `total`, `item_summary`  
不应回调 — Event-Carried State Transfer，减少耦合

</details>

---

## 10. 模块总结

```
learn-domain-design 回顾：

00 全景      — 战略/战术、子域、何时引入
01 上下文    — 限界上下文、上下文地图、ACL
02 聚合建模  — 实体、值对象、聚合、不变量
03 战术模式  — Repository、Event、应用服务

核心心法：
  通用语言贯穿代码命名
  小聚合 + ID 引用 + 事件协作
  业务规则在领域层，应用层只编排
```

---

## 11. 自检清单

- [ ] 理解四层架构及依赖方向
- [ ] 能设计 Repository 接口与实现分离
- [ ] 会用 Domain Event 实现跨聚合协作
- [ ] 区分应用服务与领域服务的职责
- [ ] 知道 CQRS 与 DDD 的配合方式

---

## 12. 延伸阅读

- 《实现领域驱动设计》第 11–15 章
- 下一模块：`learn-architecture/` — 将上下文映射到架构
- 综合：`projects/capstone_taskflow.md`
