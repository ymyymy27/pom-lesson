# pytest 语法结构参考

> 本文档系统梳理 pytest 的三层语法：**命令行**、**测试函数/fixture**、**插件与配置**。建议配合 `01_pytest_basics.md` 一起阅读。

---

## 1. 整体架构：pytest 在测试中的位置

```
┌─────────────────────────────────────────────────────────┐
│  应用代码（src/、app/、services/）                       │
├─────────────────────────────────────────────────────────┤
│  测试代码（tests/）                                      │
│  test_*.py / *_test.py → 测试函数 / 测试类               │
├─────────────────────────────────────────────────────────┤
│  pytest 核心                                             │
│  发现 → fixture 注入 → 断言 → 报告                       │
├─────────────────────────────────────────────────────────┤
│  插件层（可选）                                          │
│  pytest-cov │ pytest-asyncio │ pytest-xdist │ ...       │
└─────────────────────────────────────────────────────────┘
```

**典型调用链：**

```
pytest 命令 → 收集 tests/ → 执行 test_* 函数 → assert 失败则报告详情
                    ↓
              fixture 按依赖顺序 setup → yield → teardown
```

---

## 2. 命令行语法结构

### 2.1 通用格式

```bash
pytest [选项] [路径...] [::选择器]
```

**示例拆解：**

```bash
pytest -v tests/test_user.py::test_create_user --tb=short -x
│      │  │                    │                 │         │
│      │  │                    │                 │         └── 首个失败即停止
│      │  │                    │                 └── 简短 traceback
│      │  │                    └── 单个测试函数
│      │  └── 测试文件
│      └── 详细输出
└── 测试运行器
```

### 2.2 常用选项速查

| 选项 | 说明 |
|------|------|
| `-v` / `-vv` | 详细输出（显示每个测试名） |
| `-q` | 安静模式 |
| `-x` | 首个失败后停止 |
| `-k "expr"` | 按名称表达式过滤（如 `-k "user and not slow"`） |
| `-m marker` | 按标记运行（如 `-m "slow"`） |
| `--tb=style` | traceback 样式：`short` / `line` / `no` |
| `--lf` | 只跑上次失败的 |
| `--ff` | 先跑上次失败的 |
| `-s` | 不捕获 stdout/stderr |
| `--cov=src` | 覆盖率（需 pytest-cov） |
| `-n auto` | 并行（需 pytest-xdist） |

### 2.3 测试发现规则

| 规则 | 默认值 |
|------|--------|
| 目录 | 当前目录及子目录 |
| 文件 | `test_*.py` 或 `*_test.py` |
| 函数 | `test_*` |
| 类 | `Test*`（不能有 `__init__`） |
| 类中方法 | `test_*` |

---

## 3. 测试函数语法

### 3.1 最小测试

```python
def test_addition():
    assert 1 + 1 == 2
```

### 3.2 使用 fixture

```python
def test_user(db_session, sample_user):
    assert sample_user.name == "Alice"
```

### 3.3 异常断言

```python
import pytest

def test_divide_by_zero():
    with pytest.raises(ValueError, match="除数不能为零"):
        divide(10, 0)
```

### 3.4 参数化

```python
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_add(a, b, expected):
    assert a + b == expected
```

---

## 4. fixture 语法结构

### 4.1 定义与使用

```python
import pytest

@pytest.fixture
def sample_user():
    return User(name="Alice", email="a@b.com")

def test_name(sample_user):
    assert sample_user.name == "Alice"
```

### 4.2 作用域

| scope | 生命周期 | 典型用途 |
|-------|----------|----------|
| `function` | 每个测试（默认） | 隔离数据 |
| `class` | 每个测试类 | 类内共享 |
| `module` | 每个模块 | 模块级资源 |
| `package` | 每个包 | 少见 |
| `session` | 整个测试会话 | 数据库连接池 |

```python
@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()
```

### 4.3 setup / teardown（yield 模式）

```python
@pytest.fixture
def temp_file(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text("hello")
    yield path
    # teardown：pytest 自动在测试后执行
    if path.exists():
        path.unlink()
```

### 4.4 fixture 依赖链

