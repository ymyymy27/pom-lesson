# Neo4j 图数据库 从零开始学习教程

独立工具课，与 [`learn-redis`](../learn-redis/) 并列。Markdown 文档 + Docker 动手练习，不依赖全栈课程进度。

与 [`learn-knowledge-graph`](../../learn-ai/learn-knowledge-graph/) 的分工：

- **本课程**：Neo4j **本身**——建模、Cypher、驱动、索引、部署与运维
- **知识图谱课**：Schema → 抽取 → 入库流水线 → Graph RAG 集成（Neo4j 作为存储层之一）

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 参考 | `00_neo4j_syntax.md` | Cypher 语法结构参考（Browser / Bolt / neo4j Python） |
| 第1课 | `01_neo4j_basics.md` | Neo4j 是什么、安装、核心概念（节点/关系/属性图） |
| 第2课 | `02_data_modeling.md` | 建模模式、Label 设计、中间节点、时间有效性 |
| 第3课 | `03_cypher_crud.md` | CREATE / MATCH / SET / DELETE、模式匹配、聚合 |
| 第4课 | `04_indexes_and_performance.md` | 约束、索引、EXPLAIN/PROFILE、查询优化 |
| 第5课 | `05_python_neo4j.md` | neo4j 驱动、连接池、事务、Repository 模式 |
| 第6课 | `06_advanced_cypher.md` | 可变长度路径、APOC、图算法入门、批量导入 |
| 第7课 | `07_practical_web_app.md` | 实战：FastAPI + Neo4j（组织图谱 API） |
| 第8课 | `08_logical_databases_and_isolation.md` | **多 database、环境隔离、命名规范** |
| 第9课 | `09_deployment_and_environments.md` | **Docker / Aura 云、配置、安全、备份概览** |
| 第10课 | `10_production_operations.md` | **生产运维、监控、扩容、故障处理** |

## 学习方式

- Markdown 文档 + Neo4j Browser / Python 动手练习
- 需要先完成 [`learn-docker`](../learn-docker/) 第 1–3 课（用 Docker 运行 Neo4j）
- 每课末尾有**自检清单**；第 5、7 课有 `practice/` 可运行脚本
- 按顺序学习；第 1–7 课打基础与实战，**第 8–10 课为部署与协作必修**

## 环境准备

```bash
cd practice
docker compose up -d
# 浏览器打开 http://localhost:7474  Neo4j Browser（默认 neo4j / changeme）
pip install -r requirements.txt
python seed_demo_graph.py   # 写入演示图谱
```

- **Python**: 3.11+
- **图数据库**: Neo4j 5.x Community（Docker Compose 一键启动，含 APOC 插件）
- **依赖**: `pip install neo4j fastapi uvicorn`

## 学习顺序建议

```
learn-docker (容器基础)  →  learn-neo4j (本课程)  →  按需选学
                              │                      ├─ learn-knowledge-graph（图谱工程化）
                              │                      ├─ stage-08 Graph RAG（消费侧）
                              │                      └─ learn-se（系统设计中的图数据库案例）
```

## 与知识图谱课程的关系

| 主题 | 权威来源（本课） | 知识图谱课 |
|------|------------------|------------|
| Cypher 语法与查询优化 | `learn-neo4j` | 第 5 课概览 + 交叉引用 |
| 数据建模与索引 | `learn-neo4j` 第 2、4 课 | 第 2 课 Schema 设计 |
| Python 驱动与 API 封装 | `learn-neo4j` 第 5、7 课 | 第 8 课 Graph API |
| 实体关系抽取流水线 | — | 第 4、6 课 |
| Graph RAG / Hybrid 检索 | stage-08 | 第 9 课 |
