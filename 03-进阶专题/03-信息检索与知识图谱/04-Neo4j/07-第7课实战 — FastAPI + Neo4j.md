> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第7课：实战 — FastAPI + Neo4j

## 1. 项目架构

```
浏览器 / curl
    ↓
FastAPI (:8000)
    ├── GET  /health              → Neo4j 连通性
    ├── GET  /persons/{id}        → 查询员工
    ├── GET  /persons/{id}/projects → 参与项目
    ├── GET  /departments/{id}/members → 部门成员
    └── GET  /org/subgraph        → 组织子图（可视化用）
    ↓
Neo4j Bolt (:7687)
    演示组织图谱（Company / Department / Person / Project）
```

与 [`learn-redis/06_practical_web_app.md`](<../../02-部署与工程运维/Redis/06-第6课实战 — FastAPI + Redis.md>) 结构类似：独立小项目，专注 Neo4j 集成。

---

## 2. 项目结构

```
practice/
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── seed_demo_graph.py      # 初始化演示数据
├── graph_repo.py           # Repository 封装
└── app/
    └── main.py             # FastAPI 入口
```

---

## 3. 启动

```bash
cd 03-进阶专题/03-信息检索与知识图谱/04-Neo4j/practice
docker compose up -d
pip install -r requirements.txt
python seed_demo_graph.py
uvicorn app.main:app --reload --port 8000
```

**验证：**

```bash
curl http://localhost:8000/health
curl http://localhost:8000/persons/person_001
curl http://localhost:8000/persons/person_001/projects
curl http://localhost:8000/departments/dept_d01/members
curl "http://localhost:8000/org/subgraph?person_id=person_001&depth=2"
```

Swagger UI：`http://localhost:8000/docs`

---

## 4. 核心代码说明

### 4.1 GraphRepo `graph_repo.py`

- 封装 Cypher，应用层不拼 SQL 式字符串
- 方法：`get_person`、`list_person_projects`、`list_department_members`、`get_subgraph`

### 4.2 生命周期 `app/main.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    global repo
    repo = GraphRepo(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE)
    yield
    repo.close()
```

### 4.3 子图 API

返回节点与边列表，供前端 G6 / Cytoscape 或调试：

```python
@app.get("/org/subgraph")
def org_subgraph(person_id: str, depth: int = 2):
    if depth < 1 or depth > 4:
        raise HTTPException(400, "depth must be 1-4")
    return repo.get_subgraph(person_id, depth)
```

**安全：** 限制 `depth` 上限，防止查询爆炸。

---

## 5. 扩展练习

1. 添加 `POST /persons` 创建员工（MERGE + MEMBER_OF）
2. 添加 `GET /projects/{id}/team` 返回项目团队
3. 为所有端点加简单限流（可复用 learn-redis 的 rate_limiter 思路）
4. 在 Browser 对比 API 返回的子图与可视化

---

## 6. 与知识图谱课衔接

| 本课实现 | 知识图谱课扩展 |
|----------|----------------|
| 手工 seed 数据 | 第 4 课 LLM 抽取入库 |
| REST 查询 API | 第 8 课 GraphQL / 复杂封装 |
| 固定 Schema | 第 2 课本体与版本管理 |
| 子图导出 | 第 9 课 Graph RAG 上下文 |

---

## 7. 自检清单

- [ ] 能启动 compose + seed + FastAPI 全链路
- [ ] 理解 Repository 与路由分层
- [ ] API 查询均参数化，depth 有上限
- [ ] 健康检查包含 Neo4j 连通性

---

## 下一课

[`08-第8课逻辑数据库与环境隔离.md`](08-第8课逻辑数据库与环境隔离.md) — 多库与环境隔离
