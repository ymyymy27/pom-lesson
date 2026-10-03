# 第3课：案例 — 社交 Feed（Timeline）

> Twitter / 微博 / Instagram 首页信息流的设计经典题。

## 1. 需求澄清

### 功能需求

```
- 用户发推（Post）
- 关注其他用户
- 首页 Feed：看到关注的人的推文，按时间倒序
- 可选：点赞、评论、转发
```

### 非功能需求（假设）

| 指标 | 假设值 |
|------|--------|
| DAU | 3 亿 |
| 每用户每天发 2 条 | 6 亿写/天 |
| 每用户每天刷 20 次 Feed | 60 亿读/天 |
| Feed 延迟 | p99 < 500ms |
| 名人粉丝 | 最高 5000 万 |

---

## 2. 容量估算

```
写 QPS：6×10⁸ / 86400 ≈ 7000/s（峰值 ×3 ≈ 2 万/s）
读 QPS：6×10⁹ / 86400 ≈ 7 万/s（峰值 ≈ 20 万/s）

存储（5 年推文）：
  6×10⁸ × 365 × 5 ≈ 1.1 万亿条
  每条 ~300 bytes → ~330 PB（必须分片 + 冷热分离）

Fan-out 存储（如果用推模型）：
  平均粉丝 200 人 × 6 亿条/天 → 1200 亿 fan-out 写/天
  → 推模型在写入时开销巨大
```

---

## 3. 核心问题：Fan-out 策略

```
用户 A 发推 → 如何让 A 的所有粉丝看到？

┌─────────────────────────────────────────────────────┐
│  Pull Model（拉）                                      │
│  发推时只写 Post 表                                    │
│  读 Feed 时：查关注列表 → 查每个被关注者的 Post → 合并排序  │
│  优点：写简单                                          │
│  缺点：读慢（关注 1000 人 = 1000 次查询）                 │
├─────────────────────────────────────────────────────┤
│  Push Model（推）                                      │
│  发推时：写入每个粉丝的 Timeline（Fan-out on Write）    │
│  读 Feed 时：直接读自己的 Timeline                       │
│  优点：读极快                                          │
│  缺点：写放大（5000 万粉丝发推 = 5000 万 Timeline 写入）  │
├─────────────────────────────────────────────────────┤
│  Hybrid（混合）★ 业界主流                              │
│  普通用户（粉丝 < 1 万）：Push                           │
│  大 V（粉丝 > 1 万）：Pull（发推时不 fan-out）            │
│  读 Feed 时：Timeline（Push 部分）+ 大 V 推文（Pull 合并）│
└─────────────────────────────────────────────────────┘
```

---

## 4. High-Level 架构（Hybrid）

```
  Post Tweet                    Read Feed
      │                              │
      ↓                              ↓
┌───────────┐                 ┌──────────────┐
│ Post      │                 │ Feed Service │
│ Service   │                 └──────┬───────┘
└─────┬─────┘                        │
      │                    ┌─────────┼─────────┐
      ↓                    ↓         ↓         ↓
┌───────────┐        ┌─────────┐ ┌───────┐ ┌───────┐
│ Fan-out   │        │Timeline │ │ Post  │ │ Cache │
│ Worker    │        │ (Redis) │ │  DB   │ │       │
└─────┬─────┘        └─────────┘ └───────┘ └───────┘
      │
  粉丝 < 1万 → 写入 Timeline
  粉丝 > 1万 → 跳过大 V fan-out
```

---

## 5. 数据模型

```sql
-- 推文
CREATE TABLE posts (
    id         BIGINT PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    content    TEXT,
    created_at TIMESTAMP,
    INDEX idx_user_time (user_id, created_at DESC)
);

-- 关注关系
CREATE TABLE follows (
    follower_id  BIGINT,
    followee_id  BIGINT,
    created_at   TIMESTAMP,
    PRIMARY KEY (follower_id, followee_id)
);

-- Timeline（Push 模型，Redis 为主）
-- Key: timeline:{user_id}
-- Value: Sorted Set, score=timestamp, member=post_id
-- ZADD timeline:123 1690000000 "post_456"
```

### 读 Feed 流程

```
1. 从 Redis 读 timeline:{user_id}（Push 部分，最近 N 条）
2. 查 follows 表，找出大 V 关注列表
3. 从大 V 的 posts 表 Pull 最近推文
4. 合并 + 按时间排序 + 分页
5. 返回 Top 20
```

---

## 6. 热点与优化

### 大 V 发推（Thundering Herd）

```
5000 万粉丝 fan-out → 即使用 Hybrid，仍有风险

优化：
  - 大 V 列表维护在内存/Redis
  - 发推时异步 fan-out（消息队列削峰）
  - 粉丝 Timeline 分批写入（每批 1000）
```

### Feed 缓存

```
- 用户 Timeline 缓存 800 条（Redis Sorted Set）
- 超出部分从 DB 拉
- 用户打开 App 时预加载（Prefetch）
```

### 分页

```
❌ OFFSET 分页：OFFSET 10000 性能差
✅ Cursor 分页：?cursor=post_id_123&limit=20
   基于 (created_at, id) 复合 cursor
```

---

## 7. 扩展功能

| 功能 | 设计要点 |
|------|---------|
| 点赞 | Counter（Redis INCR），异步持久化到 DB |
| 评论 | 独立 Comment 表，post_id 索引 |
| 转发 | 新 Post 类型，`retweet_of_id` 字段 |
| 媒体 | 对象存储（S3），Post 只存 URL |
| 搜索 | Elasticsearch 索引 Post 内容 |

---

## 8. 动手练习

1. 对比 Pull/Push/Hybrid 在「1000 万粉丝大 V 发推」时的写入量
2. 设计 Feed 的 cursor 分页 API
3. 如果要求 Feed 包含「推荐内容（非关注）」，架构如何调整？

---

## 9. 自检清单

- [ ] 能解释 Fan-out on Write vs Read 的权衡
- [ ] 理解 Hybrid 模型及大 V 阈值设计
- [ ] 知道 Timeline 用 Redis Sorted Set 的原因
- [ ] 能设计 cursor 分页
- [ ] 考虑了热点、缓存、异步 fan-out

---

**下一课** → [04_case_ecommerce.md](04_case_ecommerce.md)：电商系统
