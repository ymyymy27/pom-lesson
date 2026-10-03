> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第6课：实战 — FastAPI + Redis

## 1. 项目架构

```
浏览器 / curl
    ↓
FastAPI (:8000)
    ├── GET  /articles/{id}     → Cache Aside 读文章
    ├── POST /articles/         → 写 DB + 删缓存
    ├── POST /auth/login        → 创建 Session
    ├── GET  /auth/me           → 读取 Session
    └── GET  /health            → Redis 连通性检查
    ↓
Redis (:6379)
    db0 — 缓存 + Session + 限流
```

与 [`learn-docker/05_practical_deploy.md`](../Docker/05-第5课实战部署.md) 类似：独立小项目，不依赖 Django 或 TaskFlow。

---

## 2. 项目结构

```
practice/
├── docker-compose.yml
├── requirements.txt
├── cache_service.py
├── rate_limiter.py
├── distributed_lock.py
└── app/
    ├── main.py
    └── store.py          # 模拟内存 DB
```

---

## 3. 启动

```bash
cd 03-进阶专题/02-部署与工程运维/Redis/practice
docker compose up -d
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

## 4. 核心代码说明

### 4.1 模拟数据库 `app/store.py`

内存字典模拟 PostgreSQL，便于专注 Redis 逻辑。

### 4.2 缓存读 `GET /articles/{id}`

```python
@app.get("/articles/{article_id}")
def get_article(article_id: int, request: Request):
    check_rate_limit(request, limit=100, window=60)

    key = f"article:{article_id}"
    cached = cache.get(key)
    if cached is not None:
        return {"source": "cache", "data": cached}

    article = store.get_article(article_id)
    if article is None:
        cache.set(key, None, ttl=60)
        raise HTTPException(404)

    cache.set(key, article, ttl=300)
    return {"source": "db", "data": article}
```

### 4.3 Session 登录

```python
@app.post("/auth/login")
def login(body: LoginBody, response: Response):
    user = store.authenticate(body.username, body.password)
    if not user:
        raise HTTPException(401)

    session_id = create_session(redis_client, user["id"])
    response.set_cookie("session_id", session_id, httponly=True, max_age=86400)
    return {"user": user}
```

### 4.4 健康检查

```python
@app.get("/health")
def health():
    try:
        redis_client.set("_health", "1", ex=5)
        assert redis_client.get("_health") == "1"
        redis_ok = True
    except redis.RedisError:
        redis_ok = False

    return {
        "status": "ok" if redis_ok else "degraded",
        "redis": redis_ok,
    }
```

完整代码见 `practice/app/main.py`。

---

## 5. 手动测试

```bash
# 健康检查
curl http://localhost:8000/health

# 登录（默认用户 demo / demo123）
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}' \
  -c cookies.txt

# 读文章 — 第一次 source=db，第二次 source=cache
curl http://localhost:8000/articles/1
curl http://localhost:8000/articles/1

# 当前用户
curl http://localhost:8000/auth/me -b cookies.txt

# 创建文章并观察缓存失效
curl -X POST http://localhost:8000/articles/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"title":"New Post","body":"Hello"}'
```

---

## 6. 本课 Checklist

完成以下即表示掌握 Redis 实战入门：

- [ ] Docker 启动 Redis，FastAPI 应用连通
- [ ] Cache Aside：二次请求命中缓存
- [ ] 更新/创建后缓存失效
- [ ] Session 登录与 `/auth/me`
- [ ] 限流：快速请求触发 429
- [ ] `/health` 包含 Redis 状态
- [ ] 能解释 db0 中几类 Key 的命名与 TTL

---

## 7. 继续学习（必修：部署与协作）

完成本课实战后，**务必继续第 7–10 课**（逻辑库、部署、团队协作、生产运维）：

| 课程 | 内容 |
|------|------|
| [07_logical_databases_and_isolation.md](07-第7课逻辑库隔离策略与实例规划.md) | db0–db15、隔离策略、实例规划 |
| [08_deployment_and_environments.md](08-第8课部署架构与多环境配置.md) | 多环境、Docker、安全、持久化 |
| [09_team_collaboration.md](<09-第9课团队协作规范与 Key 治理.md>) | Key 规范、协作调试、框架共存 |
| [10_production_operations.md](10-第10课生产运维高可用与故障处理.md) | 高可用、监控、故障 playbook |

| 方向 | 课程 |
|------|------|
| Django + Celery 集成 | `99-历史归档/旧版课程说明/Web旧导航/stage-06-celery-cache` |
| 性能监控与安全 | `99-历史归档/旧版课程说明/Web旧导航/stage-14-optimization` |
| 系统设计案例 | `03-进阶专题/01-软件设计与架构/learn-system-design` |
| 容器化部署 Redis | `learn-docker/05_practical_deploy.md` |

---

## 阶段总结（第 1–6 课）

- ✅ Redis 概念、安装、CLI
- ✅ 五大数据结构与选型
- ✅ redis-py、连接池、Pipeline
- ✅ 缓存模式与穿透/击穿/雪崩
- ✅ Session、限流、分布式锁、Pub/Sub、Celery 概览
- ✅ FastAPI + Redis 综合实战

👉 下一课：[07_logical_databases_and_isolation.md](07-第7课逻辑库隔离策略与实例规划.md)

**速查：** [`00-Redis 语法结构参考.md`](<00-Redis 语法结构参考.md>)
