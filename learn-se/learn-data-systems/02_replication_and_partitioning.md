# 第2课：复制与分区

## 1. 复制（Replication）

### Leader-Follower（最常用）

```
         写
Client ──→ Leader ──→ Follower 1
              │    ──→ Follower 2
              │    ──→ Follower 3
         读（可从 Follower 读）

同步复制：Leader 等 Follower 确认 → 不丢数据，延迟高
异步复制：Leader 不等 → 可能丢数据，延迟低

PostgreSQL：Streaming Replication（异步/同步可选）
MySQL：Binlog Replication
Redis：主从复制
```

### Multi-Leader

```
Region A Leader ←→ Region B Leader
  各 Region 本地写入，互相同步

优势：多数据中心、低延迟写入
劣势：冲突解决复杂
适用：CouchDB, Cassandra
```

### Leaderless（Quorum）

```
写入 N 个节点，读取 R 个节点
  W + R > N → 保证读到最新写入

Cassandra：W + R > RF（副本因子）
DynamoDB：类似

示例：N=3, W=2, R=2
  写 2 个节点成功即可
  读 2 个节点，至少 1 个有最新数据
```

---

## 2. 分区（Partitioning / Sharding）

### Range 分区

```
按 Key 范围：
  A-M → Partition 1
  N-Z → Partition 2

优势：范围查询高效
劣势：热点（最新数据集中在最后一个分区）
```

### Hash 分区

```
partition = hash(key) % num_partitions

优势：均匀分布
劣势：丧失范围查询能力
```

### 二级索引

```
问题：按 user_id 分区，但要按 email 查询
  email 不在分区键中 → 需要全局索引

方案1：全局索引（独立分区）
方案2：文档分区（Cassandra 风格，每个分区存部分索引）
```

---

## 3. 一致性模型

| 模型 | 保证 | 示例 |
|------|------|------|
| 线性一致 | 所有操作有全局顺序 | ZooKeeper, etcd |
| 顺序一致 | 同一客户端看到有序 | Kafka 单分区 |
| 因果一致 | 有因果关系的操作有序 | 评论回复 |
| 最终一致 | 无保证，最终相同 | DNS, Cassandra 默认 |
| 读己之写 | 用户总能读自己的写入 | Session 一致性 |

### 事务隔离级别

```
Read Uncommitted  — 可能脏读
Read Committed    — 只读已提交（PG 默认）
Repeatable Read   — 同一事务内读一致（PG 默认）
Serializable      — 完全隔离（最慢）

→ 大多数应用 Read Committed 足够
→ 金融/库存用 Serializable 或乐观锁
```

---

## 4. 动手练习

1. 设计一个 3 节点 PostgreSQL 主从复制方案（读写分离）
2. 1000 万用户按 user_id hash 分 4 个 shard，画出分区方案
3. 解释 Quorum 读写中 W=2, R=2, N=3 如何保证一致性

---

**下一课** → [03_batch_and_stream_processing.md](03_batch_and_stream_processing.md)
