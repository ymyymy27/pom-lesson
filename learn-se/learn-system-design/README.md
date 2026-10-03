# 系统设计

经典系统设计案例实战，训练容量估算、组件选型、权衡分析与 high-level design 能力。

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 参考 | `00_overview.md` | 系统设计方法论、面试/评审框架 |
| 第1课 | `01_capacity_estimation.md` | QPS、存储、带宽估算；Back-of-envelope |
| 第2课 | `02_case_url_shortener.md` | URL 短链：哈希、冲突、缓存、重定向 |
| 第3课 | `03_case_social_feed.md` | 社交 Feed：推拉模型、Timeline、热点 |
| 第4课 | `04_case_ecommerce.md` | 电商：库存、订单、支付、搜索 |

## 学习目标

- 能在 45 分钟内完成中等复杂度系统的 high-level design
- 掌握 Back-of-envelope 容量估算方法
- 理解推拉模型、一致性、缓存等经典权衡

## 关联课程

- `learn-architecture/` — 架构风格与分布式理论
- `learn-domain-design/` — 业务建模与限界上下文
- `projects/capstone_taskflow.md` — 综合大作业

## 学习方式

- 每课按「需求 → 估算 → 架构图 → 深入组件 → 权衡」结构学习
- 建议限时练习：先自己设计 30 分钟，再对照参考答案
- 白board 或 Excalidraw 画图，口述设计思路（费曼学习法）
