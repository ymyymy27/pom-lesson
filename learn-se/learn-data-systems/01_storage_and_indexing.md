# 第1课：存储引擎与索引

## 1. 存储引擎

### Log-Structured（LSM-Tree）

```
写入：追加到 WAL → 内存 MemTable → 刷盘 SSTable
读取：MemTable + 多个 SSTable → Bloom Filter 加速

代表：LevelDB, RocksDB, Cassandra, HBase

优势：写入极快（顺序写）
劣势：读取需查多个文件（Compaction 缓解）
适用：写多读少（日志、时序、消息）
```

### B-Tree

```
写入：原地更新页（Page）
读取：从根到叶，O(log n)

代表：PostgreSQL, MySQL InnoDB, SQLite

优势：读取快、支持范围查询
劣势：写入有随机 IO
适用：通用 OLTP（在线事务）
```

---

## 2. 索引原理

### Hash 索引

```
Key → hash(key) → Bucket → Value
O(1) 查找，但不支持范围查询
适用：等值查询（Redis、Memcached）
```

### B-Tree 索引

```
有序树结构，支持：
  - 等值查询：WHERE id = 123
  - 范围查询：WHERE age BETWEEN 20 AND 30
  - 排序：ORDER BY created_at
  - 前缀匹配：WHERE name LIKE 'Al%'

最左前缀原则（复合索引）：
  INDEX (a, b, c) 可用于：
    WHERE a = ? ✅
    WHERE a = ? AND b = ? ✅
    WHERE a = ? AND b = ? AND c = ? ✅
    WHERE b = ? ❌（跳过了 a）
```

### 全文索引

```
倒排索引（Inverted Index）：
  "Python is great" →
    Python → [doc1, doc5, doc12]
    great  → [doc1, doc3, doc7]

代表：Elasticsearch, PostgreSQL tsvector
适用：搜索、日志分析
```

### 向量索引

```
Embedding → 高维向量 → ANN（近似最近邻）
  Flat：精确，慢
  HNSW：图索引，快
  IVF：聚类 + 搜索

代表：pgvector, Milvus, Pinecone
适用：语义搜索、RAG、推荐
```

---

## 3. 索引设计原则

```
1. 为 WHERE / JOIN / ORDER BY 中的列建索引
2. 复合索引遵循最左前缀
3. 高选择性列优先（gender 低选择性，user_id 高选择性）
4. 覆盖索引避免回表
5. 不要过度索引（写性能下降、占空间）
6. 定期 EXPLAIN ANALYZE 验证索引被使用
```

---

## 4. 动手练习

1. 解释 B-Tree 和 LSM-Tree 的写入路径差异
2. 为 TaskFlow 的 tasks 表设计 3 个索引并说明适用查询
3. 用 EXPLAIN ANALYZE 对比有索引和无索引的查询性能

---

**下一课** → [02_replication_and_partitioning.md](02_replication_and_partitioning.md)
