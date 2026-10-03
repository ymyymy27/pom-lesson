# 第 05 节：Redis 基础

## 一、什么是 Redis？

Redis（Remote Dictionary Server）是一个 **基于内存的键值存储数据库**，特点是 **速度极快**（读写 10 万+/秒）。

### 1.1 Redis vs 关系型数据库

| 特性 | PostgreSQL | Redis |
|------|-----------|-------|
| 存储位置 | 磁盘 | 内存（可持久化到磁盘） |
| 数据结构 | 表（行+列） | 键值对（支持多种数据结构） |
| 查询语言 | SQL | 简单命令 |
| 速度 | 毫秒级 | 微秒级 |
| 数据量 | TB 级 | 受内存限制（GB 级） |
| 适用场景 | 持久化存储 | 缓存、会话、实时数据 |

### 1.2 Redis 在 Web 应用中的用途

```
┌────────────────────────────────────────────┐
│              Redis 常见用途                  │
├────────────────────────────────────────────┤
│ 1. 缓存 — 缓存数据库查询结果、API 响应       │
│ 2. 会话存储 — 用户登录状态（Session）         │
│ 3. 消息队列 — Celery 的消息中间件            │
│ 4. 排行榜 — 有序集合实现实时排名             │
│ 5. 计数器 — 文章浏览量、点赞数               │
│ 6. 限流 — API 请求频率限制                   │
│ 7. 分布式锁 — 防止并发冲突                   │
│ 8. 发布订阅 — 实时通知                       │
└────────────────────────────────────────────┘
```

---

## 二、安装 Redis

### 2.1 Windows（使用 Docker，推荐）

```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### 2.2 Windows（WSL 方式）

```bash
# 在 WSL 中
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

### 2.3 验证安装

```bash
# 连接 Redis CLI
redis-cli

# 测试连接
127.0.0.1:6379> PING
PONG

# 退出
127.0.0.1:6379> QUIT
```

---

## 三、Redis 数据结构

### 3.1 String（字符串）— 最基础的类型

```bash
# 设置和获取
SET name "张三"
GET name                    # "张三"

# 设置过期时间（秒）
SET token "abc123" EX 3600        # 1小时后过期
SETEX session_key 1800 "data"     # 等价写法
TTL token                          # 查看剩余秒数
EXPIRE token 7200                  # 修改过期时间

# 数字操作
SET counter 0
INCR counter               # 1（自增 1）
INCRBY counter 10          # 11（自增 10）
DECR counter               # 10（自减 1）
DECRBY counter 5           # 5

# 批量操作
MSET key1 "val1" key2 "val2" key3 "val3"
MGET key1 key2 key3

# 不存在时才设置（常用于分布式锁）
SETNX lock_key "locked"    # 仅当 lock_key 不存在时设置
```

**应用场景：** 缓存、计数器、分布式锁、会话存储

### 3.2 Hash（哈希）— 存储对象

```bash
# 设置字段
HSET user:1 name "张三"
HSET user:1 email "zs@example.com"
HSET user:1 age 25

# 批量设置
HMSET user:2 name "李四" email "ls@example.com" age 30

# 获取
HGET user:1 name                # "张三"
HMGET user:1 name email         # "张三" "zs@example.com"
HGETALL user:1                  # 获取所有字段和值

# 操作
HINCRBY user:1 age 1            # 年龄 +1
HDEL user:1 age                 # 删除字段
HEXISTS user:1 name             # 判断字段是否存在
HLEN user:1                     # 字段数量
```

**应用场景：** 存储用户信息、商品信息等结构化对象

### 3.3 List（列表）— 有序，可重复

```bash
# 从左/右推入
LPUSH queue "task1"         # 从左端推入
RPUSH queue "task2"         # 从右端推入
RPUSH queue "task3"

# 从左/右弹出
LPOP queue                  # 弹出最左边的
RPOP queue                  # 弹出最右边的

# 查看
LRANGE queue 0 -1           # 查看所有元素
LRANGE queue 0 2            # 查看前 3 个
LLEN queue                  # 列表长度
LINDEX queue 0              # 获取指定位置的元素

# 阻塞弹出（用于消息队列）
BLPOP queue 30              # 阻塞等待最多 30 秒
```

