# 第1课：Redis 基础 - 核心概念与安装

## 1. Redis 是什么？

### 一句话解释

**Redis 就是「内存里的超快字典」** —— 键值对存储，读写微秒级，常用于缓存、会话、队列和实时数据。

### 类比理解

| 日常概念 | Redis 概念 |
|---------|------------|
| 便签本（随手写、随手查） | **String** 键值 |
| 通讯录（姓名 → 电话/地址） | **Hash** 对象 |
| 排队队列 | **List** |
| 签到名单（不重复） | **Set** |
| 考试排名榜 | **Sorted Set** |

### Redis vs PostgreSQL

| 特性 | PostgreSQL | Redis |
|------|-----------|-------|
| 存储 | 磁盘（可配内存表） | 内存（可选持久化） |
| 速度 | 毫秒级 | 微秒级 |
| 查询 | SQL | 命令 |
| 事务 | ACID | 单命令原子；Multi/Exec 有限事务 |
| 适用 | 业务主数据 | 热点数据、临时状态、消息 |

**结论：** Redis 通常**不替代**关系库，而是与之配合——PostgreSQL 存权威数据，Redis 存热点与中间状态。

---

## 2. Redis 在 Web 应用中的八大用途

```
┌────────────────────────────────────────────┐
│              Redis 常见用途                 │
├────────────────────────────────────────────┤
│ 1. 缓存      — API/DB 查询结果              │
│ 2. 会话      — 登录态 Session               │
│ 3. 消息队列  — Celery Broker                │
│ 4. 计数器    — 浏览量、点赞数                │
│ 5. 限流      — API 频率控制                 │
│ 6. 分布式锁  — 并发写保护                    │
│ 7. 排行榜    — Sorted Set 实时排名          │
│ 8. 发布订阅  — 实时通知、WebSocket 推送      │
└────────────────────────────────────────────┘
```

---

## 3. 安装 Redis（Docker 方式，推荐）

```bash
cd learn-tools/learn-redis/practice
docker compose up -d
```

**连接 Redis CLI（Windows 推荐用 Docker，无需本机安装 redis-cli）：**

```powershell
# 方式 1：在容器内执行（推荐）
docker exec -it learn-redis redis-cli PING    # PONG

# 方式 2：进入交互式 CLI
docker exec -it learn-redis redis-cli
```

> Windows 若直接运行 `redis-cli` 报「无法识别命令」，说明本机未安装客户端，用上面 `docker exec` 即可。  
> 容器基于 Alpine，没有 `bash`，需进 shell 时用 `docker exec -it learn-redis sh`。

停止：`docker compose down`（加 `-v` 清空数据）

---

## 4. 第一次操作

```bash
127.0.0.1:6379> SET greeting "Hello Redis"
OK
127.0.0.1:6379> GET greeting
"Hello Redis"
127.0.0.1:6379> EXPIRE greeting 60
127.0.0.1:6379> TTL greeting
(integer) 58
127.0.0.1:6379> DEL greeting
(integer) 1
```

---

## 5. 核心概念

- **键值模型**：Key 唯一，Value 有类型（string/hash/list/set/zset）
- **单线程**：命令原子；避免 `KEYS *` 等阻塞操作
- **持久化**：RDB 快照 / AOF 日志（练习环境 compose 已开 AOF）
- **逻辑库**：db0–db15，`SELECT` 切换 → 详见 [第7课](07_logical_databases_and_isolation.md)

---

## 6. Python 快速连接

```python
import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
print(r.ping())           # True
r.set("demo", "works")
print(r.get("demo"))      # works
```

---

## 7. 练习

1. Docker 启动 Redis，`PING` 确认连通
2. CLI：`SET` → `GET` → `EXPIRE` → `TTL` → `DEL`
3. Python 写入/读取一个键
4. 思考：哪些数据适合 Redis，哪些必须 PostgreSQL？

👉 下一课：[02_data_structures.md](02_data_structures.md)
