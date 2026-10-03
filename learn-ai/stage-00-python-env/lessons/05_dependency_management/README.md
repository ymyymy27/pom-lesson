# Lesson 5: 依赖管理

> 从原始的 requirements.txt 到现代的 pyproject.toml / Poetry / PDM，系统掌握 Python 依赖管理的演进

---

## 5.1 为什么要管理依赖？

**依赖管理** 的目标：让项目在任何机器上都能复现出完全一致的运行环境。

```
问题：无依赖管理
┌──────────────────────────────────────────┐
│ 开发者的机器（手动安装）                   │
│  langchain 1.2.15                         │
│  numpy 1.26.0                             │
│  pandas 2.0.3                             │
│  (可能还装了其他杂七杂八的包)               │
└──────────────────────────────────────────┘
                    ↓
怎么告诉别人（或服务器）"我用了哪些包"？

错误做法："你 pip install langchain 就行" → 版本不确定，可能不兼容
正确做法：提供一个依赖声明文件，让 pip 安装精确的版本
```

---

## 5.2 requirements.txt

最简单、最通用的依赖声明文件。

### 基本写法

```txt
# requirements.txt
langchain==1.2.15
langchain-openai==1.1.12
numpy>=1.24.0,<2.0
pandas
requests~=2.28.0  # ~= 表示"兼容"（>=2.28.0 且 < 2.29.0）
```

### 依赖文件分割

大型项目通常按环境拆分：

```txt
# requirements.txt（基础依赖）
langchain
fastapi
pydantic

# requirements-dev.txt（开发依赖）
-r requirements.txt    # 包含基础依赖
pytest>=7.0
black
ruff
mypy

# requirements-prod.txt（生产依赖）
-r requirements.txt    # 包含基础依赖
# 不包含 dev 依赖
```

### 生成 requirements.txt

```powershell
# 导出所有已安装包的精确版本
pip freeze > requirements.txt
```

**问题**：`pip freeze` 会导出所有包，包括传递依赖和 pip 自身。

**更好的做法**：使用 `pipreqs` 只导出项目代码实际 import 的包：

```powershell
pip install pipreqs
pipreqs ./ --force   # 扫描当前目录，生成 requirements.txt
```

### 使用 requirements.txt

```powershell
# 从文件安装
pip install -r requirements.txt

# 安装时排除某些包
pip install -r requirements.txt --no-deps

# 只安装指定的 requirements 文件
pip install -r requirements-dev.txt
```

---

## 5.3 pip freeze 的坑

```powershell
# 导出
pip freeze > requirements.txt
```

**输出示例**（问题很多）：

```txt
# 这些都是传递依赖，不应该出现在项目中
certifi @ file:///.../certifi-2024.2.2-py3-none-any.whl
charset-normalizer @ file:///.../charset_normalizer-3.3.2-cp311-cp311-win_amd64.whl
idna @ file:///.../idna-3.6-py3-none-any.whl
requests-2.31.0.dist-info
urllib3 @ file:///.../urllib3-2.2.1-py3-none-any.whl
# pip 自己也在里面（不应该）
pip==26.0.1
setuptools==69.5.1
wheel==0.43.0
```

**问题 1**：包含 `@ file://` 路径，本地缓存路径，不可移植

**问题 2**：包含 pip/setuptools/wheel，不应该出现在项目依赖中

**问题 3**：包含所有传递依赖（你直接 import 的包的依赖）

**解决方案**：清理后再使用

```powershell
# 只保留你实际需要的包（手动维护）
pip freeze | Select-String -Pattern "^(?!pip|setuptools|wheel|^-)" > requirements.txt
```

---

## 5.4 setup.py / setup.cfg（传统打包方式）

在 `pyproject.toml` 成为标准之前，`setup.py` 是主流的打包方式。

### setup.py 示例

```python
from setuptools import setup, find_packages

setup(
    name="mypackage",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28",
        "numpy>=1.24",
    ],
    python_requires=">=3.8",
)
```

### setup.cfg 示例

```ini
[metadata]
name = mypackage
version = 0.1.0

[options]
install_requires =
    requests>=2.28
    numpy>=1.24
python_requires = >=3.8
```

**问题**：`setup.py` 既是配置文件又是可执行代码，容易混乱。

---

## 5.5 pyproject.toml（现代标准）

PEP 517/518/621 定义了 `pyproject.toml` 作为现代 Python 项目的标准配置格式。

### pyproject.toml 示例

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mypackage"
version = "0.1.0"
description = "我的 Python 包"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "你的名字", email = "you@example.com"}
]
dependencies = [
    "langchain>=1.0",
    "langchain-openai>=1.0",
    "fastapi>=0.100",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=23.0",
    "ruff>=0.1",
    "mypy>=1.0",
]
prod = [
    "uvicorn[standard]>=0.20",
]

[project.urls]
Homepage = "https://github.com/you/mypackage"

