# 第1课：pytest 基础 - 核心概念与第一个测试

## 1. pytest 是什么？

### 一句话解释

**pytest 就是 Python 里「写 assert 就能跑」的测试框架** —— 自动发现测试、失败时给出清晰报告，插件生态丰富。

### 类比理解

| 日常概念 | pytest 概念 |
|---------|-------------|
| 质检清单 | **测试用例** `test_*` |
| 标准样品 | **fixture** 准备好的测试数据 |
| 生产线抽检 | **测试发现** 自动找 `test_*.py` |
| 质检报告 | **终端输出** / HTML 报告 |

### pytest vs unittest

| 特性 | unittest（标准库） | pytest |
|------|-------------------|--------|
| 写法 | 类 + `self.assert*` | 函数 + `assert` |
| 学习曲线 | 较陡 | 平缓 |
| fixture | setUp/tearDown | `@pytest.fixture` 更灵活 |
| 插件 | 少 | cov、asyncio、xdist 等 |
| 失败信息 | 一般 | 详细 diff |

**结论：** 新项目优先 pytest；老项目可共存，逐步迁移。

---

## 2. pytest 在开发流程中的位置

```
┌────────────────────────────────────────────┐
│              开发循环                       │
├────────────────────────────────────────────┤
│ 1. 写/改功能代码                            │
│ 2. 写/改测试（test_*.py）                   │
│ 3. pytest 本地运行                          │
│ 4. 绿 → 提交；红 → 修复                     │
│ 5. CI 再次跑 pytest（见第 7 课）            │
└────────────────────────────────────────────┘
```

测试金字塔（详见 `learn-se/learn-fundamentals/03_testing_and_quality.md`）：

```
        /\
       /E2E\        少量
      /──────\
     / 集成测试 \    适量
    /────────────\
   /   单元测试    \  大量 ← 本课程重点
  /────────────────\
```

---

## 3. 安装与环境

```bash
cd learn-tools/learn-pytest/practice
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
pytest --version    # pytest 8.x
```

**requirements.txt 核心依赖：**

```
pytest>=8.0.0
pytest-cov>=4.0.0
httpx>=0.27.0
```

---

## 4. 第一个测试

### 4.1 项目结构（practice 目录）

```
practice/
├── src/
│   └── calculator.py    # 被测代码
├── tests/
│   └── test_calculator.py
├── pytest.ini
└── requirements.txt
```

### 4.2 被测代码

```python
# src/calculator.py
def add(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b
```

### 4.3 测试代码

```python
# tests/test_calculator.py
from calculator import add, divide
import pytest

def test_add():
    assert add(2, 3) == 5

def test_divide():
    assert divide(10, 2) == 5

def test_divide_by_zero():
    with pytest.raises(ValueError, match="除数不能为零"):
        divide(10, 0)
```

### 4.4 运行

```bash
# 在 practice 目录下（pytest.ini 已配置 pythonpath=src）
pytest -v
```

**预期输出：**

```
tests/test_calculator.py::test_add PASSED
tests/test_calculator.py::test_divide PASSED
tests/test_calculator.py::test_divide_by_zero PASSED
3 passed
```

---

## 5. 测试发现规则

pytest **自动收集**测试，无需手动注册：

| 类型 | 命名规则 |
|------|----------|
| 文件 | `test_*.py` 或 `*_test.py` |
| 函数 | `test_*` |
| 类 | `Test*`（不要写 `__init__`） |
| 类方法 | `test_*` |

```bash
pytest tests/test_calculator.py           # 单个文件
pytest tests/test_calculator.py::test_add # 单个测试
pytest -k "divide"                        # 名称含 divide 的测试
```

---

## 6. AAA 模式

好的测试结构：**Arrange → Act → Assert**

```python
def test_add_negative_numbers():
    # Arrange（准备）
    a, b = -1, -2

    # Act（执行）
    result = add(a, b)

    # Assert（断言）
    assert result == -3
```

一个测试只验证**一个行为**；多个无关断言应拆成多个测试。

---

## 7. 失败时 pytest 告诉你什么

故意写错断言：

```python
def test_wrong():
    assert add(2, 3) == 6
```

输出会包含：

- 哪个文件、哪一行
- 期望值 vs 实际值（`assert 5 == 6`）
- 局部变量（`-l` 或 `--showlocals`）

```bash
pytest -vv --showlocals
```

---

## 8. 测试类（可选）

函数式测试足够应对大多数场景；需要分组时可用类：

```python
class TestCalculator:
    def test_add(self):
        assert add(1, 1) == 2

    def test_divide(self):
        assert divide(4, 2) == 2
```

**注意：** 类名必须以 `Test` 开头，且**不要**定义 `__init__`。

---

## 9. 练习

1. 克隆/进入 `practice`，安装依赖，运行 `pytest -v` 确保全绿
2. 为 `calculator.py` 添加 `multiply(a, b)`，并写对应测试
3. 故意让测试失败，观察 pytest 的错误报告
4. 用 `pytest -k "add"` 只运行加法相关测试

<details>
<summary>multiply 参考答案</summary>

```python
# src/calculator.py
def multiply(a, b):
    return a * b

# tests/test_calculator.py
def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(0, 100) == 0
    assert multiply(-2, 3) == -6
```

</details>

---

## 10. 自检清单

- [ ] 能解释 pytest 与 unittest 的主要区别
- [ ] 知道测试文件/函数的命名规则
- [ ] 会写 `assert` 和 `pytest.raises`
- [ ] 会用 `pytest -v`、`-k` 运行测试
- [ ] 理解 AAA 测试结构

👉 下一课：[02_assertions_and_fixtures.md](02_assertions_and_fixtures.md)
