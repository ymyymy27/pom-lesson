# 第3课：行为型模式

行为型模式关注**对象之间的通信、职责分配和算法封装**。

---

## 1. 策略模式（Strategy）

### 动机
定义一系列算法，将每个算法封装起来，使它们可以互换。

```python
class SortStrategy(ABC):
    @abstractmethod
    def sort(self, data: list) -> list: ...

class QuickSort(SortStrategy):
    def sort(self, data):
        return sorted(data)  # 简化示意

class MergeSort(SortStrategy):
    def sort(self, data):
        ...

class Sorter:
    def __init__(self, strategy: SortStrategy):
        self.strategy = strategy

    def set_strategy(self, strategy: SortStrategy):
        self.strategy = strategy

    def sort(self, data):
        return self.strategy.sort(data)
```

**适用：** 支付方式、折扣规则、压缩算法、路由策略。

**vs 状态模式：** 策略由客户端切换；状态由对象内部自动转换。

---

## 2. 观察者模式（Observer）

### 动机
定义对象间一对多依赖，当一个对象状态改变时，所有依赖者自动收到通知。

```python
class Subject:
    def __init__(self):
        self._observers: list[Observer] = []

    def attach(self, observer):
        self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    def notify(self, event: str):
        for obs in self._observers:
            obs.update(event)

class Observer(ABC):
    @abstractmethod
    def update(self, event: str): ...

class EmailNotifier(Observer):
    def update(self, event):
        print(f"Email: {event}")

class SMSNotifier(Observer):
    def update(self, event):
        print(f"SMS: {event}")

# 使用
order = Subject()
order.attach(EmailNotifier())
order.attach(SMSNotifier())
order.notify("Order #123 shipped")
```

**现代变体：**
- 事件总线（Event Bus）
- Pub/Sub（Redis, RabbitMQ）
- React 的 `useState` + re-render

**注意：** 避免循环通知；考虑弱引用防止内存泄漏。

---

## 3. 命令模式（Command）

### 动机
将请求封装为对象，从而支持参数化、排队、日志、撤销。

```python
class Command(ABC):
    @abstractmethod
    def execute(self): ...
    @abstractmethod
    def undo(self): ...

class Light:
    def __init__(self):
        self.is_on = False

    def turn_on(self):
        self.is_on = True
    def turn_off(self):
        self.is_on = False

class TurnOnCommand(Command):
    def __init__(self, light: Light):
        self.light = light

    def execute(self):
        self.light.turn_on()
    def undo(self):
        self.light.turn_off()

class RemoteControl:
    def __init__(self):
        self.history: list[Command] = []

    def press(self, cmd: Command):
        cmd.execute()
        self.history.append(cmd)

    def undo(self):
        if self.history:
            self.history.pop().undo()
```

**适用：** 撤销/重做、任务队列、宏命令、事务日志。

---

## 4. 状态模式（State）

### 动机
对象内部状态改变时改变其行为，看起来像是改变了类。

```python
class OrderState(ABC):
    @abstractmethod
    def pay(self, order): ...
    @abstractmethod
    def ship(self, order): ...
    @abstractmethod
    def cancel(self, order): ...

class PendingState(OrderState):
    def pay(self, order):
        order.state = PaidState()
        print("Payment received")
    def ship(self, order):
        print("Cannot ship: not paid")
    def cancel(self, order):
        order.state = CancelledState()

class PaidState(OrderState):
    def pay(self, order):
        print("Already paid")
    def ship(self, order):
        order.state = ShippedState()
        print("Shipped")
    def cancel(self, order):
        order.state = RefundingState()

class Order:
    def __init__(self):
        self.state = PendingState()

    def pay(self):
        self.state.pay(self)
    def ship(self):
        self.state.ship(self)
```

**vs 大量 if/elif：** 每个状态的行为内聚在一个类中，新增状态只需新增类（OCP）。

**适用：** 订单状态机、TCP 连接状态、工作流引擎、游戏角色状态。

---

## 5. 模板方法模式（Template Method）

### 动机
在父类中定义算法骨架，子类重写特定步骤。

