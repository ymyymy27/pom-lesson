> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Neo4j 语法结构参考

> 本文档系统梳理 Neo4j 的三层语法：**Neo4j Browser / cypher-shell**、**Cypher 查询语言**、**Python neo4j 驱动**。建议配合 `01-第1课Neo4j 基础 — 核心概念与安装.md` 一起阅读。

---

## 1. 整体架构：Neo4j 在应用中的位置

```
┌─────────────────────────────────────────────────────────┐
│  应用层（FastAPI / Django / 批处理脚本）                  │
│  neo4j Python Driver · Spring Data Neo4j                │
├─────────────────────────────────────────────────────────┤
│  连接协议层                                              │
│  Bolt 7687 — 二进制协议（推荐）                          │
│  HTTP 7474 — Browser UI / REST（管理用）                 │
├─────────────────────────────────────────────────────────┤
│  查询引擎层                                              │
│  Cypher — 声明式图模式匹配                               │
├─────────────────────────────────────────────────────────┤
│  存储引擎层                                              │
│  节点 (Node) · 关系 (Relationship) · 属性 (Property)     │
│  原生图索引 · 约束                                       │
├─────────────────────────────────────────────────────────┤
│  持久化 (data volume)                                    │
└─────────────────────────────────────────────────────────┘
```

**典型调用链：**

```
应用 → neo4j Driver → Bolt 7687 → Cypher 引擎 → 图存储
                                      ↓
                              Browser 7474（可视化调试）
```

---

## 2. 核心概念速查

| 概念 | Neo4j 术语 | 示例 |
|------|-----------|------|
| 实体类型 | Label（可多标签） | `:Person:Employee` |
| 连接 | Relationship Type（有方向） | `-[:WORKS_AT]->` |
| 字段 | Property | `{name: '张三', age: 30}` |
| 业务主键 | 属性 + UNIQUE 约束 | `Person.id` |
| 数据库 | Database（4.0+ 多库） | `neo4j`, `kg_dev` |

---

## 3. Cypher 语法结构

### 3.1 语句分类

| 类别 | 关键字 | 作用 |
|------|--------|------|
| **读** | `MATCH`, `OPTIONAL MATCH`, `WITH`, `RETURN` | 模式匹配与投影 |
| **写** | `CREATE`, `MERGE`, `SET`, `REMOVE`, `DELETE` | 增删改 |
| **模式** | `UNWIND`, `FOREACH` | 批量展开、迭代 |
| **Schema** | `CREATE INDEX`, `CREATE CONSTRAINT`, `DROP` | 索引与约束 |
| **管理** | `SHOW`, `CALL`, `LOAD CSV` | 元数据、过程调用、导入 |
| **分析** | `EXPLAIN`, `PROFILE` | 查询计划 |

### 3.2 模式匹配语法

```cypher
// 基本格式
(变量:Label {属性: 值})-[变量:TYPE {属性: 值}]->(变量:Label)

// 示例拆解
MATCH (p:Person {name: '张三'})-[:WORKS_AT {since: 2020}]->(c:Company)
│     │  │       │              │  │         │              │  │
│     │  │       │              │  │         │              │  └── 目标节点 Label
│     │  │       │              │  │         │              └── 关系类型 + 属性
│     │  │       │              │  │         └── 关系属性
│     │  │       │              │  └── 关系类型
│     │  │       │              └── 有向箭头
│     │  │       └── 节点属性过滤
│     │  └── 节点 Label
│     └── 节点变量名
```

### 3.3 常用读查询模板

```cypher
-- 精确匹配
MATCH (p:Person {id: $id}) RETURN p

-- 模糊匹配
MATCH (p:Person) WHERE p.name CONTAINS '张' RETURN p LIMIT 20

-- 多跳路径
MATCH (p:Person {name: $name})-[:REPORTS_TO*1..3]->(boss:Person)
RETURN boss.name

-- 聚合
MATCH (c:Company)<-[:WORKS_AT]-(p:Person)
RETURN c.name, count(p) AS headcount ORDER BY headcount DESC

-- 可选匹配（左连接语义）
MATCH (p:Person)
OPTIONAL MATCH (p)-[:WORKS_ON]->(proj:Project)
RETURN p.name, collect(proj.name) AS projects
```

### 3.4 常用写操作模板

```cypher
-- 创建
CREATE (p:Person {id: randomUUID(), name: '张三', created_at: datetime()})

-- 幂等写入（推荐生产）
MERGE (p:Person {id: $id})
SET p += $properties, p.updated_at = datetime()

-- 更新
MATCH (p:Person {id: $id}) SET p.title = $title

-- 删除关系
MATCH (p:Person {id: $id})-[r:WORKS_AT]->() DELETE r

-- 删除节点（需先删关系或用 DETACH）
MATCH (p:Person {id: $id}) DETACH DELETE p
```

