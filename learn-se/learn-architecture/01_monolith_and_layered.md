# 第1课：单体、分层与整洁架构

> **本课覆盖谱系 · 单体族**：纯单体 → 分层 → 模块化单体 → 六边形 → 洋葱 → 整洁  
> 上一课：[`00_architecture_overview.md`](00_architecture_overview.md) · 下一课：[`02_microservices_and_distributed.md`](02_microservices_and_distributed.md)

## 1. 单体架构（Monolith）

### 定义
所有功能在一个代码库、一个部署单元中。

```
┌─────────────────────────────────┐
│         Monolithic App          │
│  ┌───────┐ ┌───────┐ ┌───────┐ │
│  │ User  │ │ Order │ │ Pay   │ │
│  └───────┘ └───────┘ └───────┘ │
│         Shared Database          │
└─────────────────────────────────┘
           一个进程 / 一个部署
```

### 优点

| 优点 | 说明 |
|------|------|
| 简单 | 一个 repo、一次部署 |
| 开发快 | 无网络调用开销 |
| 调试易 | 本地跑全家桶 |
| 事务简单 | 本地 ACID 事务 |
| 适合早期 | MVP 快速验证 |

### 缺点

| 缺点 | 说明 |
|------|------|
| 扩展难 | 只能整体扩展 |
| 部署风险 | 改一行要部署全部 |
| 技术栈绑定 | 全项目用一种语言/框架 |
| 团队协作 | 大团队改同一 codebase 冲突多 |

### 模块化单体（Modular Monolith）

**最佳实践：** 即使是单体，也要**模块化** —— 清晰的模块边界，为未来拆分做准备。

```
monolith/
├── modules/
│   ├── users/       ← 独立模块，内部高内聚
│   │   ├── api.py
│   │   ├── service.py
│   │   └── repo.py
│   ├── orders/
│   └── payments/
└── shared/          ← 最小化共享代码
```

**规则：**
- 模块间通过**公开接口**通信，不直接访问对方内部
- 每个模块有自己的数据模型（可以同库不同 schema）
- 禁止跨模块的直接数据库 JOIN

---

## 2. 分层架构（Layered Architecture）

### 经典四层

```
┌─────────────────────────────────┐
│     Presentation Layer          │  ← UI / API Controller
├─────────────────────────────────┤
│     Business Logic Layer        │  ← Service / Domain
├─────────────────────────────────┤
│     Persistence Layer           │  ← Repository / DAO
├─────────────────────────────────┤
│     Database                    │
└─────────────────────────────────┘
         只能向下依赖 ↓
```

### 依赖规则

**严格分层：** 上层依赖下层，下层不知道上层。

```python
# ✅ Controller → Service → Repository
class UserController:
    def __init__(self, service: UserService):
        self.service = service

    def get_user(self, user_id: int):
        return self.service.get_user(user_id)

# ❌ Controller 直接访问 Repository
class UserController:
    def get_user(self, user_id):
        return UserRepository().find(user_id)  # 跳层
```

### 常见变体

| 名称 | 特点 |
|------|------|
| 三层架构 | Presentation + Business + Data |
| MVC | Model-View-Controller |
| MVP | Model-View-Presenter |
| MVVM | Model-View-ViewModel（前端常见） |

---

## 3. 六边形架构（Hexagonal / Ports & Adapters）

### 核心思想
**业务逻辑在中心，外部世界通过「端口+适配器」接入。**

```
                    ┌──────────────┐
   HTTP API ───────▷│              │
                    │   Domain     │
   CLI ────────────▷│   (Core)     │
                    │              │
   Database ───────▷│              │
                    └──────────────┘
                    ▲            ▲
                 Adapter      Adapter
                 (Port)       (Port)
```

### 端口 vs 适配器

| 概念 | 含义 | 示例 |
|------|------|------|
| Port（端口） | 接口定义 | `UserRepository` 抽象 |
| Adapter（适配器） | 具体实现 | `PostgresUserRepo`, `InMemoryUserRepo` |
| Driving Adapter | 驱动核心的入口 | REST Controller, CLI |
| Driven Adapter | 被核心驱动的出口 | DB, Email, External API |

### Python 示例

```python
# Port — 核心业务定义的接口
class UserRepository(ABC):
    @abstractmethod
    def find_by_id(self, user_id: int) -> User | None: ...
    @abstractmethod
    def save(self, user: User) -> None: ...

# Domain — 纯业务逻辑，零外部依赖
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def register(self, email: str, name: str) -> User:
        if self.repo.find_by_email(email):
            raise DuplicateEmailError(email)
        user = User(email=email, name=name)
        self.repo.save(user)
        return user

# Adapter — 数据库实现
class PostgresUserRepository(UserRepository):
    def __init__(self, session):
        self.session = session
    def find_by_id(self, user_id):
        ...
    def save(self, user):
        ...

# Driving Adapter — HTTP 入口
class UserController:
    def __init__(self, service: UserService):
        self.service = service

    def register(self, request):
        user = self.service.register(request.email, request.name)
        return {"id": user.id}
```

---

