# 第4课：案例 — 电商系统

> 综合案例：串联 DDD 建模、库存、订单、支付、搜索，适合作为阶段总结。

## 1. 需求澄清

### 功能需求

```
- 商品浏览、搜索、详情
- 购物车
- 下单、支付
- 库存管理
- 订单状态跟踪
- 可选：秒杀、优惠券、推荐
```

### 非功能需求（假设）

| 指标 | 假设值 |
|------|--------|
| DAU | 5000 万 |
| 下单 | 50 万单/天（峰值 10 倍） |
| 商品 SKU | 1000 万 |
| 搜索 | p99 < 200ms |
| 下单 | 强一致（不能超卖） |
| 可用性 | 99.95% |

---

## 2. DDD 限界上下文

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Catalog    │  │   Order     │  │  Payment    │
│  商品目录    │  │  订单       │  │  支付       │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
│  Inventory  │  │  Shipping   │  │  Promotion  │
│  库存       │  │  物流       │  │  促销       │
└─────────────┘  └─────────────┘  └─────────────┘

上下文关系：
  Order → Inventory：Customer-Supplier（下单扣库存）
  Order → Payment：Customer-Supplier（下单后支付）
  Catalog → Search：Published Language（商品数据同步到搜索）
```

→ 详见 `learn-domain-design/`

---

## 3. High-Level 架构

```
                         ┌─────────────┐
  Client ──────────────→ │ API Gateway │
                         └──────┬──────┘
                                │
        ┌───────────┬───────────┼───────────┬───────────┐
        ↓           ↓           ↓           ↓           ↓
  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ Catalog  │ │  Order   │ │ Inventory│ │ Payment  │ │ Search   │
  │ Service  │ │ Service  │ │ Service  │ │ Service  │ │ Service  │
  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
       │            │            │            │            │
       ↓            ↓            ↓            ↓            ↓
     PG+Redis     PG          PG+Redis      PG         Elasticsearch
                              │
                         ┌────┴────┐
                         │  Kafka  │ ← 领域事件总线
                         └─────────┘
```

---

## 4. 核心流程：下单

```
用户点击「提交订单」：

  1. Order Service 创建订单（状态：Pending）
  2. 发布 OrderCreated 事件
  3. Inventory Service 消费 → 预扣库存（Reserve）
     - 成功 → 发布 InventoryReserved
     - 失败（库存不足）→ 发布 InventoryFailed → Order 取消
  4. Payment Service 消费 InventoryReserved → 发起支付
     - 成功 → PaymentCompleted → Order 状态 → Paid
     - 失败/超时 → 发布 PaymentFailed → 释放库存
  5. Shipping Service 消费 PaymentCompleted → 创建物流单

Saga 编排：
  OrderCreated → ReserveInventory → ProcessPayment → CreateShipment
  任一步失败 → 逆序补偿（ReleaseInventory, CancelOrder）
```

### 库存防超卖

```
❌ SELECT count → if > 0 → UPDATE（并发会超卖）

✅ 方案1：数据库乐观锁
  UPDATE inventory SET stock = stock - 1, version = version + 1
  WHERE sku_id = ? AND stock > 0 AND version = ?

✅ 方案2：Redis 预扣 + 异步同步 DB
  DECR stock:{sku_id}  （原子操作）
  if result >= 0 → 扣减成功
  else → INCR 回滚 → 库存不足

✅ 方案3：秒杀专用 — Redis + Lua 脚本原子扣减
```

---

## 5. 搜索服务

```
Catalog Service ──CDC/事件──→ Elasticsearch

搜索索引：
  {
    "sku_id": "12345",
    "title": "iPhone 15 Pro",
    "category": "electronics/phone",
    "price": 7999,
    "brand": "Apple",
    "tags": ["5G", "旗舰"],
    "sales_count": 50000
  }

查询：
  - 关键词搜索（match）
  - 过滤（category, price range）
  - 排序（price, sales_count, relevance）
  - 分页（from/size 或 search_after）
```

---

## 6. 数据模型（Order 聚合）

```sql
-- 订单（聚合根）
CREATE TABLE orders (
    id           BIGINT PRIMARY KEY,
    user_id      BIGINT NOT NULL,
    status       VARCHAR(20),  -- pending/paid/shipped/completed/cancelled
    total_amount DECIMAL(10,2),
    created_at   TIMESTAMP,
    version      INT DEFAULT 0  -- 乐观锁
);

-- 订单项（聚合内实体）
CREATE TABLE order_items (
    id       BIGINT PRIMARY KEY,
    order_id BIGINT REFERENCES orders(id),
    sku_id   BIGINT,
    quantity INT,
    price    DECIMAL(10,2)
);

-- 库存
CREATE TABLE inventory (
    sku_id   BIGINT PRIMARY KEY,
    stock    INT NOT NULL,
    reserved INT DEFAULT 0,  -- 预扣库存
    version  INT DEFAULT 0
);
```

---

## 7. 秒杀场景（扩展）

```
1000 件商品，100 万人抢：

1. 静态化商品页（CDN）
2. 答题/验证码（防机器人）
3. 请求进入消息队列（削峰）
4. Redis 原子扣减库存
5. 扣减成功 → 异步创建订单
6. 前端轮询/WebSocket 通知结果

关键：不在 DB 层做秒杀，Redis + MQ 扛流量
```

---

## 8. 容量估算

```
下单 QPS：50万/86400 × 10 ≈ 60/s（峰值）
  → 单 Order Service 实例可扛，但 Payment 需独立扩展

商品浏览 QPS：5000万 DAU × 50 页/天 / 86400 ≈ 3 万/s
  → CDN + 缓存 + 读副本

搜索 QPS：~1 万/s → Elasticsearch 3 节点集群

Kafka：OrderCreated 等事件 ~100/s，轻松
```

---

## 9. 动手练习

1. 画出下单 Saga 的完整流程和补偿路径
2. 设计秒杀系统的架构（从 100 万 QPS 到最终 1000 个订单）
3. 结合 `learn-domain-design/`，为电商画上下文地图

---

## 10. 自检清单

- [ ] 能划分电商的限界上下文
- [ ] 理解下单 Saga 和库存预扣
- [ ] 知道三种防超卖方案及适用场景
- [ ] 能设计搜索同步链路
- [ ] 了解秒杀的削峰和 Redis 原子扣减

---

**阶段总结** → 回到 [`STUDY_ROADMAP.md`](../STUDY_ROADMAP.md) 阶段五检验