```python
class DataProcessor(ABC):
    def process(self):
        data = self.read_data()
        result = self.transform(data)
        self.write_result(result)

    @abstractmethod
    def read_data(self): ...

    @abstractmethod
    def transform(self, data): ...

    def write_result(self, result):
        print(f"Writing: {result}")  # 默认实现，可覆盖

class CSVProcessor(DataProcessor):
    def read_data(self):
        return ["row1", "row2"]
    def transform(self, data):
        return [r.upper() for r in data]

class JSONProcessor(DataProcessor):
    def read_data(self):
        return {"key": "value"}
    def transform(self, data):
        return {k: v.upper() for k, v in data.items()}
```

**适用：** 框架钩子（Django 的 `View.dispatch`）、ETL 流程、测试生命周期（setup/test/teardown）。

**vs 策略模式：** 模板方法用继承固定骨架；策略用组合替换整个算法。

---

## 6. 责任链模式（Chain of Responsibility）

### 动机
使多个对象都有机会处理请求，避免发送者与接收者耦合。

```python
class Handler(ABC):
    def __init__(self):
        self._next: Handler | None = None

    def set_next(self, handler):
        self._next = handler
        return handler  # 支持链式设置

    def handle(self, request) -> str | None:
        if self._next:
            return self._next.handle(request)
        return None

class AuthHandler(Handler):
    def handle(self, request):
        if not request.get("token"):
            return "401 Unauthorized"
        return super().handle(request)

class RateLimitHandler(Handler):
    def handle(self, request):
        if request.get("count", 0) > 100:
            return "429 Too Many Requests"
        return super().handle(request)

class BusinessHandler(Handler):
    def handle(self, request):
        return "200 OK"

# 组装链
auth = AuthHandler()
rate = RateLimitHandler()
biz = BusinessHandler()
auth.set_next(rate).set_next(biz)
```

**适用：** 中间件、审批流、日志级别过滤、异常处理链。

**Python/Web：** Flask/Express/Koa 的中间件就是责任链 + 装饰器。

---

## 7. 迭代器模式（Iterator）

### 动机
提供顺序访问聚合对象元素的方法，而不暴露内部表示。

```python
class BookCollection:
    def __init__(self):
        self._books = []

    def add(self, book):
        self._books.append(book)

    def __iter__(self):
        return iter(self._books)  # Python 内置支持

# for book in collection: ...
```

**Python：** 协议 `__iter__` / `__next__` 是语言内置的迭代器模式。生成器 (`yield`) 是更 Pythonic 的实现。

---

## 8. 中介者模式（Mediator）

### 动机
用中介对象封装一组对象的交互，使对象不需要显式相互引用。

```python
class ChatRoom:  # 中介者
    def __init__(self):
        self.users: dict[str, User] = {}

    def register(self, user):
        self.users[user.name] = user
        user.room = self

    def send(self, message, sender: str):
        for name, user in self.users.items():
            if name != sender:
                user.receive(message, sender)

class User:
    def __init__(self, name):
        self.name = name
        self.room = None

    def send(self, message):
        self.room.send(message, self.name)

    def receive(self, message, sender):
        print(f"{self.name} received from {sender}: {message}")
```

**适用：** 聊天室、对话框组件通信、空管塔台调度。

**vs 观察者：** 中介者中心化路由；观察者去中心化广播。

---

## 9. 备忘录模式（Memento）

### 动机
在不破坏封装的前提下，捕获并外部化对象的内部状态，以便恢复。

```python
class EditorMemento:
    def __init__(self, content: str):
        self.content = content

class Editor:
    def __init__(self):
        self.content = ""

    def write(self, text):
        self.content += text

    def save(self) -> EditorMemento:
        return EditorMemento(self.content)

    def restore(self, memento: EditorMemento):
        self.content = memento.content

class History:
    def __init__(self):
        self.states: list[EditorMemento] = []

    def push(self, memento):
        self.states.append(memento)

    def pop(self) -> EditorMemento:
        return self.states.pop()
```

**适用：** 编辑器撤销、游戏存档、数据库快照。

---

## 10. 访问者模式（Visitor）

### 动机
在不改变元素类的前提下，定义作用于元素的新操作。