**应用场景：** 消息队列、最新消息列表、操作日志

### 3.4 Set（集合）— 无序，不重复

```bash
# 添加
SADD online_users "user:1" "user:2" "user:3"

# 查看
SMEMBERS online_users       # 所有成员
SCARD online_users          # 成员数量
SISMEMBER online_users "user:1"  # 是否存在

# 删除
SREM online_users "user:1"

# 集合运算
SADD group_a "user:1" "user:2" "user:3"
SADD group_b "user:2" "user:3" "user:4"

SINTER group_a group_b     # 交集: user:2, user:3
SUNION group_a group_b     # 并集: user:1, user:2, user:3, user:4
SDIFF group_a group_b      # 差集: user:1（在 a 不在 b）
```

**应用场景：** 在线用户、标签、共同好友、去重

### 3.5 Sorted Set（有序集合）— 带分数排序

```bash
# 添加（分数 + 成员）
ZADD leaderboard 100 "user:1"
ZADD leaderboard 85 "user:2"
ZADD leaderboard 92 "user:3"
ZADD leaderboard 78 "user:4"

# 排名（从高到低）
ZREVRANGE leaderboard 0 2 WITHSCORES   # 前 3 名

# 排名（从低到高）
ZRANGE leaderboard 0 -1 WITHSCORES     # 所有成员

# 查询
ZSCORE leaderboard "user:1"            # 查看分数
ZRANK leaderboard "user:1"             # 排名（升序，0 开始）
ZREVRANK leaderboard "user:1"          # 排名（降序）
ZCARD leaderboard                      # 成员数量

# 修改分数
ZINCRBY leaderboard 10 "user:2"        # 分数 +10

# 范围查询
ZRANGEBYSCORE leaderboard 80 100       # 分数在 80-100 之间的成员
ZCOUNT leaderboard 80 100              # 分数在 80-100 之间的数量
```

**应用场景：** 排行榜、优先级队列、延迟队列

---

## 四、通用命令

```bash
# 键管理
KEYS *                  # 查看所有键（生产环境勿用！）
SCAN 0 MATCH user:*     # 安全地遍历键
EXISTS key              # 判断键是否存在
DEL key1 key2           # 删除键
TYPE key                # 查看键的类型
RENAME old_key new_key  # 重命名键

# 过期时间
EXPIRE key 3600         # 设置 1 小时后过期
TTL key                 # 查看剩余秒数（-1=永不过期，-2=已过期/不存在）
PERSIST key             # 移除过期时间

# 数据库管理
SELECT 0                # 切换到数据库 0（共 16 个，0-15）
DBSIZE                  # 当前数据库的键数量
FLUSHDB                 # 清空当前数据库
FLUSHALL                # 清空所有数据库（危险！）
INFO                    # 查看 Redis 服务器信息
```

---

## 五、Python 操作 Redis

### 5.1 安装

```bash
pip install redis
```

### 5.2 基础操作

```python
import redis
import json

# 连接 Redis
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True,  # 自动将 bytes 解码为 str
)

# 测试连接
print(r.ping())  # True

# ===== String =====
r.set("name", "张三")
print(r.get("name"))          # "张三"

r.setex("token", 3600, "abc123")  # 1小时过期

r.set("counter", 0)
r.incr("counter")                  # 1
r.incrby("counter", 10)           # 11

# ===== Hash =====
r.hset("user:1", mapping={
    "name": "张三",
    "email": "zs@example.com",
    "age": 25,
})
print(r.hgetall("user:1"))
# {'name': '张三', 'email': 'zs@example.com', 'age': '25'}

# ===== List =====
r.rpush("tasks", "task1", "task2", "task3")
print(r.lrange("tasks", 0, -1))   # ['task1', 'task2', 'task3']
print(r.lpop("tasks"))             # 'task1'

# ===== Set =====
r.sadd("online", "user:1", "user:2", "user:3")
print(r.smembers("online"))
print(r.sismember("online", "user:1"))  # True

# ===== Sorted Set =====
r.zadd("leaderboard", {"user:1": 100, "user:2": 85, "user:3": 92})
print(r.zrevrange("leaderboard", 0, 2, withscores=True))
# [('user:1', 100.0), ('user:3', 92.0), ('user:2', 85.0)]
```

