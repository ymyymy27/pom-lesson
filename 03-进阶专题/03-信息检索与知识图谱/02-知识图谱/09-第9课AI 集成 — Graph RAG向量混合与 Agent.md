> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第9课：AI 集成 — Graph RAG、向量混合与 Agent

> 前置：第 5、8 课 · [`stage-08-rag/06-graph-rag.md`](<../../../02-方向选修/02-AI应用/参考资料/04-RAG/06-Graph RAG向量检索 + 知识图谱.md>)\
> 本课侧重**已有图谱**如何接入 AI；Graph RAG 补充课侧重检索架构

---

## 1. 集成全景

```
                    ┌──────────────┐
                    │   用户问题    │
                    └──────┬───────┘
                           ↓
              ┌────────────────────────┐
              │     Query Router        │
              │  关系推理 vs 语义相似    │
              └─────────┬──────────────┘
                        ↓
         ┌──────────────┴──────────────┐
         ↓                             ↓
┌─────────────────┐          ┌─────────────────┐
│  向量库检索       │          │  图谱子图遍历     │
│  ChromaDB/Milvus │          │  Neo4j Cypher    │
└────────┬────────┘          └────────┬────────┘
         └──────────────┬──────────────┘
                        ↓
                 Context 合并 + Rerank
                        ↓
                    LLM 生成
```

---

## 2. 何时走图谱 vs 向量？

| 问题类型 | 路由 | 示例 |
|----------|------|------|
| 语义相似 | 向量 | 「介绍敏捷开发方法」 |
| 单跳事实 | 图谱 | 「张三的邮箱是什么？」 |
| 多跳关系 | 图谱 | 「张三上司管理的部门有哪些项目？」 |
| 混合 | Hybrid | 「订单系统有哪些后端负责人及其汇报链？」 |

```python
RELATION_KEYWORDS = ["的上司", "的部门", "负责", "汇报", "参与", "归属"]

def route_query(question: str) -> str:
    if any(kw in question for kw in RELATION_KEYWORDS):
        return "graph"
    return "hybrid"  # 默认混合更稳
```

---

## 3. Hybrid RAG 实现

```python
def hybrid_retrieve(question: str, vector_store, graph_repo, top_k: int = 5) -> list[str]:
    contexts = []

    # 1. 向量检索文档 chunk
    docs = vector_store.similarity_search(question, k=top_k)
    contexts.extend(d.page_content for d in docs)

    # 2. 实体识别 → 图谱扩展
    entities = extract_entities_from_question(question)  # LLM 或 NER
    for ent in entities:
        hit = graph_repo.search_people(ent, limit=1)
        if hit:
            subgraph = graph_repo.get_subgraph(hit[0]["id"], depth=2)
            contexts.append(format_subgraph_text(subgraph))

    # 3. 去重 + Rerank（可选 cross-encoder）
    return rerank_and_trim(question, contexts, max_tokens=3000)


def format_subgraph_text(subgraph: dict) -> str:
    """将子图转为 LLM 可读文本"""
    lines = ["【知识图谱事实】"]
    for node in subgraph.get("nodes", []):
        lines.append(f"- {node.get('label', 'Entity')}: {node.get('name', node.get('id'))}")
    for edge in subgraph.get("edges", []):
        lines.append(f"- ({edge['from_name']}) -[{edge['type']}]-> ({edge['to_name']})")
    return "\n".join(lines)
```

详细架构见 [`stage-08-rag/06-graph-rag.md`](<../../../02-方向选修/02-AI应用/参考资料/04-RAG/06-Graph RAG向量检索 + 知识图谱.md>)。

---

## 4. 向量 + 图谱双写索引

文档入库时**同时**更新两个存储：

```
文档 chunk
   ├─ embed → 向量库 (metadata: doc_id, chunk_id)
   └─ 抽取实体关系 → Neo4j
         └─ Document -MENTIONS→ Entity
```

