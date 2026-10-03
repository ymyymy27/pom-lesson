> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 01 节：pytest 基础

## 一、为什么用 pytest？

pytest 是 Python 最流行的测试框架，相比 unittest 更简洁、更强大。

| 特性 | unittest | pytest |
|------|----------|--------|
| 断言 | `self.assertEqual(a, b)` | `assert a == b` |
| 测试发现 | 需要继承 TestCase | 函数名以 `test_` 开头即可 |
| Fixture | setUp/tearDown | `@pytest.fixture`（更灵活） |
| 参数化 | 繁琐 | `@pytest.mark.parametrize` |
| 插件 | 少 | 丰富（pytest-django、pytest-cov 等） |

### 1.1 安装

```bash
pip install pytest pytest-django pytest-cov factory-boy faker
```

### 1.2 配置

```ini
# pytest.ini 或 pyproject.toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["tests.py", "test_*.py", "*_tests.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "slow: 慢速测试",
    "integration: 集成测试",
]
```

---

## 二、编写第一个测试

```python
# tests/test_basic.py

def test_addition():
    assert 1 + 1 == 2

def test_string():
    name = "TaskFlow"
    assert name.lower() == "taskflow"
    assert "Task" in name

def test_list():
    tasks = [1, 2, 3]
    assert len(tasks) == 3
    assert 2 in tasks
```

```bash
# 运行测试
pytest                          # 运行所有测试
pytest tests/test_basic.py      # 运行指定文件
pytest -k "test_addition"       # 按名称匹配
pytest -v                       # 详细输出
pytest --tb=long                # 完整错误追踪
```

---

## 三、Fixture

Fixture 是 pytest 的核心特性，用于 **准备测试数据和环境**。

```python
import pytest

@pytest.fixture
def sample_task():
    """提供一个示例任务数据"""
    return {
        "title": "学习 pytest",
        "priority": 8,
        "status": "pending",
    }

@pytest.fixture
def task_list():
    """提供任务列表"""
    return [
        {"id": 1, "title": "任务1", "status": "pending"},
        {"id": 2, "title": "任务2", "status": "completed"},
        {"id": 3, "title": "任务3", "status": "in_progress"},
    ]

# 使用 fixture（参数名即 fixture 名）
def test_task_title(sample_task):
    assert sample_task["title"] == "学习 pytest"

def test_task_count(task_list):
    assert len(task_list) == 3

def test_filter_pending(task_list):
    pending = [t for t in task_list if t["status"] == "pending"]
    assert len(pending) == 1
```

### 3.1 Fixture 作用域

```python
@pytest.fixture(scope="function")   # 默认，每个测试函数重新创建
def user():
    return create_user()

@pytest.fixture(scope="class")      # 每个测试类创建一次
def db_connection():
    conn = connect()
    yield conn
    conn.close()

@pytest.fixture(scope="module")     # 每个模块创建一次
def api_client():
    return APIClient()

@pytest.fixture(scope="session")    # 整个测试会话只创建一次
def app_config():
    return load_config()
```

### 3.2 conftest.py

`conftest.py` 中的 fixture 自动对同目录及子目录的测试可用。

```python
# tests/conftest.py
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
    )

@pytest.fixture
def auth_client(api_client, user):
    """已认证的 API 客户端"""
    api_client.force_authenticate(user=user)
    return api_client
```

---

## 四、参数化测试

```python
import pytest

@pytest.mark.parametrize("priority,expected", [
    (0, "低"),
    (5, "中"),
    (8, "高"),
    (10, "紧急"),
])
def test_priority_label(priority, expected):
    def get_label(p):
        if p >= 9: return "紧急"
        if p >= 7: return "高"
        if p >= 4: return "中"
        return "低"
    
    assert get_label(priority) == expected

@pytest.mark.parametrize("status", ["pending", "in_progress", "completed", "cancelled"])
def test_valid_status(status):
    valid_statuses = {"pending", "in_progress", "completed", "cancelled"}
    assert status in valid_statuses
```

---

## 五、异常测试

```python
import pytest

def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0

def test_invalid_task():
    with pytest.raises(ValueError, match="标题不能为空"):
        create_task(title="")

def test_task_not_found():
    with pytest.raises(Task.DoesNotExist):
        Task.objects.get(pk=99999)
```

---

## 六、测试覆盖率

```bash
# 运行测试并生成覆盖率报告
pytest --cov=apps --cov-report=html --cov-report=term-missing

# 查看 htmlcov/index.html
```

```ini
# .coveragerc
[run]
source = apps
omit =
    */migrations/*
    */tests/*
    */admin.py
    */apps.py

[report]
show_missing = true
fail_under = 80
```

---

## 七、练习

1. 安装 pytest 和 pytest-django，配置 `pytest.ini`
2. 编写简单的断言测试，熟悉 `assert` 语法
3. 创建 `conftest.py`，定义 `user`、`api_client`、`auth_client` fixture
4. 使用 `@pytest.mark.parametrize` 编写参数化测试
5. 使用 `pytest.raises` 测试异常场景
6. 运行 `pytest --cov`，查看测试覆盖率
