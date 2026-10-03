import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：监控体系（Prometheus / Grafana / 告警）
==============================================================================

AI 服务上线后，需要全面监控：
  性能（延迟/吞吐）、资源（GPU/CPU/内存）、
  业务（token/费用/错误率）、质量（用户反馈）

本课内容：
1. 监控体系概述
2. Prometheus 指标采集
3. 自定义 AI 指标
4. Grafana 仪表板
5. 告警规则
6. GPU 监控
==============================================================================
"""

import json
import time
import numpy as np
from collections import defaultdict
from datetime import datetime

print("=" * 60)
print("第5课：监控体系")
print("=" * 60)

# ============================================================================
# 1. 监控体系
# ============================================================================
print("\n--- 1. 监控体系 ---")
print("""
AI 服务监控四层：

┌──────────────────────────────────────────────────────┐
│  质量指标（Quality）                                  │
│  用户满意度 / 回答相关性 / 幻觉率                    │
├──────────────────────────────────────────────────────┤
│  业务指标（Business）                                 │
│  QPS / Token消耗 / 费用 / 错误率 / 缓存命中          │
├──────────────────────────────────────────────────────┤
│  性能指标（Performance）                              │
│  延迟 P50/P95/P99 / TTFT / 吞吐量                   │
├──────────────────────────────────────────────────────┤
│  资源指标（Resource）                                 │
│  GPU利用率 / GPU显存 / CPU / 内存 / 磁盘             │
└──────────────────────────────────────────────────────┘

技术栈：
  采集: Prometheus（拉取模式）
  存储: Prometheus TSDB（时序数据库）
  展示: Grafana（仪表板）
  告警: Alertmanager → 飞书/钉钉/邮件
""")

# ============================================================================
# 2. Prometheus 指标
# ============================================================================
print("\n--- 2. Prometheus ---")
print("""
Prometheus 四种指标类型：

  Counter:    只增不减的计数器（请求总数、token总数）
  Gauge:      可增可减的仪表盘（活跃会话数、GPU使用率）
  Histogram:  分布统计（延迟分布 P50/P95/P99）
  Summary:    类似 Histogram，客户端计算分位数

FastAPI 集成：
```python
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge

# 自动采集 HTTP 指标
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# 自定义指标
llm_requests = Counter(
    'llm_requests_total', 'Total LLM API calls',
    ['model', 'status']
)
llm_latency = Histogram(
    'llm_latency_seconds', 'LLM response latency',
    ['model'],
    buckets=[0.5, 1, 2, 5, 10, 30]
)
llm_tokens = Counter(
    'llm_tokens_total', 'Total tokens consumed',
    ['model', 'type']
)
active_sessions = Gauge(
    'active_sessions', 'Active chat sessions'
)
```

