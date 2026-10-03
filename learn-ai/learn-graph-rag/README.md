# GraphRAG 专项课：从原理到实战

> 定位：`learn-ai` 体系下的 GraphRAG 深度课程（独立于 stage-08 概览课）。
> 前置：完成 `stage-07-vector-db/` 与 `stage-08-rag/`（或具备 RAG 基础）；
> 建图工程细节可交叉参考 [`learn-knowledge-graph/`](../learn-knowledge-graph/)。

## 这门课讲什么

普通 RAG 用"向量相似度"检索文本块，遇到**多跳推理、全局总结、实体关系查询**就会失灵。
GraphRAG 把文档先变成"实体—关系"图，再用图算法（遍历、社区检测、PageRank）做检索，
让 LLM 回答真正"有关系"的问题。

本课程覆盖：

- 向量 RAG 的边界与 GraphRAG 的适用场景
- 知识图谱概念、Schema、实体关系抽取
- 图存储与 Cypher 检索
- Microsoft GraphRAG 算法详解（Leiden 社区检测、Local/Global/DRIFT Search）
- LightRAG、HippoRAG、KAG、nano-graphrag 等框架对比
- GraphRAG 评估与生产实践
- 本地可跑的实战：NetworkX + Ollama 实现 mini GraphRAG

## 课程目录

| 课时 | 主题 | 文件 |
|------|------|------|
| 00 | 课程总览与学习路线 | `00-课程总览.md` |
| 01 | 从向量 RAG 到 GraphRAG | `01-从向量RAG到GraphRAG.md` |
| 02 | 知识图谱核心概念 | `02-知识图谱核心概念.md` |
| 03 | 实体与关系抽取 | `03-实体与关系抽取.md` |
| 04 | 图存储与检索基础 | `04-图存储与检索基础.md` |
| 05 | Microsoft GraphRAG 算法详解 | `05-Microsoft-GraphRAG算法详解.md` |
| 06 | 检索与生成策略 | `06-检索与生成策略.md` |
| 07 | 主流框架与变体 | `07-主流框架与变体.md` |
| 08 | 评估体系 | `08-评估体系.md` |
| 09 | 生产实践 | `09-生产实践.md` |
| 10 | 实战项目 | `10-实战项目.md` |

## 本机环境

- Ollama：`qwen2.5:7b`（对话/抽取）+ `qwen3-embedding:4b`（向量，2560 维）
- Python：`networkx` 已安装（图算法与原型）；Neo4j 可选（见第 4 课）
- 所有实战代码都在 [`practice/`](practice/)，不依赖外网，可直接运行

## 建议节奏

```
第 1 天：00 + 01 + 02（理解为什么、图谱是什么）
第 2 天：03 + 04 + 跑 practice/01_build_kg.py
第 3 天：05 + 06 + 跑 practice/02、03
第 4 天：07 + 08（框架对比与评估）
第 5 天：09 + 10（生产化与完整项目）
```

每课末尾都有"练习与自测"，先自己写答案，再对照课程内容。

