# 第3课：测试与质量保障

## 1. 为什么需要测试？

### 一句话解释
**测试就是给代码买的「保险」** —— 改代码时有人告诉你有没有搞砸。

### 没有测试的代价

```
开发者：我就改了一行代码...
（部署到生产）
用户：登录不了！！
开发者：不可能啊，在我电脑上能跑...
（3 小时排查）
原因：改支付逻辑时影响了登录模块
```

### 测试带来的价值

| 价值 | 说明 |
|------|------|
| 信心 | 重构和加功能时不怕 |
| 文档 | 测试用例描述系统行为 |
| 设计反馈 | 难测的代码往往设计有问题 |
| 回归防护 | 旧 Bug 不会复现 |

---

## 2. 测试金字塔

```
          /\
         /  \        E2E 测试（端到端）
        / E2E\       少量，慢，贵，覆盖关键路径
       /──────\
      /        \
     /  集成测试 \    适量，测模块间交互
    /────────────\
   /              \
  /    单元测试     \   大量，快，便宜，测单个函数/类
 /──────────────────\
```

| 层级 | 测什么 | 速度 | 数量 | 工具示例 |
|------|--------|------|------|---------|
| 单元测试 | 单个函数/类 | 毫秒 | 最多 | pytest, Jest |
| 集成测试 | 模块间协作 | 秒 | 中等 | pytest + DB |
| E2E 测试 | 完整用户流程 | 分钟 | 最少 | Playwright, Cypress |

**反模式 — 冰淇淋锥（测试反金字塔）：**

```
  /──────────\
 /   大量 E2E  \    ← 慢、脆、难维护
/──────────────\
 \  少量单元测试 /   ← 反馈慢，定位难
  \────────────/
```

---

## 3. 单元测试

### 3.1 基本结构：AAA

```python
def test_calculate_discount():
    # Arrange（准备）
    price = 100
    discount_rate = 0.2

    # Act（执行）
    result = calculate_discount(price, discount_rate)

    # Assert（断言）
    assert result == 80
```

### 3.2 pytest 实战

```python
# test_user_service.py
import pytest
from user_service import UserService, UserNotFoundError

@pytest.fixture
def user_service(mock_repo):
    return UserService(repo=mock_repo)

def test_create_user_success(user_service):
    user = user_service.create(name="Alice", email="a@b.com")
    assert user.name == "Alice"
    assert user.id is not None

def test_get_user_not_found(user_service):
    with pytest.raises(UserNotFoundError):
        user_service.get(user_id=999)

@pytest.mark.parametrize("email,valid", [
    ("test@example.com", True),
    ("invalid", False),
    ("", False),
])
def test_email_validation(email, valid):
    assert is_valid_email(email) == valid
```

### 3.3 Mock 与隔离

```python
from unittest.mock import Mock, patch

def test_send_welcome_email(user_service, mock_email_sender):
    user_service.create(name="Bob", email="bob@test.com")
    mock_email_sender.send.assert_called_once()
    call_args = mock_email_sender.send.call_args
    assert "Bob" in call_args[0][1]  # 邮件正文含用户名

@patch("user_service.external_api.fetch_data")
def test_with_external_api(mock_fetch):
    mock_fetch.return_value = {"status": "ok"}
    result = process_external_data()
    assert result["status"] == "ok"
```

**Mock 原则：** 只 Mock 外部依赖（数据库、API、文件系统），不 Mock 被测对象本身。

### 3.4 好的测试特征（FIRST）

| 字母 | 含义 | 说明 |
|------|------|------|
| F | Fast | 快速运行 |
| I | Independent | 测试间互不依赖 |
| R | Repeatable | 任何环境结果一致 |
| S | Self-validating | 自动 pass/fail，不需人工看 |
| T | Timely | 与生产代码同时写（TDD） |

---

## 4. TDD：测试驱动开发

### 红-绿-重构循环

```
  ┌──────────────────────────────────┐
  │  1. 红：写一个失败的测试          │
  │         ↓                        │
  │  2. 绿：写最少代码让测试通过       │
  │         ↓                        │
  │  3. 重构：优化代码，测试仍绿       │
  │         ↓                        │
  │  回到 1，下一个功能               │
  └──────────────────────────────────┘
```

### TDD 示例：实现 Stack

```python
# Step 1: 红
def test_empty_stack_has_size_zero():
    stack = Stack()
    assert stack.size() == 0

# Step 2: 绿（最小实现）
class Stack:
    def size(self):
        return 0

# Step 3: 下一个测试
def test_push_increases_size():
    stack = Stack()
    stack.push(1)
    assert stack.size() == 1

# ... 持续迭代
```

