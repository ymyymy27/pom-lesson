# Agno 智能体开发 从零开始学习教程

> 基于 [Agno 官方文档](https://docs.agno.com/first-agent) 整理，Markdown 文档 + 动手练习。

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 参考 | `00_agno_syntax.md` | Agno 语法结构参考（Agent / Team / Workflow / AgentOS） |
| 第1课 | `01_first_agent.md` | Agno 是什么、环境搭建、第一个 Agent |
| 第2课 | `02_tools_and_output.md` | Tools 工具、Structured Output 结构化输出 |
| 第3课 | `03_knowledge_memory.md` | Knowledge RAG、Memory 记忆、Session 会话 |
| 第4课 | `04_team_workflow.md` | Team 多智能体协作、Workflow 流程编排 |
| 第5课 | `05_agentos_service.md` | AgentOS 服务化、Tracing、UI、部署入门 |
| 第6课 | `06_production_and_security.md` | 生产部署、Agent 安全、Eval、可观测性 |

## 前置课程

建议先完成 [`learn-ai/stage-04`](../learn-ai/stage-04-llm-basics/) 和 [`learn-ai/stage-05`](../learn-ai/stage-05-llm-api/)，RAG 原理见 [`learn-ai/stage-08`](../learn-ai/stage-08-rag/)，Agent 生态全景见 [`learn-ai/stage-09`](../learn-ai/stage-09-ai-agent/)。

| 文件 | 对应课程 |
|------|----------|
| `practice/sorting_hat.py` | 第1课 |
| `practice/tools_agent.py` | 第2课 |
| `practice/knowledge_agent.py` | 第3课 |
| `practice/research_team.py` | 第4课 |
| `practice/workbench.py` | 第5课 |
| [`learn-knowledge-graph/practice/agno_graph_agent.py`](../learn-ai/learn-knowledge-graph/practice/agno_graph_agent.py) | 知识图谱 × Agno 接入（第 11 课） |

## 学习方式

- Markdown 文档 + 终端动手练习
- 每课末尾有「动手练习」和「验收标准」
- 按顺序学习，后一课依赖前一课的概念
- 官方文档索引：https://docs.agno.com/llms.txt

## 环境准备

### 前置知识

- Python 3.12+
- 会使用 PowerShell / 终端
- 了解什么是 API Key（OpenAI 或其他 LLM 提供商）

### 快速开始（Windows PowerShell）

```powershell
cd learn-agno\practice
uv venv --python 3.12
.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
$env:OPENAI_API_KEY="sk-你的密钥"
python sorting_hat.py
```

### 依赖说明

| 阶段 | 安装命令 |
|------|----------|
| 第1–4课 | `uv pip install -r requirements.txt` |
| 第5课 AgentOS | `uv pip install -r requirements-os.txt` |

## 官方资源

- [Build Your First Agent](https://docs.agno.com/first-agent)
- [Agent 概述](https://docs.agno.com/agents/overview)
- [AgentOS 介绍](https://docs.agno.com/agent-os/introduction)
- [AgentOS UI](https://os.agno.com)
