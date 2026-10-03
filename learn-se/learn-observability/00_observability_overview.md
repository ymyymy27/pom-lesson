# 可观测性全景

## 1. 三支柱

```
Metrics（指标）  — 系统状态的数值时间序列（QPS、延迟、错误率）
Logs（日志）     — 离散事件记录（请求、错误、审计）
Traces（追踪）   — 跨服务请求的完整调用链
```

| 支柱 | 回答的问题 | 典型工具 |
|------|-----------|----------|
| Metrics | 系统是否健康？趋势如何？ | Prometheus、Grafana |
| Logs | 发生了什么？ | ELK、Loki、CloudWatch |
| Traces | 慢在哪里？哪个服务拖后腿？ | Jaeger、Tempo、OpenTelemetry |

---

## 2. 与 SRE 的关系

```
SLI（指标）→ SLO（目标）→ 告警 → 故障响应

可观测性 = 测量 SLI 的基础设施
```

详见 [`learn-reliability/01_sli_slo_sla.md`](../learn-reliability/01_sli_slo_sla.md)

---

## 3. 2026 最佳实践

- **OpenTelemetry** 成为追踪标准（vendor-neutral）
- **结构化日志**（JSON）替代纯文本
- **关联 ID**：`trace_id` 贯穿 logs + metrics + traces
- **RED 方法**：Rate、Errors、Duration（服务级）
- **USE 方法**：Utilization、Saturation、Errors（资源级）

---

**下一课** → [`01_logging_metrics_tracing.md`](01_logging_metrics_tracing.md)