```python
class Element(ABC):
    @abstractmethod
    def accept(self, visitor): ...

class ConcreteElementA(Element):
    def accept(self, visitor):
        visitor.visit_a(self)
    def operation_a(self):
        return "A"

class ConcreteElementB(Element):
    def accept(self, visitor):
        visitor.visit_b(self)
    def operation_b(self):
        return "B"

class Visitor(ABC):
    @abstractmethod
    def visit_a(self, element): ...
    @abstractmethod
    def visit_b(self, element): ...

class ExportVisitor(Visitor):
    def visit_a(self, element):
        return f"Export A: {element.operation_a()}"
    def visit_b(self, element):
        return f"Export B: {element.operation_b()}"
```

**适用：** AST 编译器遍历、文档导出（多种格式）、复杂对象结构的统计。

**代价：** 新增元素类型需改所有 Visitor — 元素结构稳定、操作频繁增加时合适。

---

## 11. 解释器模式（Interpreter）

### 动机
给定一种语言，定义其文法表示，并定义解释器。

```python
class Expression(ABC):
    @abstractmethod
    def interpret(self, context: dict) -> int: ...

class Number(Expression):
    def __init__(self, value):
        self.value = value
    def interpret(self, context):
        return self.value

class Variable(Expression):
    def __init__(self, name):
        self.name = name
    def interpret(self, context):
        return context[self.name]

class Add(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def interpret(self, context):
        return self.left.interpret(context) + self.right.interpret(context)

# (x + 3) where x=5 → 8
expr = Add(Variable("x"), Number(3))
print(expr.interpret({"x": 5}))
```

**适用：** 简单 DSL、规则引擎、SQL WHERE 解析。

**注意：** 复杂文法用 parser generator（如 Lark、PLY）更合适。

---

## 12. 行为型模式对比

| 需求 | 模式 |
|------|------|
| 算法可切换 | 策略 |
| 状态驱动行为 | 状态 |
| 一对多通知 | 观察者 |
| 操作可撤销 | 命令 |
| 流程固定步骤可变 | 模板方法 |
| 请求沿链处理 | 责任链 |
| 统一遍历 | 迭代器 |
| 多对象协调 | 中介者 |
| 保存/恢复状态 | 备忘录 |
| 新操作不改结构 | 访问者 |

---

## 13. 动手练习

### 练习 1：购物车折扣策略

实现策略模式：普通用户无折扣、VIP 9 折、批发 7 折。运行 `practice/behavioral/strategy_demo.py`。

### 练习 2：订单状态机

扩展本文 Order 示例，增加 `ShippedState`、`DeliveredState`、`CancelledState`，画出状态转换图。

---

## 14. 自检清单

- [ ] 能区分策略模式和状态模式
- [ ] 能实现观察者模式并知道其现代变体
- [ ] 理解命令模式的撤销机制
- [ ] 知道责任链在中间件中的应用
- [ ] 能说出模板方法与策略模式的区别

---

## 15. 延伸阅读

- `practice/behavioral/strategy_demo.py`
- 下一课：`04_patterns_in_practice.md`

---

# 深入篇：行为型的底层逻辑

> 行为型管"对象怎么协作"。这一篇给每个模式讲清：
> **机关、隔离的变化、代价、易混对象、AI 应用**。

## 0. 协作问题的三种层次

对象协作时，变化可能发生在三个层面：

| 层次 | 问题 | 模式 |
|---|---|---|
| 算法层 | 同一件事怎么做 | 策略、模板方法 |
| 消息层 | 谁通知谁、请求怎么传 | 观察者、责任链、中介者、命令 |
| 状态层 | 行为怎么随状态/时间变 | 状态、备忘录 |
| 结构遍历层 | 怎么访问、怎么加操作 | 迭代器、访问者、解释器 |

---

## 1. 策略：策略靠选

### 机关

```python
class Context:
    def __init__(self, strategy): self.strategy = strategy
    def set_strategy(self, strategy): self.strategy = strategy  # 运行时可换
    def execute(self): return self.strategy.calculate(...)
```

### 深层洞察

- 隔离的变化：**算法**——加算法 = 加策略类，Context 零改动（OCP）；
- 与状态的区别：策略是**客户端主动选**，状态是**内部自动变**；
- Python 里纯计算策略可以退化成函数（一等公民）；
- 别把每个 if 都变策略：3 个以上分支且频繁扩展才考虑（Rule of Three）。

