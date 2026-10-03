> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第5课：conftest 与插件生态

## 1. conftest.py 是什么？

### 一句话解释

**conftest.py = 测试目录里的「公共 fixture 库」** —— pytest 自动加载，无需 import。

### 发现规则

```
practice/
├── src/
├── tests/
│   ├── conftest.py          ← 全局 fixture（client、db）
│   ├── test_api.py
│   └── unit/
│       ├── conftest.py      ← 仅 unit/ 生效
│       └── test_utils.py
└── pytest.ini
```

| 规则 | 说明 |
|------|------|
| 文件名固定 | 必须叫 `conftest.py` |
| 不自动 import | 测试里**不要** `from conftest import ...` |
| 作用域 | 所在目录及子目录 |
| 可多个 | 子目录可覆盖父级 fixture |

---

## 2. 典型 conftest 内容

```python
# tests/conftest.py
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_user():
    return {"id": 1, "name": "Alice", "email": "a@b.com"}
```

---

## 3. pytest.ini / pyproject.toml 配置

```ini
# practice/pytest.ini
[pytest]
testpaths = tests
pythonpath = src
addopts = -v --tb=short --strict-markers
markers =
    slow: 耗时测试
    integration: 集成测试
filterwarnings =
    ignore::DeprecationWarning
```

**常用 addopts：**

| 选项 | 作用 |
|------|------|
| `-v` | 详细输出 |
| `--tb=short` | 简短 traceback |
| `--strict-markers` | 未注册 marker 报错 |
| `--cov=src --cov-report=term-missing` | 覆盖率 |

---

## 4. pytest-cov：代码覆盖率

```bash
pip install pytest-cov

pytest --cov=src --cov-report=term-missing
pytest --cov=src --cov-report=html   # 生成 htmlcov/index.html
```

**解读：**

```
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
src/calculator.py       12      2    83%   15-16
```

- **Stmts**：可执行语句数
- **Miss**：未覆盖行
- **健康范围**：70–90%（非 100% 崇拜）

```ini
# 覆盖率门槛（CI 用）
addopts = --cov=src --cov-fail-under=80
```

---

## 5. pytest-asyncio：异步测试

```bash
pip install pytest-asyncio
```

```python
import pytest

@pytest.mark.asyncio
async def test_async_fetch():
    result = await fetch_data("http://example.com")
    assert result is not None
```

**pytest.ini 配置（pytest-asyncio 0.21+）：**

```ini
[pytest]
asyncio_mode = auto
```

---

## 6. pytest-xdist：并行执行

```bash
pip install pytest-xdist

pytest -n auto          # 按 CPU 核数并行
pytest -n 4             # 4 进程
```

**注意：**

- 测试必须**相互独立**（不共享可变全局状态）
- 集成测试慎用（数据库竞争）
- 与 `--cov` 可组合

---

## 7. pytest-mock

见第 4 课，`mocker` fixture 来自此插件（`pytest-mock` 包）。

---

## 8. 其他常用插件

| 插件 | 用途 |
|------|------|
| pytest-django | Django 集成、数据库 fixture |
| pytest-httpx | Mock httpx 请求 |
| pytest-timeout | 超时杀死慢测试 |
| pytest-randomly | 随机顺序暴露依赖 |
| pytest-sugar | 更美观的输出 |

---

## 9. 插件与 fixture 协作示例

```python
# tests/conftest.py
import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: 集成测试")

@pytest.fixture(scope="session")
def docker_services():
    """仅 integration 标记的测试需要"""
    # 启动 testcontainers 等
    yield
    # teardown
```

---

## 10. 练习

1. 把 `practice/tests/conftest.py` 中的公共 fixture 整理清楚
2. 运行 `pytest --cov=src --cov-report=term-missing`，找出未覆盖行并补测试
3. 在 `pytest.ini` 注册 `slow`、`integration` 标记

---

## 11. 自检清单

- [ ] 理解 conftest.py 的发现与作用域
- [ ] 会配置 `pytest.ini` / `addopts`
- [ ] 会用 pytest-cov 查看覆盖率
- [ ] 知道 pytest-asyncio、pytest-xdist 的适用场景
- [ ] 未注册 marker 时知道用 `--strict-markers` 捕获

👉 下一课：[06_integration_testing.md](06-第6课集成测试.md)