**TDD 的好处：**
- 强制先想接口再写实现
- 天然高测试覆盖率
- 设计更模块化（易测 = 低耦合）

**TDD 不是银弹：** 探索性原型、UI 布局、一次性脚本不一定适合。

---

## 5. 集成测试与 E2E

### 集成测试示例

```python
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()

def test_create_and_query_user(db_session):
    repo = UserRepository(db_session)
    user = repo.create(name="Test", email="t@t.com")
    found = repo.find_by_id(user.id)
    assert found.name == "Test"
```

### E2E 测试示例（Playwright）

```python
def test_login_flow(page):
    page.goto("http://localhost:3000/login")
    page.fill("#email", "user@test.com")
    page.fill("#password", "password123")
    page.click("button[type=submit]")
    page.wait_for_url("**/dashboard")
    assert page.locator("h1").text_content() == "Dashboard"
```

---

## 6. 代码审查（Code Review）

### 审查什么

| 维度 | 检查点 |
|------|--------|
| 正确性 | 逻辑是否正确，边界情况 |
| 设计 | 是否符合 SOLID，职责清晰 |
| 可读性 | 命名、结构、注释 |
| 测试 | 是否有测试，覆盖关键路径 |
| 安全 | SQL 注入、XSS、权限检查 |

### 审查礼仪

**提 PR 的人：**
- PR 尽量小（< 400 行）
- 写清楚改了什么、为什么
- 自己先 Review 一遍

**审查者：**
- 对事不对人：「这里可以提取函数」而非「你写错了」
- 区分「必须改」和「建议改」
- 24 小时内响应

### 审查清单模板

```markdown
## PR 自检
- [ ] 测试通过
- [ ] 新功能有测试
- [ ] 无 console.log / print 调试代码
- [ ] 文档/API 已更新（如需要）

## Reviewer 关注
- [ ] 业务逻辑正确
- [ ] 错误处理完善
- [ ] 无性能隐患（N+1 查询等）
```

---

## 7. 质量度量

| 指标 | 含义 | 健康范围（参考） |
|------|------|----------------|
| 测试覆盖率 | 代码被测试执行的比例 | 70–90%（非 100% 崇拜） |
| 圈复杂度 | 函数分支数量 | < 10 |
| 重复率 | 重复代码占比 | < 5% |
| Bug 密度 | Bug 数 / KLOC | 因项目而异 |
| MTTR | 平均修复时间 | 越短越好 |

**覆盖率陷阱：**

```python
# 100% 覆盖率但毫无断言价值
def test_get_user():
    service.get_user(1)  # 没 assert，只测了「不崩溃」
```

**关注：** 覆盖关键路径和业务逻辑，而非数字本身。

---

## 8. 静态分析与 CI

```yaml
# .github/workflows/ci.yml 示例
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=src --cov-report=term
      - run: ruff check .
      - run: mypy src/
```

**常用工具：**

| 语言 | 测试 | Lint | 类型检查 |
|------|------|------|---------|
| Python | pytest | ruff, flake8 | mypy |
| JavaScript | Jest, Vitest | ESLint | TypeScript |
| Go | testing | golangci-lint | 内置 |
| Java | JUnit | Checkstyle | 编译器 |

---

## 9. 动手练习

### 练习 1：为函数写测试

为以下函数写 pytest 测试（含边界情况）：

```python
def divide(a, b):
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b
```

<details>
<summary>参考答案</summary>

```python
import pytest

def test_divide_normal():
    assert divide(10, 2) == 5

def test_divide_negative():
    assert divide(-10, 2) == -5

def test_divide_by_zero():
    with pytest.raises(ValueError, match="除数不能为零"):
        divide(10, 0)

def test_divide_float():
    assert divide(1, 3) == pytest.approx(0.333, rel=1e-2)
```

</details>

### 练习 2：TDD 练习

用 TDD 实现 `PasswordValidator`，要求：
- 至少 8 位
- 含大写、小写、数字
- 每通过一个条件写一个测试

---

## 10. 自检清单

- [ ] 能画出测试金字塔并解释各层职责
- [ ] 会用 pytest 写单元测试（含 fixture 和 parametrize）
- [ ] 理解 TDD 红-绿-重构循环
- [ ] 知道 Code Review 应关注什么
- [ ] 理解覆盖率不是唯一质量指标

---

## 11. 延伸阅读

- 《测试驱动开发》— Kent Beck
- pytest 文档：https://docs.pytest.org/
- 下一课：`04_refactoring.md`
- 关联：`learn-dev-methods/02_devops_and_cicd.md` — CI/CD 流水线
