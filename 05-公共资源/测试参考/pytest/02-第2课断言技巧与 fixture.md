> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第2课：断言技巧与 fixture

## 1. 为什么需要 fixture？

### 一句话解释

**fixture 就是测试的「标准样品生产线」** —— 把重复的准备/清理逻辑抽出来，测试函数只关注断言。

### 没有 fixture 的问题

```python
def test_create_order():
    db = connect_db()
    db.execute("DELETE FROM orders")  # 重复
    user = User(name="Alice")
    db.save(user)                     # 重复
    order = create_order(user, items=[...])
    assert order.status == "pending"
    db.close()                        # 重复

def test_cancel_order():
    db = connect_db()                 # 又写一遍...
    ...
```

---

## 2. fixture 基础

```python
import pytest
from models import User

@pytest.fixture
def sample_user():
    return User(id=1, name="Alice", email="a@b.com")

def test_user_name(sample_user):
    assert sample_user.name == "Alice"

def test_user_email(sample_user):
    assert sample_user.email == "a@b.com"
```

**规则：**

- 参数名与 fixture 函数名一致，pytest 自动注入
- 每个使用 `sample_user` 的测试都会得到**独立调用**（默认 scope=function）
- fixture 定义在测试文件、同级 `conftest.py` 或父级 `conftest.py` 中

---

## 3. fixture 作用域

```python
@pytest.fixture(scope="function")  # 默认：每个测试一次
def fresh_counter():
    return Counter()

@pytest.fixture(scope="module")     # 每个文件一次
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")   # 整个 pytest 会话一次
def app_config():
    return load_config("test")
```

| scope | 何时用 | 注意 |
|-------|--------|------|
| function | 需要完全隔离 | 默认，最安全 |
| module | 建表等昂贵操作 | 测试间可能共享状态 |
| session | 全局连接池 | 必须保证不污染 |

---

## 4. setup / teardown：yield 模式

```python
@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    # --- 测试结束后执行 ---
    session.close()
    transaction.rollback()
    connection.close()
```

执行顺序：

```
fixture setup → 测试运行 → fixture teardown（yield 之后）
```

---

## 5. fixture 依赖链

```python
@pytest.fixture
def db_engine():
    return create_engine("sqlite:///:memory:")

@pytest.fixture
def db_session(db_engine):
    Base.metadata.create_all(db_engine)
    session = Session(db_engine)
    yield session
    session.close()

@pytest.fixture
def sample_user(db_session):
    user = User(name="Bob")
    db_session.add(user)
    db_session.commit()
    return user

def test_user_exists(db_session, sample_user):
    found = db_session.get(User, sample_user.id)
    assert found.name == "Bob"
```

pytest 按依赖图**自动排序** fixture 的执行顺序。

---

## 6. 断言进阶

### 6.1 浮点数

```python
def test_pi():
    assert 1 / 3 == pytest.approx(0.333333, rel=1e-4)
```

### 6.2 集合与顺序

```python
def test_tags():
    assert set(get_tags()) == {"python", "pytest"}

def test_order():
    assert get_steps() == ["login", "browse", "checkout"]
```

### 6.3 异常

```python
with pytest.raises(ValueError) as exc_info:
    parse_age("abc")
assert "invalid" in str(exc_info.value)
```

### 6.4 警告

```python
def test_deprecated(recwarn):
    use_old_api()
    assert len(recwarn) == 1
    assert issubclass(recwarn[0].category, DeprecationWarning)
```

---

## 7. 内置 fixture 常用项

### tmp_path — 临时目录

```python
def test_write_file(tmp_path):
    file = tmp_path / "output.txt"
    file.write_text("hello")
    assert file.read_text() == "hello"
    # 测试结束后目录自动删除
```

### capsys — 捕获输出

```python
def test_print_greeting(capsys):
    print("Hello")
    captured = capsys.readouterr()
    assert captured.out == "Hello\n"
```

---

## 8. autouse fixture

```python
@pytest.fixture(autouse=True)
def reset_global_state():
    GLOBAL_CACHE.clear()
    yield
    GLOBAL_CACHE.clear()
```

每个测试**自动**执行，无需在参数中声明。适合：重置全局状态、设置环境变量（慎用，降低可读性）。

---

## 9. fixture 参数化

同一 fixture 提供多组数据，测试会**笛卡尔积**展开：

```python
@pytest.fixture(params=["sqlite", "postgres"])
def db_backend(request):
    return create_db(request.param)

def test_connection(db_backend):
    assert db_backend.ping()
```

若只需参数化测试、不需 fixture，见第 3 课 `@pytest.mark.parametrize`。

---

## 10. 练习

在 `practice/tests/` 中：

1. 为 `UserService` 编写 `sample_user` fixture
2. 用 `tmp_path` 测试「把用户列表写入 JSON 文件再读回」
3. 用 `yield` fixture 模拟「测试前插入数据、测试后清理」

<details>
<summary>fixture 参考答案片段</summary>

```python
# tests/conftest.py
import pytest
from user_service import User, UserService

@pytest.fixture
def user_service():
    return UserService()

@pytest.fixture
def sample_user():
    return User(id=1, name="Alice", email="a@b.com")

# tests/test_user_service.py
def test_get_user(user_service, sample_user, monkeypatch):
    monkeypatch.setattr(user_service, "repo", MockRepo([sample_user]))
    user = user_service.get(1)
    assert user.name == "Alice"
```

</details>

---

## 11. 自检清单

- [ ] 能编写并使用 `@pytest.fixture`
- [ ] 理解 function / module / session 作用域
- [ ] 会用 yield 做 teardown
- [ ] 会使用 `tmp_path`、`capsys`
- [ ] 知道 conftest.py 的作用（第 5 课深入）

👉 下一课：[03_parametrize_and_markers.md](03-第3课参数化与标记.md)
