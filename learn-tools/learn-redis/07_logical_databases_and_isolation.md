# 第7课：逻辑库、隔离策略与实例规划

> 前置：第 1–4 课（概念、数据结构、Python 客户端、Key 设计）  
> 关联：[`04_caching_patterns.md`](04_caching_patterns.md) Key 规范 · [`08_deployment_and_environments.md`](08_deployment_and_environments.md) 多环境部署

本课解决一个在实际项目和团队协作中**反复被问、但入门教程往往一句话带过**的问题：

**Redis 的 db0、db1… 到底是什么？和 MySQL 的 database 一样吗？团队共用一台 Redis 怎么隔离？该用 `SELECT` 还是 Key 前缀？**

---

## 1. 先建立正确心智模型

### 1.1 三个层次，不要混为一谈

```
层次 1：Redis 进程（实例 Instance）
         └── 一台机器 / 一个容器 / 一个 redis-server 进程
         └── 占用独立端口（默认 6379）
         └── 拥有独立内存上限 maxmemory

层次 2：逻辑库（Logical Database，db0–db15）
         └── 同一个实例内的「命名空间分区」
         └── 用 SELECT 或 URL 末尾 /N 切换
         └── 共享同一进程内存，不是物理隔离

层次 3：Key 前缀（Namespace）
         └── 同一个 db 内的键名约定
         └── myapp:cache:article:42
         └── 纯约定，Redis 不感知
```

**常见误区：** 把 db1 当成「另一个数据库服务器」。实际上 db0 和 db1 在同一进程、同一块内存里，只是 key 查找时按当前选中的 db 编号过滤。

### 1.2 与 MySQL 的对比

| 维度 | MySQL Database | Redis Logical DB |
|------|----------------|------------------|
| 隔离强度 | 库级权限、独立 schema | 仅 key 空间分隔 |
| 资源隔离 | 可独立备份策略 | 共享内存与 CPU |
| 连接方式 | `USE dbname` | `SELECT N` |
| 最大数量 | 很多 | 默认 16（可配置 `databases`） |
| Cluster 模式 | N/A | **只支持 db0** |
| 删库误操作 | `DROP DATABASE` | `FLUSHDB`（当前 db）/ `FLUSHALL`（全部 db） |

---

## 2. 逻辑库的工作原理

### 2.1 默认配置

Redis 默认开启 **16 个逻辑库**：db0 到 db15。

- 新连接默认落在 **db0**
- 配置项 `databases 16` 在 `redis.conf` 中
- 可通过 `CONFIG GET databases` 查看

### 2.2 CLI 动手验证

在 `learn-redis` 容器中（建议 `--raw`）：

```bash
docker exec -it learn-redis redis-cli --raw
```

```bash
# ── 1. 在 db0 写入 ──
127.0.0.1:6379> SET user:1 "张三-db0"
OK
127.0.0.1:6379> GET user:1
张三-db0

# ── 2. 切换到 db1 ──
127.0.0.1:6379> SELECT 1
OK
127.0.0.1:6379> GET user:1
(nil)                    # db1 里没有这个 key

127.0.0.1:6379> SET user:1 "李四-db1"
OK

# ── 3. 切回 db0 ──
127.0.0.1:6379> SELECT 0
OK
127.0.0.1:6379> GET user:1
张三-db0                 # db0 的数据完好

# ── 4. 查看各 db 的 key 数量 ──
127.0.0.1:6379> INFO keyspace
# Keyspace
# db0:keys=1,expires=0,avg_ttl=0
# db1:keys=1,expires=0,avg_ttl=0

127.0.0.1:6379> DBSIZE
(integer) 1              # 仅当前 db（db0）的 key 数
```

**要点：**

- 同名 key `user:1` 在 db0 和 db1 是**两个完全独立的键**
- `GET` / `DEL` / `SCAN` 只作用于**当前选中的 db**
- `KEYS *` 不会跨 db 扫描

### 2.3 `SELECT` 命令细节

```bash
SELECT 0    # 切换到 db0，返回 OK
SELECT 16   # 超出范围 → ERR DB index is out of range
```

**注意：** `SELECT` 会改变**当前连接**的上下文。如果连接池中的连接被复用，且某次操作调用了 `SELECT 1` 但未切回，后续请求可能读写错误的 db——这是生产事故常见原因之一。

---

## 3. 应用层如何指定逻辑库

### 3.1 连接 URL 中的 `/N`

```python
import redis

# db0（默认，可省略 /0）
r0 = redis.from_url("redis://localhost:6379/0", decode_responses=True)

# db1 — Celery Broker 常见写法
r1 = redis.from_url("redis://localhost:6379/1", decode_responses=True)

# 带密码
r = redis.from_url("redis://:s3cret@localhost:6379/0", decode_responses=True)
```

URL 格式：`redis://[:password@]host:port/db_number`

### 3.2 构造函数参数

```python
r = redis.Redis(host="localhost", port=6379, db=2, decode_responses=True)
```

### 3.3 Celery 的典型分库

