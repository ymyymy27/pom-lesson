# 数据密集型系统精要

基于 DDIA（Designing Data-Intensive Applications）核心思想，补齐存储、复制、分区与流处理知识。

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 参考 | `00_ddia_overview.md` | 数据系统分类、CAP、存储引擎概览 |
| 第1课 | `01_storage_and_indexing.md` | 存储引擎、B-Tree vs LSM、索引原理 |
| 第2课 | `02_replication_and_partitioning.md` | 复制、分区、一致性模型 |
| 第3课 | `03_batch_and_stream_processing.md` | 批处理、流处理、CDC、数据管道 |

## 学习目标

- 理解关系型 vs 文档 vs 列式存储的选型
- 掌握复制、分区、一致性的权衡
- 了解批处理与流处理的数据管道设计

## 关联课程

- `learn-architecture/03_event_driven_and_data.md` — 事件驱动与 CQRS
- `learn-system-design/` — 系统设计中的存储选型
- `learn-performance/02_optimization_patterns.md` — 索引与查询优化

## 推荐书单

- 《Designing Data-Intensive Applications》（DDIA，Martin Kleppmann）— 必读
