# 第3课：弹性模式与混沌工程

## 1. 为什么需要弹性设计？

### 一句话解释

**弹性（Resilience）= 系统在部分组件故障时仍能提供服务，且能快速恢复。**

### 分布式系统的默认假设

```
❌ 网络是可靠的
❌ 延迟为零
❌ 带宽无限
❌ 网络是安全的
❌ 拓扑不变
❌ 只有一个管理员
❌ 传输不丢包
❌ 时钟同步

—— 分布式计算的 8 个谬误（Fallacies）
```

**结论：** 故障不是「会不会发生」，而是「何时发生」。架构设计必须内置容错。

---

## 2. 弹性模式全景

```
请求进入
    ↓
┌─────────┐   过载保护    ┌─────────┐   下游故障    ┌─────────┐
│  限流    │─────────────▷│  熔断    │─────────────▷│  降级    │
│ Rate    │              │ Circuit │              │ Fallback│
│ Limit   │              │ Breaker │              │         │
└─────────┘              └─────────┘              └─────────┘
    ↓                         ↓                         ↓
  保护自身                 快速失败                   保核心功能
```

| 模式 | 解决什么问题 | 一句话 |
|------|-------------|--------|
| 超时 | 下游挂死拖垮调用方 | 不等 forever |
| 重试 | 瞬时网络抖动 | 有限次 + 退避 |
| 熔断 | 下游持续故障 | 停止调用，快速失败 |
| 限流 | 流量过载 | 保护系统不被打垮 |
| 降级 | 非核心功能故障 | 关次要，保核心 |
| 舱壁隔离 | 故障扩散 | 资源池隔离 |
| 幂等 | 重试导致重复 | 同一操作多次 = 一次 |

---

## 3. 超时（Timeout）

### 原则

```
每个外部调用都必须设超时，包括：
  - HTTP 请求
  - 数据库查询
  - Redis / MQ 操作
  - 文件 I/O
```

### 超时层级

```
Client timeout     3000ms  ← 用户能等的上限
    ↓
Gateway timeout    2500ms  ← 留 500ms 给客户端
    ↓
Service timeout    2000ms
    ↓
DB query timeout   1000ms  ← 最内层最短
```

**规则：** 外层超时 > 内层超时之和，否则外层先超时，内层还在跑（资源泄漏）。

### Python 示例

```python
import httpx

async def fetch_recommendations(user_id: int) -> list:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"http://rec-svc/users/{user_id}")
            return resp.json()
    except httpx.TimeoutException:
        return []  # 降级：无推荐也能用
```

---

## 4. 重试（Retry）

### 何时重试

```
✅ 网络超时、连接重置
✅ HTTP 502/503/504
✅ 数据库死锁（有限次）

❌ HTTP 400/401/403/404（客户端错误，重试无意义）
❌ 业务逻辑错误（余额不足）
❌ 非幂等操作且无幂等键
```

### 退避策略

```
指数退避 + 抖动（Exponential Backoff + Jitter）

第 1 次：等 100ms ± 随机
第 2 次：等 200ms ± 随机
第 3 次：等 400ms ± 随机
最多 3 次 → 放弃，走降级
```

```python
import random
import time

def retry_with_backoff(func, max_retries=3, base_delay=0.1):
    for attempt in range(max_retries):
        try:
            return func()
        except TransientError:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.05)
            time.sleep(delay)
```

---

## 5. 熔断器（Circuit Breaker）

### 三种状态

```
        失败率超阈值
  ┌──────────────────────┐
  │                      ▼
 Closed ──────────▷ Open（拒绝所有请求）
  ▲                      │
  │    探测成功           │ 冷却期结束
  │                      ▼
  └──────────── Half-Open（放行少量探测请求）
```

| 状态 | 行为 |
|------|------|
| Closed | 正常调用，统计失败率 |
| Open | 直接返回错误/降级，不调用下游 |
| Half-Open | 放行 1-5 个请求探测，成功 → Closed，失败 → Open |

### 参数建议

