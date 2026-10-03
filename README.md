# Learn — 全栈开发者学习工作区

面向开发者的系统化学习仓库，涵盖软件工程理论、全栈实战、AI 应用开发、开发工具与产品经理技能。

## 课程轨道一览

| 轨道 | 目录 | 定位 | 前置要求 |
|------|------|------|----------|
| 软件工程 | [`learn-se/`](learn-se/) | 架构、设计模式、DDD、SRE、安全、API、权限/多租户 | 1+ 项目经验 |
| 全栈 Web | [`learn-fullstack/`](learn-fullstack/) | Django + React + Docker + CI/CD | Python 基础 |
| AI 开发 | [`learn-ai/`](learn-ai/) | ML → LLM → RAG → Agent → MLOps | Web + Python |
| 搜索引擎 | [`learn-search-engine/`](learn-search-engine/) | 检索原理 → BM25 → Elasticsearch → 向量搜索/RAG | Python 基础 |
| 开发工具 | [`learn-tools/`](learn-tools/) | Git、Shell、Docker、SQL、pip/uv | 无 |
| 命令行 | [`learn-cli/`](learn-cli/) | Windows PowerShell 实战 | 无 |
| 移动开发 | [`learn-flutter/`](learn-flutter/) | Flutter + Dart 跨平台 App | 编程基础 + Web/API 经验 |
| Agno 智能体 | [`learn-agno/`](learn-agno/) | Agno 框架专精 | learn-ai stage-04/05 |
| Neovim | [`learn-neovim/`](learn-neovim/) | 编辑器效率与插件 | 无 |
| 产品经理 | [`learn-pm/`](learn-pm/) | 产品思维 + AI 产品 | 无 |

## 推荐学习路径

```
入门工具链          工程思维              实战落地
learn-tools    →   learn-se         →   learn-fullstack
learn-cli          learn-fundamentals     TaskFlow 项目
                   learn-architecture
                          ↓
                    AI 专项（可选）
                   learn-ai → learn-agno

                           ↓
                     移动端（可选）
          learn-fullstack → learn-flutter（TaskFlow App）
```

## 贯穿项目

| 项目 | 涉及轨道 | 说明 |
|------|----------|------|
| **TaskFlow** | learn-se、learn-fullstack | 任务协作平台：SE 偏架构设计，全栈偏实现 |
| **TaskFlow App** | learn-fullstack、learn-flutter | TaskFlow 移动客户端：Flutter 对接 DRF 后端 |
| **AI Hub** | learn-ai、learn-agno | AI 智能助手平台：分类 → RAG → Agent |

## 轨道间分工（避免重复学习）

| 主题 | 权威来源 | 其他轨道 |
|------|----------|----------|
| Python 环境 | AI 线 → `stage-00-python-env` | fullstack stage-01 链接；tools → `learn-pip` |
| Shell | Windows → `learn-cli` | Linux/Mac → `learn-tools/learn-shell` |
| Git | 工作流 → `learn-tools/learn-git` | 命令速查 → `learn-cli` L8 |
| Docker | 概念 → `learn-tools/learn-docker` | 部署 → fullstack stage-12；命令 → learn-cli L9 |
| 组网/内网穿透 | 概念与实战 → `learn-tools/learn-network` | 部署 → fullstack stage-13；Docker 网络 → learn-docker L4 |
| Redis | 命令与模式 → `learn-tools/learn-redis` | Django 集成 → fullstack stage-06；架构案例 → learn-se |
| REST/API 设计 | 理论 → `learn-se/learn-api-design` | 实现 → fullstack stage-04 DRF |
| 敏捷/Scrum | 工程实践 → `learn-se/learn-dev-methods` | PM 视角 → `learn-pm` |
| RAG | 原理 → `learn-ai/stage-08` | Agno 封装 → `learn-agno` L3 |
| AI Agent | 生态全景 → `learn-ai/stage-09` | Agno 专精 → `learn-agno` |

## 2025–2026 新技术补充索引

各轨道已新增或更新的「新技术」课时见 [`COURSE_GAP_ANALYSIS.md`](COURSE_GAP_ANALYSIS.md)。

| 新技术领域 | 补充位置 |
|------------|----------|
| 平台工程 / IDP / AI 辅助开发 | `learn-se/learn-dev-methods/05_platform_engineering_and_ai_dev.md` |
| OWASP LLM Top 10 / Agentic AI 安全 | `learn-se/learn-security/04_llm_and_agent_security.md` |
| Agent 评估 / MCP 2026 更新 | `learn-ai/stage-09-ai-agent/08-agent-evaluation-and-harness.md` |
| Graph RAG | `learn-ai/stage-08-rag/06-graph-rag.md` |
| React Compiler / 前端 2026 趋势 | `learn-fullstack/stage-09-frontend-advanced/06-前端新技术2026.md` |
| Prometheus + Grafana 实战 | `learn-fullstack/stage-14-optimization/05-Prometheus与Grafana实战.md` |
| 可观测性 | `learn-se/learn-observability/` |
| uv 现代 Python 工具链 | `learn-tools/learn-pip/06_modern_tooling_uv.md` |
| TaskFlow 项目骨架 | `learn-fullstack/project/taskflow/` |
| AI Hub 项目骨架 | `learn-ai/projects/ai-hub/` |
| Agno 生产与安全 | `learn-agno/06_production_and_security.md` |
| Neovim LSP | `learn-neovim/lessons/11_lsp_and_completion/lesson.md` |
| DDD 战略设计 | `learn-se/learn-domain-design/04_strategic_design.md` |
| 认证授权与多租户（RBAC/ABAC/权限中台） | `learn-se/learn-permission/`（9 课 + 3 练习） |
| 消息队列集成 | `learn-se/learn-architecture/06_messaging_and_integration.md` |
| XGBoost / LlamaIndex / CrewAI | `learn-ai/` 各 stage 补充课 |
| 推理引擎全景 | `learn-ai/learn-inference-engine/`（10 课，多引擎实战 + 思考模型服务） |
| PM 模板库 | `learn-pm/templates/` |

## 快速入口

- 软件工程新手 → [`learn-se/GETTING_STARTED.md`](learn-se/GETTING_STARTED.md)
- AI 开发新手 → [`learn-ai/STUDY_ROADMAP.md`](learn-ai/STUDY_ROADMAP.md)
- 搜索引擎实战 → [`learn-search-engine/GETTING_STARTED.md`](learn-search-engine/GETTING_STARTED.md)
- 全栈实战 → [`learn-fullstack/GETTING_STARTED.md`](learn-fullstack/GETTING_STARTED.md)
- 移动开发 → [`learn-flutter/GETTING_STARTED.md`](learn-flutter/GETTING_STARTED.md)
- 缺口分析与更新记录 → [`COURSE_GAP_ANALYSIS.md`](COURSE_GAP_ANALYSIS.md)
