import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第7课：完整项目 - AI 服务运维平台
==============================================================================

整合前6课知识，构建一个 AI 服务运维管理平台：

功能：
1. 模型注册与版本管理
2. 服务健康检查
3. 性能指标采集
4. 告警系统
5. 自动化评估
6. 部署管理

架构：
  模型注册 → 评估 → 质量门禁 → Docker 部署 → 监控 → 告警
==============================================================================
"""

import json
import re
import time
import hashlib
import uuid
import numpy as np
from collections import defaultdict, OrderedDict
from datetime import datetime

import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"

print("=" * 60)
print("第7课：完整项目 - AI 服务运维平台")
print("=" * 60)

# ============================================================================
# 1. 模型注册表
# ============================================================================

class ModelRegistry:
    """模型注册与版本管理"""

    def __init__(self):
        self.models = {}

    def register(self, name: str, run_id: str, metrics: dict = None,
                 params: dict = None) -> dict:
        if name not in self.models:
            self.models[name] = {"versions": []}
        version = len(self.models[name]["versions"]) + 1
        entry = {
            "version": version, "run_id": run_id,
            "stage": "None", "metrics": metrics or {},
            "params": params or {},
            "created": datetime.now().isoformat(),
        }
        self.models[name]["versions"].append(entry)
        return entry

    def promote(self, name: str, version: int, stage: str):
        versions = self.models[name]["versions"]
        if stage == "Production":
            for v in versions:
                if v["stage"] == "Production":
                    v["stage"] = "Archived"
        versions[version - 1]["stage"] = stage

    def get_production(self, name: str) -> dict:
        for v in self.models.get(name, {}).get("versions", []):
            if v["stage"] == "Production":
                return v
        return None

    def rollback(self, name: str) -> dict:
        """回滚到上一个 Production 版本"""
        versions = self.models[name]["versions"]
        archived = [v for v in versions if v["stage"] == "Archived"]
        if archived:
            latest_archived = archived[-1]
            # 当前 Production → Archived
            for v in versions:
                if v["stage"] == "Production":
                    v["stage"] = "Archived"
            latest_archived["stage"] = "Production"
            return latest_archived
        return None

# ============================================================================
# 2. 健康检查
# ============================================================================

class HealthChecker:
    """服务健康检查"""

    def __init__(self):
        self.services = {}
        self.history = []

    def register_service(self, name: str, url: str, check_type: str = "http"):
        self.services[name] = {"url": url, "type": check_type, "status": "unknown"}

    def check_all(self) -> dict:
        results = {}
        for name, svc in self.services.items():
            start = time.time()
            try:
                resp = httpx.get(svc["url"], timeout=3.0)
                latency = round((time.time() - start) * 1000)
                status = "healthy" if resp.status_code < 400 else "degraded"
                results[name] = {"status": status, "latency_ms": latency}
            except:
                results[name] = {"status": "unhealthy", "latency_ms": -1}
            svc["status"] = results[name]["status"]

        self.history.append({"time": datetime.now().isoformat(), "results": results})
        return results

# ============================================================================
# 3. 指标采集
# ============================================================================

class MetricsCollector:
    """性能指标采集"""

    def __init__(self):
        self.counters = defaultdict(float)
        self.histograms = defaultdict(list)
        self.gauges = {}

    def inc(self, name: str, value: float = 1, labels: dict = None):
        key = f"{name}" + (f"_{json.dumps(labels, sort_keys=True)}" if labels else "")
        self.counters[key] += value

    def observe(self, name: str, value: float):
        self.histograms[name].append(value)

    def set(self, name: str, value: float):
        self.gauges[name] = value

    def summary(self) -> dict:
        result = {"counters": dict(self.counters), "gauges": dict(self.gauges)}
        result["histograms"] = {}
        for name, vals in self.histograms.items():
            arr = np.array(vals)
            result["histograms"][name] = {
                "count": len(vals), "mean": round(float(np.mean(arr)), 2),
                "p50": round(float(np.percentile(arr, 50)), 2),
                "p95": round(float(np.percentile(arr, 95)), 2),
            }
        return result

# ============================================================================
# 4. 告警系统
# ============================================================================

class AlertSystem:
    """告警系统"""

    def __init__(self):
        self.rules = []
        self.fired_alerts = []

    def add_rule(self, name: str, check_fn, severity: str = "warning",
                 message: str = ""):
        self.rules.append({
            "name": name, "check_fn": check_fn,
            "severity": severity, "message": message,
        })

    def evaluate(self, context: dict) -> list:
        fired = []
        for rule in self.rules:
            try:
                if rule["check_fn"](context):
                    alert = {
                        "name": rule["name"],
                        "severity": rule["severity"],
                        "message": rule["message"],
                        "time": datetime.now().isoformat(),
                    }
                    fired.append(alert)
                    self.fired_alerts.append(alert)
            except:
                pass
        return fired

# ============================================================================
# 5. 评估流水线
# ============================================================================

class EvalPipeline:
    """自动化评估"""

    def __init__(self, test_cases: list):
        self.test_cases = test_cases

    def run(self, model_fn) -> dict:
        correct, latencies = 0, []
        for case in self.test_cases:
            start = time.time()
            try:
                answer = model_fn(case["question"])
                latencies.append(time.time() - start)
                if any(kw.lower() in answer.lower() for kw in case.get("keywords", [])):
                    correct += 1
            except:
                pass
        arr = np.array(latencies) if latencies else np.array([0])
        return {
            "accuracy": correct / len(self.test_cases) if self.test_cases else 0,
            "avg_latency": round(float(np.mean(arr)), 3),
            "p95_latency": round(float(np.percentile(arr, 95)), 3),
            "total": len(self.test_cases), "correct": correct,
        }

    def quality_gate(self, results: dict, min_acc=0.8, max_lat=5.0) -> bool:
        return results["accuracy"] >= min_acc and results["p95_latency"] <= max_lat

# ============================================================================
# 6. 运维平台
# ============================================================================
print("\n--- 1. 构建平台 ---")

class MLOpsPlatform:
    """AI 服务运维平台"""

    def __init__(self):
        self.registry = ModelRegistry()
        self.health = HealthChecker()
        self.metrics = MetricsCollector()
        self.alerts = AlertSystem()
        self.deployments = []

        # 注册服务
        self.health.register_service("ollama", f"{OLLAMA_URL}/")
        self.health.register_service("ollama_api", f"{OLLAMA_URL}/api/tags")

        # 告警规则
        self.alerts.add_rule(
            "高错误率",
            lambda ctx: ctx.get("error_rate", 0) > 0.05,
            "critical", "错误率>5%"
        )
        self.alerts.add_rule(
            "高延迟",
            lambda ctx: ctx.get("p95_latency", 0) > 5,
            "warning", "P95延迟>5s"
        )
        self.alerts.add_rule(
            "服务不健康",
            lambda ctx: any(s.get("status") == "unhealthy"
                          for s in ctx.get("health", {}).values()),
            "critical", "有服务不可用"
        )

    def register_model(self, name: str, run_id: str,
                       metrics: dict = None, params: dict = None) -> dict:
        entry = self.registry.register(name, run_id, metrics, params)
        self.metrics.inc("models_registered")
        return entry

    def deploy_model(self, name: str, version: int) -> dict:
        """部署模型（模拟）"""
        self.registry.promote(name, version, "Production")
        deployment = {
            "model": name, "version": version,
            "status": "deployed",
            "time": datetime.now().isoformat(),
        }
        self.deployments.append(deployment)
        self.metrics.inc("deployments")
        return deployment

    def evaluate_model(self, model_fn, test_cases: list) -> dict:
        """评估模型"""
        pipeline = EvalPipeline(test_cases)
        results = pipeline.run(model_fn)
        passed = pipeline.quality_gate(results)
        self.metrics.inc("evaluations")
        return {"results": results, "passed": passed}

    def check_health(self) -> dict:
        return self.health.check_all()

    def check_alerts(self) -> list:
        health = self.check_health()
        metrics_summary = self.metrics.summary()
        histograms = metrics_summary.get("histograms", {})
        latency_info = histograms.get("request_latency", {})

        context = {
            "health": health,
            "error_rate": self.metrics.counters.get("errors", 0) /
                         max(self.metrics.counters.get("requests", 1), 1),
            "p95_latency": latency_info.get("p95", 0),
        }
        return self.alerts.evaluate(context)

    def status(self) -> dict:
        return {
            "models": {name: len(data["versions"])
                      for name, data in self.registry.models.items()},
            "deployments": len(self.deployments),
            "metrics": self.metrics.summary(),
            "alerts": len(self.alerts.fired_alerts),
        }

platform = MLOpsPlatform()
print("MLOps 平台已启动！")

# ============================================================================
# 7. 使用演示
# ============================================================================

# --- 注册模型 ---
print("\n--- 2. 注册模型 ---")

v1 = platform.register_model("qa-bot", "run-001",
    metrics={"accuracy": 0.85, "f1": 0.83},
    params={"method": "LoRA", "lora_r": 16})
v2 = platform.register_model("qa-bot", "run-002",
    metrics={"accuracy": 0.89, "f1": 0.87},
    params={"method": "QLoRA", "lora_r": 8})
v3 = platform.register_model("qa-bot", "run-003",
    metrics={"accuracy": 0.91, "f1": 0.90},
    params={"method": "QLoRA", "lora_r": 16})

for v in platform.registry.list_versions("qa-bot"):
    print(f"  v{v['version']}: {v['params'].get('method','')} "
          f"acc={v['metrics'].get('accuracy',0):.2f} stage={v['stage']}")

# --- 评估 ---
print("\n--- 3. 评估模型 ---")

test_cases = [
    {"question": "什么是RAG？", "keywords": ["检索", "生成"]},
    {"question": "Docker有什么用？", "keywords": ["容器", "部署"]},
    {"question": "LoRA原理？", "keywords": ["低秩", "矩阵"]},
    {"question": "监控有哪些指标？", "keywords": ["延迟", "错误"]},
    {"question": "什么是向量数据库？", "keywords": ["embedding", "向量"]},
]

def mock_model(q):
    answers = {
        "RAG": "RAG是检索增强生成，通过检索文档辅助生成",
        "Docker": "Docker用于容器化部署，环境隔离",
        "LoRA": "LoRA通过低秩矩阵分解减少参数",
        "监控": "关键指标包括延迟、错误率、吞吐量",
        "向量": "向量数据库存储embedding向量，支持语义搜索",
    }
    for k, v in answers.items():
        if k in q:
            time.sleep(0.01)
            return v
    return "不知道"

eval_result = platform.evaluate_model(mock_model, test_cases)
print(f"  准确率: {eval_result['results']['accuracy']:.2f}")
print(f"  P95延迟: {eval_result['results']['p95_latency']}s")
print(f"  质量门禁: {'✓ 通过' if eval_result['passed'] else '✗ 未通过'}")

# --- 部署 ---
print("\n--- 4. 部署模型 ---")

if eval_result["passed"]:
    deploy = platform.deploy_model("qa-bot", 3)
    print(f"  部署: {deploy}")
    prod = platform.registry.get_production("qa-bot")
    print(f"  当前生产: v{prod['version']}")

# --- 健康检查 ---
print("\n--- 5. 健康检查 ---")

health = platform.check_health()
for name, result in health.items():
    icon = "✓" if result["status"] == "healthy" else "✗"
    print(f"  {icon} {name}: {result['status']} ({result['latency_ms']}ms)")

# --- 模拟运行指标 ---
print("\n--- 6. 模拟运行 ---")

np.random.seed(42)
for _ in range(100):
    platform.metrics.inc("requests")
    latency = np.random.exponential(1.2) + 0.3
    platform.metrics.observe("request_latency", latency)
    if np.random.random() < 0.02:
        platform.metrics.inc("errors")

platform.metrics.set("active_sessions", 35)
platform.metrics.set("cache_hit_rate", 0.42)

# --- 告警 ---
print("\n--- 7. 告警检查 ---")

alerts = platform.check_alerts()
if alerts:
    for a in alerts:
        print(f"  [{a['severity']}] {a['name']}: {a['message']}")
else:
    print("  无告警 ✓")

# --- 平台状态 ---
status = platform.status()

print(f"""
┌────────────────────────────────────────────────────────┐
│          AI 服务运维平台 - 项目架构                      │
├────────────────────────────────────────────────────────┤
│                                                        │
│  MLOpsPlatform（主平台）                               │
│  ├── register_model()    注册模型版本                  │
│  ├── evaluate_model()    自动化评估                    │
│  ├── deploy_model()      部署到生产                    │
│  ├── check_health()      服务健康检查                  │
│  ├── check_alerts()      告警评估                      │
│  └── status()            平台状态                      │
│                                                        │
│  组件                                                  │
│  ├── ModelRegistry:  模型版本管理                      │
│  │   └── None → Staging → Production → Archived       │
│  ├── HealthChecker:  多服务健康检查                    │
│  ├── MetricsCollector: 指标采集                        │
│  ├── AlertSystem:    告警规则引擎                      │
│  └── EvalPipeline:   自动评估+质量门禁               │
│                                                        │
│  整合的知识                                            │
│  ├── 第1课: Docker 容器化                             │
│  ├── 第2课: Docker Compose 编排                       │
│  ├── 第3课: 模型服务（Ollama/vLLM）                  │
│  ├── 第4课: 推理优化（量化/批处理/KV Cache）         │
│  ├── 第5课: 监控体系（Prometheus/Grafana）            │
│  └── 第6课: MLflow 与 CI/CD                           │
│                                                        │
│  当前状态                                              │
│  ├── 注册模型: {status['models']}                     │
│  ├── 部署次数: {status['deployments']}                              │
│  ├── 告警次数: {status['alerts']}                              │
│  └── 请求统计: {status['metrics']['counters']}        │
│                                                        │
│  扩展方向                                              │
│  → FastAPI Web 管理界面                                │
│  → 真实 MLflow 集成                                    │
│  → Prometheus + Grafana 监控                           │
│  → GitHub Actions CI/CD                                │
│  → A/B 测试 & 灰度发布                                │
│  → GPU 资源调度                                        │
│  → 自动扩缩容                                          │
└────────────────────────────────────────────────────────┘
""")

print("=" * 60)
print("[完成] 第7课完成！你已经学会了：")
print("  [v] 模型注册与版本管理")
print("  [v] 服务健康检查")
print("  [v] 性能指标采集")
print("  [v] 告警系统")
print("  [v] 自动化评估与质量门禁")
print("  [v] 部署管理")
print("  [v] 端到端 MLOps 运维平台")
print("=" * 60)
print("\nlearn-mlops 课程全部完成！🎉")
print("\n恭喜！所有深讲课程全部完成！")