[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
```

### 为什么用 pyproject.toml？

1. **声明式**：不是代码，是纯配置文件
2. **标准化**：被 pip、Poetry、PDm、setuptools 等所有工具支持
3. **多工具配置合一**：black、ruff、mypy 等工具的配置都可以写在里面
4. **支持可选依赖**：用 `[project.optional-dependencies]` 分组

### 使用 pyproject.toml 安装

```powershell
# 安装项目（开发模式）
pip install -e .

# 安装可选依赖
pip install -e ".[dev]"      # 开发依赖
pip install -e ".[prod]"      # 生产依赖
pip install -e ".[dev,prod]"  # 全部
```

---

## 5.6 Poetry

Poetry 是一个现代的依赖管理和打包工具，比 pip + setuptools 更优雅。

### 安装

```powershell
pip install poetry
```

### 核心命令

```powershell
# 初始化项目（创建 pyproject.toml）
poetry init

# 安装依赖（自动创建虚拟环境 + pyproject.toml）
poetry add 包名

# 安装开发依赖
poetry add --dev pytest

# 安装所有依赖
poetry install

# 安装时不创建虚拟环境（使用现有环境）
poetry install --no-root

# 导出为 requirements.txt（兼容性场景）
poetry export -f requirements.txt --output requirements.txt

# 更新依赖到最新兼容版本
poetry update

# 查看依赖树
poetry show --tree
```

### poetry.lock 的作用

Poetry 会生成 `poetry.lock` 文件，记录每个包**精确的下载 URL 和哈希值**。

```
pyproject.toml  → 声明"我需要 langchain >= 1.0"
poetry.lock      → 记录"我实际安装的是 langchain 1.2.15，来源是 xxx，hash 是 yyy"
```

**效果**：即使上游更新了 langchain 1.3.0，你的项目仍会用 lock 文件中的 1.2.15，确保环境完全一致。

```powershell
# 安装时会读取 poetry.lock，安装精确的锁定版本
poetry install

# 更新 lock 文件
poetry update
```

### 推荐项目结构（Poetry）

```
my-project/
├─ src/
│   └─ mypackage/
│       ├─ __init__.py
│       └─ main.py
├─ tests/
│   └─ test_main.py
├─ pyproject.toml
├─ poetry.lock
├─ .gitignore
└─ README.md
```

---

## 5.7 PDM（Python Development Master）

PDM 是另一个现代依赖管理工具，更轻量，理念与 Poetry 类似。

### 安装

```powershell
pip install pdm
```

### 核心命令

```powershell
# 初始化项目
pdm init

# 添加依赖
pdm add 包名
pdm add -d dev 包名  # 开发依赖

# 安装依赖
pdm install

# 从 lock 更新
pdm update
```

PDM 也支持 `pyproject.toml`，且生成 `pdm.lock`。

---

## 5.8 依赖管理工具对比

| 工具 | 依赖声明 | 虚拟环境 | Lock 文件 | 学习曲线 |
|-----|---------|---------|---------|---------|
| pip + requirements.txt | requirements.txt | 需额外创建 venv | 无（需 pip-tools） | 低 |
| pip + pip-tools | requirements.in + *.txt | 需额外创建 venv | 有（*.txt） | 中 |
| Poetry | pyproject.toml | 内置 | poetry.lock | 低 |
| PDM | pyproject.toml | 内置 | pdm.lock | 低 |
| Conda | environment.yml | 内置 | 无原生 lock | 中 |

### 推荐

| 场景 | 推荐工具 |
|-----|---------|
| 个人项目 / 简单脚本 | pip + venv + requirements.txt |
| 中型团队 / 多人协作 | Poetry 或 PDM + pyproject.toml |
| 数据科学 / ML | Conda（方便 GPU 包管理） |
| 需要发布到 PyPI | Poetry 或 PDM + pyproject.toml |

---

## 5.9 依赖版本约束符号解释

```
>= 1.0       大于等于 1.0
> 1.0        大于 1.0
<= 1.0       小于等于 1.0
< 1.0        小于 1.0
== 1.0       精确等于 1.0（锁死版本）
~= 1.0       兼容 1.0（>=1.0 且 < 下一个主版本）
!= 1.0       不等于 1.0

# 组合
>=1.0,<2.0   大于等于1.0 且 小于2.0
```

---

## 5.10 实战：规范化你的 AI 学习项目

假设你在 `stage-05-llm-api` 项目中，现在用它来演示规范化。

### 当前问题（猜测）

```
stage-05-llm-api/
├─ study/
│   └─ 01.py          # 直接 import langchain，没有 venv
├─ learn-langchain/
│   └─ 01_chat_models.py  # 同样的问题
└─ 没有 requirements.txt
```

### 规范化步骤

**Step 1: 创建虚拟环境**

```powershell
cd stage-05-llm-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Step 2: 安装依赖**

```powershell
pip install langchain langchain-openai
```

**Step 3: 生成 requirements.txt**

```powershell
pip freeze > requirements.txt
# 然后手动清理掉 pip, setuptools, wheel 和各种 @ file:// 行
```

**Step 4: 规范化后的结构**

```
stage-05-llm-api/
├─ .venv/                    # 虚拟环境
├─ study/
│   └─ 01.py
├─ learn-langchain/
│   └─ 01_chat_models.py
├─ requirements.txt          # 依赖声明
├─ requirements-dev.txt      # （可选）开发依赖
└─ README.md
```

---

## 课后练习

1. 在你的 `study/` 目录下创建虚拟环境并激活
2. 安装你需要的包（如 langchain）
3. 生成并查看 `requirements.txt`
4. 理解 `==`、`>=`、`~=` 三种版本约束的区别
5. 如果你的项目有多个环境（dev/prod），练习拆分 requirements 文件

---

## 下一步

→ [Lesson 6: IDE 环境配置（Cursor / VS Code）](../06_ide_configuration/README.md)