```cypher
// 文档与实体关联，支持溯源
MERGE (d:Document {id: $doc_id})
MERGE (p:Person {id: $person_id})
MERGE (d)-[:MENTIONS {chunk_id: $chunk_id}]->(p)
```

检索时可从向量 hit 的 `doc_id` 反查图谱扩展。

---

## 5. Graph 作为 Agent 工具

```python
from langchain.tools import tool

@tool
def query_org_graph(question: str) -> str:
    """查询组织架构知识图谱。适用于人员、部门、项目关系问题。"""
    entities = extract_entities_from_question(question)
    if not entities:
        return "未能识别实体，请提供更具体的人名或项目名。"
    results = []
    for name in entities:
        people = graph_repo.search_people(name, limit=3)
        for p in people:
            data = graph_repo.get_person_with_projects(p["id"])
            results.append(json.dumps(data, ensure_ascii=False))
    return "\n".join(results) if results else "未找到匹配实体。"

# Agent 工具列表
tools = [query_org_graph, search_documents, calculator]
```

**Agent 设计要点：**

- 工具描述清晰（何时调用图谱）
- 返回结构化 JSON 或简洁文本
- 限制子图大小，防 context 爆炸

---

## 6. Microsoft GraphRAG 思路（宏观问答）

适合**大量文档 + 全局理解**（研报、制度库）：

1. 构建实体关系图
2. **社区检测**（Leiden）聚类
3. 每个社区生成摘要
4. Global Search：跨社区聚合回答宏观问题
5. Local Search：从实体出发局部检索

```
「公司有哪些主要业务线及其负责人？」→ Global Search
「张三在订单系统的具体职责？」      → Local Search
```

参考：[Microsoft GraphRAG](https://github.com/microsoft/graphrag)

---

## 7. 评估：图谱增强是否有效？

| 指标 | 方法 |
|------|------|
| 答案准确率 | 黄金 QA 集，对比纯向量 vs Hybrid |
| 关系召回 | 多跳问题子图是否包含必要路径 |
| 幻觉率 | 答案是否可在图谱路径中验证 |
| 延迟 | P95 检索 + 生成耗时 |

```python
eval_cases = [
    {
        "question": "张三参与的项目负责人是谁？",
        "expected_entities": ["张三", "订单系统", "李四"],
        "requires_hops": 2,
    },
]
```

---

## 8. 集成检查清单

```
□ 向量库与 Neo4j  entity id 对齐策略
□ Document -MENTIONS-> Entity 溯源链
□ Hybrid 路由规则或 LLM Router
□ 子图深度 / 节点数上限
□ Graph API 只读账号 for Agent
□ RAG Eval 黄金集含多跳问题
```

---

## 9. 动手练习

1. 阅读 [`stage-08-rag/06-graph-rag.md`](<../../../02-方向选修/02-AI应用/参考资料/04-RAG/06-Graph RAG向量检索 + 知识图谱.md>) 并完成其练习 1–3
2. 实现 `format_subgraph_text()` 将 demo 图谱转为自然语言
3. 设计 Agent 的 `query_org_graph` 工具描述（让 LLM 知道何时调用）
4. 写 5 条 Hybrid 比纯向量更有优势的 eval 问题

---

## 10. 自检清单

- [ ] 能描述 Hybrid RAG 的数据流
- [ ] 知道 Query Router 的基本策略
- [ ] 理解 Document-MENTIONS-Entity 溯源设计
- [ ] 会将 Graph API 封装为 Agent 工具
- [ ] 了解 GraphRAG Global/Local Search 分工

---

## 下一课

[`10-第10课生产部署 — 架构监控与团队协作.md`](<10-第10课生产部署 — 架构监控与团队协作.md>) — 生产部署与运维

**延伸：** 若使用 Agno 框架工程化接入图谱，见 [`11-第11课Agno 工程化接入 — 图谱工具Hybrid RAG 与生产部署.md`](<11-第11课Agno 工程化接入 — 图谱工具Hybrid RAG 与生产部署.md>)。
