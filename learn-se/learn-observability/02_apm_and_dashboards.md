# 第2课：APM 与 Dashboard

## 1. Grafana Dashboard 设计

### TaskFlow 推荐面板

| 面板 | PromQL / 数据源 |
|------|----------------|
| 请求 QPS | `rate(http_requests_total[5m])` |
| P95 延迟 | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` |
| 错误率 | `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])` |
| Celery 队列长度 | `celery_queue_length` |
| DB 连接池 | `django_db_connections` |

---

## 2. 告警规则

```yaml
# prometheus/alerts.yml
groups:
  - name: taskflow
    rules:
      - alert: HighErrorRate
        expr: error_rate > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "错误率超过 5%"

      - alert: SLOBurnRate
        expr: slo_error_budget_burn_rate > 14.4
        for: 1h
        labels:
          severity: warning
```

---

## 3. APM 工具选型

| 工具 | 类型 | 适用 |
|------|------|------|
| Prometheus + Grafana | 自托管 | 中小团队、K8s |
| Datadog | SaaS | 全栈 APM、企业 |
| New Relic | SaaS | 应用性能 |
| Sentry | 错误追踪 | 前后端异常 |
| Jaeger / Tempo | 追踪 | 微服务链路 |

---

## 4. 可观测性成熟度

```
Level 0：无监控，出问题靠用户反馈
Level 1：基础 metrics + 日志
Level 2：Dashboard + 告警 + SLO
Level 3：分布式追踪 + 自动根因分析
Level 4：AIOps 异常检测 + 自愈
```

---

## 5. 动手练习

1. 导入 Grafana Dashboard（Django ID: 17658）
2. 配置 Slack 告警 webhook
3. 定义 TaskFlow 的 2 个 SLI 并在 Grafana 展示

---

**关联** → [`learn-reliability/`](../learn-reliability/)