指标端点 /metrics 输出示例：
```
# HELP llm_requests_total Total LLM API calls
# TYPE llm_requests_total counter
llm_requests_total{model="qwen2.5:7b",status="success"} 1523
llm_requests_total{model="gpt-4o-mini",status="success"} 892
llm_requests_total{model="gpt-4o-mini",status="error"} 12

# HELP llm_latency_seconds LLM response latency
# TYPE llm_latency_seconds histogram
llm_latency_seconds_bucket{model="qwen2.5:7b",le="1"} 423
llm_latency_seconds_bucket{model="qwen2.5:7b",le="2"} 1102
```
""")

# ============================================================================
# 3. 自定义 AI 指标
# ============================================================================
print("\n--- 3. AI 指标 ---")

class PrometheusSimulator:
    """Prometheus 指标模拟器"""

    def __init__(self):
        self.counters = defaultdict(float)
        self.gauges = {}
        self.histograms = defaultdict(list)

    def counter_inc(self, name: str, value: float = 1, labels: dict = None):
        key = self._key(name, labels)
        self.counters[key] += value

    def gauge_set(self, name: str, value: float, labels: dict = None):
        key = self._key(name, labels)
        self.gauges[key] = value

    def histogram_observe(self, name: str, value: float, labels: dict = None):
        key = self._key(name, labels)
        self.histograms[key].append(value)

    def _key(self, name, labels=None):
        if labels:
            l = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
            return f"{name}{{{l}}}"
        return name

    def format_metrics(self) -> str:
        """输出 Prometheus 格式"""
        lines = []
        for name, value in self.counters.items():
            lines.append(f"{name} {value}")
        for name, value in self.gauges.items():
            lines.append(f"{name} {value}")
        for name, values in self.histograms.items():
            arr = np.array(values)
            lines.append(f"{name}_count {len(values)}")
            lines.append(f"{name}_sum {np.sum(arr):.2f}")
            for bucket in [0.5, 1, 2, 5, 10, 30]:
                count = np.sum(arr <= bucket)
                lines.append(f'{name}_bucket{{le="{bucket}"}} {count}')
        return "\n".join(lines)

prom = PrometheusSimulator()

# 模拟 AI 服务运行
np.random.seed(42)
for _ in range(200):
    model = np.random.choice(["qwen2.5:7b", "gpt-4o-mini"], p=[0.6, 0.4])
    status = np.random.choice(["success", "error"], p=[0.97, 0.03])
    latency = np.random.exponential(1.5) + 0.3
    tokens = int(np.random.normal(350, 100))

    prom.counter_inc("llm_requests_total", labels={"model": model, "status": status})
    if status == "success":
        prom.histogram_observe("llm_latency_seconds", latency, labels={"model": model})
        prom.counter_inc("llm_tokens_total", tokens, labels={"model": model, "type": "total"})

prom.gauge_set("active_sessions", 42)
prom.gauge_set("cache_hit_rate", 0.38)
prom.gauge_set("gpu_utilization", 0.72)
prom.gauge_set("gpu_memory_used_gb", 12.4)

# 输出指标
metrics = prom.format_metrics()
print("Prometheus 指标示例（前15行）:")
for line in metrics.split("\n")[:15]:
    print(f"  {line}")
print(f"  ... (共{len(metrics.split(chr(10)))}行)")

# 统计摘要
print(f"\n指标摘要:")
for name, values in prom.histograms.items():
    arr = np.array(values)
    print(f"  {name}:")
    print(f"    count={len(arr)}, mean={np.mean(arr):.2f}s, "
          f"p50={np.percentile(arr,50):.2f}s, "
          f"p95={np.percentile(arr,95):.2f}s, "
          f"p99={np.percentile(arr,99):.2f}s")

# ============================================================================
# 4. Grafana 仪表板
# ============================================================================
print("\n--- 4. Grafana ---")
print("""
Grafana 仪表板设计：

┌─────────────────────────────────────────────────────────┐
│                   AI Service Dashboard                   │
├──────────────┬──────────────┬──────────────┬────────────┤
│   QPS        │  延迟 P95    │  错误率      │ Token/min  │
│   ▂▃▅▆▇    │  ▁▂▃▂▁     │  ▁▁▁▂▁      │ ▂▃▅▇▇    │
│   45.2/s     │  2.3s        │  1.2%        │ 15.2K      │
├──────────────┴──────────────┴──────────────┴────────────┤
│                    延迟分布                               │
│  ▁▂▅▇▅▃▂▁▁                                           │
│  P50: 1.2s  P95: 3.5s  P99: 8.2s                       │
├──────────────┬──────────────┬──────────────┬────────────┤
│  GPU 利用率  │  GPU 显存    │  活跃会话    │ 缓存命中率 │
│   72%        │  12.4/24 GB  │   42          │  38%       │
├──────────────┴──────────────┴──────────────┴────────────┤
│               模型调用分布（饼图）                        │
│  qwen2.5:7b  60%  ●                                     │
│  gpt-4o-mini 35%  ●                                     │
│  gpt-4o       5%  ●                                     │
└─────────────────────────────────────────────────────────┘

Docker Compose 集成：
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

# prometheus.yml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'ai-service'
    static_configs:
      - targets: ['api:8000']
