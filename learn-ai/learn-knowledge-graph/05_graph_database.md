# 第5课：图数据库工程 — Neo4j 深度实践

> 前置：第 2 课（Schema）、[`00_kg_glossary.md`](00_kg_glossary.md) Cypher 速查  
> 环境：`practice/docker-compose.yml`  
> **Neo4j 系统学习**：详见 [`learn-neo4j`](../../learn-tools/learn-neo4j/) 独立工具课（Cypher 语法、驱动、部署运维）

本课聚焦 Neo4j 在**知识图谱场景**下的建模、索引、批量导入、查询优化——图谱能否上生产的关键。

---

## 1. Neo4j 架构速览

```
┌─────────────────────────────────────────┐
│  Neo4j Browser / 应用 (Bolt 7687)      │
├─────────────────────────────────────────┤
│  Cypher 查询引擎                         │
│  · 模式匹配 · 图遍历 · 聚合              │
├─────────────────────────────────────────┤
│  存储引擎                                │
│  · 节点/关系/属性 · 原生索引              │
├─────────────────────────────────────────┤
│  持久化 (data volume)                    │
└─────────────────────────────────────────┘
```

| 概念 | Neo4j 术语 |
|------|-----------|
| 节点类型 | Label（可多标签 `:Person:Employee`） |
| 关系类型 | Relationship Type（有方向） |
| 属性 | Property（key-value） |
| 连接协议 | Bolt (`bolt://localhost:7687`) |

---

## 2. 数据建模模式

### 2.1 星型 vs 链式

```
星型（推荐查询中心实体）          链式（层级组织）
      Department                      CEO
         ↑                              ↑
    Person → Project              VP → Director → Manager
```

### 2.2 中间节点模式（Reification）

关系本身有复杂属性或需被关联时，升格为节点：

```cypher
// ❌ 关系过于复杂
(p)-[:WORKS_ON {role, start_date, end_date, allocation_pct, ...}]->(proj)

// ✅ 中间节点 Employment / Assignment
(p)-[:HAS_ASSIGNMENT]->(a:Assignment {role, start_date})-[:ON_PROJECT]->(proj)
```

### 2.3 时间有效性

```cypher
(p)-[:WORKS_AT {from: date('2020-01-01'), to: null}]->(c:Company)

// 查询「2023 年在职」
MATCH (p)-[r:WORKS_AT]->(c)
WHERE r.from <= date('2023-12-31')
  AND (r.to IS NULL OR r.to >= date('2023-01-01'))
RETURN p, c
```

---

## 3. 批量导入

### 3.1 UNWIND 批量 MERGE（中等规模）

```cypher
UNWIND $batch AS row
MERGE (p:Person {id: row.id})
SET p += row.properties, p.updated_at = datetime()
```

Python 侧分批（每批 500–2000）：

```python
def batch_merge_nodes(session, label: str, records: list[dict], batch_size=1000):
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        session.run(f"""
            UNWIND $batch AS row
            MERGE (n:{label} {{id: row.id}})
            SET n += row.properties
        """, batch=batch)
```

### 3.2 neo4j-admin import（大规模初始 load）

适合 **百万级+** 首次全量导入（需停库离线）：

```bash
# CSV 格式：nodes.csv, relationships.csv
neo4j-admin database import full \
  --nodes=Person=import/nodes_person.csv \
  --relationships=import/rels_works_at.csv \
  --overwrite-destination=true
```

### 3.3 导入策略选择

| 数据量 | 方式 | 说明 |
|--------|------|------|
| < 10 万节点 | UNWIND + MERGE | 在线、幂等 |
| 10 万 – 500 万 | 批量 LOAD CSV / UNWIND | 分批 + 索引先行 |
| > 500 万初始 | neo4j-admin import | 离线高速 |
| 增量更新 | MERGE + 时间戳过滤 | 第 6 课流水线 |

---

## 4. 索引与约束（性能基础）