### 5.3 缓存模式

```python
import json
from typing import Optional

class CacheService:
    """简易缓存服务"""
    
    def __init__(self, redis_client: redis.Redis, default_ttl: int = 3600):
        self.redis = redis_client
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[dict]:
        """从缓存获取数据"""
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    def set(self, key: str, value: dict, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        ttl = ttl or self.default_ttl
        self.redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
    
    def delete(self, key: str) -> None:
        """删除缓存"""
        self.redis.delete(key)
    
    def get_or_set(self, key: str, fetch_func, ttl: Optional[int] = None) -> dict:
        """缓存不存在时调用 fetch_func 获取数据并缓存"""
        data = self.get(key)
        if data is not None:
            print(f"[Cache HIT] {key}")
            return data
        
        print(f"[Cache MISS] {key}")
        data = fetch_func()
        self.set(key, data, ttl)
        return data

# 使用示例
cache = CacheService(r)

def fetch_user_from_db(user_id: int) -> dict:
    """模拟从数据库查询用户"""
    print(f"查询数据库: user {user_id}")
    return {"id": user_id, "name": "张三", "email": "zs@example.com"}

# 第一次调用 — Cache MISS，查询数据库
user = cache.get_or_set("user:1", lambda: fetch_user_from_db(1))

# 第二次调用 — Cache HIT，直接返回缓存
user = cache.get_or_set("user:1", lambda: fetch_user_from_db(1))
```

### 5.4 管道（Pipeline）— 批量操作提高性能

```python
# 不用管道：每条命令一次网络往返
r.set("key1", "val1")   # 一次网络往返
r.set("key2", "val2")   # 一次网络往返
r.set("key3", "val3")   # 一次网络往返
# 共 3 次网络往返

# 用管道：所有命令打包成一次网络往返
pipe = r.pipeline()
pipe.set("key1", "val1")
pipe.set("key2", "val2")
pipe.set("key3", "val3")
results = pipe.execute()
# 只有 1 次网络往返，性能提升显著
```

---

## 六、Redis 在 TaskFlow 项目中的应用规划

```
TaskFlow 项目中 Redis 的用途：

1. API 缓存
   键: "api:tasks:list:page=1"
   值: JSON 序列化的任务列表
   过期: 5 分钟

2. 用户会话
   键: "session:{session_id}"
   值: 用户信息 JSON
   过期: 24 小时

3. 任务统计缓存
   键: "stats:project:{project_id}"
   值: {"total": 50, "completed": 30, ...}
   过期: 10 分钟

4. 在线用户
   键: "online_users"
   类型: Set
   值: {"user:1", "user:2", ...}

5. Celery 消息队列
   Redis 作为 Celery 的 Broker（消息中间件）

6. API 限流
   键: "rate_limit:{user_id}:{endpoint}"
   值: 请求次数
   过期: 1 分钟
```

---

## 七、练习

### 基础练习

1. 安装 Redis（Docker 方式），用 redis-cli 连接并测试 PING
2. 用 redis-cli 练习五种数据结构的基本操作
3. 用 Python redis 库连接 Redis，实现字符串、哈希、列表的基本操作

### 进阶练习

4. 用 Python 实现一个 `CacheService` 类，支持 `get`、`set`、`delete`、`get_or_set` 方法
5. 用 Sorted Set 实现一个简易排行榜：添加玩家分数、查看 Top 10、更新分数
6. 用 Redis 实现一个简易的 API 限流器：每个用户每分钟最多请求 60 次

## 阶段总结

至此，第 02 阶段全部完成。你已经掌握：

- ✅ SQL 基础（CRUD、WHERE、ORDER BY、聚合）
- ✅ SQL 进阶（JOIN、子查询、CTE、窗口函数）
- ✅ PostgreSQL 安装配置与特有功能（JSONB、数组、UUID）
- ✅ 数据库设计（范式、ER 图、索引、事务）
- ✅ Redis 五种数据结构与 Python 操作

**下一阶段** → 第 03 阶段：Django 核心（项目结构/路由/视图/ORM/Admin）
