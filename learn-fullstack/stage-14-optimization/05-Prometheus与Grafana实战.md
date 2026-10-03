# Prometheus 与 Grafana 实战

> 2025–2026 补充课 — 补齐 stage-14 监控短板  
> 前置：[`04-监控与日志.md`](04-监控与日志.md)

## 1. 为什么需要 Prometheus + Grafana？

stage-14 已覆盖 Sentry（错误追踪）和简易 metrics 端点。生产环境还需要：

```
Sentry     →  错误与异常（What broke?）
Prometheus →  指标时序数据（How is it performing?）
Grafana    →  可视化 Dashboard（Show me the trends）
```

| 工具 | 职责 |
|------|------|
| Prometheus | 拉取（Pull）metrics，存储时序数据，告警规则 |
| Grafana | 连接 Prometheus，绘制 Dashboard |
| Alertmanager | 告警路由（Slack/PagerDuty/邮件） |

---

## 2. Django 暴露 Metrics

### 安装 django-prometheus

```bash
pip install django-prometheus
```

```python
# settings.py
INSTALLED_APPS = [
    'django_prometheus',
    # ...
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ... 其他 middleware ...
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# urls.py
urlpatterns = [
    path('', include('django_prometheus.urls')),  # /metrics 端点
    # ...
]
```

访问 `http://localhost:8000/metrics` 可看到：

```
django_http_requests_total_by_method_total{method="GET"} 42
django_http_requests_latency_seconds_bucket{le="0.1"} 38
django_db_query_duration_seconds_count 156
```

### 自定义业务指标

```python
from prometheus_client import Counter, Histogram

TASK_CREATED = Counter(
    'taskflow_tasks_created_total',
    'Total tasks created',
    ['project_id'],
)

REQUEST_DURATION = Histogram(
    'taskflow_api_duration_seconds',
    'API request duration',
    ['endpoint', 'method'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)

# 在视图中使用
def create_task(request):
    with REQUEST_DURATION.labels(endpoint='/tasks', method='POST').time():
        task = Task.objects.create(...)
        TASK_CREATED.labels(project_id=task.project_id).inc()
        return Response(...)
```

---

## 3. Docker Compose 部署监控栈

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus:v2.55.0
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:11.4.0
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana

  # Django 应用（已有）
  web:
    build: .
    ports:
      - "8000:8000"

volumes:
  grafana-data:
```

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'taskflow-django'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:9121']  # redis_exporter

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

启动：

```powershell
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

---

## 4. Grafana Dashboard 配置

### 首次登录

1. 访问 `http://localhost:3001`（admin / admin）
2. Configuration → Data Sources → Add Prometheus
3. URL: `http://prometheus:9090` → Save & Test

### 推荐 Dashboard 面板

| 面板 | PromQL 示例 |
|------|-------------|
| 请求 QPS | `rate(django_http_requests_total_by_method_total[5m])` |
| P95 延迟 | `histogram_quantile(0.95, rate(django_http_requests_latency_seconds_bucket[5m]))` |
| 错误率 | `rate(django_http_responses_total_by_status_total{status=~"5.."}[5m])` |
| DB 查询耗时 | `rate(django_db_query_duration_seconds_sum[5m]) / rate(django_db_query_duration_seconds_count[5m])` |
| 任务创建数 | `increase(taskflow_tasks_created_total[1h])` |

### 导入社区 Dashboard

Grafana → Dashboards → Import → 输入 ID：

- **Django**: `17658`
- **Redis**: `763`
- **PostgreSQL**: `9628`

---

## 5. 告警规则

```yaml
# monitoring/alerts.yml
groups:
  - name: taskflow
    rules:
      - alert: HighErrorRate
        expr: |
          rate(django_http_responses_total_by_status_total{status=~"5.."}[5m])
          / rate(django_http_requests_total_by_method_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "错误率超过 5%"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(django_http_requests_latency_seconds_bucket[5m])
          ) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "P95 延迟超过 2 秒"
```

---

## 6. 与 Sentry 的分工

```
┌─────────────────────────────────────────────────┐
│                   可观测性三层                      │
├─────────────┬───────────────┬───────────────────┤
│   Metrics   │     Logs      │      Traces       │
│ Prometheus  │  Django/ELK   │  OpenTelemetry    │
│  + Grafana  │  + Loki       │  + Jaeger/Tempo   │
├─────────────┴───────────────┴───────────────────┤
│              Errors: Sentry                       │
└─────────────────────────────────────────────────┘
```

TaskFlow 最小监控栈：**Sentry + Prometheus + Grafana**。

---

## 7. 动手练习

1. 为 TaskFlow 添加 `/metrics` 端点并验证输出
2. 用 Docker Compose 启动 Prometheus + Grafana
3. 创建 Dashboard：QPS、P95 延迟、错误率三个面板
4. 添加一条告警规则：错误率 > 5% 持续 5 分钟

---

## 8. 自检清单

- [ ] 能解释 Prometheus Pull 模型
- [ ] 会在 Django 中暴露 metrics
- [ ] 能写基本的 PromQL 查询
- [ ] 能在 Grafana 中创建 Dashboard
- [ ] 理解 Metrics / Logs / Errors 的分工

---

## 参考

- [django-prometheus 文档](https://github.com/korfuri/django-prometheus)
- [Prometheus 官方文档](https://prometheus.io/docs/)
- [Grafana Dashboard 库](https://grafana.com/grafana/dashboards/)