## 4. 洋葱架构（Onion Architecture）

Jeffrey Palermo 提出，与六边形、整洁架构同属 **「核心隔离族」**，强调 **领域模型在最中心**。

```
                    ┌─────────────────────────┐
                    │   Infrastructure         │  ← DB、Web、消息、文件
                    │  ┌───────────────────┐  │
                    │  │ Application Services│  │  ← 用例编排、DTO 转换
                    │  │  ┌─────────────┐   │  │
                    │  │  │ Domain Model │   │  │  ← 实体、值对象、领域服务
                    │  │  │  (核心)      │   │  │
                    │  │  └─────────────┘   │  │
                    │  └───────────────────┘  │
                    └─────────────────────────┘
              依赖方向：Infrastructure → Application → Domain
              Domain 层零外部依赖（不 import 框架/ORM）
```

### 与六边形 / 整洁的关系

| | 六边形 | 洋葱 | 整洁 |
|---|--------|------|------|
| 核心 | Domain + Ports | Domain Model | Entities |
| 外层 | Adapters | Infrastructure | Frameworks |
| 中间层 | （隐含在用例中） | Application Services | Use Cases |
| 关键差异 | 强调 Port 接口 | 强调 Domain 零依赖 | 强调同心圆 + 用例层 |

三者可以 **合并使用**：洋葱的目录结构 + 六边形的 Port/Adapter 命名 + 整洁的依赖规则。

### 目录示例

```
src/
├── domain/                 # 最内层：纯 Python，无框架
│   ├── order.py            # Order 实体 + 领域规则
│   └── exceptions.py
├── application/            # 用例层：编排 domain，定义 Port 接口
│   ├── place_order.py
│   └── ports.py            # OrderRepository 等抽象接口
└── infrastructure/         # 最外层：FastAPI、SQLAlchemy 实现
    ├── web/routes.py
    └── persistence/order_repo.py
```

### 何时用 / 何时别用

- **用**：领域规则复杂（定价、风控、审批流）、需要长期演进、团队重视单测
- **别用**：纯 CRUD、原型验证——三层目录 + Port 的样板成本大于收益

---

## 5. 整洁架构（Clean Architecture）

Robert C. Martin 提出的同心圆模型，与六边形思想一致。

```
        ┌─────────────────────────────┐
        │      Frameworks & Drivers    │  ← Web, DB, UI
        │  ┌───────────────────────┐  │
        │  │   Interface Adapters   │  │  ← Controllers, Gateways
        │  │  ┌─────────────────┐  │  │
        │  │  │  Application     │  │  │  ← Use Cases
        │  │  │  ┌───────────┐  │  │  │
        │  │  │  │  Entities  │  │  │  │  ← Domain Models
        │  │  │  └───────────┘  │  │  │
        │  │  └─────────────────┘  │  │
        │  └───────────────────────┘  │
        └─────────────────────────────┘
              依赖方向：外 → 内
```

### 核心规则

1. **依赖规则：** 源码依赖只能指向内层
2. **Entities：** 企业级业务规则（User, Order）
3. **Use Cases：** 应用级业务规则（RegisterUser, PlaceOrder）
4. **外层：** 知道内层；内层不知道外层

### 目录结构示例

```
src/
├── domain/              # Entities — 最内层
│   ├── user.py
│   └── order.py
├── use_cases/           # Application — 用例
│   ├── register_user.py
│   └── place_order.py
├── adapters/            # Interface Adapters
│   ├── web/             # HTTP Controllers
│   ├── persistence/     # Repository 实现
│   └── messaging/       # 消息适配器
└── infrastructure/      # Frameworks & Drivers
    ├── database.py
    └── config.py
```

---

## 6. 四种架构对比

| | 分层架构 | 六边形 | 洋葱 | 整洁架构 |
|---|---------|--------|------|---------|
| 核心 | 按技术职责分层 | 业务在中心 | Domain Model | 同心圆 + Use Cases |
| 依赖方向 | 上→下 | 外→内 | 外→内 | 外→内 |
| DB 位置 | 最底层 | 外侧 Adapter | Infrastructure 层 | 最外圈 |
| 测试 | 需 Mock 下层 | 核心可纯单测 | Domain 零依赖可单测 | 核心可纯单测 |
| 复杂度 | 低 | 中 | 中 | 中高 |
| 适合 | CRUD 应用 | 复杂业务 | DDD 项目 | 长期演进的大系统 |

---

## 7. 何时用哪种？

```
项目规模小、CRUD 为主？
  └─ 是 → 分层架构（三层/MVC）

业务规则复杂、需长期维护？
  └─ 是 → 六边形 / 洋葱 / 整洁架构

团队 < 5 人、快速 MVP？
  └─ 模块化单体 + 简单分层

团队 > 10 人、模块独立演进？
  └─ 考虑微服务（下一课）
```

---

## 8. 动手练习

### 练习 1：分层违规识别

以下代码违反了什么原则？如何改？

