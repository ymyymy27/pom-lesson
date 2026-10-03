> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第6课：现代 Python 工具链 — uv

> 2025–2026 新技术补充课  
> 前置：[`01-第1课pip 是什么 & 基本命令.md`](<01-第1课pip 是什么 & 基本命令.md>) ~ [`03-第3课虚拟环境（venv）与 pip 配合使用.md`](<03-第3课虚拟环境（venv）与 pip 配合使用.md>)

## 1. 为什么需要 uv？

传统 Python 项目管理需要多个工具：

```
pyenv      → Python 版本
venv       → 虚拟环境
pip        → 安装包
pip-tools  → 锁文件
pipx       → CLI 工具
poetry     → 项目管理（可选）
```

**uv**（Astral 出品，Rust 编写）将上述能力合并为**单一二进制**，速度比 pip 快 10–100 倍。

| 对比 | pip + venv | Poetry | uv |
|------|-----------|--------|-----|
| 安装速度 | 基准 | ~10x | **10–100x** |
| 锁文件 | 需 pip-tools | poetry.lock | uv.lock |
| Python 版本管理 | 需 pyenv | 不支持 | ✅ 内置 |
| 独立二进制 | ❌ 需 Python | ❌ 需 Python | ✅ 无需 Python |
| CI 友好度 | 一般 | 好 | **极好** |

---

## 2. 安装 uv

```powershell
# Windows（PowerShell）
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或通过 pip
pip install uv

# 验证
uv --version
```

---

## 3. 核心命令对照

| 旧方式 | uv 方式 |
|--------|---------|
| `python -m venv .venv` | `uv venv` |
| `pip install requests` | `uv add requests` |
| `pip install -r requirements.txt` | `uv sync` |
| `pip freeze > requirements.txt` | `uv lock`（自动生成 uv.lock） |
| `pyenv install 3.12` | `uv python install 3.12` |
| `pipx run ruff` | `uvx ruff` |
| `python script.py` | `uv run python script.py` |

---

## 4. 新项目快速开始

```powershell
# 创建项目
mkdir my-project && cd my-project
uv init

# 添加依赖
uv add fastapi uvicorn pydantic

# 添加开发依赖
uv add --dev pytest ruff

# 运行（自动使用项目 venv，无需 activate）
uv run python main.py
uv run pytest
```

生成的 `pyproject.toml`：

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.34.0",
    "pydantic>=2.10.0",
]

[dependency-groups]
dev = ["pytest>=8.0", "ruff>=0.9.0"]
```

`uv.lock` 提供**跨平台确定性**安装。

---

## 5. 从现有项目迁移

### 从 requirements.txt

```powershell
# 初始化
uv init

# 导入现有依赖
uv add $(Get-Content requirements.txt)

# 生成锁文件
uv lock
```

### 从 Poetry

```powershell
# 使用 migrate-to-uv 工具
uvx migrate-to-uv

# 重建环境
uv sync
```

---

## 6. Docker 中使用 uv

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./

# 利用 uv 缓存层，安装依赖到系统（容器场景）
RUN uv sync --frozen --no-dev

COPY . .
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0"]
```

**优势：** Docker 构建速度显著提升（MLOps 社区常见 2–5x 加速）。

---

## 7. CI/CD 示例（GitHub Actions）

```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.12"
      - run: uv sync
      - run: uv run pytest
      - run: uv run ruff check .
```

**注意：** uv 作为独立二进制，CI 无需预装 Python 即可安装依赖。

---

## 8. uv vs pip：何时仍用 pip？

| 场景 | 建议 |
|------|------|
| 新项目 | **uv** |
| 已有 Poetry 项目且稳定 | 可继续 Poetry，或 migrate-to-uv |
| 仅需临时装一个包 | `uv pip install xxx` 或 `uvx` |
| 遗留 requirements.txt 项目 | `uv pip install -r requirements.txt` |
| 发布到 PyPI 的库 | uv 或 Poetry 均可 |

---

## 9. 与 learn-ai / learn-fullstack 的关系

- **learn-ai stage-00**：venv/pip 基础仍需要理解；uv 作为**现代替代**推荐
- **learn-fullstack**：Django 项目可用 `uv add django djangorestframework`
- **learn-tools**：本课为 pip 课程的**第 6 课扩展**，不替代 pip 基础

---

## 10. 动手练习

1. 用 `uv init` 创建项目，添加 `httpx` 和 `pytest`
2. 将本工作区 `requirements.txt` 导入 uv 项目并 `uv sync`
3. 写一条 GitHub Actions 用 uv 跑测试
4. 对比 `pip install` vs `uv sync` 的冷安装时间

---

## 11. 自检清单

- [ ] 能解释 uv 相比 pip+venv 的优势
- [ ] 会用 `uv add`、`uv sync`、`uv run`
- [ ] 知道如何从 requirements.txt 迁移
- [ ] 能在 Dockerfile 中使用 uv
- [ ] 理解 uv.lock 的作用

---

## 参考

- [uv 官方文档](https://docs.astral.sh/uv/)
- [uv GitHub](https://github.com/astral-sh/uv)
- [Poetry Was Good, Uv Is Better — MLOps Community](https://mlops.community/blog/poetry-was-good-uv-is-better-an-mlops-migration-story-2025-02-03)
