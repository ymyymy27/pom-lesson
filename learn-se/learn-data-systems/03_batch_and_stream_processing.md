# 第3课：批处理与流处理

## 1. 数据管道

```
数据源 → 传输 → 处理 → 存储 → 服务

示例：
  App DB → CDC → Kafka → Flink → Elasticsearch → 搜索 API
  App Logs → Filebeat → Kafka → Spark → Data Warehouse → BI
  User Events → SDK → Kafka → Real-time Dashboard
```

---

## 2. 批处理（Batch Processing）

```
特点：有界数据集、高吞吐、延迟分钟~小时级

MapReduce 模型：
  Map：    每条记录 → (key, value)
  Shuffle：按 key 分组
  Reduce：  每组 → 聚合结果

  Word Count 示例：
  "hello world hello" →
    Map: (hello,1), (world,1), (hello,1)
    Shuffle: hello → [1,1], world → [1]
    Reduce: hello → 2, world → 1

现代工具：
  Spark：内存计算，比 MapReduce 快 10-100x
  dbt：SQL 转换，数据仓库建模
  Airflow：工作流调度
```

### 适用场景

```
- 日/周报生成
- 数据仓库 ETL
- 机器学习训练数据准备
- 历史数据分析
```

---

## 3. 流处理（Stream Processing）

```
特点：无界数据流、低延迟、毫秒~秒级

事件流：
  Event → Topic（Kafka）→ Consumer Group → 处理 → 输出

Kafka 核心概念：
  Topic：消息分类
  Partition：Topic 的分片（有序）
  Consumer Group：并行消费（每组内不重复）
  Offset：消费位置

处理语义：
  At-most-once：可能丢（fire-and-forget）
  At-least-once：可能重复（默认，需幂等）
  Exactly-once：精确一次（Kafka Transaction + 幂等 Producer）
```

### 流处理框架

| 框架 | 模型 | 特点 |
|------|------|------|
| Kafka Streams | 库（嵌入 App） | 轻量，与 Kafka 深度集成 |
| Flink | 独立集群 | 精确一次，复杂事件处理 |
| Spark Streaming | 微批 | 统一批流 API |

### 窗口操作

```
Tumbling Window（滚动）：每 5 分钟统计
  [0-5), [5-10), [10-15) ...

Sliding Window（滑动）：每 1 分钟统计过去 5 分钟
  [0-5), [1-6), [2-7) ...

Session Window：用户活跃期间
  30 分钟无活动 → 窗口关闭
```

---

## 4. CDC（Change Data Capture）

```
捕获数据库变更 → 实时同步到其他系统

PostgreSQL：Logical Replication / Debezium
MySQL：Binlog → Debezium

流程：
  PG WAL → Debezium → Kafka → Consumer
                              ├→ Elasticsearch（搜索索引）
                              ├→ Data Warehouse（分析）
                              └→ Cache Invalidation（缓存失效）

用途：
  - 读写分离（写 PG，读 ES）
  - 缓存同步
  - 审计日志
  - 微服务间数据同步
```

---

## 5. Lambda vs Kappa 架构

```
Lambda（批 + 流双路径）：
  实时路径：Kafka → Flink → Redis（秒级）
  批处理路径：HDFS → Spark → DW（小时级）
  合并：Serving Layer 合并两路结果

  优点：成熟、精确
  缺点：两套代码、维护复杂

Kappa（纯流）：
  所有数据走 Kafka → 流处理
  需要历史重算？重放 Topic

  优点：简单、统一
  缺点：重算成本高

现代趋势：Kappa + 流批一体（Flink/Spark Unified）
```

---

## 6. 动手练习

1. 设计 TaskFlow 的搜索同步管道（PG → CDC → ES）
2. 对比 Lambda 和 Kappa 架构，为 TaskFlow 活动日志选型
3. 解释 Kafka 的 At-least-once 语义及幂等消费方案

---

## 7. 自检清单

- [ ] 理解批处理 MapReduce 模型
- [ ] 知道 Kafka 的核心概念和消费语义
- [ ] 理解 CDC 的作用和流程
- [ ] 能对比 Lambda 和 Kappa 架构

---

**恭喜完成 learn-se 扩展模块！** → 回到 [`STUDY_ROADMAP.md`](../STUDY_ROADMAP.md)
