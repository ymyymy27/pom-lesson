# 第8课：查询服务 — Graph API 与可视化

> 前置：第 5 课（Cypher）  
> 实战：`practice/graph_api.py`

图谱的价值在**被消费**。本课讲如何把 Cypher 封装为稳定的 Graph API，并对接可视化。

---

## 1. 为什么需要 Graph API 层？

```
❌ 业务方直接写 Cypher
   · 查询逻辑散落 · 无权限控制 · Schema 变更击穿调用方

✅ Graph API 层（Repository / Service）
   · 固定查询模板 · 参数校验 · 缓存 · 限流 · 版本化
```

---

## 2. 分层架构

```
┌─────────────────────────────────────────┐
│  Client: Web / Mobile / RAG / Agent     │
├─────────────────────────────────────────┤
│  REST / GraphQL API (FastAPI)           │
├─────────────────────────────────────────┤
│  GraphService — 业务查询封装             │
├─────────────────────────────────────────┤
│  GraphRepository — Cypher 执行           │
├─────────────────────────────────────────┤
│  Neo4j Driver                           │
└─────────────────────────────────────────┘
```

---

## 3. Repository 模式

```python
# practice/graph_api.py 核心片段

class GraphRepository:
    def __init__(self, driver):
        self._driver = driver

    def get_person_with_projects(self, person_id: str) -> dict | None:
        query = """
        MATCH (p:Person {id: $id})
        OPTIONAL MATCH (p)-[:WORKS_ON]->(proj:Project)
        RETURN p {.*, projects: collect(proj {.id, .name, .status})} AS person
        """
        with self._driver.session() as session:
            record = session.run(query, id=person_id).single()
            return record["person"] if record else None

    def search_people(self, name: str, limit: int = 20) -> list[dict]:
        query = """
        MATCH (p:Person)
        WHERE p.name CONTAINS $name AND coalesce(p.status, 'active') = 'active'
        RETURN p {.id, .name, .email, .title} AS person
        ORDER BY p.name
        LIMIT $limit
        """
        with self._driver.session() as session:
            return [r["person"] for r in session.run(query, name=name, limit=limit)]

    def get_subgraph(self, entity_id: str, depth: int = 2, limit: int = 50) -> dict:
        depth = min(depth, 3)  # 强制上限，防爆炸
        query = """
        MATCH path = (start {id: $id})-[*1..$depth]-(neighbor)
        WITH nodes(path) AS ns, relationships(path) AS rs
        UNWIND ns AS n
        WITH collect(DISTINCT n) AS nodes, rs
        UNWIND rs AS r
        RETURN nodes, collect(DISTINCT r) AS rels
        LIMIT $limit
        """
        # 生产环境建议返回序列化 JSON，而非原始 Node 对象
        ...
```

---

## 4. FastAPI REST 封装

```python
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="Org Knowledge Graph API")
repo = GraphRepository(driver)

class PersonResponse(BaseModel):
    id: str
    name: str
    email: str | None = None
    projects: list[dict] = []

@app.get("/v1/persons/{person_id}", response_model=PersonResponse)
def get_person(person_id: str):
    data = repo.get_person_with_projects(person_id)
    if not data:
        raise HTTPException(404, "Person not found")
    return data

@app.get("/v1/persons/search")
def search_persons(q: str = Query(min_length=1), limit: int = Query(default=20, le=100)):
    return {"results": repo.search_people(q, limit)}

@app.get("/v1/subgraph/{entity_id}")
def subgraph(entity_id: str, depth: int = 2):
    return repo.get_subgraph(entity_id, depth=depth)
```

### API 设计规范

| 规范 | 说明 |
|------|------|
| 版本前缀 | `/v1/` |
| 深度限制 | `depth ≤ 3` |
| 分页 | `limit` + `cursor` |
| 错误码 | 404 实体不存在、400 参数非法 |
| 超时 | 查询 > 5s 返回 504 或降级 |

---

## 5. GraphQL（可选）

适合前端灵活组合查询：

```graphql
type Person {
  id: ID!
  name: String!
  projects: [Project!]!
  department: Department
}

type Query {
  person(id: ID!): Person
  searchPersons(name: String!, limit: Int = 20): [Person!]!
}
```

**权衡：** GraphQL 灵活但需防深度攻击（`max_depth=3`）、复杂度分析。

---

## 6. 缓存策略

| 查询类型 | 缓存 | TTL |
|----------|------|-----|
| 实体详情 | Redis | 5–15 min |
| 搜索结果 | Redis | 1–5 min |
| 子图遍历 | 短 TTL 或禁缓存 | — |
| 写后 | 失效相关 key | — |

```python
CACHE_KEY = "kg:person:{id}"

def get_person_cached(person_id: str):
    if cached := redis.get(CACHE_KEY.format(id=person_id)):
        return json.loads(cached)
    data = repo.get_person_with_projects(person_id)
    if data:
        redis.setex(CACHE_KEY.format(id=person_id), 600, json.dumps(data))
    return data
```

---

## 7. 可视化

### 7.1 Neo4j Browser / Bloom

- 开发调试、领域专家探索
- 不适合嵌入生产 UI

### 7.2 前端图可视化

| 库 | 特点 |
|----|------|
| Cytoscape.js | 功能全、定制强 |
| G6 (AntV) | 中文文档、企业级 |
| vis-network | 轻量快速 |

```javascript
// API 返回 { nodes: [{id, label, ...}], edges: [{source, target, type}] }
fetch(`/v1/subgraph/${entityId}?depth=2`)
  .then(r => r.json())
  .then(data => cy.json({ elements: toCytoscape(data) }));
```

---

## 8. Natural Language → Cypher（进阶）

```
用户：「研发一部有哪些人在做订单系统？」
         ↓
   LLM Text2Cypher（需 Schema 上下文 + 只读账号 + 校验）
         ↓
   人工/规则校验 → 执行 → 返回
```

**安全要求：**

- 只读数据库用户
- 禁止 `CREATE/DELETE/DETACH`
- `LIMIT` 强制注入
- Schema 白名单

---

## 9. 动手练习

1. 启动 `uvicorn practice.graph_api:app --reload`，访问 `/docs`
2. 调用 `GET /v1/persons/search?q=张`
3. 为 `get_person` 添加 Redis 缓存（可选）
4. 设计 3 个 REST 端点满足你的业务场景

---

## 10. 自检清单

- [ ] 理解 Graph API 层的必要性
- [ ] 会用 Repository 模式封装 Cypher
- [ ] 能设计 REST API 版本与限流策略
- [ ] 知道子图查询的深度限制原因
- [ ] 了解 NL2Cypher 的安全约束

---

## 下一课

[`09_integration_rag_llm.md`](09_integration_rag_llm.md) — 与 RAG、LLM、Agent 集成
