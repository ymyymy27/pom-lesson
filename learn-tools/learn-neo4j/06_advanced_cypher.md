# 第6课：进阶 Cypher — 路径、APOC 与批量导入

> 前置：第 3–5 课  
> 环境：Docker Compose 已启用 APOC 插件

---

## 1. 路径查询

### 1.1 最短路径

```cypher
MATCH (a:Person {name: '张三'}), (b:Person {name: '王五'})
MATCH path = shortestPath((a)-[:REPORTS_TO*]-(b))
RETURN path, length(path) AS hops
```

### 1.2 所有简单路径（慎用）

```cypher
MATCH path = (a:Person {name: '张三'})-[:REPORTS_TO*1..5]->(b:Person {name: '李四'})
RETURN path LIMIT 10
```

### 1.3 子图导出（供 API / RAG）

```cypher
MATCH (p:Person {id: $id})-[r*1..2]-(m)
RETURN p, r, m LIMIT 100
```

---

## 2. 列表与 UNWIND

```cypher
UNWIND ['张三', '李四', '王五'] AS name
MATCH (p:Person {name: name})
RETURN p.name, p.title

// 从参数批量 MERGE
UNWIND $batch AS row
MERGE (p:Person {id: row.id})
SET p += row.properties
```

---

## 3. LOAD CSV（中等规模导入）

```cypher
LOAD CSV WITH HEADERS FROM 'file:///import/persons.csv' AS row
MERGE (p:Person {id: row.id})
SET p.name = row.name, p.email = row.email
```

CSV 文件需放到 Neo4j 的 `import` 目录（Docker 可挂载 volume）。

---

## 4. neo4j-admin import（大规模初始 load）

适合 **百万级+** 首次全量、可停库离线：

```bash
# nodes.csv: id:ID(Person), name, email
# rels.csv: :START_ID(Person), :END_ID(Project), role
neo4j-admin database import full \
  --nodes=Person=import/nodes_person.csv \
  --relationships=WORKS_ON=import/rels_works_on.csv \
  --overwrite-destination=true
```

| 数据量 | 方式 |
|--------|------|
| < 10 万节点 | UNWIND + MERGE（在线） |
| 10 万 – 500 万 | LOAD CSV / 分批 UNWIND |
| > 500 万初始 | neo4j-admin import（离线） |
| 增量 | MERGE + 时间戳（见知识图谱第 6 课） |

---

## 5. APOC 常用过程

本课程 compose 已安装 APOC：

```cypher
// 批量赋值
MATCH (p:Person) WHERE p.status IS NULL
CALL apoc.create.setProperty(p, 'status', 'active') YIELD node
RETURN count(node)

// 导出 JSON 子图
MATCH (p:Person {id: $id})-[r*1..2]-(m)
WITH p, collect(DISTINCT m) AS nodes, collect(DISTINCT r) AS rels
RETURN apoc.export.json.data(nodes, rels, null, {stream: true})

// 周期性清理（示例）
CALL apoc.periodic.iterate(
  "MATCH (p:Person) WHERE p.status = 'deleted' RETURN p",
  "DETACH DELETE p",
  {batchSize: 1000}
)
```

更多：`CALL apoc.help('export')`

---

## 6. 图算法入门（GDS 插件）

Community 版可了解概念；**GDS 库**需单独安装（Enterprise / 独立插件）。

常见算法：

| 算法 | 用途 |
|------|------|
| PageRank | 影响力排名 |
| Louvain | 社区发现 |
| Shortest Path | 路径（也可用 Cypher） |
| Node Similarity | 相似实体 |

```cypher
// GDS 典型流程（需 gds 插件）
CALL gds.graph.project('myGraph', 'Person', 'REPORTS_TO')
CALL gds.pageRank.stream('myGraph') YIELD nodeId, score
```

本课程以 Cypher + APOC 为主；大规模分析见 Neo4j 官方 GDS 文档。

---

## 7. 工程查询模式速查

```cypher
-- 一度邻居
MATCH (p:Person {id: $id})-[r]-(n) RETURN type(r), n LIMIT 50

-- 共同邻居
MATCH (a:Person {id: $id1})-[:WORKS_ON]->(proj)<-[:WORKS_ON]-(b:Person {id: $id2})
RETURN proj.name

-- 推荐：同事还参与的项目
MATCH (me:Person {id: $id})-[:MEMBER_OF]->(d)<-[:MEMBER_OF]-(colleague)
MATCH (colleague)-[:WORKS_ON]->(proj)
WHERE NOT (me)-[:WORKS_ON]->(proj)
RETURN DISTINCT proj.name LIMIT 10
```

---

## 8. 动手练习

1. 用 `shortestPath` 查找张三到王五的汇报链（若无直接链，换 REPORTS_TO 方向）
2. 编写 UNWIND 批量 MERGE 3 个新 Project
3. 用 APOC `apoc.periodic.iterate` 批量给无 `status` 的 Person 设默认值（若有）
4. 导出某 Person 二度邻居子图（Browser 可视化）

---

## 9. 自检清单

- [ ] 会写 shortestPath 与有限深度路径
- [ ] 会选择 UNWIND MERGE vs admin import
- [ ] 了解 APOC 在批量运维中的作用
- [ ] 知道 GDS 与 Cypher 遍历的适用边界

---

## 下一课

[`07_practical_web_app.md`](07_practical_web_app.md) — FastAPI 实战
