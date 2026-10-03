> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 10 课：实战项目——公司知识库 GraphRAG

## 1. 项目目标

基于前面 9 课，用本地 Ollama + NetworkX 实现一个 mini GraphRAG：

1. 从公司制度/组织文档抽取实体关系，构建知识图谱
2. 对比"纯向量 RAG"与"图检索"在多跳问题上的差异
3. 实现社区检测 + 社区摘要 + Global/Local 检索（GraphRAG 思想）
4. 输出一个可回答多跳与全局问题的问答系统

## 2. 数据

`practice/data/星辰科技内部资料（虚构样例）.md`：一份虚构公司"星辰科技"的资料，
包含组织架构、项目、技术栈、制度等，故意埋了多跳关系链。

## 3. 项目结构

```
practice/
├── data/
│   └── sample_docs.md        # 原始文档
├── 01_build_kg.py            # 抽取 + 建图（NetworkX）
├── 02_retrieval_compare.py   # 向量 vs 图 vs 混合 对比
├── 03_mini_graphrag.py       # 社区检测 + 摘要 + Global/Local
├── 04_text2cypher.py         # Text2Cypher 演示（可选 Neo4j）
└── requirements.txt
```

## 4. 分步实施

### Step 1：建图（01_build_kg.py）

- 读取文档，分块
- LLM 抽取三元组（带 Schema 约束），Ollama 不可用时用规则兜底
- 实体归一化、去重、合并描述
- 生成 `kg.json`，打印图统计与示例路径

### Step 2：对比实验（02_retrieval_compare.py）

同一批多跳问题：

- 纯向量：Embedding 检索 Top-3 文本块
- 纯图：实体链接 + k 跳子图
- 混合：两路融合

观察：图检索是否找全路径，向量是否漏链。

### Step 3：mini GraphRAG（03_mini_graphrag.py）

- 社区检测（Louvain/贪心模块度，NetworkX 内置）
- LLM 生成社区摘要（可用模板兜底）
- Global Search：社区摘要向量初筛 → Map-Reduce 回答
- Local Search：实体 → k 跳子图 → 回答

### Step 4：Text2Cypher（04_text2cypher.py）

- 给定 Schema，让 LLM 生成 Cypher
- 已安装 Neo4j 驱动且配置环境变量时执行，否则只打印

## 5. 验收标准

- [ ] 能回答"张三的上级管理的部门负责什么项目？"并给出路径
- [ ] 能回答"公司主要用哪些技术？"（全局问题）
- [ ] 对比实验里能看出向量 RAG 的局限
- [ ] 每个回答能溯源到文档
- [ ] 文档没覆盖的问题会拒答

## 6. 扩展方向

1. **换真图数据库**：把 NetworkX 换成 Neo4j，见 `learn-knowledge-graph/practice/docker-compose.yml`
2. **换框架**：用 nano-graphrag / LightRAG 重跑同一数据，对比效果与成本
3. **加评估**：按第 8 课设计 20 题评测集，量化对比
4. **Agentic**：用 LangGraph 做"计划-检索-验证"循环
5. **可视化**：用 pyvis / Gephi 导出图，观察社区结构

## 7. 最终自测

学完本课程后，你应该能独立回答：

1. 什么时候该用 GraphRAG，什么时候不该？
2. Schema 怎么设计？抽取质量怎么保证？
3. Microsoft GraphRAG 的索引与检索原理是什么？
4. LightRAG / HippoRAG / KAG 分别解决什么问题？
5. 怎么评估一个 GraphRAG 系统？

如果这 5 个问题都能讲清楚，这门课就完成了。

## 练习

1. 运行全部 4 个脚本，记录每个脚本的输出。
2. 修改 Schema 或数据，观察检索结果变化。
3. 写一篇 500 字的项目复盘：做了什么、踩了什么坑、效果如何。
