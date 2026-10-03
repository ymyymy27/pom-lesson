# 第2课：API 高级模式

## 1. 幂等性（Idempotency）

```
同一请求执行多次 = 执行一次的效果

HTTP 方法天然幂等：GET、PUT、DELETE
POST 不幂等 → 需要 Idempotency Key

场景：支付、下单、创建资源
  客户端网络超时 → 重试 → 不能重复扣款
```

```python
# 客户端
headers = {"Idempotency-Key": "uuid-v4-unique-key"}
response = requests.post("/api/v1/orders", json=order_data, headers=headers)

# 服务端
def create_order(request):
    key = request.headers.get("Idempotency-Key")
    if key:
        existing = cache.get(f"idempotency:{key}")
        if existing:
            return existing  # 返回之前的结果

    order = OrderService.create(request.data)
    if key:
        cache.set(f"idempotency:{key}", order, ttl=86400)
    return order
```

---

## 2. 错误处理规范

```python
# 错误码体系
ERROR_CODES = {
    "VALIDATION_ERROR": 422,      # 参数验证失败
    "AUTHENTICATION_FAILED": 401, # 未登录
    "PERMISSION_DENIED": 403,     # 无权限
    "RESOURCE_NOT_FOUND": 404,    # 资源不存在
    "CONFLICT": 409,              # 冲突（重复、状态不对）
    "RATE_LIMITED": 429,          # 限流
    "INTERNAL_ERROR": 500,        # 服务端错误
}

# 好的错误响应
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      {"field": "email", "message": "Invalid email format", "code": "invalid_format"},
      {"field": "password", "message": "Must be at least 8 characters", "code": "too_short"}
    ]
  }
}

# 规则：
# - 4xx：客户端问题，message 可以具体
# - 5xx：服务端问题，message 要模糊（不暴露内部信息）
# - 始终返回 request_id 方便排查
```

---

## 3. Rate Limiting

```
响应 Header：
  X-RateLimit-Limit: 1000       # 窗口内总配额
  X-RateLimit-Remaining: 998    # 剩余配额
  X-RateLimit-Reset: 1690000000 # 重置时间戳

超限响应：429 Too Many Requests
  Retry-After: 60

分级限流：
  匿名用户：100 req/min
  认证用户：1000 req/min
  Premium：10000 req/min
  按 API Key 限流（开放平台）
```

---

## 4. Webhook（事件回调）

```
App 发生事件 → POST 到用户注册的 URL

注册：
  POST /api/v1/webhooks
  {"url": "https://client.com/hook", "events": ["task.created", "task.completed"]}

推送：
  POST https://client.com/hook
  Headers:
    X-Webhook-Signature: HMAC-SHA256(payload, secret)
    X-Webhook-ID: wh_abc123
    X-Webhook-Timestamp: 1690000000
  Body:
    {"event": "task.created", "data": {...}}

重试策略：
  失败 → 1min → 5min → 30min → 2h → 24h（最多 5 次）
  签名验证 + Timestamp 防重放（5 分钟窗口）
```

---

## 5. 批量操作

```
# 批量创建
POST /api/v1/tasks/batch
{"tasks": [{...}, {...}, {...}]}

# 批量更新
PATCH /api/v1/tasks/batch
{"ids": ["task_1", "task_2"], "update": {"status": "done"}}

# 响应
{
  "data": {
    "succeeded": [{"id": "task_1"}, {"id": "task_2"}],
    "failed": [{"id": "task_3", "error": "not found"}]
  }
}
```

---

## 6. 动手练习

1. 设计支付 API 的幂等性方案（含 Idempotency-Key 流程）
2. 为 TaskFlow 设计 Webhook 注册和推送协议
3. 定义项目的错误码体系（至少 10 个）

---

**下一课** → [03_graphql_grpc_async.md](03_graphql_grpc_async.md)
