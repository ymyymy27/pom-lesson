# 软件工程课程

面向开发者的系统软件工程学习路径，涵盖工程基础、设计模式、领域建模、架构设计、系统设计、API/安全、权限/多租户、可靠性/可观测性、性能、数据系统与开发方式 **13 大模块**。

## 快速开始

👉 **第一次学习？** 先看 [`GETTING_STARTED.md`](GETTING_STARTED.md)（5 分钟定位起点）

👉 **系统深度学习？** 按 [`STUDY_ROADMAP.md`](STUDY_ROADMAP.md) 12 周计划执行

## 课程目录

| 模块 | 目录 | 内容 | 课时 |
|------|------|------|------|
| 软件工程基础 | `learn-fundamentals/` | SDLC、SOLID、测试与质量、重构 | 4 课 |
| 设计模式 | `learn-design-patterns/` | 创建型/结构型/行为型模式、实战与反模式 | 5 课 |
| 领域驱动设计 | `learn-domain-design/` | 限界上下文、聚合、战术/战略设计 | 4 课 |
| 架构设计 | `learn-architecture/` | 完整谱系 30+ 风格、SOA/洋葱/ES/ETL 精讲、ADR、集成、案例 | 11 课 |
| 系统设计 | `learn-system-design/` | 容量估算、URL 短链/Feed/电商经典案例 | 5 课 |
| API 设计 | `learn-api-design/` | REST 最佳实践、版本策略、OpenAPI 契约 | 3 课 |
| 安全架构 | `learn-security/` | 威胁建模、认证授权、OWASP、LLM/Agent 安全 | 4 课 |
| 认证授权与多租户 | `learn-permission/` | 认证、RBAC/ABAC、组织模型、数据权限、多租户隔离、权限中台 | 9 课 |
| 可靠性工程 | `learn-reliability/` | SLI/SLO、故障响应、熔断/限流/混沌工程 | 4 课 |
| 可观测性 | `learn-observability/` | 日志/指标/追踪、APM Dashboard | 3 课 |
| 开发方式 | `learn-dev-methods/` | 敏捷/Scrum/Kanban、DevOps/CI/CD、平台工程、协作与技术债 | 5 课 |
| 性能工程 | `learn-performance/` | Profiling、优化模式、负载测试 | 4 课 |
| 数据系统 | `learn-data-systems/` | DDIA 精要：存储/复制/流处理 | 4 课 |
| 综合实战 | `projects/` | TaskFlow 架构大作业 | 1 项 |

**统计：** 13 大模块 · 60+ 课 · 8 个 Python 设计模式示例 + 3 个权限练习 · 1 个综合大作业

> 缺口分析与 2025–2026 新技术补充见工作区 [`COURSE_GAP_ANALYSIS.md`](../COURSE_GAP_ANALYSIS.md)

## 学习顺序建议

```
learn-fundamentals → learn-design-patterns → learn-domain-design
   工程基础与原则        代码级设计能力           业务建模能力
                              ↓
              learn-architecture + learn-api-design + learn-security
                     系统级架构          API 契约         安全设计
                              ↓
                    learn-permission（可选：权限与多租户专题）
                              ↓
                    learn-system-design → learn-reliability
                       案例实战能力          可靠性工程
                              ↓
                       learn-dev-methods → projects/
                        团队协作与交付          综合大作业
```

**进阶路径（与现有课程联动）：**

```
learn-se（本模块）  +  learn-fullstack（全栈实战）  +  learn-tools（Git/Docker）
     理论与设计              动手做项目                    工具落地
```

## 学习方式

- 以 **Markdown 文档** 为主，配合 **Python 代码示例** 理解设计模式
- 每课包含：概念讲解 → 类比理解 → 代码/图示 → 动手练习 → 自检清单
- 建议按 [`STUDY_ROADMAP.md`](STUDY_ROADMAP.md) 顺序学习；有项目经验后可跳读架构与系统设计
- 设计模式模块建议边读边在 `learn-design-patterns/practice/` 运行示例代码

## 适用人群

- 有一定编程基础，想系统补齐软件工程知识的开发者
- 从「能写代码」进阶到「能设计系统、带团队交付」的工程师
- 准备技术面试或架构评审的同学

## 模块关系

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            learn-se 软件工程                                   │
├──────────┬─────────────┬──────────────┬──────────────┬───────────┬────────────┤
│fundamentals│design-patterns│domain-design │ architecture │system-design│api+security│
│ 为什么/原则  │  类怎么组织    │  业务怎么建模  │  系统怎么拆    │ 案例怎么设计 │接口与安全  │
├──────────┴─────────────┴──────────────┴──────────────┴───────────┴────────────┤
│              learn-reliability + learn-dev-methods + projects/                │
│                   可靠性工程  +  敏捷/DevOps/协作  +  TaskFlow 大作业           │
└──────────────────────────────────────────────────────────────────────────────┘
         ↓              ↓              ↓              ↓              ↓
    单文件/单模块     模块间关系        业务边界         服务间关系       端到端设计
```

**2026-08 新增：** [`learn-permission/`](learn-permission/README.md) 认证授权与多租户专题，9 课 + 3 个可运行练习，与 `learn-security`（原理）、`learn-fullstack`（实战）互补。

## 推荐书单

| 阶段 | 书籍 |
|------|------|
| 原则 | 《Clean Code》《重构：改善既有代码的设计》 |
| 模式 | 《Head First 设计模式》、refactoring.guru |
| 领域 | 《领域驱动设计精粹》《实现领域驱动设计》 |
| 架构 | 《Software Architecture: The Hard Parts》《Building Microservices》 |
| 数据 | 《Designing Data-Intensive Applications》（DDIA，必读） |
| API | 《RESTful Web APIs》 |
| 安全 | OWASP Top 10、OWASP ASVS、OWASP LLM/Agentic AI Top 10 |
| 可靠性 | 《Site Reliability Engineering》（Google SRE Book） |
| 交付 | 《Accelerate》《Team Topologies》 |
