> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第5课：Session、限流、分布式锁与消息队列

## 1. Session 存储

JWT 无状态；Session 有状态，服务端存登录信息，适合「主动失效」场景。

```python
import json
import secrets

def create_session(r, user_id: int, ttl: int = 86400) -> str:
    session_id = secrets.token_urlsafe(32)
    key = f"myapp:session:{session_id}"
    r.setex(key, ttl, json.dumps({"user_id": user_id}))
    return session_id

def get_session(r, session_id: str) -> dict | None:
    raw = r.get(f"myapp:session:{session_id}")
    return json.loads(raw) if raw else None

def destroy_session(r, session_id: str) -> None:
    r.delete(f"myapp:session:{session_id}")
```

对比 JWT：Session 占 Redis 内存，但可立即踢下线；JWT 难撤销（需黑名单，又是 Redis String）。

---

## 2. API 限流

### 2.1 固定窗口（简单易实现）

```python
def is_rate_limited(r, key: str, limit: int, window: int) -> bool:
    """返回 True 表示已超限"""
    count = r.incr(key)
    if count == 1:
        r.expire(key, window)
    return count > limit

# 每 IP 每分钟 60 次
# key = f"myapp:ratelimit:{ip}:/api/login"
```

### 2.2 滑动窗口（更平滑）

见 `practice/rate_limiter.py` — 用 Sorted Set 存请求时间戳。

---

## 3. 分布式锁

多实例部署时，内存锁无效；用 Redis `SET NX EX`：

```python
# 加锁
ok = r.set("myapp:lock:resource:1", token, nx=True, ex=30)

# 释放必须用 Lua — 只删自己的锁
UNLOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""
unlock = r.register_script(UNLOCK_SCRIPT)
unlock(keys=["myapp:lock:resource:1"], args=[token])
```

完整实现见 `practice/distributed_lock.py`。

**注意：**

- 必须设过期，防死锁
- 业务耗时应小于锁 TTL，或实现续期
- 复杂场景考虑 Redlock 或数据库悲观锁

---

## 4. 发布订阅（Pub/Sub）

```python
# 订阅方（独立进程）
pubsub = r.pubsub()
pubsub.subscribe("notifications")
for message in pubsub.listen():
    if message["type"] == "message":
        print(message["data"])

# 发布方
r.publish("notifications", json.dumps({"event": "new_comment", "id": 42}))
```

特点：fire-and-forget，订阅者离线则消息丢失。需持久化时用 **Stream** 或消息队列（Kafka/RabbitMQ）。

---

## 5. Redis 作为 Celery Broker

```
Django/FastAPI  →  Celery Producer  →  Redis (List/Stream)  →  Celery Worker
```

```python
# celery_app.py 配置片段
broker_url = "redis://localhost:6379/1"
result_backend = "redis://localhost:6379/2"
```

Celery 把任务序列化后推入 Redis；Worker `BLPOP` 消费。详细 Celery API 见全栈 `stage-06-celery-cache`；本课理解 **Redis 充当中间件** 即可。

---

## 6. 能力对照表

| 需求 | 结构/命令 | 本课脚本 |
|------|-----------|----------|
| 登录 Session | String + EX | 上文示例 |
| 接口限流 | INCR + EX / ZSet | `rate_limiter.py` |
| 并发写保护 | SET NX + Lua | `distributed_lock.py` |
| 实时广播 | Pub/Sub | 上文示例 |
| 异步任务 | List + Celery | 配置说明 |

---

## 7. 练习

```bash
cd 03-进阶专题/02-部署与工程运维/Redis/practice
python rate_limiter.py
python distributed_lock.py
```

1. 实现 Session：创建 / 读取 / 销毁
2. 用固定窗口限制某接口 10 次/分钟
3. 用分布式锁保护「库存扣减」模拟函数，开 10 线程仅成功扣减 1 次

👉 下一课：[06_practical_web_app.md](<06-第6课实战 — FastAPI + Redis.md>)\
👉 部署与协作专题（第 6 课后建议学习）：[07_logical_databases_and_isolation.md](07-第7课逻辑库隔离策略与实例规划.md)