```python
# routes.py
@app.get("/users/{id}")
def get_user(id: int):
    conn = sqlite3.connect("app.db")
    row = conn.execute("SELECT * FROM users WHERE id=?", (id,)).fetchone()
    return {"id": row[0], "name": row[1]}
```

<details>
<summary>参考答案</summary>

违反：跳层（Controller 直接访问 DB）、SQL 在路由层、无业务逻辑层。

改进：Controller → UserService → UserRepository → DB

</details>

### 练习 2：画架构图

为一个「博客系统」（用户、文章、评论）画：
1. 分层架构图
2. 六边形架构的 Port/Adapter 标注

---

## 9. 自检清单

- [ ] 能解释单体架构的优缺点
- [ ] 理解模块化单体的意义
- [ ] 能画出四层架构并说明依赖方向
- [ ] 理解 Port/Adapter 和依赖倒置的关系
- [ ] 能说出洋葱架构与六边形、整洁的差异
- [ ] 能根据项目规模选择合适的架构风格

---

## 10. 延伸阅读

- 《Clean Architecture》— Robert C. Martin
- 《Implementing Domain-Driven Design》— Vaughn Vernon
- 下一课：`02_microservices_and_distributed.md`
- 关联：`learn-fullstack/` 全栈项目实践

---

# 深入篇：单体族的底层逻辑

## 1. 单体族的核心决策：一个部署单元 vs 内部边界

单体族所有风格共享同一个前提：**一个部署单元**。
它们之间的区别只有一个问题：**这个单元内部怎么切**。

```
纯单体：不切（什么都在一起）
分层：  按技术职责切（水平）
模块化：按业务域切（垂直）
六边形：按"核心 vs 外部"切（同心 + Port）
洋葱：  领域在绝对中心，Infrastructure 在最外
整洁：  六边形 + 用例层 + 依赖方向严格化
```

切得越细，**可维护性越好、但结构约束越强**；切得越粗，开发越快、但长期越乱。
单体族的全部权衡都在这条线上。

## 2. 分层架构的深层原理

### 为什么只能向下依赖？

依赖方向 = 变化方向。上层（Controller）天天变（接口改、参数改），
下层（Repository）变化慢。如果下层依赖上层，**慢的跟着快的变**——
一次 API 改动会穿透所有层。只向下依赖，保证"变化快的不拖累变化慢的"。

### 分层的真实代价

- **跨层需求要"打洞"**：一个简单需求要穿过 Controller → Service → Repository 三层，
  样板代码多；
- **层泄漏**：SQL 出现在 Controller、业务规则散落在 Repository——层被"打通"后
  约束失效，比不分层还糟；
- **贫血模型**：Service 越来越肥、Model 越来越空——分层架构容易长成"事务脚本"。

**判断标准**：分层不是目的，**依赖方向稳定**才是。如果某层形同虚设，
删掉它，别硬撑四层。

## 3. 模块化单体的深层原理

模块化单体是"**以未来拆分为目标写单体**"：

```python
modules/
├── users/    # 对外只暴露公开接口
│   └── api.py      # 其他模块只允许 import 这里
├── orders/
└── payments/
shared/       # 共享代码要最小化，否则模块边界名存实亡
```

三条硬规则为什么是硬的：

1. **模块间只走公开接口**——否则"模块化"退化成"按目录分类的单体"；
2. **禁止跨模块 DB JOIN**——JOIN 是模块边界的隐形杀手：数据一 JOIN，模块就耦合了；
3. **共享代码最小化**——shared/ 越大，模块独立性越差。

**模块化成功与否的检验**：能不能把某个模块"整个搬走"而不改其他模块？
能 → 边界合格；不能 → 边界是画出来的，不是设计出来的。

## 4. 六边形 / 整洁架构的深层原理

### 为什么依赖必须"外 → 内"？

让业务核心**不认识任何外部技术**（HTTP、DB、框架），才能：

- **核心可纯单测**：不启动数据库、不 mock 网络，直接测业务规则；
- **技术可替换**：换数据库 = 换 Driven Adapter，核心零改动；
- **边界可测试**：用 InMemory 适配器做端到端测试。

这本质是**依赖倒置（DIP）的架构化**——设计模式课里"面向抽象"放大到整个系统。

### 何时它反而是过度设计？

六边形/整洁的价值在**业务规则复杂、长期演进**。CRUD 应用里，
核心只是"表单 → 数据库"的搬运工——六边形只会增加样板。

**判断标准**：问自己"业务规则真的复杂到需要独立成核心吗？"
答不上来 → 分层就够。

## 5. 单体族的"由浅入深"选型表

| 阶段 | 推荐 | 原因 |
|---|---|---|
| MVP / 原型 | 纯单体 + 简单分层 | 最快验证 |
| 业务增长、需要边界 | 模块化单体 | 为未来拆分留退路 |
| 业务规则复杂 | 六边形 / 洋葱 / 整洁 | 核心可测试、可演进 |
| 团队大、模块独立部署 | 微服务（下一课） | 部署边界 = 团队边界 |

**核心心法：架构先求"能改"，再求"好看"。**
模块化单体是性价比最高的起点——它给"未来拆微服务"留了最便宜的退路。
