# 第5课：Python neo4j 驱动

> 前置：第 3–4 课  
> 代码：`practice/graph_repo.py`

---

## 1. 安装与连接

```bash
pip install neo4j
```

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "changeme"),
    max_connection_lifetime=3600,
    max_connection_pool_size=50,
    connection_acquisition_timeout=30,
)
driver.verify_connectivity()
```

| 参数 | 说明 |
|------|------|
| `max_connection_pool_size` | 连接池上限 |
| `max_connection_lifetime` | 连接最大存活秒数 |
| `connection_acquisition_timeout` | 等待空闲连接超时 |

**原则：** 应用内 **Driver 单例**，每个请求用 `session`，不要每请求 new Driver。

---

## 2. Session 与事务

```python
# 简单读
with driver.session(database="neo4j") as session:
    result = session.run(
        "MATCH (p:Person {id: $id}) RETURN p.name AS name",
        id="person_001",
    )
    record = result.single()
    name = record["name"] if record else None

# 写事务（多步原子）
def create_person_with_dept(tx, person: dict, dept_id: str):
    tx.run("""
        MERGE (p:Person {id: $id})
        SET p += $props, p.updated_at = datetime()
        WITH p
        MATCH (d:Department {id: $dept_id})
        MERGE (p)-[:MEMBER_OF]->(d)
    """, id=person["id"], props=person, dept_id=dept_id)

with driver.session() as session:
    session.execute_write(create_person_with_dept, person_data, "dept_d01")
```

| API | 用途 |
|-----|------|
| `session.run()` | 单条 Cypher，自动事务 |
| `session.execute_read(fn)` | 读事务，可重试 |
| `session.execute_write(fn)` | 写事务，失败回滚 |
| `result.single()` | 取一条 |
| `result.data()` | 转 list[dict] |

---

## 3. Repository 模式

`practice/graph_repo.py` 封装常用操作：

```python
class GraphRepo:
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._database = database

    def close(self):
        self._driver.close()

    def _session(self):
        return self._driver.session(database=self._database)

    def get_person(self, person_id: str) -> dict | None:
        with self._session() as session:
            rec = session.run(
                "MATCH (p:Person {id: $id}) RETURN p",
                id=person_id,
            ).single()
            return dict(rec["p"]) if rec else None

    def list_department_members(self, dept_id: str) -> list[str]:
        query = """
        MATCH (d:Department {id: $dept_id})<-[:MEMBER_OF]-(p:Person)
        RETURN p.name AS name ORDER BY name
        """
        with self._session() as session:
            return [r["name"] for r in session.run(query, dept_id=dept_id)]
```

---

## 4. 批量写入

```python
def batch_merge_persons(tx, records: list[dict]):
    tx.run("""
        UNWIND $batch AS row
        MERGE (p:Person {id: row.id})
        SET p += row.properties, p.updated_at = datetime()
    """, batch=records)

BATCH_SIZE = 1000
for i in range(0, len(all_records), BATCH_SIZE):
    batch = all_records[i : i + BATCH_SIZE]
    with driver.session() as session:
        session.execute_write(batch_merge_persons, batch)
```

每批 500–2000 条；过大单事务占内存，过小网络开销高。

---

## 5. 错误处理

```python
from neo4j.exceptions import ServiceUnavailable, TransientError, ClientError

try:
    with driver.session() as session:
        session.run("MATCH (p:Person {id: $id}) RETURN p", id=person_id)
except ServiceUnavailable:
    # 连接失败 — 重试或降级
    ...
except ClientError as e:
    # Cypher 语法错误、约束冲突
    if "ConstraintValidationFailed" in str(e):
        ...
except TransientError:
    # 死锁等 — 可重试 execute_write
    ...
```

---

## 6. 配置与环境变量

```python
import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "changeme")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
```

参考 `practice/.env.example`；生产密码走密钥管理，勿提交仓库。

---

## 7. FastAPI 生命周期集成

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

repo: GraphRepo | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global repo
    repo = GraphRepo(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE)
    yield
    repo.close()

app = FastAPI(lifespan=lifespan)
```

---

## 8. 动手练习

1. 运行 `python graph_repo.py` 查看示例查询输出
2. 在 `GraphRepo` 中添加 `get_person_projects(person_id)` 方法
3. 实现批量 MERGE 10 条测试 Person（UNWIND）
4. 故意违反 UNIQUE 约束，捕获 `ClientError`

---

## 9. 自检清单

- [ ] Driver 单例 + Session  per 请求
- [ ] 写操作用 `execute_write`，参数化查询
- [ ] 批量写入分批 UNWIND
- [ ] 应用退出时 `driver.close()`

---

## 下一课

[`06_advanced_cypher.md`](06_advanced_cypher.md) — 进阶 Cypher 与批量导入