### 3.5 索引与约束

```cypher
-- 唯一约束（自动建索引）
CREATE CONSTRAINT person_id IF NOT EXISTS
FOR (p:Person) REQUIRE p.id IS UNIQUE;

-- 单字段索引
CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);

-- 复合索引（Neo4j 5.13+）
CREATE INDEX person_dept IF NOT EXISTS FOR (p:Person) ON (p.name, p.status);

-- 查看
SHOW INDEXES;
SHOW CONSTRAINTS;
```

---

## 4. Browser / cypher-shell 命令

### 4.1 Neo4j Browser（http://localhost:7474）

- 连接串：`neo4j://localhost:7687`
- 默认账号：`neo4j` / 首次登录需改密（本课程 compose 预设 `changeme`）
- 左侧可拖拽可视化节点；右上角可切换表格/文本/图视图

### 4.2 cypher-shell（容器内 CLI）

```bash
# 进入 shell
docker exec -it learn-neo4j cypher-shell -u neo4j -p changeme

# 单条命令
docker exec learn-neo4j cypher-shell -u neo4j -p changeme \
  "MATCH (n) RETURN count(n) AS nodes"
```

### 4.3 常用 Browser 快捷写法

| 写法 | 含义 |
|------|------|
| `:help` | 帮助 |
| `:clear` | 清空结果 |
| `:schema` | 查看 Label、关系类型、索引 |
| `:params {id: 'p1'}` | 设置参数，后续用 `$id` |
| `:use kg_dev` | 切换 database（多库环境） |

---

## 5. Python neo4j 驱动速查

### 5.1 连接

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "changeme"),
    max_connection_lifetime=3600,
    max_connection_pool_size=50,
)
driver.verify_connectivity()
```

### 5.2 读 / 写

```python
# 读（自动读事务）
with driver.session(database="neo4j") as session:
    result = session.run(
        "MATCH (p:Person {id: $id}) RETURN p.name AS name",
        id="person_001",
    )
    record = result.single()
    print(record["name"] if record else None)

# 写（显式写事务）
def create_person(tx, person_id: str, name: str):
    tx.run(
        "MERGE (p:Person {id: $id}) SET p.name = $name, p.updated_at = datetime()",
        id=person_id, name=name,
    )

with driver.session() as session:
    session.execute_write(create_person, "person_001", "张三")
```

### 5.3 批量写入

```python
def batch_merge(tx, records: list[dict]):
    tx.run("""
        UNWIND $batch AS row
        MERGE (p:Person {id: row.id})
        SET p += row.properties
    """, batch=records)

# 每批 500–2000 条
```

### 5.4 驱动 API 对照

| 场景 | API | 说明 |
|------|-----|------|
| 单次查询 | `session.run(query, **params)` | 最常用 |
| 读事务 | `session.execute_read(fn, *args)` | 可重试 |
| 写事务 | `session.execute_write(fn, *args)` | 多步原子写 |
| 关闭 | `driver.close()` | 应用退出时 |
| 超时 | `session.run(q, timeout=30)` | 防慢查询 |

---

## 6. 与 SQL 的对照

| SQL | Cypher |
|-----|--------|
| `SELECT * FROM person WHERE id = 1` | `MATCH (p:Person {id: '1'}) RETURN p` |
| `INSERT INTO person ...` | `CREATE (p:Person {...})` |
| `UPDATE person SET ...` | `MATCH (p:Person) SET p.name = ...` |
| `DELETE FROM person` | `MATCH (p:Person) DETACH DELETE p` |
| `JOIN` 多表 | 模式 `(a)-[:REL]->(b)` 一次匹配 |
| `GROUP BY` | `RETURN ... count(x)` |
| `CREATE INDEX` | `CREATE INDEX ... FOR (n:Label) ON (n.prop)` |

**关键差异：** Cypher 用**图模式**描述关联，多跳遍历不需要多层 JOIN。

---

## 7. 常见错误与排查

| 现象 | 原因 | 处理 |
|------|------|------|
| `Unable to connect` | 容器未启动 / 端口占用 | `docker compose ps` |
| `Authentication failed` | 密码错误 | 检查 `NEO4J_AUTH` |
| `Node already exists with label X and property id` | 违反 UNIQUE 约束 | 用 MERGE 代替 CREATE |
| `Cannot delete node, still has relationships` | 未删关系 | `DETACH DELETE` |
| 查询极慢 | 无索引 / 路径过深 | 加约束、`PROFILE`、缩小 `*1..N` |

---

## 下一课

[`01-第1课Neo4j 基础 — 核心概念与安装.md`](<01-第1课Neo4j 基础 — 核心概念与安装.md>) — Neo4j 基础与第一次操作
