import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：可观测性（日志 / 追踪 / 监控）
==============================================================================

AI 服务上线后，需要知道：
  发生了什么（日志）、慢在哪里（追踪）、健不健康（监控）

本课内容：
1. 可观测性三要素
2. 结构化日志
3. 调用链路追踪
4. 性能指标监控
5. Token 用量统计
6. 告警与仪表板
==============================================================================
"""

import json
import time
import uuid
import logging
from datetime import datetime
from collections import defaultdict

print("=" * 60)
print("第5课：可观测性")
print("=" * 60)

# ============================================================================
# 1. 三要素
# ============================================================================
print("\n--- 1. 三要素 ---")
print("""
可观测性 = Logs + Traces + Metrics

┌──────────────────┬──────────────────────────────────────┐
│  日志 (Logs)     │  记录"发生了什么"                    │
│                  │  请求内容、错误信息、关键事件         │
│                  │  工具: Python logging / ELK           │
├──────────────────┼──────────────────────────────────────┤
│  追踪 (Traces)   │  记录"慢在哪里"                     │
│                  │  每个步骤的耗时和数据流               │
│                  │  工具: LangSmith / OpenTelemetry      │
├──────────────────┼──────────────────────────────────────┤
│  指标 (Metrics)  │  记录"整体健康度"                    │
│                  │  QPS、延迟、错误率、token用量         │
│                  │  工具: Prometheus + Grafana           │
└──────────────────┴──────────────────────────────────────┘

AI 服务特有的可观测需求：
  • Token 用量和成本
  • LLM 响应延迟（首token / 总延迟）
  • 检索质量（RAG 场景）
  • 幻觉率 / 回答质量
  • 模型可用性
""")

# ============================================================================
# 2. 结构化日志
# ============================================================================
print("\n--- 2. 结构化日志 ---")

class StructuredLogger:
    """结构化 AI 服务日志"""

    def __init__(self, service_name: str = "ai-service"):
        self.service = service_name
        self.logs = []

    def _log(self, level: str, event: str, **kwargs):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "service": self.service,
            "event": event,
            **kwargs,
        }
        self.logs.append(entry)
        # 格式化输出
        extras = " ".join(f"{k}={v}" for k, v in kwargs.items())
        print(f"  [{level}] {event} {extras}")

    def info(self, event: str, **kwargs):
        self._log("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs):
        self._log("WARN", event, **kwargs)

    def error(self, event: str, **kwargs):
        self._log("ERROR", event, **kwargs)

    def llm_call(self, model: str, latency_ms: int, tokens: int, **kwargs):
        """记录 LLM 调用"""
        self._log("INFO", "llm_call",
                  model=model, latency_ms=latency_ms, tokens=tokens, **kwargs)

    def request(self, method: str, path: str, status: int,
                latency_ms: int, **kwargs):
        """记录 API 请求"""
        level = "INFO" if status < 400 else "ERROR"
        self._log(level, "http_request",
                  method=method, path=path, status=status,
                  latency_ms=latency_ms, **kwargs)

logger = StructuredLogger()

# 模拟日志记录
logger.info("service_started", version="1.0.0")
logger.llm_call(model="qwen2.5:7b", latency_ms=850, tokens=320, task="chat")
logger.request("POST", "/chat", 200, latency_ms=920, user="user123")
logger.llm_call(model="gpt-4o-mini", latency_ms=1200, tokens=580, task="rag")
logger.warning("high_latency", model="gpt-4o", latency_ms=5200)
logger.error("llm_timeout", model="gpt-4o", timeout_s=30)

print(f"""
生产日志最佳实践：
  ✅ JSON 格式（便于 ELK 解析）
  ✅ 包含 request_id（关联请求链路）
  ✅ 包含 user_id（追踪用户行为）
  ✅ 记录 model/tokens/latency
  ❌ 不记录完整 prompt（隐私+空间）
  ❌ 不记录 API key