```cypher
// 必做：业务主键唯一约束
CREATE CONSTRAINT person_id IF NOT EXISTS
FOR (p:Person) REQUIRE p.id IS UNIQUE;

// 高频过滤字段
CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX project_status IF NOT EXISTS FOR (p:Project) ON (p.status);

// 复合索引（Neo4j 5.13+）
CREATE INDEX person_dept IF NOT EXISTS
FOR (p:Person) ON (p.name, p.status);
```

### 查询计划分析

```cypher
EXPLAIN
MATCH (p:Person {name: '张三'})-[:WORKS_ON]->(proj)
RETURN proj.name;

PROFILE  // 实际执行统计
MATCH (p:Person {name: '张三'})-[:WORKS_ON*1..3]->(x)
RETURN x LIMIT 100;
```

**优化原则：**

- 可变长度路径 `*1..N` 的 N 不宜过大（生产建议 ≤ 4）
- 始终 `LIMIT` 防止爆炸
- 高基数字段（id、email）走索引，低基数（gender）慎用

---

## 5. 常用工程查询模式

### 5.1 一度邻居

```cypher
MATCH (p:Person {id: $id})-[r]-(neighbor)
RETURN type(r) AS rel, labels(neighbor) AS labels, neighbor
LIMIT 50
```

### 5.2 最短路径

```cypher
MATCH (a:Person {name: '张三'}), (b:Person {name: '王五'})
MATCH path = shortestPath((a)-[:REPORTS_TO*]-(b))
RETURN path
```

### 5.3 子图导出（供 RAG 上下文）

```cypher
MATCH (p:Person {name: $name})-[r*1..2]-(m)
RETURN p, r, m
LIMIT 100
```

---

## 6. Python 驱动最佳实践

```python
from neo4j import GraphDatabase
from contextlib import contextmanager

class GraphRepo:
    def __init__(self, uri: str, user: str, password: str):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    @contextmanager
    def session(self, database: str = "neo4j"):
        with self._driver.session(database=database) as session:
            yield session

    def get_person_projects(self, person_id: str) -> list[str]:
        query = """
        MATCH (p:Person {id: $id})-[:WORKS_ON]->(proj:Project)
        RETURN proj.name AS name ORDER BY name
        """
        with self.session() as s:
            return [r["name"] for r in s.run(query, id=person_id)]
```

| 实践 | 说明 |
|------|------|
| 参数化查询 | 防 Cypher 注入 |
| 连接池 | Driver 单例，勿每请求 new |
| 事务 | 多步写操作用 `execute_write` |
| 超时 | `session.run(query, timeout=30)` |

---

## 7. 多数据库与环境隔离

Neo4j 4.0+ 支持单实例多 database：

```
neo4j (system) — 管理库
├── kg_dev      — 开发
├── kg_staging  — 预发
└── kg_prod     — 生产
```

```python
with driver.session(database="kg_dev") as session:
    session.run("MATCH (n) RETURN count(n)")
```

与 Redis 逻辑库隔离思路相同（参见 `learn-redis/07_logical_databases_and_isolation.md`）：**环境优先分实例/分库，而非仅靠 Label 前缀。**

---

## 8. 动手练习

1. 运行 `python practice/seed_demo_graph.py`，在 Browser 中可视化全图
2. 为 `Person.email` 添加唯一约束并测试冲突
3. 用 `PROFILE` 对比「有索引 vs 无索引」的查询耗时
4. 编写查询：找出参与项目数最多的 5 名员工

---

## 9. 自检清单

- [ ] 理解 Label、Relation、Property 在 Neo4j 中的对应
- [ ] 会选择 UNWIND MERGE vs admin import
- [ ] 能创建约束和索引并用 EXPLAIN/PROFILE 分析
- [ ] 掌握可变长度路径的风险与 LIMIT 用法
- [ ] 会用 Python 驱动做参数化查询

---

## 下一课

[`06_construction_pipeline.md`](06_construction_pipeline.md) — 构建流水线自动化