---

## 2. 观察者：点名

### 机关

```python
class Subject:
    def attach(self, obs): self._observers.append(obs)
    def notify(self, event):
        for obs in self._observers: obs.update(event)
```

### 深层洞察

- 隔离的变化：**谁关心事件、怎么通知**——加观察者 = 注册，事件源零改动；
- 结构面是一对多引用，行为面是通知循环——它是"结构 vs 行为"两面性的最佳标本；
- 四个实战坑：通知顺序别假设、单个观察者异常要隔离、
  必须能注销（防泄漏）、同步通知会阻塞（异步用消息队列）；
- 总线 = 观察者 + 事件名订阅 + 中央路由（不认识订阅者的观察者）。

---

## 3. 命令：动作对象化

### 机关

```python
class Command(ABC):
    def execute(self): ...
    def undo(self): ...
class CompleteTask(Command):
    def __init__(self, task): self._task = task; self._prev = task.status
    def undo(self): self._task.status = self._prev   # 存现场，才能撤销
```

### 深层洞察

- 隔离的变化：**动作的触发与管理方式**（保存、排队、撤销、延迟、宏）；
- 撤销的机关 = 执行前保存"之前的状态"（这是内联版备忘录）；
- 和策略的区别：策略封装"算法"（怎么算），命令封装"动作 + 接收者 + 参数"
  （做什么、对谁做）；
- AI 应用：工具调用封装成命令 → 审计、重放、回滚、UI 展示调用序列。

---

## 4. 状态：状态靠变

### 机关

```python
class TodoState:
    def start(self, task): task.transition_to(InProgressState())  # 自己决定下一步
    def complete(self, task): raise ValueError("非法操作")
```

### 深层洞察

- 隔离的变化：**状态规则**——加状态 = 加状态类，Context 零改动；
- 状态转换由**状态对象自己发起**（外部不知道什么时候变）——这是和策略的分界线；
- 非法转换当场报错 = 状态机的强约束；
- 状态对象通常无状态（只有规则）——可共享（呼应享元）；
- AI 应用：Agent 生命周期（idle → thinking → tool_calling → done）、
  会话认证状态、流式生成状态。

---

## 5. 模板方法：好莱坞原则

### 机关

```python
class Agent(ABC):
    def run(self, task):                # 骨架
        plan = self.plan(task)          # 抽象步骤
        result = self.execute(plan)
        self.after(result)              # 钩子（可选）
        return result
```

### 深层洞察

- 好莱坞原则：**别打电话给我们，我们会打给你**——父类调子类，不是子类调父类；
- 钩子 = 默认空实现的可选插槽；
- 与策略的区别：模板方法用**继承**固定骨架；策略用**组合**换整个算法；
- 和工厂方法的关系：工厂方法就是模板方法在"创建"上的应用；
- 骨架频繁变时慎用（改父类影响所有子类）。

---

## 6. 责任链：谁合适谁停

### 机关

```python
class Handler:
    def set_next(self, h): self._next = h; return h
    def handle(self, req):
        if self.can_handle(req): return self.do(req)   # 拦截并结束
        return self._next.handle(req)                  # 传下去
```

### 深层洞察

- 隔离的变化：**处理者集合与顺序**——挂节点 = 加处理者，客户端只碰链头；
- 与装饰器的区别：装饰器**层层都执行**（增强）；责任链**谁能处理谁停**（拦截）；
- 中间件是两者混合：记录型 = 装饰器，拦截型 = 责任链；
- 链太长是调试噩梦（请求走到哪了、被谁拦了）——配日志或显式链对象。

---

## 7. 迭代器：位置 + 移动规则

### 机关

```python
def __iter__(self): return self
def __next__(self):
    if done: raise StopIteration
    return item
```

### 深层洞察

- 隔离的变化：**遍历方式**——调用方与集合内部结构解耦；
- 机关是"位置状态"（`_current`）+ 结束信号（`StopIteration`）；
- Python 里这是语言内置协议：`for` = `iter()` + `next()`，
  生成器（`yield`）是它的语法糖；
- 和组合配合：树的遍历顺序（前序/中序/后序）= 不同的迭代器；
- AI 应用：流式输出、RAG 分块懒加载、数据库游标、分页。