""")

# ============================================================================
# 3. 调用链路追踪
# ============================================================================
print("\n--- 3. 链路追踪 ---")

class AITracer:
    """AI 调用链路追踪"""

    def __init__(self):
        self.traces = {}

    def start_trace(self, request_id: str = None) -> str:
        trace_id = request_id or str(uuid.uuid4())[:8]
        self.traces[trace_id] = {
            "trace_id": trace_id,
            "start_time": time.time(),
            "steps": [],
            "metadata": {},
        }
        return trace_id

    def add_step(self, trace_id: str, name: str, **data) -> None:
        step = {
            "name": name,
            "start_time": time.time(),
            **data,
        }
        self.traces[trace_id]["steps"].append(step)

    def end_step(self, trace_id: str, **data) -> None:
        steps = self.traces[trace_id]["steps"]
        if steps:
            steps[-1]["end_time"] = time.time()
            steps[-1]["duration_ms"] = round(
                (steps[-1]["end_time"] - steps[-1]["start_time"]) * 1000
            )
            steps[-1].update(data)

    def end_trace(self, trace_id: str) -> dict:
        trace = self.traces[trace_id]
        trace["end_time"] = time.time()
        trace["total_ms"] = round((trace["end_time"] - trace["start_time"]) * 1000)
        return trace

    def print_trace(self, trace_id: str):
        trace = self.traces[trace_id]
        print(f"  Trace: {trace['trace_id']} ({trace.get('total_ms', '?')}ms)")
        for step in trace["steps"]:
            duration = step.get("duration_ms", "?")
            extras = {k: v for k, v in step.items()
                      if k not in ("name", "start_time", "end_time", "duration_ms")}
            extras_str = " ".join(f"{k}={v}" for k, v in extras.items())
            print(f"    ├── {step['name']}: {duration}ms {extras_str}")

tracer = AITracer()

# 模拟 RAG 请求追踪
tid = tracer.start_trace()

tracer.add_step(tid, "input_validation")
time.sleep(0.001)
tracer.end_step(tid, status="ok")

tracer.add_step(tid, "embedding", model="nomic-embed-text")
time.sleep(0.05)
tracer.end_step(tid, tokens=15, dim=768)

tracer.add_step(tid, "vector_search", engine="chromadb")
time.sleep(0.02)
tracer.end_step(tid, results=5, top_score=0.89)

tracer.add_step(tid, "reranking")
time.sleep(0.01)
tracer.end_step(tid, input=5, output=3)

tracer.add_step(tid, "llm_generation", model="qwen2.5:7b")
time.sleep(0.1)
tracer.end_step(tid, prompt_tokens=450, completion_tokens=120)

tracer.add_step(tid, "response_format")
time.sleep(0.001)
tracer.end_step(tid)

trace = tracer.end_trace(tid)
tracer.print_trace(tid)

print("""
生产追踪工具：
  LangSmith:      LangChain 官方，AI 专用
  OpenTelemetry:  通用标准，兼容 Jaeger/Zipkin
  Langfuse:       开源 LLM 可观测平台