```
失败率阈值：50%（滑动窗口 10 秒）
最小请求数：20（样本太少不触发）
Open 持续时间：30 秒
Half-Open 探测数：3
```

### Python 简化实现

```python
from enum import Enum
from datetime import datetime, timedelta

class State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = State.CLOSED
        self.opened_at = None

    def call(self, func, fallback=None):
        if self.state == State.OPEN:
            if datetime.now() - self.opened_at > timedelta(seconds=self.recovery_timeout):
                self.state = State.HALF_OPEN
            else:
                return fallback() if fallback else None

        try:
            result = func()
            if self.state == State.HALF_OPEN:
                self.state = State.CLOSED
                self.failure_count = 0
            return result
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = State.OPEN
                self.opened_at = datetime.now()
            raise
```

**工具：** resilience4j（Java）、Polly（.NET）、pybreaker（Python）

---

## 6. 限流（Rate Limiting）

### 常见算法

| 算法 | 特点 | 适用 |
|------|------|------|
| 固定窗口 | 简单，边界突发 | 粗粒度限流 |
| 滑动窗口 | 更平滑 | API 网关 |
| 令牌桶 | 允许突发 | 大多数 API |
| 漏桶 | 严格匀速 | 消息消费 |

### 令牌桶原理

```
桶容量：100 令牌
补充速率：10 令牌/秒

请求到达 → 取 1 令牌 → 有则通过，无则拒绝（429）
允许短时突发（桶里有存货时）
```

### 限流维度

```
按 IP：防 DDoS
按 User ID：防单用户滥用
按 API Key：SaaS 套餐配额
按接口：热点接口单独限
全局：保护整体系统
```

### 分层限流

```
CDN/WAF 层  → 10000 req/s（挡大流量）
API Gateway → 1000 req/s（按租户）
Service 层  → 100 req/s（按接口）
```

---

## 7. 降级（Degradation）

### 降级策略

```
功能降级：
  推荐系统挂了 → 展示默认热门列表
  评论加载失败 → 隐藏评论区，核心内容仍可用
  搜索慢 → 只搜标题，不搜正文

数据降级：
  缓存未命中 → 返回过期缓存（stale-while-revalidate）
  实时数据不可用 → 展示 5 分钟前的快照

体验降级：
  图片加载失败 → 占位图
  视频高清不可用 → 切换标清
```

### 降级开关

```python
class FeatureFlags:
    def __init__(self, redis_client):
        self.redis = redis_client

    def is_enabled(self, flag: str, default=True) -> bool:
        val = self.redis.get(f"flag:{flag}")
        return val != b"off" if val else default

# 使用
if flags.is_enabled("recommendation_service"):
    recs = await rec_service.get(user_id)
else:
    recs = DEFAULT_HOT_ITEMS  # 降级
```

**关键：** 降级方案要提前设计并测试，不能故障时临时想。

---

## 8. 舱壁隔离（Bulkhead）

### 类比

```
船舱隔离：一个舱进水，其他舱不受影响
```

### 线程池隔离

```
┌─────────────────────────────────────┐
│           应用进程                    │
│  ┌──────────┐  ┌──────────┐         │
│  │ 核心池    │  │ 非核心池  │         │
│  │ 50 线程  │  │ 20 线程  │         │
│  │ 订单/支付 │  │ 推荐/统计 │         │
│  └──────────┘  └──────────┘         │
└─────────────────────────────────────┘

推荐服务慢 → 只耗尽非核心池 → 订单/支付不受影响
```

### 连接池隔离

```
PostgreSQL 连接池：
  核心服务：max=50
  报表服务：max=10（防止慢查询拖垮主业务）
```

---

## 9. 组合实战：TaskFlow 通知服务

```
场景：Task 分配后发送通知（邮件 + 推送 + Slack）

设计：
  1. 主流程：Task 状态变更 → 写 DB → 发 Domain Event → 返回 200
  2. 通知消费：异步处理，与主流程解耦
  3. 每个渠道独立：
     - 超时 3s
     - 重试 2 次（指数退避）
     - 熔断：连续 5 次失败 → 跳过该渠道 60s
  4. 降级：Slack 不可用 → 只发邮件，记录失败待补偿
  5. 限流：单用户 10 条/分钟，防 @提及 轰炸
```

