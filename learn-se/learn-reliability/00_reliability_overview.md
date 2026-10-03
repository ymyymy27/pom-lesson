# 可靠性工程全景

## 1. SRE 是什么？

### 一句话解释

**SRE（Site Reliability Engineering）= 用软件工程的方法解决运维问题，让系统可靠运行。**

### SRE vs 传统运维

| 维度 | 传统运维 | SRE |
|------|---------|-----|
| 目标 | 系统不挂 | 系统可靠 + 快速迭代 |
| 方法 | 手动操作、变更窗口 | 自动化、持续部署 |
| 故障 | 避免故障 | 接受故障，快速恢复 |
| 度量 |  uptime 百分比 | SLI/SLO + 错误预算 |
| 工具 | Shell 脚本 | 代码（Infrastructure as Code） |

---

## 2. 可靠性核心概念

```
可用性（Availability）：
  系统正常运行时间 / 总时间
  99.9% = 年停机 8.76 小时
  99.99% = 年停机 52.6 分钟

可靠性（Reliability）：
  系统在需要时能正确工作的程度
  包含：可用性 + 数据正确性 + 延迟达标

可维护性（Maintainability）：
  故障后多快能恢复

可观测性（Observability）：
  通过外部输出理解系统内部状态的能力
```

### 几个 9 的含义

| 可用性 | 年停机 | 适用场景 |
|--------|--------|---------|
| 99%（2 个 9） | 3.65 天 | 内部工具 |
| 99.9%（3 个 9） | 8.76 小时 | 普通 SaaS |
| 99.95% | 4.38 小时 | 电商平台 |
| 99.99%（4 个 9） | 52.6 分钟 | 支付/金融 |
| 99.999%（5 个 9） | 5.26 分钟 | 电信级 |

---

## 3. SRE 与 DevOps 的关系

```
DevOps：文化运动，打破 Dev 和 Ops 的墙
SRE：    Google 对 DevOps 的具体实现

SRE 的具象化：
  - 50% 时间写代码（自动化、工具）
  - 50% 时间运维（On-call、故障响应）
  - 用 SLI/SLO 量化可靠性
  - 用错误预算平衡「快」与「稳」
```

---

## 4. 本模块知识地图

```
         ┌─────────────────┐
         │  SLI / SLO / SLA │  ← 定义「多可靠算够」
         └────────┬────────┘
                  ↓
         ┌─────────────────┐
         │  可观测性         │  ← 日志 / 指标 / 追踪
         │  (Metrics/Logs)  │
         └────────┬────────┘
                  ↓
    ┌─────────────┼─────────────┐
    ↓             ↓             ↓
 告警         故障响应       弹性设计
 On-call      Postmortem    熔断/限流/降级
                  ↓
         ┌─────────────────┐
         │   混沌工程        │  ← 主动验证可靠性
         └─────────────────┘
```

---

## 5. 可观测性三支柱

```
Metrics（指标）— 系统健康度趋势
  Prometheus + Grafana
  例：QPS、错误率、延迟分位数

Logs（日志）— 发生了什么
  结构化 JSON，带 trace_id
  例：{"level":"error","msg":"payment failed","order_id":123}

Traces（追踪）— 请求经过了谁
  OpenTelemetry → Jaeger / Tempo
  例：API → Auth → Order → Payment → DB
```

**架构阶段就要规划：** 不是上线后才补监控。

---

## 6. 可靠性设计层次

```
L1 基础设施：多 AZ、自动扩缩、健康检查
L2 应用弹性：超时、重试、熔断、限流、降级
L3 数据可靠：备份、复制、幂等、对账
L4 流程保障：On-call、Runbook、Postmortem、Game Day
L5 组织文化：无责复盘、错误预算、Blameless
```

---

## 7. 学习路线

```
00_reliability_overview.md（本文）
        ↓
01_sli_slo_sla.md — 定义「多可靠算够」
        ↓
02_incident_response.md — 故障来了怎么办
        ↓
03_resilience_patterns.md — 熔断/限流/混沌工程
        ↓
projects/capstone_taskflow.md — 综合练习
```

---

## 8. 自检清单

- [ ] 能区分可用性、可靠性、可维护性
- [ ] 知道几个 9 对应的年停机时间
- [ ] 理解 SRE 与 DevOps 的关系
- [ ] 知道可观测性三支柱
- [ ] 理解可靠性设计的五个层次

---

## 9. 延伸阅读

- 《Site Reliability Engineering》（Google SRE Book）
- 《The Site Reliability Workbook》
- 《Release It!》（弹性模式）

**下一课** → [01_sli_slo_sla.md](01_sli_slo_sla.md)
