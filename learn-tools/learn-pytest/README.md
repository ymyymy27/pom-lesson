# pytest 测试框架 从零开始学习教程

独立工具课，与 [`learn-pip`](../learn-pip/) 并列。Markdown 文档 + 可运行练习代码，不依赖全栈课程进度。

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 参考 | `00_pytest_syntax.md` | pytest 语法结构参考（命令行 / 断言 / fixture / 插件） |
| 第1课 | `01_pytest_basics.md` | pytest 是什么、安装、第一个测试、发现规则 |
| 第2课 | `02_assertions_and_fixtures.md` | 断言技巧、fixture 生命周期、作用域 |
| 第3课 | `03_parametrize_and_markers.md` | 参数化、标记、skip / xfail、分组运行 |
| 第4课 | `04_mocking_and_isolation.md` | Mock、monkeypatch、捕获输出、临时文件 |
| 第5课 | `05_conftest_and_plugins.md` | conftest.py、常用插件（cov / asyncio / xdist） |
| 第6课 | `06_integration_testing.md` | 测试 API、数据库、FastAPI TestClient |
| 第7课 | `07_practical_project.md` | 实战：完整项目测试（单元 + 集成 + CI） |

## 学习方式

- Markdown 文档 + `practice/` 目录中的可运行代码
- 需要先完成 [`learn-pip`](../learn-pip/) 第 3 课（虚拟环境）
- 每课都有可运行的示例和动手练习
- 按顺序学习，最后一课整合全部能力

## 环境准备

```bash
cd practice
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
pytest -v
```

- **Python**: 3.11+
- **依赖**: pytest、pytest-cov、httpx（见 `practice/requirements.txt`）

## 学习顺序建议

```
learn-pip (虚拟环境)  →  learn-pytest (本课程)  →  按需选学
                              │                      ├─ learn-fullstack (Django/DRF 测试)
                              │                      ├─ learn-se/03_testing_and_quality (测试理论)
                              │                      └─ learn-dev-methods/02_devops_and_cicd (CI 集成)
```

## 与其他课程的关系

| 主题 | 权威来源（本课） | 其他课程 |
|------|------------------|----------|
| pytest 语法与 fixture | `learn-pytest` | — |
| 测试金字塔 / TDD 理论 | — | `learn-se/learn-fundamentals/03_testing_and_quality.md` |
| Django/DRF 测试 | — | `learn-fullstack/stage-04-drf` |
| CI 中运行 pytest | `learn-pytest` 第 7 课 | `learn-dev-methods/02_devops_and_cicd.md` |
