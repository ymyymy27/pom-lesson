> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Redis 语法结构参考

> 本文档系统梳理 Redis 的三层语法：**CLI 命令行**、**五大数据结构**、**Python redis-py**。建议配合 `01-第1课Redis 基础 - 核心概念与安装.md` 一起阅读。

---

## 1. 整体架构：Redis 在应用中的位置

```
┌─────────────────────────────────────────────────────────┐
│  应用层（Django / FastAPI / Celery Worker）              │
│  django.core.cache / redis-py / Celery Broker URL       │
├─────────────────────────────────────────────────────────┤
│  Redis 协议层（RESP）                                    │
│  TCP 6379 — 单线程事件循环处理命令                       │
├─────────────────────────────────────────────────────────┤
│  数据结构层                                              │
│  String │ Hash │ List │ Set │ Sorted Set │ Stream ...  │
├─────────────────────────────────────────────────────────┤
│  持久化（可选）                                          │
│  RDB 快照 │ AOF 日志                                     │
└─────────────────────────────────────────────────────────┘
```

**典型调用链：**

```
应用 → redis-py / redis-cli → Redis Server → 内存数据结构
                                    ↓
                              RDB / AOF（持久化到磁盘）
```

---

## 2. CLI 命令语法结构

### 2.1 通用格式

```bash
redis-cli [全局选项] [命令 [参数...]]
```

**示例拆解：**

```bash
redis-cli -h localhost -p 6379 SET user:1:name "张三" EX 3600
│         │  │         │  │   │  │              │      │
│         │  │         │  │   │  │              │      └── 过期秒数
│         │  │         │  │   │  │              └── 值
│         │  │         │  │   │  └── 键名
│         │  │         │  │   └── 命令
│         │  │         │  └── 端口
│         │  │         └── 主机
│         └── 客户端
```

### 2.2 常用全局选项

| 选项 | 说明 |
|------|------|
| `-h HOST` | 主机（默认 127.0.0.1） |
| `-p PORT` | 端口（默认 6379） |
| `-a PASSWORD` | 密码（生产环境必须设置） |
| `-n DB` | 选择数据库编号（0–15） |
| `--raw` | 原始输出（避免转义） |
| `--no-auth-warning` | 隐藏命令行传密码的警告 |

### 2.3 命令分类速查

| 类别 | 常见命令 | 作用 |
|------|----------|------|
| **连接** | `PING`, `AUTH`, `SELECT`, `QUIT` | 测试连接、认证、切换 DB |
| **String** | `SET`, `GET`, `INCR`, `SETEX`, `SETNX` | 字符串、计数、锁 |
| **Hash** | `HSET`, `HGET`, `HGETALL`, `HINCRBY` | 对象字段 |
| **List** | `LPUSH`, `RPUSH`, `LPOP`, `LRANGE`, `BLPOP` | 队列、日志 |
| **Set** | `SADD`, `SMEMBERS`, `SISMEMBER`, `SINTER` | 去重、集合运算 |
| **Sorted Set** | `ZADD`, `ZRANGE`, `ZREVRANGE`, `ZINCRBY` | 排行榜、优先级 |
| **Key 管理** | `EXISTS`, `DEL`, `EXPIRE`, `TTL`, `SCAN` | 键生命周期 |
| **服务器** | `INFO`, `DBSIZE`, `FLUSHDB`, `MONITOR` | 运维诊断 |

---

## 3. 五大数据结构语法

### 3.1 String（字符串）

```bash
SET key value [EX seconds | PX milliseconds | EXAT timestamp]
GET key
SETEX key seconds value          # SET + EX 简写
SETNX key value                  # 仅当 key 不存在时设置（分布式锁基础）
INCR key / DECR key
INCRBY key increment
MSET k1 v1 k2 v2
MGET k1 k2
APPEND key value
STRLEN key
```

### 3.2 Hash（哈希）

```bash
HSET key field value [field value ...]
HGET key field
HMGET key field [field ...]
HGETALL key
HINCRBY key field increment
HDEL key field [field ...]
HEXISTS key field
HLEN key
```

### 3.3 List（列表）

```bash
LPUSH key element [element ...]
RPUSH key element [element ...]
LPOP key [count]
RPOP key [count]
LRANGE key start stop            # 0 -1 表示全部
LLEN key
LINDEX key index
BLPOP key timeout                # 阻塞弹出（秒，0=永久阻塞）
BRPOP key timeout
```

### 3.4 Set（集合）