```

PromQL 常用查询：
  rate(llm_requests_total[5m])                      # QPS
  histogram_quantile(0.95, llm_latency_seconds)     # P95 延迟
  sum(rate(llm_tokens_total[5m])) by (model)        # Token/s
  rate(llm_requests_total{status="error"}[5m])      # 错误率
""")

# ============================================================================
# 5. 告警规则
# ============================================================================
print("\n--- 5. 告警 ---")

class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.rules = []
        self.alerts = []

    def add_rule(self, name: str, condition: str,
                 severity: str, message: str):
        self.rules.append({
            "name": name,
            "condition": condition,
            "severity": severity,
            "message": message,
        })

    def evaluate(self, metrics: dict) -> list:
        """评估告警规则"""
        fired = []
        for rule in self.rules:
            try:
                if eval(rule["condition"], {"__builtins__": {}}, metrics):
                    alert = {
                        "name": rule["name"],
                        "severity": rule["severity"],
                        "message": rule["message"],
                        "time": datetime.now().isoformat(),
                    }
                    fired.append(alert)
                    self.alerts.append(alert)
            except:
                pass
        return fired

alerts = AlertManager()

# 定义告警规则
alerts.add_rule("高错误率", "error_rate > 0.05", "critical",
                "错误率超过5%: {error_rate:.1%}")
alerts.add_rule("高延迟", "p95_latency > 5", "warning",
                "P95延迟超过5秒: {p95_latency:.1f}s")
alerts.add_rule("GPU显存不足", "gpu_memory_pct > 0.9", "warning",
                "GPU显存使用超90%: {gpu_memory_pct:.0%}")
alerts.add_rule("Token预算超限", "daily_cost > daily_budget * 0.8", "warning",
                "费用超日预算80%: ${daily_cost:.2f}/${daily_budget:.2f}")
alerts.add_rule("低缓存命中", "cache_hit_rate < 0.2", "info",
                "缓存命中率低于20%: {cache_hit_rate:.0%}")

# 模拟指标
test_metrics = {
    "error_rate": 0.012,
    "p95_latency": 3.5,
    "gpu_memory_pct": 0.72,
    "daily_cost": 7.5,
    "daily_budget": 10.0,
    "cache_hit_rate": 0.38,
}

fired = alerts.evaluate(test_metrics)
print(f"告警评估 (当前指标):")
for k, v in test_metrics.items():
    print(f"  {k}: {v}")
print(f"\n触发告警: {len(fired)} 条")
for a in fired:
    icon = "🔴" if a["severity"] == "critical" else "🟡" if a["severity"] == "warning" else "🔵"
    print(f"  {icon} [{a['severity']}] {a['name']}: {a['message']}")

# 模拟异常
print(f"\n模拟异常场景:")
bad_metrics = {
    "error_rate": 0.08, "p95_latency": 7.2,
    "gpu_memory_pct": 0.95, "daily_cost": 9.5,
    "daily_budget": 10.0, "cache_hit_rate": 0.15,
}
fired = alerts.evaluate(bad_metrics)
print(f"触发告警: {len(fired)} 条")
for a in fired:
    icon = "🔴" if a["severity"] == "critical" else "🟡" if a["severity"] == "warning" else "🔵"
    print(f"  {icon} [{a['severity']}] {a['name']}")

print("""
告警通道：
  飞书/钉钉: Webhook → JSON POST
  邮件: SMTP
  PagerDuty: 值班轮换
  Slack: Webhook

告警去重与降噪：
  ✅ 相同告警5分钟内只发一次
  ✅ 告警恢复时发送恢复通知
  ✅ 按严重程度分级通知
""")

# ============================================================================
# 6. GPU 监控
# ============================================================================
print("\n--- 6. GPU 监控 ---")
print("""
GPU 监控指标：

  nvidia-smi 命令:
  ```
  +-------+----------------------+--------+----------+
  | GPU   | Name                 | Util%  | Memory   |
  +-------+----------------------+--------+----------+
  |   0   | NVIDIA A100 80GB    |  72%   | 52G/80G  |
  +-------+----------------------+--------+----------+
  ```

  Prometheus GPU Exporter:
  ```yaml
  services:
    nvidia-exporter:
      image: utkuozdemir/nvidia_gpu_exporter:1.2
      ports: ["9835:9835"]
      deploy:
        resources:
          reservations:
            devices:
              - driver: nvidia
                count: all
                capabilities: [gpu]
  ```

  关键 GPU 指标:
    nvidia_gpu_utilization       GPU 计算利用率
    nvidia_gpu_memory_used       显存使用量
    nvidia_gpu_memory_total      显存总量
    nvidia_gpu_temperature       温度
    nvidia_gpu_power_usage       功耗

  告警阈值建议:
    GPU 利用率 < 30%  → 资源浪费，考虑缩容
    GPU 利用率 > 90%  → 考虑扩容
    GPU 温度 > 85°C   → 散热问题
    显存 > 90%        → 需要优化或扩容
""")

print("=" * 60)
print("[完成] 第5课完成！你已经学会了：")
print("  [v] AI 服务监控四层体系")
print("  [v] Prometheus 指标类型与采集")
print("  [v] 自定义 AI 指标（LLM延迟/token/错误率）")
print("  [v] Grafana 仪表板设计")
print("  [v] 告警规则与通知")
print("  [v] GPU 监控")
print("=" * 60)
print("\n下一课：06_mlflow_and_cicd.py - MLflow 与 CI/CD")
