# 第2课：五大数据结构

> 命令速查见 [`00_redis_syntax.md`](00_redis_syntax.md)

## 1. String（字符串）

最基础类型，可存文本、数字、JSON 字符串。

```bash
SET name "张三"
GET name
SET counter 0
INCR counter              # 1
INCRBY counter 10         # 11
SETEX token 3600 "abc"    # 带过期
SETNX lock:1 "held"       # 不存在才设置（锁的基础）
```

| 场景 | 示例键 |
|------|--------|
| 缓存 JSON | `myapp:cache:article:42` |
| 验证码 | `myapp:otp:13800138000` |
| 计数器 | `myapp:views:article:42` |
| 分布式锁 | `myapp:lock:order:1001` |

---

## 2. Hash（哈希）

适合存「对象」—— 一个 Key 下多个 field，比多个 String 更省内存。

```bash
HSET user:1 name "张三" email "zs@example.com" age 25
HGET user:1 name
HGETALL user:1
HINCRBY user:1 age 1
HDEL user:1 age
```

| 场景 | 说明 |
|------|------|
| 用户资料缓存 | `user:{id}` → name, avatar, role |
| 购物车 | `cart:{user_id}` → sku_id → quantity |

---

## 3. List（列表）

有序、可重复；双端进出，适合队列与最新列表。

```bash
RPUSH logs "login" "view" "logout"
LRANGE logs 0 -1
LPOP logs
BLPOP queue 30              # 阻塞 30 秒等待元素
```

| 场景 | 模式 |
|------|------|
| 简单队列 | `RPUSH` + `BLPOP` |
| 最新 N 条 | `LPUSH` + `LTRIM 0 99` |
| 时间线（简单版） | List 存 ID，详情另查 |

---

## 4. Set（集合）

无序、不重复；支持交并差。

```bash
SADD online user:1 user:2 user:3
SISMEMBER online user:1     # 1
SREM online user:1
SADD tag:article:1 python redis web
SINTER tag:article:1 tag:article:2   # 共同标签
```

| 场景 | 说明 |
|------|------|
| 在线用户 | `SADD online_users {uid}` |
| 标签 | 文章标签、用户兴趣 |
| 去重 | 已读消息 ID 集合 |

---

## 5. Sorted Set（有序集合）

每个成员带 **score**，按分数排序。

```bash
ZADD leaderboard 100 "alice" 85 "bob" 92 "carol"
ZREVRANGE leaderboard 0 2 WITHSCORES    # Top 3
ZINCRBY leaderboard 10 "bob"
ZSCORE leaderboard "alice"
ZREVRANK leaderboard "alice"          # 排名（0=第一）
```

| 场景 | score 含义 |
|------|------------|
| 排行榜 | 积分、销量 |
| 延迟队列 | 执行时间戳 |
| 优先级任务 | 优先级数值 |

---

## 6. 结构选型决策树

```
需要排序？
  ├─ 是 → 需要唯一成员？
  │        ├─ 是 → Sorted Set
  │        └─ 否 → List
  └─ 否 → 需要唯一？
           ├─ 是 → Set
           └─ 否 → 是对象多个字段？
                    ├─ 是 → Hash
                    └─ 否 → String
```

---

## 7. Python 示例

```python
import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# String
r.set("page:views", 0)
r.incr("page:views")

# Hash
r.hset("user:1", mapping={"name": "张三", "role": "admin"})
print(r.hgetall("user:1"))

# List
r.rpush("recent:actions", "login", "create_post")
print(r.lrange("recent:actions", 0, -1))

# Set
r.sadd("online", "u1", "u2")
print(r.sismember("online", "u1"))

# Sorted Set
r.zadd("scores", {"player_a": 100, "player_b": 85})
print(r.zrevrange("scores", 0, 0, withscores=True))
```

---

## 8. 练习

1. CLI 练习五种结构各 3 条命令
2. 用 Sorted Set 实现排行榜：添加 5 个玩家、查 Top 3、给某人加分
3. 用 Set 模拟「文章标签」，求两篇文章的共同标签（`SINTER`）
4. 用 Hash 缓存一个用户对象，用 `HINCRBY` 增加 login_count 字段

👉 下一课：[03_python_redis.md](03_python_redis.md)