```bash
SADD key member [member ...]
SREM key member [member ...]
SMEMBERS key
SISMEMBER key member
SCARD key                        # 成员数量
SINTER key [key ...]             # 交集
SUNION key [key ...]             # 并集
SDIFF key [key ...]              # 差集
```

### 3.5 Sorted Set（有序集合）

```bash
ZADD key score member [score member ...]
ZSCORE key member
ZRANK key member                 # 升序排名（0 起）
ZREVRANK key member              # 降序排名
ZRANGE key start stop [WITHSCORES]
ZREVRANGE key start stop [WITHSCORES]
ZINCRBY key increment member
ZCARD key
ZCOUNT key min max
ZRANGEBYSCORE key min max
```

---

## 4. Key 命名与 TTL 规范

### 4.1 推荐命名格式

```
{项目}:{业务}:{实体}:{标识}
```

```
myapp:cache:user:42
myapp:session:sess_abc123
myapp:ratelimit:192.168.1.1:/api/login
myapp:lock:order:1001
```

**原则：**

- 用冒号分层，便于 `SCAN myapp:cache:*` 按前缀管理
- 避免 `KEYS *`（阻塞生产环境）
- 键名尽量短但可读

### 4.2 TTL 相关命令

```bash
EXPIRE key seconds
EXPIREAT key unix-timestamp
PERSIST key                      # 移除过期
TTL key                          # 剩余秒（-1=永不过期，-2=不存在）
PTTL key                         # 剩余毫秒
```

---

## 5. Python redis-py 语法结构

### 5.1 连接方式

```python
import redis

# 单连接
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True,       # bytes → str
    socket_timeout=5,
)

# 连接池（生产推荐）
pool = redis.ConnectionPool(
    host="localhost",
    port=6379,
    max_connections=20,
    decode_responses=True,
)
r = redis.Redis(connection_pool=pool)

# URL 方式（与 Celery / Django 配置一致）
r = redis.from_url("redis://localhost:6379/0")
```

### 5.2 命令映射（CLI → Python）

| CLI | Python |
|-----|--------|
| `SET k v EX 3600` | `r.set("k", "v", ex=3600)` |
| `GET k` | `r.get("k")` |
| `HSET k f v` | `r.hset("k", "f", "v")` 或 `r.hset("k", mapping={...})` |
| `LPUSH k v` | `r.lpush("k", "v")` |
| `SADD k m` | `r.sadd("k", "m")` |
| `ZADD k 100 m` | `r.zadd("k", {"m": 100})` |
| `EXPIRE k 60` | `r.expire("k", 60)` |
| `DEL k1 k2` | `r.delete("k1", "k2")` |

### 5.3 Pipeline（批量命令）

```python
pipe = r.pipeline()
pipe.set("a", 1)
pipe.incr("counter")
pipe.expire("counter", 60)
results = pipe.execute()         # 一次网络往返
```

### 5.4 分布式锁（SET NX EX）

```python
# 加锁
ok = r.set("myapp:lock:resource", "token", nx=True, ex=30)

# 释放（应用 Lua 保证原子性，见第 5 课）
```

---

## 6. 数据库编号约定

Redis 默认 16 个逻辑库（db0–db15），**同一实例内隔离，非物理隔离**。

| DB | 常见用途 |
|----|----------|
| db0 | 业务缓存、Session |
| db1 | Celery Broker |
| db2 | Celery Result Backend |

```bash
SELECT 1                         # CLI 切换
```

```python
r = redis.from_url("redis://localhost:6379/1")
```

> **深度专题：** 逻辑库 vs Key 前缀 vs 独立实例、Cluster 限制、团队 db 分配表 → 见 [`07-第7课逻辑库隔离策略与实例规划.md`](07-第7课逻辑库隔离策略与实例规划.md)

---

## 7. 运维常用命令

```bash
INFO                             # 服务器信息
INFO memory                      # 内存使用
INFO stats                       # 命令统计
DBSIZE                           # 当前 DB 键数量
SCAN 0 MATCH myapp:* COUNT 100   # 安全遍历键（替代 KEYS）
MONITOR                          # 实时打印所有命令（调试用，生产慎用）
CLIENT LIST                      # 连接列表
SLOWLOG GET 10                   # 慢查询
CONFIG GET maxmemory             # 内存上限配置
```

---

## 8. 与 Django / Celery 配置对照

```python
# Django settings.py
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/0",
    }
}

# Celery
CELERY_BROKER_URL = "redis://localhost:6379/1"
CELERY_RESULT_BACKEND = "redis://localhost:6379/2"
```

底层均为 Redis 协议，本课掌握的命令与模式可直接迁移到 Django / Celery 项目。