```python
@pytest.fixture
def db_session(db_engine):
    session = Session(db_engine)
    yield session
    session.rollback()
    session.close()

def test_query(db_session, sample_user):
    ...
```

---

## 5. 标记（marker）语法

```python
import pytest

@pytest.mark.slow
def test_heavy_computation():
    ...

@pytest.mark.skip(reason="功能未实现")
def test_future_feature():
    ...

@pytest.mark.skipif(sys.platform == "win32", reason="仅 Linux")
def test_unix_only():
    ...

@pytest.mark.xfail(reason="已知 Bug #123")
def test_known_bug():
    ...
```

**运行：**

```bash
pytest -m slow          # 只跑 slow
pytest -m "not slow"    # 排除 slow
```

---

## 6. 内置 fixture 速查

| fixture | 作用 |
|---------|------|
| `tmp_path` | 临时目录（Path 对象） |
| `tmpdir` | 临时目录（legacy，推荐 tmp_path） |
| `monkeypatch` | 临时修改属性/环境变量 |
| `capsys` | 捕获 stdout/stderr |
| `caplog` | 捕获 logging |
| `recwarn` | 捕获 warnings |
| `request` | 当前测试的元信息 |

---

## 7. conftest.py 规则

```
project/
├── src/
│   └── app/
├── tests/
│   ├── conftest.py      ← tests 包及子目录共享
│   ├── test_api.py
│   └── unit/
│       ├── conftest.py  ← 仅 unit/ 子目录
│       └── test_utils.py
└── pytest.ini
```

- `conftest.py` 中的 fixture **自动发现**，无需 import
- 子目录的 conftest 可覆盖/扩展父级 fixture
- **不要**在测试文件中 `from conftest import ...`

---

## 8. 配置文件

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
markers =
    slow: 耗时测试
    integration: 集成测试
filterwarnings =
    ignore::DeprecationWarning
```

### pyproject.toml（现代项目推荐）

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
markers = [
    "slow: 耗时测试",
    "integration: 集成测试",
]
```

---

## 9. 常用插件命令

| 插件 | 安装 | 典型用法 |
|------|------|----------|
| pytest-cov | `pip install pytest-cov` | `pytest --cov=src --cov-report=html` |
| pytest-asyncio | `pip install pytest-asyncio` | `@pytest.mark.asyncio` |
| pytest-xdist | `pip install pytest-xdist` | `pytest -n auto` |
| pytest-mock | `pip install pytest-mock` | `mocker.patch(...)` |
| httpx | `pip install httpx` | FastAPI `TestClient` 底层 |

---

## 10. 断言增强

```python
# 近似浮点
assert result == pytest.approx(0.333, rel=1e-2)

# 集合/列表（顺序无关）
assert set(items) == {"a", "b", "c"}

# 字典子集
assert {"name": "Alice"} == pytest.approx({"name": "Alice", "id": 1}, abs=0)
# 或手动：
assert response["name"] == "Alice"
assert "id" in response

# 异常消息
with pytest.raises(ValueError, match=r"invalid.*email"):
    validate_email("bad")
```

---

## 11. 与 unittest 对比

| 特性 | unittest | pytest |
|------|----------|--------|
| 断言 | `self.assertEqual()` | 原生 `assert` |
| 发现 | 继承 `TestCase` | `test_*` 函数即可 |
| fixture | `setUp` / `tearDown` | `@pytest.fixture` + yield |
| 参数化 | 较繁琐 | `@pytest.mark.parametrize` |
| 插件 | 有限 | 丰富生态 |

pytest **兼容** unittest 风格的测试类，可渐进迁移。

---

## 12. 快速诊断

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 收集到 0 个测试 | 文件/函数命名不符 | 检查 `test_` 前缀 |
| fixture not found | 未在 conftest 或同文件定义 | 检查作用域与路径 |
| import 错误 | PYTHONPATH 未包含 src | `pip install -e .` 或 conftest 加 path |
| 测试互相影响 | 共享可变状态 | 缩小 fixture scope 或每次新建 |
| 慢 | 集成测试过多 | 标记 `-m "not integration"` |

👉 下一课：[01_pytest_basics.md](01_pytest_basics.md)