```python
# celery_app.py
broker_url = "redis://localhost:6379/1"       # 任务队列
result_backend = "redis://localhost:6379/2"   # 任务结果
```

```
同一 Redis 实例
├── db0  → Web 应用（缓存、Session、限流）
├── db1  → Celery Broker（List 结构存任务）
└── db2  → Celery Result Backend（任务结果）
```

**为什么 Celery 常用不同 db？** 历史习惯和配置简单——三个 URL 指向同一 host:6379，只改末尾数字，队列 key 与业务 key 不会混在一起，`KEYS`/`SCAN` 排查时边界清晰。

### 3.4 运行时 `SELECT` 的风险（不推荐）

```python
# ⚠️ 不推荐：在共享连接池里动态 SELECT
r = redis.from_url("redis://localhost:6379/0")
r.execute_command("SELECT", 1)   # 污染连接池中的连接
r.set("task", "data")              # 写入了 db1，但其他代码以为在 db0
```

**最佳实践：** 需要多个 db 时，创建**多个 Redis 客户端实例**，每个固定一个 db 编号，不要运行时 `SELECT`。

---

## 4. 三种隔离策略深度对比

这是本课**最核心的决策框架**。

### 4.1 策略 A：逻辑库隔离（SELECT / URL `/N`）

```
实例 redis://prod:6379
├── /0  业务缓存 + Session
├── /1  Celery Broker
└── /2  Celery Result
```

| 优点 | 缺点 |
|------|------|
| 配置简单，改 URL 末尾数字即可 | Redis Cluster **不支持**（只有 db0） |
| Celery 等框架文档默认此方式 | 团队容易忘记「该用 db 几」 |
| 同一 db 内 `SCAN *` 不会扫到其他模块 | `FLUSHDB` 误操作仍可能发生 |
| | 连接池 + 动态 SELECT 易出 bug |
| | 运维/监控需按 db 分别看 keyspace |

**适用：** 单机 Redis、框架约定（Celery）、小团队、明确文档化了 db 分配表。

### 4.2 策略 B：Key 前缀隔离（推荐作为默认）

```
全部使用 db0，靠 key 名区分：

myapp:cache:article:42
myapp:session:abc123
myapp:ratelimit:192.168.1.1:/api/login
celery:broker:...
```

| 优点 | 缺点 |
|------|------|
| Cluster 兼容 | 需要团队统一命名规范 |
| 见名知意，运维友好 | 前缀设计不当会 key 冲突 |
| `SCAN myapp:cache:*` 可精确排查 | 所有 key 共享同一 db 的内存淘汰 |
| 不依赖 SELECT，连接池更安全 | Celery 需额外配置 key 前缀 |

**适用：** 现代项目默认方案、上 Cluster 前、多模块共用实例。

### 4.3 策略 C：独立实例隔离（生产环境推荐）

```
dev-redis      localhost:6379
staging-redis  redis-staging.internal:6379
prod-redis     redis-prod.internal:6379
```

| 优点 | 缺点 |
|------|------|
| 环境/项目完全隔离 | 多实例运维成本 |
| 误 `FLUSHALL` 不影响其他环境 | 内存/连接资源翻倍 |
| 可独立设置 maxmemory、持久化策略 | |
| 安全边界清晰（prod 密码、网络隔离） | |

**适用：** dev/staging/prod 分离、多项目共用运维平台、合规要求。

### 4.4 决策流程图

```
需要 Redis Cluster？
├── 是 → 只用 db0 + Key 前缀（策略 B）
└── 否 → 是否多环境（dev/staging/prod）？
         ├── 是 → 每环境独立实例（策略 C）+ 实例内 Key 前缀（策略 B）
         └── 否 → 是否 Celery 等框架默认分库？
                  ├── 是 → db0 业务 + db1/db2 框架（策略 A + B 组合）
                  └── 否 → db0 + Key 前缀（策略 B）
```

### 4.5 实际团队推荐组合

```
生产：     独立实例（C） + Key 前缀（B） + 密码 + 内网
预发：     独立实例（C） + 与 prod 相同前缀规范
本地开发：  Docker compose 独立容器（C） + dev 前缀（B）
Celery：    同实例 db1/db2（A）或 独立实例（C），二选一写进文档
```

---

## 5. 逻辑库的运维命令

### 5.1 查看与切换

```bash
SELECT 0
DBSIZE                           # 当前 db 的 key 总数
INFO keyspace                    # 所有 db 的 key 统计
```

### 5.2 清空（危险操作）

```bash
FLUSHDB      # 清空当前 SELECT 的 db — 生产环境需二次确认
FLUSHALL     # 清空所有 db — 灾难级操作
```

**协作场景：** 新人本地调试时执行 `FLUSHALL`，若共用实例且无环境隔离，会删掉所有人的数据。对策见第 9 课。

### 5.3 迁移 key 到另一个 db

Redis **没有** `MOVE key TO db2` 这种跨 db 原子命令。只能：

```bash
# 方式 1：DUMP + RESTORE（同实例跨 db）
SELECT 0
DUMP mykey                       # 获取序列化 blob
SELECT 1
RESTORE mykey 0 "<dump_blob>"    # 写入 db1
SELECT 0
DEL mykey                        # 确认后删除源 key

# 方式 2：应用层读 db0 写 db1（更可控）
```

