# 数据密集型系统全景

## 1. 三类系统

Martin Kleppmann 在 DDIA 中将数据系统分为三类：

```
┌─────────────────────────────────────────────────┐
│              数据密集型应用                        │
├──────────────┬──────────────┬───────────────────┤
│  存储系统     │  检索系统     │  处理系统          │
│  (Storage)   │  (Retrieval) │  (Processing)     │
├──────────────┼──────────────┼───────────────────┤
│ PostgreSQL   │ Elasticsearch│ Spark (批处理)    │
│ MongoDB      │ Redis        │ Kafka/Flink (流)  │
│ S3           │ 全文索引      │ MapReduce        │
│ Cassandra    │ 向量数据库    │ CDC 管道          │
└──────────────┴──────────────┴───────────────────┘
```

---

## 2. 数据库选型

| 类型 | 代表 | 数据模型 | 适用 |
|------|------|---------|------|
| 关系型 | PostgreSQL, MySQL | 表 + SQL | 事务、复杂查询、JOIN |
| 文档型 | MongoDB | JSON 文档 | 灵活 Schema、嵌套数据 |
| 键值型 | Redis, DynamoDB | Key-Value | 缓存、Session、计数器 |
| 列式 | ClickHouse, BigQuery | 列存储 | 分析、OLAP、报表 |
| 图 | Neo4j | 节点 + 边 | 社交关系、推荐 |
| 时序 | InfluxDB, TimescaleDB | 时间序列 | 监控、IoT |
| 向量 | Pinecone, Milvus | 向量嵌入 | 语义搜索、RAG |

### 选型决策

```
需要 ACID 事务？        → 关系型
Schema 频繁变化？       → 文档型
纯缓存/计数/Session？   → 键值型
海量数据分析/报表？     → 列式
关系遍历（好友的好友）？ → 图
监控指标/IoT 数据？     → 时序
AI 语义搜索？           → 向量
```

---

## 3. CAP 与 PACELC

```
CAP（分区容忍下二选一）：
  C (Consistency)  — 所有节点看到相同数据
  A (Availability) — 每个请求都有响应
  P (Partition)    — 网络分区时仍运行

  CP：ZooKeeper, HBase, MongoDB（默认）
  AP：Cassandra, DynamoDB, CouchDB

PACELC（CAP 的扩展）：
  如果有 Partition (P)：
    选 Availability (A) 还是 Consistency (C)？
  否则 (E, normal operation)：
    选 Latency (L) 还是 Consistency (C)？

  大多数系统：PA/EL（分区时可用，正常时低延迟）
```

---

## 4. 本模块知识地图

```
存储引擎（B-Tree / LSM-Tree）
        ↓
索引（Hash / B-Tree / 全文 / 向量）
        ↓
复制（Leader-Follower / Multi-Leader / Leaderless）
        ↓
分区（Range / Hash / 二级索引）
        ↓
一致性（线性一致 / 因果一致 / 最终一致）
        ↓
批处理（MapReduce / Spark） vs 流处理（Kafka / Flink）
```

---

**下一课** → [01_storage_and_indexing.md](01_storage_and_indexing.md)
