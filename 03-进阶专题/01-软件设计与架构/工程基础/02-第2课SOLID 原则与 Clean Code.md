> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第2课：SOLID 原则与 Clean Code

## 1. 为什么需要设计原则？

### 一句话解释
**设计原则就是「好代码的交通规则」** —— 不遵守也能跑，但遵守了更安全、更好维护。

### 没有原则时常见的问题

```python
# ❌ 一个类什么都干
class UserManager:
    def create_user(self, data): ...
    def send_email(self, user): ...
    def generate_report(self): ...
    def connect_database(self): ...
    def render_html(self, user): ...
```

```python
# ✅ 职责分离
class UserService:      # 只管用户业务
class EmailService:     # 只管发邮件
class ReportGenerator:  # 只管报表
class UserRepository:   # 只管数据库
```

---

## 2. SOLID 五大原则

SOLID 是面向对象设计的五个核心原则首字母缩写。

### 2.1 S — 单一职责原则（Single Responsibility）

**定义：** 一个类/模块应该只有一个引起它变化的原因。

**类比：** 厨师只做饭，服务员只上菜，收银员只收钱。

```python
# ❌ 违反 SRP
class Order:
    def calculate_total(self): ...
    def save_to_database(self): ...
    def send_confirmation_email(self): ...

# ✅ 遵循 SRP
class Order:
    def calculate_total(self): ...

class OrderRepository:
    def save(self, order): ...

class OrderNotifier:
    def send_confirmation(self, order): ...
```

**判断方法：** 用「和」连接类的职责 —— 如果出现「和」，可能违反了 SRP。

### 2.2 O — 开闭原则（Open/Closed）

**定义：** 对扩展开放，对修改关闭。

**类比：** 电源插座 —— 不用改插座就能插不同电器（扩展），插座本身不用改（关闭修改）。

```python
# ❌ 每加一种支付方式就要改这个函数
def process_payment(method, amount):
    if method == "credit_card":
        ...
    elif method == "paypal":
        ...
    elif method == "alipay":  # 又加一种，改原代码
        ...

# ✅ 扩展开放：新增支付方式只需新增类
from abc import ABC, abstractmethod

class PaymentProcessor(ABC):
    @abstractmethod
    def pay(self, amount: float) -> bool: ...

class CreditCardProcessor(PaymentProcessor):
    def pay(self, amount): ...

class AlipayProcessor(PaymentProcessor):
    def pay(self, amount): ...

def checkout(processor: PaymentProcessor, amount):
    return processor.pay(amount)  # 不用改
```

### 2.3 L — 里氏替换原则（Liskov Substitution）

**定义：** 子类对象应该能替换父类对象，且程序行为不变。

**类比：** 正方形是特殊矩形，但如果「改宽度时高度不变」的矩形子类替换普通矩形，面积计算就错了。

```python
# ❌ 经典反例：正方形继承矩形
class Rectangle:
    def set_width(self, w): self.width = w
    def set_height(self, h): self.height = h

class Square(Rectangle):  # 违反 LSP
    def set_width(self, w):
        self.width = self.height = w  # 破坏了「宽高独立」的期望

# ✅ 更好的设计：不强行继承，用组合或独立抽象
class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

class Rectangle(Shape): ...
class Square(Shape): ...
```

**实践检查：** 子类是否增强了父类的前置条件？是否削弱了后置条件？是否抛出父类没有的异常？

### 2.4 I — 接口隔离原则（Interface Segregation）

**定义：** 客户端不应被迫依赖它不使用的方法。

**类比：** 遥控器 —— 电视遥控不需要空调按钮。

```python
# ❌ 臃肿接口
class Worker(ABC):
    @abstractmethod
    def work(self): ...
    @abstractmethod
    def eat(self): ...

class Robot(Worker):  # 机器人不需要 eat，却被迫实现
    def eat(self):
        raise NotImplementedError("Robot doesn't eat")

# ✅ 接口隔离
class Workable(ABC):
    @abstractmethod
    def work(self): ...

class Eatable(ABC):
    @abstractmethod
    def eat(self): ...

class Human(Workable, Eatable): ...
class Robot(Workable): ...
```

### 2.5 D — 依赖倒置原则（Dependency Inversion）

**定义：** 高层模块不应依赖低层模块，两者都应依赖抽象。

**类比：** 你按「充电接口标准（USB-C）」买线，而不是按「某品牌手机型号」买 —— 依赖标准，不依赖具体实现。

```python
# ❌ 高层直接依赖具体实现
class UserService:
    def __init__(self):
        self.db = MySQLDatabase()  # 绑死 MySQL

# ✅ 依赖抽象
class Database(ABC):
    @abstractmethod
    def save(self, data): ...

class UserService:
    def __init__(self, db: Database):  # 注入抽象
        self.db = db

# 使用时
service = UserService(PostgresDatabase())
service = UserService(MySQLDatabase())  # 可替换
```

**依赖注入（DI）三种方式：**

| 方式 | 示例 | 常用场景 |
|------|------|---------|
| 构造函数注入 | `__init__(self, db)` | 最常用，依赖明确 |
| 属性注入 | `service.db = db` | 可选依赖 |
| 方法注入 | `process(self, notifier)` | 单次使用的依赖 |

---

## 3. SOLID 关系图

```
        SRP（基础：职责清晰）
           ↓
    OCP（扩展而不修改）
           ↓
    LSP（子类可替换）
           ↓
    ISP（接口精简）
           ↓
    DIP（依赖抽象）
           ↓
    可测试、可扩展、可维护的代码
```

