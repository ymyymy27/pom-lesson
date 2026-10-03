> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Graph RAG：向量检索 + 知识图谱

> 2025–2026 新技术补充课  
> 前置：stage-08 前序 RAG 课时、[`learn-vector-db/`](../03-向量检索)\
> 构建侧：如何搭建图谱见 [`learn-knowledge-graph/`](../../../../03-进阶专题/03-信息检索与知识图谱/02-知识图谱)（Schema → 抽取 → Neo4j → 流水线）

## 1. 纯向量 RAG 的局限

```
用户问：「张三的上司的部门负责什么项目？」

纯向量 RAG：
  → 检索「张三」「上司」「部门」「项目」相关 chunk
  → 可能漏掉跨文档的关系链
  → 幻觉风险高

Graph RAG：
  → 张三 ──reports_to──→ 李四 ──manages──→ 研发部 ──owns──→ ProjectX
  → 沿关系图遍历，精确聚合
```

| 场景 | 向量 RAG | Graph RAG |
|------|----------|-----------|
| 语义相似问答 | ✅ 强 | 一般 |
| 多跳关系推理 | ❌ 弱 | ✅ 强 |
| 实体精确匹配 | 一般 | ✅ 强 |
| 实现复杂度 | 低 | 中高 |
| 维护成本 | 低 | 需维护图谱 |

**2026 趋势：** 生产 RAG  increasingly 采用 **Hybrid = 向量检索 + 图谱遍历 + Rerank**。

---

## 2. Graph RAG 架构

```
文档入库
   ↓
┌──────────────┐     ┌──────────────┐
│  Chunk + Embed│     │ 实体/关系抽取  │
│  → 向量库     │     │  → 知识图谱    │
└──────┬───────┘     └──────┬───────┘
       │                    │
       └────────┬───────────┘
                ↓
           查询时 Hybrid
                ↓
    向量 Top-K + 图谱子图扩展
                ↓
           Rerank → LLM 生成
```

---

## 3. 实体关系抽取

### LLM 抽取（快速原型）

```python
EXTRACT_PROMPT = """
从以下文本中提取实体和关系，输出 JSON：
{"entities": [{"name": str, "type": str}],
 "relations": [{"source": str, "relation": str, "target": str}]}

文本：{text}
"""

def extract_graph_elements(text: str, llm) -> dict:
    response = llm.invoke(EXTRACT_PROMPT.format(text=text))
    return json.loads(response.content)
```

### 生产级方案

| 方案 | 工具 |
|------|------|
| LLM 抽取 | GPT-4 / 本地模型 + Instructor |
| NLP 管道 | spaCy NER + 规则 |
| 专用框架 | Microsoft GraphRAG、LlamaIndex KnowledgeGraph |

---

## 4. 存储选型

| 组件 | 选项 | 适用 |
|------|------|------|
| 向量库 | ChromaDB、FAISS、Milvus | 语义检索 |
| 图数据库 | Neo4j、NebulaGraph、Amazon Neptune | 关系遍历 |
| 一体化 | LlamaIndex PropertyGraph | 中小规模 |

### Neo4j 示例

```cypher
// 创建实体和关系
CREATE (p:Person {name: '张三'})
CREATE (m:Person {name: '李四'})
CREATE (d:Department {name: '研发部'})
CREATE (p)-[:REPORTS_TO]->(m)
CREATE (m)-[:MANAGES]->(d)

// 多跳查询：张三的上司管理的部门
MATCH (p:Person {name: '张三'})-[:REPORTS_TO]->(boss)-[:MANAGES]->(dept)
RETURN dept.name
```

---

## 5. Hybrid 检索实现

```python
def hybrid_rag_query(question: str, vector_db, graph_db, top_k: int = 5):
    # Step 1: 向量检索
    vector_results = vector_db.similarity_search(question, k=top_k)

    # Step 2: 从问题中识别实体，扩展图谱
    entities = extract_entities(question)
    graph_context = []
    for entity in entities:
        subgraph = graph_db.query(f"""
            MATCH (n {{name: '{entity}'}})-[r*1..2]-(m)
            RETURN n, r, m LIMIT 20
        """)
        graph_context.extend(subgraph)

    # Step 3: 合并上下文
    combined = merge_contexts(vector_results, graph_context)

    # Step 4: Rerank（可选，用 cross-encoder）
    ranked = rerank(question, combined)

    return ranked[:top_k]
```

---

## 6. Microsoft GraphRAG 思路

Microsoft GraphRAG（2024–2025）核心创新：

1. **社区检测**：对图谱做 Leiden 聚类，生成社区摘要
2. **Global Search**：跨社区聚合回答宏观问题
3. **Local Search**：从实体出发局部检索回答细节问题

适合：**大量非结构化文档 + 需要全局理解** 的场景（如企业知识库、研报分析）。

---

## 7. 何时用 Graph RAG？

```
决策树：

问题需要多跳关系推理？
  ├─ 是 → 考虑 Graph RAG 或 Hybrid
  └─ 否 → 纯向量 RAG 通常足够

实体关系是否稳定、可抽取？
  ├─ 是 → Graph RAG 收益大
  └─ 否 → 维护图谱成本高，谨慎采用

数据规模？
  ├─ < 10万 chunk → LlamaIndex PropertyGraph 够用
  └─ > 100万 → Neo4j + 向量库分离部署
```

---

## 8. AI Hub 集成建议

| AI Hub 模块 | RAG 策略 |
|-------------|----------|
| FAQ 问答 | 纯向量 RAG |
| 组织架构查询 | Graph RAG |
| 项目知识库 | Hybrid（向量 + 项目-人员-任务关系图） |

---

## 9. 动手练习

1. 用 LLM 从 3 段文本抽取实体关系，手动画图谱
2. 写一个 Cypher 查询：找出某项目的所有参与者和他们的角色
3. 对比同一问题在「纯向量」vs「Hybrid」下的回答差异
4. 设计 AI Hub 知识库的 Graph Schema（5 个 Node 类型 + 5 个 Relation 类型）

---

## 10. 自检清单

- [ ] 能解释 Graph RAG 解决的核心问题
- [ ] 能描述 Hybrid RAG 的四步流程
- [ ] 知道向量库与图数据库的分工
- [ ] 能判断何时需要 Graph RAG vs 纯向量
- [ ] 了解 Microsoft GraphRAG 的社区摘要思路

---

## 参考

- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)
- [GraphRAG 专项课（原理→算法→框架→实战）](../../../../03-进阶专题/03-信息检索与知识图谱/03-GraphRAG)
- [Neo4j GraphRAG](https://neo4j.com/labs/genai-ecosystem/)
- [LlamaIndex Knowledge Graph](https://docs.llamaindex.ai/en/stable/examples/index_structs/knowledge_graph/)
