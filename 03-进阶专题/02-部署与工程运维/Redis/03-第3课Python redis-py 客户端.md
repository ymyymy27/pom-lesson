> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第3课：Python redis-py 客户端

## 1. 安装与连接

```bash
pip install redis
```

### 1.1 基础连接

```python
import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True,   # 返回 str 而非 bytes
    socket_connect_timeout=5,
    socket_timeout=5,
)

assert r.ping() is True
```

### 1.2 URL 连接（推荐）

与 Django、Celery 配置风格一致：

```python
r = redis.from_url(
    "redis://localhost:6379/0",
    decode_responses=True,
)

# 带密码：redis://:password@localhost:6379/0
```

### 1.3 连接池

每个请求新建 TCP 连接开销大；生产环境用连接池：

```python
pool = redis.ConnectionPool.from_url(
    "redis://localhost:6379/0",
    max_connections=20,
    decode_responses=True,
)
r = redis.Redis(connection_pool=pool)
```

**原则：** 全局一个 Pool，应用内复用 `Redis` 实例。

---

## 2. 常用 API 模式

### 2.1 字符串与 JSON

Redis 只存字符串；复杂对象需序列化：

```python
import json

def cache_set(key: str, data: dict, ttl: int = 3600):
    r.setex(key, ttl, json.dumps(data, ensure_ascii=False))

def cache_get(key: str) -> dict | None:
    raw = r.get(key)
    return json.loads(raw) if raw else None
```

### 2.2 批量操作

```python
r.mset({"k1": "v1", "k2": "v2"})
print(r.mget("k1", "k2"))    # ['v1', 'v2']
```

### 2.3 条件写入

```python
# 仅当不存在时设置 — 分布式锁第一步
locked = r.set("myapp:lock:job", "1", nx=True, ex=30)
if locked:
    try:
        ...  # 临界区
    finally:
        r.delete("myapp:lock:job")
```

---

## 3. Pipeline — 减少网络往返

```python
# ❌ 3 次 RTT
r.set("a", 1)
r.set("b", 2)
r.set("c", 3)

# ✅ 1 次 RTT
pipe = r.pipeline()
pipe.set("a", 1)
pipe.set("b", 2)
pipe.set("c", 3)
pipe.execute()
```

适用：批量写入缓存、批量计数、导入数据。

---

## 4. 事务 MULTI / EXEC（了解）

```python
pipe = r.pipeline(transaction=True)
pipe.multi()
pipe.incr("balance")
pipe.decr("pending")
results = pipe.execute()
```

注意：Redis 事务**不会**在命令冲突时回滚；复杂原子逻辑更常用 **Lua 脚本**（第 5 课）。

---

## 5. 错误处理

```python
import redis

try:
    r = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    r.ping()
except redis.ConnectionError:
    print("Redis 不可用，降级走数据库")
except redis.TimeoutError:
    print("Redis 超时")
```

**生产建议：**

- 缓存失败不应拖垮主流程（降级读 DB）
- 设置合理 `socket_timeout`
- 健康检查：`cache.set('_ping', '1', ex=5)` + `get`

---

## 6. 封装 CacheService

见 `practice/cache_service.py`：

```python
"""简易缓存服务 — 可直接运行: python cache_service.py"""
import json
import redis
from typing import Any, Callable, Optional

class CacheService:
    def __init__(self, client: redis.Redis, prefix: str = "myapp:cache", default_ttl: int = 3600):
        self.redis = client
        self.prefix = prefix
        self.default_ttl = default_ttl

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    def get(self, key: str) -> Optional[Any]:
        raw = self.redis.get(self._key(key))
        return json.loads(raw) if raw else None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self.redis.setex(self._key(key), ttl or self.default_ttl, json.dumps(value, ensure_ascii=False))

    def delete(self, key: str) -> None:
        self.redis.delete(self._key(key))

    def get_or_set(self, key: str, fetch: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached
        data = fetch()
        self.set(key, data, ttl)
        return data
```

---

## 7. 练习

1. 用连接池连接 Redis，对比有/无 Pipeline 写入 1000 个键的耗时
2. 实现 `CacheService`，对模拟 DB 查询函数做 `get_or_set`
3. 写一个 `health_check(redis_client) -> bool` 函数

```bash
cd 03-进阶专题/02-部署与工程运维/Redis/practice
python cache_service.py
```

👉 下一课：[04_caching_patterns.md](04-第4课缓存模式与常见问题.md)
