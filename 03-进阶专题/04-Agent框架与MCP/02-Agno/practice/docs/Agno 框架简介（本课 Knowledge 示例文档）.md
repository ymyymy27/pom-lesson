> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Agno 框架简介（本课 Knowledge 示例文档）

## 什么是 Agno

Agno 是一个 Python 智能体开发框架，用于构建 Agent、Team、Workflow，并通过 AgentOS 发布为 API 服务。

## 核心组件

- **Agent**：单智能体，包含 model、instructions、tools
- **Team**：多智能体协作，由协调者分配任务
- **Workflow**：确定性流程，支持 Step、Parallel、Loop 等
- **AgentOS**：基于 FastAPI 的运行时，提供 Session、Tracing、REST API

## 典型用途

1. 文件整理与分析（Workspace 工具）
2. 文档问答（Knowledge RAG）
3. 多角色研究写作（Team）
4. 固定 pipeline（Workflow）
5. 生产 API 服务（AgentOS + os.agno.com UI）

## 模型配置

模型使用 `provider:model_id` 格式，例如 `openai:gpt-4o`。

## 官方文档

- 入门：https://docs.agno.com/first-agent
- 索引：https://docs.agno.com/llms.txt
