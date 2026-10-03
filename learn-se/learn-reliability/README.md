# 可靠性工程（SRE）

让系统「可靠运行」而不仅是「能跑起来」——SLI/SLO、故障响应、弹性设计。

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 参考 | `00_reliability_overview.md` | SRE 文化、可靠性 vs 可用性、Google SRE 概览 |
| 第1课 | `01_sli_slo_sla.md` | SLI/SLO/SLA、错误预算、可靠性目标 |
| 第2课 | `02_incident_response.md` | 故障响应、Postmortem、On-call 实践 |
| 第3课 | `03_resilience_patterns.md` | 熔断、限流、降级、混沌工程 |

## 学习目标

- 能为服务定义 SLI/SLO，理解错误预算如何平衡可靠性与交付速度
- 掌握故障响应流程和无责 Postmortem 方法
- 理解熔断、限流、降级等弹性模式

## 关联课程

- `learn-architecture/02_microservices_and_distributed.md` — 分布式容错
- `learn-dev-methods/02_devops_and_cicd.md` — CI/CD 与部署
- `learn-performance/` — 性能与可靠性交叉

## 推荐书单

- 《Site Reliability Engineering》（Google SRE Book）
- 《The Site Reliability Workbook》