生产环境迁移通常改配置 + 双写 + 切流量，而非手动 DUMP。

---

## 6. db 分配表示例（团队文档模板）

在项目 `docs/redis-db-allocation.md` 中维护：

```markdown
# Redis 实例：redis-prod.internal:6379

| DB | 用途 | 负责团队 | Key 前缀示例 | 备注 |
|----|------|----------|--------------|------|
| 0 | 业务缓存、Session、限流 | Backend | `myapp:cache:*` `myapp:session:*` | 主业务 |
| 1 | Celery Broker | Platform | 由 Celery 管理 | 勿手动 FLUSHDB |
| 2 | Celery Result | Platform | 由 Celery 管理 | TTL 自动过期 |
| 3–15 | 预留 | — | — | 未使用 |

# 禁止事项
- 禁止 FLUSHALL
- 禁止在生产 db0 执行 KEYS *
- 禁止未文档化就占用新 db
```

---

## 7. 与 Docker Desktop 里「practice」堆栈的关系

你可能在 Docker Desktop 看到：

```
practice          ← Compose 项目名（目录名 practice/）
  └── redis       ← 服务名
        └── 实际容器名 learn-redis（container_name 指定）
```

这与逻辑库 **无关**：

| 名称 | 类型 | 来源 |
|------|------|------|
| `practice` | Compose 项目 | 文件夹 `practice/` |
| `redis` | Compose 服务 | `docker-compose.yml` 的 `services.redis` |
| `learn-redis` | 容器名 | `container_name: learn-redis` |
| `db0` | 逻辑库 | Redis 内部，连接 URL `/0` |

`docker start practice` 失败，是因为 **没有名叫 practice 的容器**；应使用 `docker compose up -d` 或 `docker start learn-redis`。

---

## 8. 常见事故与排查

### 8.1 「我 SET 了但 GET 不到」

排查清单：

1. 是否连错了**实例**（6379 vs 9787，learn-redis vs dify 的 redis）？
2. 是否连错了 **db**（应用写 db0，CLI 在 db1）？
3. Key 是否带了**前缀**（代码写 `myapp:cache:article:1`，CLI 查 `article:1`）？
4. Key 是否**已过期**（`TTL key` 返回 -2 表示不存在）？

```bash
# 排查脚本
redis-cli -n 0 GET "myapp:cache:article:1"
redis-cli -n 1 GET "myapp:cache:article:1"
TTL "myapp:cache:article:1"
INFO keyspace
```

### 8.2 连接池 + SELECT 导致数据错乱

**现象：** 间歇性读到错误数据，难以复现。

**原因：** 连接 A 被线程 1 用于 `SELECT 1`，归还池后线程 2 复用连接 A 却以为在 db0。

**修复：** 禁止运行时 SELECT；每 db 独立客户端或 URL 固定 `/N`。

### 8.3 Celery 任务丢失 / 业务缓存被清

**原因：** 某人在 db1 执行 `FLUSHDB` 想清缓存，实际 Celery broker 也在 db1；或 `FLUSHALL`。

**修复：** 文档化 db 分配；dev 环境独立实例；生产禁用 FLUSH 权限（ACL）。

---

## 9. 练习

### 练习 1：逻辑库隔离实验

```bash
docker exec -it learn-redis redis-cli --raw
```

1. db0 写入 `SET app:config "v1"`
2. `SELECT 1`，写入同名 key 值 `"v2"`
3. 分别 `SELECT 0` 和 `SELECT 1` 读取，确认隔离
4. `INFO keyspace` 查看两个 db 的 keys 计数
5. 在 db1 执行 `FLUSHDB`，确认 db0 数据仍在

### 练习 2：URL 连接不同 db

```python
import redis

r0 = redis.from_url("redis://localhost:6379/0", decode_responses=True)
r1 = redis.from_url("redis://localhost:6379/1", decode_responses=True)

r0.set("test", "from-db0")
print(r1.get("test"))   # None
r1.set("test", "from-db1")
print(r0.get("test"))   # from-db0
print(r1.get("test"))   # from-db1
```

### 练习 3：设计 db 分配表

为你的假想项目（Web + Celery + 限流）写一份 db 分配表，并说明哪些场景你会改用 Key 前缀或独立实例。

---

## 10. 本课 Checklist

- [ ] 能区分 Redis **实例 / 逻辑库 / Key 前缀** 三个层次
- [ ] 能解释 db0 与 db1 同名 key 为何互不影响
- [ ] 知道 Cluster 只支持 db0
- [ ] 能说出三种隔离策略及推荐组合
- [ ] 理解 Celery 使用 `/1`、`/2` 的原因
- [ ] 知道连接池 + 动态 SELECT 的风险
- [ ] 能使用 `INFO keyspace`、`DBSIZE`、`TTL` 排查 key 丢失

---

👉 下一课：[08_deployment_and_environments.md](08_deployment_and_environments.md) — 部署架构与多环境配置
