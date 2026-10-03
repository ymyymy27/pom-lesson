# 领域驱动设计（DDD）

用业务语言建模，划分限界上下文，为架构拆分和团队协作提供「共同语言」。

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 参考 | `00_ddd_overview.md` | DDD 全景、战略 vs 战术、何时引入 |
| 第1课 | `01_bounded_context.md` | 限界上下文、上下文地图、通用语言 |
| 第2课 | `02_aggregates_and_modeling.md` | 实体、值对象、聚合、不变量 |
| 第3课 | `03_tactical_patterns.md` | Repository、Domain Event、应用服务、防腐层 |
| 第4课 | `04_strategic_design.md` | 子域划分、上下文映射、演进策略 |

## 学习目标

- 能用业务语言划分限界上下文，绘制上下文地图
- 理解聚合边界与不变量，避免「大聚合」反模式
- 掌握 Repository、Domain Event 等战术模式的适用场景

## 关联课程

- `learn-architecture/02_microservices_and_distributed.md` — 按限界上下文拆分微服务
- `learn-design-patterns/` — 战术模式与 GoF 模式的配合
- `learn-system-design/04_case_ecommerce.md` — 电商领域建模案例

## 学习方式

- 每课都有电商/任务平台等领域示例，建议边读边画自己的上下文地图
- 第 2 课是核心，聚合设计决定后续架构质量
- 与 `learn-architecture/` 配合：先 DDD 建模，再选架构风格