```python
async def notify_task_assigned(task_id: int, assignee_id: int):
    channels = [
        ("email", send_email, timeout=5),
        ("push", send_push, timeout=3),
        ("slack", send_slack, timeout=3),
    ]
    for name, sender, timeout in channels:
        if not circuit_breakers[name].is_closed():
            logger.warning(f"Skip {name}: circuit open")
            continue
        try:
            await asyncio.wait_for(sender(task_id, assignee_id), timeout=timeout)
        except Exception as e:
            circuit_breakers[name].record_failure()
            await dead_letter_queue.put({"channel": name, "task_id": task_id, "error": str(e)})
```

---

## 10. 混沌工程（Chaos Engineering）

### 是什么？

**在生产或类生产环境中，主动注入故障，验证系统弹性。**

```
不是「等故障发生再修」
而是「主动制造小故障，发现大隐患」
```

### 原则（Netflix Chaos Engineering）

1. 建立稳态假设（正常时系统的关键指标）
2. 引入真实世界的事件（服务器宕机、网络延迟）
3. 在生产中运行实验（从小规模开始）
4. 自动运行实验（持续验证）
5. 最小化爆炸半径（先 Canary，再扩大）

### 常见实验

| 实验 | 注入 | 验证 |
|------|------|------|
| 实例终止 | Kill 1 个 Pod | LB 剔除，无 5xx 飙升 |
| 网络延迟 | +500ms 到 DB | 超时有降级，无级联 |
| 依赖故障 | Mock 503 | 熔断生效，降级正常 |
| 资源耗尽 | CPU 100% | 限流保护核心接口 |
| 磁盘满 | 写满 /tmp | 日志轮转，服务不挂 |

### 成熟度路径

```
Level 0：有 Runbook，故障后手动修
Level 1：有监控告警，MTTR < 1h
Level 2：有熔断/降级，核心功能有 Fallback
Level 3：定期 Game Day（模拟故障演练）
Level 4：自动化混沌实验（Chaos Mesh / Litmus）
```

---

## 11. 弹性设计 Checklist

设计任何服务时，逐项检查：

```
□ 每个外部调用有超时吗？
□ 重试有次数限制和退避吗？幂等吗？
□ 下游故障会熔断吗？还是无限等待？
□ 流量突增有限流吗？分层了吗？
□ 非核心功能有降级方案吗？测过吗？
□ 线程/连接池有隔离吗？
□ 有 Dead Letter Queue 处理最终失败吗？
□ 监控覆盖：熔断状态、限流触发、降级次数？
```

---

## 12. 动手练习

1. 为 TaskFlow 的「文件附件上传」设计弹性方案（含超时、重试、降级）
2. 画出熔断器三种状态转换图，标注触发条件
3. 设计一个 Game Day 场景：「Redis 完全不可用」，列出预期行为和验证点
4. 用 Python 实现一个简单的令牌桶限流器

---

## 13. 自检清单

- [ ] 能解释超时、重试、熔断、限流、降级的区别和配合
- [ ] 知道重试必须配合幂等或幂等键
- [ ] 理解熔断器三种状态及转换条件
- [ ] 能设计分层限流策略
- [ ] 了解混沌工程的基本原理和实验类型
- [ ] 会用弹性设计 Checklist 审查架构

---

## 14. 延伸阅读

- 《Release It!》（Michael Nygard）— 弹性模式经典
- Netflix Chaos Engineering 官网
- Google SRE Book — 过载保护章节
- 关联：`learn-architecture/02_microservices_and_distributed.md` — 分布式容错
- 关联：`learn-architecture/03_event_driven_and_data.md` — 异步解耦

**恭喜完成可靠性工程模块！** → 返回 [`README.md`](README.md) 或继续 [`projects/capstone_taskflow.md`](../projects/capstone_taskflow.md)