---

## 8. 中介者：传话

### 机关

```python
class Colleague:
    def send(self, event): self._mediator.notify(self, event)   # 只认中介者
class Mediator:
    def notify(self, sender, event): ...   # 协调逻辑集中在这里
```

### 深层洞察

- 解决的问题：n 个对象互持引用 = 蜘蛛网（n×(n-1)/2 条线）；
- 隔离的变化：**协作关系**——加同事/改流程只动中介者；
- 与观察者：观察者是一对多广播（点名），中介者是多对多协调（传话）；
- 与外观：外观是单向简化入口，中介者是双向协调；
- 最大的坑：中介者变"上帝对象"——对策是拆小中介者或把规则数据化
  （共享状态 + 图，如 LangGraph）。

---

## 9. 备忘录：快照

### 机关

```python
class Originator:
    def save(self) -> Memento: ...
    def restore(self, memento): ...
class Caretaker:
    def checkpoint(self, m): self._history.append(m)
    def rollback(self, originator): originator.restore(self._history.pop())
```

### 深层洞察

- 三个角色的纪律：Originator 生成/恢复，Memento 不透明，Caretaker 只保管不碰内容；
- **窄接口**思想：Caretaker 不知道快照里是什么；
- 保存时必须复制可变字段（否则快照跟着变，失效）；
- Python 没有真正私有，不透明靠约定——纪律比语法重要；
- 与命令配合 = 撤销/重做；状态大时用增量快照；
- AI 应用：Agent 检查点、对话回滚、配置回滚、断点续跑。

---

## 10. 访问者：双分派

### 机关

```python
class Num(Element):
    def accept(self, visitor):
        return visitor.visit_num(self)    # "我是 Num，请按 Num 处理我"
```

### 深层洞察

- 为什么不能 `visitor.visit(node)`？调用点不知道 node 的具体类型，
  省掉 accept 就得回去写 if/else；
- **双分派**：`accept`（第 1 跳：节点的运行时类型决定）
  → `visit_x`（第 2 跳：访问者的运行时类型决定）——行为由两个对象共同决定；
- 隔离的变化：**对稳定结构的操作**——加操作 = 加 Visitor，节点零改动；
- 代价：加新节点类型要改所有 Visitor（接口强制提醒 = 既是痛也是安全）；
- 适用条件：**结构稳定、操作频繁变**（AST/编译器领域）；
- Python `ast.NodeVisitor` 就是它。

---

## 11. 解释器：语法对象化

### 机关

```python
class Add(Expr):
    def interpret(self):
        return self.left.interpret() + self.right.interpret()   # 递归
```

### 深层洞察

- 每一条语法规则 = 一个类，每个对象自己解释自己；
- 解释器 = 组合（树）+ 节点自带 `interpret`；访问者 = 组合（树）+ 操作外置；
- 只管"解释"，不管"解析"：文本 → AST 是 parser 的活（lark/ANTLR），
  AST → 结果才是解释器的活；
- GoF 自己也说：适合**简单且频繁变化的小语法**；
  语法复杂时用解析器生成器，别手写；
- AI 应用：规则引擎 DSL、表达式引擎、Prompt 模板小语言、工作流 DSL。

---

## 12. 行为型的"对比总表"

| 对比组 | 区别 |
|---|---|
| 策略 vs 状态 | 主动选 vs 自动变 |
| 观察者 vs 中介者 vs 总线 | 点名 vs 传话 vs 广播 |
| 命令 vs 备忘录 | 动作可撤销 vs 状态可恢复（常配合） |
| 模板方法 vs 策略 | 继承固定骨架 vs 组合换算法 |
| 责任链 vs 装饰器 | 谁合适谁停 vs 层层都执行 |
| 访问者 vs 解释器 | 操作外置 vs 逻辑内嵌 |

## 13. 行为型自检

- [ ] 能说出"策略靠选、状态靠变"的具体含义
- [ ] 能解释双分派为什么需要 accept
- [ ] 能说出命令撤销的机关（执行前保存现场）
- [ ] 能区分观察者、中介者、总线
- [ ] 能手写责任链的"拦截或放行"结构
- [ ] 知道解释器模式在什么情况下不该手写