""")

# ============================================================================
# 4. 性能指标
# ============================================================================
print("\n--- 4. 性能指标 ---")

class MetricsCollector:
    """性能指标收集器"""

    def __init__(self):
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.gauges = {}

    def increment(self, name: str, value: int = 1, labels: dict = None):
        key = self._key(name, labels)
        self.counters[key] += value

    def observe(self, name: str, value: float, labels: dict = None):
        key = self._key(name, labels)
        self.histograms[key].append(value)

    def set_gauge(self, name: str, value: float, labels: dict = None):
        key = self._key(name, labels)
        self.gauges[key] = value

    def _key(self, name: str, labels: dict = None) -> str:
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name

    def summary(self) -> dict:
        result = {"counters": dict(self.counters), "gauges": dict(self.gauges)}
        result["histograms"] = {}
        for name, values in self.histograms.items():
            import numpy as np
            arr = np.array(values)
            result["histograms"][name] = {
                "count": len(values),
                "mean": round(float(np.mean(arr)), 2),
                "p50": round(float(np.percentile(arr, 50)), 2),
                "p95": round(float(np.percentile(arr, 95)), 2),
                "p99": round(float(np.percentile(arr, 99)), 2),
            }
        return result

metrics = MetricsCollector()

# 模拟指标收集
import numpy as np
np.random.seed(42)

for _ in range(100):
    model = np.random.choice(["qwen2.5:7b", "gpt-4o-mini"])
    latency = np.random.exponential(800) + 200
    tokens = int(np.random.normal(400, 100))
    status = np.random.choice([200, 200, 200, 200, 500], p=[0.24, 0.24, 0.24, 0.24, 0.04])

    metrics.increment("requests_total", labels={"model": model})
    metrics.observe("request_latency_ms", latency, labels={"model": model})
    metrics.observe("tokens_used", tokens, labels={"model": model})
    if status >= 400:
        metrics.increment("errors_total", labels={"model": model})

metrics.set_gauge("active_sessions", 42)
metrics.set_gauge("cache_hit_rate", 0.35)

summary = metrics.summary()
print(f"指标摘要:")
print(f"  计数器:")
for k, v in summary["counters"].items():
    print(f"    {k}: {v}")
print(f"  仪表盘:")
for k, v in summary["gauges"].items():
    print(f"    {k}: {v}")
print(f"  直方图:")
for k, v in summary["histograms"].items():
    print(f"    {k}: mean={v['mean']}, p95={v['p95']}, p99={v['p99']}")

# ============================================================================
# 5. Token 统计
# ============================================================================
print("\n--- 5. Token 统计 ---")

class TokenTracker:
    """Token 用量统计"""

    def __init__(self):
        self.usage = []

    def record(self, model: str, prompt_tokens: int,
               completion_tokens: int, cost_per_1k: float = 0):
        total = prompt_tokens + completion_tokens
        cost = total / 1000 * cost_per_1k
        self.usage.append({
            "model": model,
            "prompt": prompt_tokens,
            "completion": completion_tokens,
            "total": total,
            "cost": cost,
            "time": time.time(),
        })

    def summary(self) -> dict:
        by_model = {}
        for u in self.usage:
            m = u["model"]
            if m not in by_model:
                by_model[m] = {"calls": 0, "prompt": 0, "completion": 0, "cost": 0}
            by_model[m]["calls"] += 1
            by_model[m]["prompt"] += u["prompt"]
            by_model[m]["completion"] += u["completion"]
            by_model[m]["cost"] += u["cost"]
        total_cost = sum(v["cost"] for v in by_model.values())
        total_tokens = sum(u["total"] for u in self.usage)
        return {"by_model": by_model, "total_cost": round(total_cost, 4),
                "total_tokens": total_tokens, "total_calls": len(self.usage)}

token_tracker = TokenTracker()
for _ in range(50):
    model = np.random.choice(["qwen2.5:7b", "gpt-4o-mini"])
    pt = int(np.random.normal(300, 80))
    ct = int(np.random.normal(150, 50))
    cost = 0 if model == "qwen2.5:7b" else 0.0003
    token_tracker.record(model, pt, ct, cost)

ts = token_tracker.summary()
print(f"Token 统计:")
print(f"  总调用: {ts['total_calls']}次, 总token: {ts['total_tokens']}, 总费用: ${ts['total_cost']}")
for m, info in ts["by_model"].items():
    print(f"  {m}: {info['calls']}次, prompt={info['prompt']}, "
          f"completion={info['completion']}, cost=${info['cost']:.4f}")

# ============================================================================
# 6. 告警
# ============================================================================
print("\n--- 6. 告警 ---")
print("""
告警规则：
  🔴 错误率 > 5%（1分钟内）
  🔴 LLM 调用延迟 P95 > 5秒
  🟡 Token 用量超日预算 80%
  🟡 缓存命中率 < 20%
  🟡 活跃会话 > 1000
  🔵 新模型版本可用

告警通道：
  飞书/钉钉 Webhook
  邮件通知
  PagerDuty（值班轮换）

仪表板 (Grafana)：
  ┌────────────┬────────────┬────────────┐
  │   QPS      │  延迟 P95  │  错误率     │
  │   ▂▃▅▆▇   │  ▁▂▃▂▁    │  ▁▁▁▂▁     │
  ├────────────┼────────────┼────────────┤
  │  Token用量 │  模型分布  │  缓存命中   │
  │  ▂▃▅▇▇   │  ◉40% ◯   │  35%       │
  └────────────┴────────────┴────────────┘
""")

print("=" * 60)
print("[完成] 第5课完成！你已经学会了：")
print("  [v] 可观测性三要素（日志/追踪/指标）")
print("  [v] 结构化日志设计")
print("  [v] AI 调用链路追踪")
print("  [v] 性能指标收集（计数器/直方图/仪表盘）")
print("  [v] Token 用量与成本统计")
print("  [v] 告警规则与仪表板")
print("=" * 60)
print("\n下一课：06_safety_and_guard.py - 安全护栏")
