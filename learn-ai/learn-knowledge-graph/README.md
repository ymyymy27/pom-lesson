# 知识图谱工程化 从零到生产

独立专课，与 [`stage-08-rag/06-graph-rag.md`](../stage-08-rag/06-graph-rag.md) 互补：

- **本课程**：如何**构建、治理、运维**知识图谱（Schema → 抽取 → 入库 → 质量 → API → 部署）
- **Graph RAG 补充课**：如何在 RAG 中**使用**已有图谱做 Hybrid 检索

Markdown 文档 + Docker 动手练习，默认技术栈：**Python 3.11+ · Neo4j · LLM 抽取**。

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 参考 | `00_kg_glossary.md` | 术语表、RDF vs 属性图、技术选型速查 |
| 第1课 | `01_kg_fundamentals.md` | 知识图谱是什么、应用场景、工程全景图 |
| 第2课 | `02_schema_and_ontology.md` | Schema 设计、本体建模、版本管理 |
| 第3课 | `03_data_acquisition.md` | 数据源、结构化/半结构化/非结构化接入 |
| 第4课 | `04_entity_relation_extraction.md` | NER、关系抽取、LLM 抽取、实体对齐 |
| 第5课 | `05_graph_database.md` | Neo4j 图谱工程（建模、索引、批量导入；系统学习见 [`learn-neo4j`](../../learn-tools/learn-neo4j/)） |
| 第6课 | `06_construction_pipeline.md` | ETL 流水线、增量更新、任务调度 |
| 第7课 | `07_quality_and_governance.md` | 质量指标、冲突消解、权限与审计 |
| 第8课 | `08_query_and_api.md` | 图查询封装、GraphQL/REST API、可视化 |
| 第9课 | `09_integration_rag_llm.md` | 与向量库、RAG、Agent 集成 |
| 第10课 | `10_deployment_and_operations.md` | 部署架构、监控、备份、团队协作 |
| 第11课 | `11_agno_integration.md` | Agno 工程化接入、Hybrid 优化、AgentOS 部署 |

## 学习方式

- Markdown 文档 + 终端 / Python 动手练习
- 建议前置：Python 基础、[`learn-docker`](../../learn-tools/learn-docker/) 容器基础
- 与 AI 路线交叉：完成 stage-04（Prompt）和 stage-07（向量库）后学第 4、9 课更顺畅
- 每课末尾有**自检清单**；第 6、8、11 课有 `practice/` 可运行脚本

## 环境准备

```bash
cd practice
docker compose up -d
# 浏览器打开 http://localhost:7474  Neo4j Browser（默认 neo4j / changeme）
pip install -r requirements.txt
python seed_demo_graph.py   # 写入演示图谱
```

- **Python**: 3.11+
- **图数据库**: Neo4j 5.x（Docker Compose 一键启动）
- **可选**: OpenAI / 本地 LLM API Key（第 4 课抽取练习；第 11 课 Agno 接入见 `requirements-agno.txt`）

## 学习顺序建议

```
learn-docker (容器)  →  learn-knowledge-graph (本课程)
                              │
                              ├─ stage-08 06-graph-rag.md（消费侧：Hybrid RAG）
                              ├─ stage-09 Agent（图谱作为 Agent 工具）
                              ├─ learn-agno（Agno 框架 + 第 11 课图谱接入）
                              └─ learn-se 系统设计（大规模图谱架构案例）
```

## 与 Graph RAG 补充课的分工

| 主题 | 权威来源 | 说明 |
|------|----------|------|
| Schema 设计、本体建模 | 本课第 2 课 | Graph RAG 课假设 Schema 已存在 |
| 实体关系抽取流水线 | 本课第 4、6 课 | Graph RAG 仅概览抽取 |
| Neo4j / Cypher 工程实践 | 本课第 5、8 课 | Graph RAG 有基础 Cypher 示例 |
| Hybrid 检索与 Rerank | stage-08 Graph RAG | 本课第 9 课做交叉引用 |
| 生产部署与运维 | 本课第 10 课 | — |
| Agno 框架接入与 AgentOS 部署 | 本课第 11 课 + learn-agno | 第 9 课 LangChain 示例为概念对照 |