---

## 4. Clean Code 核心实践

《Clean Code》（Robert C. Martin）与 SOLID 同源，强调可读性。

### 4.1 命名

```python
# ❌
def calc(d, t): ...
x = getData()

# ✅
def calculate_shipping_cost(distance_km, weight_kg): ...
active_users = fetch_active_users()
```

**规则：**
- 名字应表达意图，避免缩写（除非行业通用如 `id`, `url`）
- 布尔变量用 `is_`, `has_`, `can_` 前缀
- 函数名用动词：`fetch_`, `create_`, `validate_`

### 4.2 函数

```python
# ❌ 函数太长、做多件事
def process_order(order):
    # 50 行：验证、计价、扣库存、发邮件、写日志...

# ✅ 小函数，单一职责
def process_order(order):
    validate_order(order)
    total = calculate_total(order)
    deduct_inventory(order.items)
    save_order(order, total)
    notify_customer(order)
```

**规则：**
- 函数尽量短（通常 < 20 行）
- 参数尽量少（0–2 个最佳，超过 3 个考虑对象封装）
- 无副作用：函数名说做什么就做什么

### 4.3 注释

```python
# ❌ 注释解释糟糕的代码
# 加 1 是因为数组从 0 开始
index = i + 1

# ✅ 代码自解释，注释解释「为什么」
# 跳过 CSV 文件头行
index = i + 1
```

**好注释：** 法律信息、复杂算法的意图、TODO 带 Issue 号  
**坏注释：** 重复代码含义、注释掉的死代码、误导性注释

### 4.4 错误处理

```python
# ❌ 吞掉异常
try:
    result = risky_operation()
except:
    pass

# ✅ 明确处理或向上抛出
try:
    result = risky_operation()
except ConnectionError as e:
    logger.error("Database unavailable: %s", e)
    raise ServiceUnavailableError("请稍后重试") from e
```

### 4.5 DRY 与 YAGNI

| 原则 | 含义 | 实践 |
|------|------|------|
| DRY | Don't Repeat Yourself | 重复逻辑提取为函数/类 |
| YAGNI | You Aren't Gonna Need It | 不为「可能将来需要」过度设计 |

**平衡：** DRY 是消除**知识重复**，不是消除**代码相似**。两处代码看起来一样但变化原因不同，不应强行合并。

---

## 5. 代码坏味道（Code Smells）

| 坏味道 | 表现 | 对应重构 |
|--------|------|---------|
| 过长函数 | > 30 行 | 提取函数 |
| 过大类 | 承担太多职责 | 拆分类（SRP） |
| 过长参数列表 | > 3 个参数 | 引入参数对象 |
| 重复代码 | 复制粘贴 | 提取公共方法 |
| 散弹式修改 | 改一个功能要改很多类 | 搬移方法/内联类 |
| 依恋情结 | 类过度使用另一个类的数据 | 搬移方法 |
| 数据泥团 | 多个类有相同字段组 | 提取类 |
|  switch/if-else 链 | 类型判断分支过多 | 多态/策略模式 |

---

## 6. 动手练习

### 练习 1：识别违反的原则

以下代码违反了哪些 SOLID 原则？

```python
class ReportService:
    def __init__(self):
        self.db = SQLiteConnection("report.db")

    def generate_pdf_report(self, user_id):
        data = self.db.query(f"SELECT * FROM orders WHERE user_id={user_id}")
        # 生成 PDF...
        self.send_email(data)
        return pdf_bytes

    def send_email(self, data):
        smtp = SMTPClient("smtp.gmail.com")
        smtp.send(...)
```

<details>
<summary>参考答案</summary>

- **SRP**：生成报表 + 发邮件 + 数据库连接
- **OCP**：新增 CSV 格式需改 `generate_pdf_report`
- **DIP**：直接依赖 `SQLiteConnection`、`SMTPClient` 具体类
- **额外问题**：SQL 注入风险（f-string 拼接 SQL）

</details>

### 练习 2：重构

将上面的 `ReportService` 重构为符合 SOLID 的结构（写出类名和职责即可）。

<details>
<summary>参考答案</summary>

```python
class OrderRepository(ABC):
    @abstractmethod
    def find_by_user(self, user_id: int) -> list: ...

class ReportFormatter(ABC):
    @abstractmethod
    def format(self, data: list) -> bytes: ...

class Notifier(ABC):
    @abstractmethod
    def notify(self, content: bytes) -> None: ...

class ReportService:
    def __init__(self, repo, formatter, notifier):
        self.repo = repo
        self.formatter = formatter
        self.notifier = notifier

    def generate_and_send(self, user_id: int):
        data = self.repo.find_by_user(user_id)
        report = self.formatter.format(data)
        self.notifier.notify(report)
        return report
```

</details>

---

## 7. 自检清单

- [ ] 能解释 SOLID 每个字母的含义并举例
- [ ] 能识别代码中的 SRP、OCP 违反
- [ ] 理解依赖注入与 DIP 的关系
- [ ] 知道 DRY 和 YAGNI 如何平衡
- [ ] 能列出至少 5 种代码坏味道

---

## 8. 延伸阅读

- 《Clean Code》— Robert C. Martin
- 《重构：改善既有代码的设计》— Martin Fowler
- 下一课：`03-第3课测试与质量保障.md`
- 设计模式：`learn-design-patterns/` — 原则的具体模式化解决方案
