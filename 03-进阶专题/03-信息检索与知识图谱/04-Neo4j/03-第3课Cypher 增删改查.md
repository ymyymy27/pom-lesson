> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第3课：Cypher 增删改查

> 前置：第 1–2 课、[`00-Neo4j 语法结构参考.md`](<00-Neo4j 语法结构参考.md>)\
> 环境：Neo4j Browser 或 `cypher-shell`

---

## 1. CREATE — 创建

```cypher
// 单节点
CREATE (p:Person {id: 'p1', name: '张三', created_at: datetime()})

// 节点 + 关系（一条语句）
CREATE (p:Person {id: 'p2', name: '李四'})
CREATE (c:Company {id: 'c1', name: '示例科技'})
CREATE (p)-[:WORKS_AT {since: 2024}]->(c)

// 批量（小数据）
CREATE
  (d:Department {id: 'd1', name: '研发部'}),
  (p:Person {id: 'p3', name: '王五'}),
  (p)-[:MEMBER_OF]->(d)
```

**注意：** `CREATE` 每次都会新建；生产写入优先用 `MERGE`（见 §4）。

---

## 2. MATCH + RETURN — 查询

### 2.1 基本匹配

```cypher
MATCH (p:Person {name: '张三'})
RETURN p

// 指定返回字段
MATCH (p:Person)-[:WORKS_ON]->(proj:Project)
RETURN p.name AS employee, proj.name AS project, proj.status
```

### 2.2 WHERE 过滤

```cypher
MATCH (p:Person)
WHERE p.status = 'active' AND p.title CONTAINS '工程师'
RETURN p.name, p.title
ORDER BY p.name
SKIP 0 LIMIT 20
```

| 运算符 | 示例 |
|--------|------|
| 比较 | `p.age >= 18` |
| 字符串 | `p.name STARTS WITH '张'`、`CONTAINS`、`=~ '.*经理.*'` |
| 集合 | `p.id IN ['p1', 'p2']` |
| 空值 | `p.email IS NOT NULL` |

### 2.3 关系方向

```cypher
// 有向：员工 → 项目
MATCH (p:Person)-[:WORKS_ON]->(proj:Project) RETURN p, proj

// 无方向：任意邻居
MATCH (p:Person {name: '张三'})-[r]-(neighbor)
RETURN type(r), labels(neighbor), neighbor

// 反向
MATCH (proj:Project)<-[:WORKS_ON]-(p:Person) RETURN proj.name, collect(p.name)
```

---

## 3. 聚合与排序

```cypher
// 计数
MATCH (p:Person)-[:WORKS_ON]->(proj:Project)
RETURN proj.name, count(p) AS members ORDER BY members DESC

// collect 列表
MATCH (p:Person {name: '张三'})-[:WORKS_ON]->(proj)
RETURN p.name, collect(proj.name) AS projects

// DISTINCT
MATCH (p:Person)-[:MEMBER_OF]->(d:Department)
RETURN DISTINCT d.name
```

---

## 4. MERGE — 幂等写入

```cypher
// 有则匹配，无则创建
MERGE (p:Person {id: $id})
SET p.name = $name, p.updated_at = datetime()

// MERGE 整条模式（节点 + 关系）
MERGE (p:Person {id: $pid})
MERGE (proj:Project {id: $proj_id})
MERGE (p)-[r:WORKS_ON]->(proj)
SET r.role = $role
```

**MERGE 规则：** 只匹配模式中的**完整模式**；未指定的属性不会参与匹配。

---

## 5. SET / REMOVE — 更新

```cypher
// 更新属性
MATCH (p:Person {id: 'person_001'})
SET p.title = '技术负责人', p.updated_at = datetime()

// 批量更新（map 展开）
MATCH (p:Person {id: $id})
SET p += $properties

// 添加 Label
MATCH (p:Person {id: $id}) SET p:Manager

// 删除属性
MATCH (p:Person {id: $id}) REMOVE p.temp_field
```

---

## 6. DELETE — 删除

```cypher
// 删关系
MATCH (p:Person {id: $id})-[r:WORKS_ON]->(proj:Project {id: $proj_id})
DELETE r

// 删节点（必须先无关系）
MATCH (p:Person {id: $id}) DETACH DELETE p

// 清空库（仅开发！）
MATCH (n) DETACH DELETE n
```

---

## 7. OPTIONAL MATCH — 左连接语义

```cypher
MATCH (p:Person)
OPTIONAL MATCH (p)-[:WORKS_ON]->(proj:Project)
RETURN p.name, proj.name AS project
// 无项目时 project 为 null
```

配合 `collect` 避免 null 行重复：

```cypher
MATCH (p:Person)
OPTIONAL MATCH (p)-[:WORKS_ON]->(proj:Project)
RETURN p.name, collect(proj.name) AS projects
```

---

## 8. WITH — 管道中间结果

```cypher
MATCH (p:Person)-[:WORKS_ON]->(proj:Project)
WITH proj, count(p) AS cnt
WHERE cnt >= 2
RETURN proj.name, cnt
ORDER BY cnt DESC
```

`WITH` 类似 SQL 子查询/CTE，用于分步过滤与聚合。

---

## 9. 参数化查询（必做）

Browser 中：

```cypher
:param id => 'person_001'
MATCH (p:Person {id: $id}) RETURN p
```

Python 中始终用 `$param`，**禁止**字符串拼接 Cypher（防注入）。

---

## 10. 动手练习

基于 `seed_demo_graph.py` 数据：

1. 查询「研发一部」所有成员姓名
2. 查询参与「订单系统」项目的员工及其 role
3. 用 MERGE 添加新员工并关联到已有项目
4. 统计每个 Department 的人数，按降序排列
5. 找出没有参与任何项目的 Person（OPTIONAL MATCH + WHERE proj IS NULL）

---

## 11. 自检清单

- [ ] 熟练使用 CREATE / MATCH / MERGE / SET / DELETE
- [ ] 会用 WHERE、ORDER BY、SKIP/LIMIT
- [ ] 理解 OPTIONAL MATCH 与 collect 的配合
- [ ] 所有应用查询都使用参数化

---

## 下一课

[`04-第4课索引约束与查询优化.md`](04-第4课索引约束与查询优化.md) — 索引与查询优化
