import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第4课：LLM 路由与模型管理
==============================================================================

不同任务适合不同模型——路由器自动选择最优模型。
兼顾成本、速度、质量。

本课内容：
1. LLM 路由概念
2. 模型注册与配置
3. 任务路由策略
4. 降级与容错
5. 成本控制
6. 多模型管理
==============================================================================
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum

import httpx

OLLAMA_URL = "http://localhost:11434"

print("=" * 60)
print("第4课：LLM 路由")
print("=" * 60)

# ============================================================================
# 1. LLM 路由概念
# ============================================================================
print("\n--- 1. 路由概念 ---")
print("""
为什么需要 LLM 路由？

  不同模型各有所长：
    GPT-4o:      最强推理，最贵
    GPT-4o-mini: 性价比高，通用
    DeepSeek:    代码能力强，便宜
    Qwen-local:  本地运行，免费
    Claude:      长文本，安全

  不同任务需求不同：
    简单聊天 → 用便宜的
    复杂推理 → 用最强的
    代码生成 → 用代码专长的
    翻译     → 用本地的（免费）

  LLM 路由器 = 根据任务自动选模型

  ┌─────────┐     ┌─────────────┐     ┌──────────┐
  │ 用户请求 │────→│  LLM Router  │────→│ 最优模型  │
  │         │     │             │     │          │
  │ 任务类型 │     │ 路由规则     │     │ GPT-4o   │
  │ 优先级   │     │ 成本预算     │     │ DeepSeek │
  │ 预算     │     │ 可用性检查   │     │ Qwen     │
  └─────────┘     └─────────────┘     └──────────┘
""")

# ============================================================================
# 2. 模型配置
# ============================================================================
print("\n--- 2. 模型配置 ---")

class TaskType(Enum):
    CHAT = "chat"
    CODE = "code"
    REASONING = "reasoning"
    TRANSLATION = "translation"
    SUMMARY = "summary"
    CREATIVE = "creative"

@dataclass
class ModelConfig:
    name: str
    provider: str         # openai / ollama / deepseek
    base_url: str = ""
    cost_per_1k: float = 0  # 每千token成本(美元)
    max_tokens: int = 4096
    supports_tools: bool = False
    quality_score: float = 0.5  # 0-1 质量评分
    speed_score: float = 0.5    # 0-1 速度评分
    status: str = "available"

# 模型注册
models = {
    "gpt-4o": ModelConfig(
        "gpt-4o", "openai", cost_per_1k=0.01,
        max_tokens=128000, supports_tools=True,
        quality_score=1.0, speed_score=0.6
    ),
    "gpt-4o-mini": ModelConfig(
        "gpt-4o-mini", "openai", cost_per_1k=0.0003,
        max_tokens=128000, supports_tools=True,
        quality_score=0.8, speed_score=0.8
    ),
    "deepseek-chat": ModelConfig(
        "deepseek-chat", "deepseek",
        base_url="https://api.deepseek.com",
        cost_per_1k=0.0003, max_tokens=64000,
        quality_score=0.85, speed_score=0.7
    ),
    "qwen2.5:7b": ModelConfig(
        "qwen2.5:7b", "ollama",
        base_url=OLLAMA_URL,
        cost_per_1k=0, max_tokens=32000,
        quality_score=0.7, speed_score=0.9
    ),
}

print(f"注册模型:")
print(f"  {'模型':<18} {'提供商':<10} {'成本/1K':>8} {'质量':>6} {'速度':>6}")
print(f"  {'-'*52}")
for name, m in models.items():
    print(f"  {name:<18} {m.provider:<10} ${m.cost_per_1k:<7.4f} {m.quality_score:>5.1f} {m.speed_score:>5.1f}")

# ============================================================================
# 3. 路由策略
# ============================================================================
print("\n--- 3. 路由策略 ---")

class LLMRouter:
    """LLM 路由器"""

    def __init__(self, models: dict):
        self.models = models
        self.routing_rules = {
            TaskType.CHAT: ["gpt-4o-mini", "qwen2.5:7b"],
            TaskType.CODE: ["deepseek-chat", "gpt-4o"],
            TaskType.REASONING: ["gpt-4o", "deepseek-chat"],
            TaskType.TRANSLATION: ["qwen2.5:7b", "gpt-4o-mini"],
            TaskType.SUMMARY: ["gpt-4o-mini", "qwen2.5:7b"],
            TaskType.CREATIVE: ["gpt-4o", "gpt-4o-mini"],
        }
        self.usage_log = []

    def route(self, task_type: TaskType,
              prefer_local: bool = False,
              max_cost: float = None,
              min_quality: float = 0.0) -> ModelConfig:
        """根据任务选择最优模型"""

        # 本地优先
        if prefer_local:
            local = [m for m in self.models.values()
                     if m.provider == "ollama" and m.status == "available"]
            if local:
                return local[0]

        # 按路由规则候选
        candidates = self.routing_rules.get(task_type, ["gpt-4o-mini"])
        available = []
        for name in candidates:
            m = self.models.get(name)
            if not m or m.status != "available":
                continue
            if max_cost is not None and m.cost_per_1k > max_cost:
                continue
            if m.quality_score < min_quality:
                continue
            available.append(m)

        if not available:
            # 降级到任何可用模型
            available = [m for m in self.models.values() if m.status == "available"]

        if not available:
            raise RuntimeError("没有可用模型")

        selected = available[0]
        self.usage_log.append({
            "task": task_type.value,
            "model": selected.name,
            "time": time.time(),
        })
        return selected

    def get_usage_summary(self) -> dict:
        summary = {}
        for entry in self.usage_log:
            model = entry["model"]
            summary[model] = summary.get(model, 0) + 1
        return summary

router = LLMRouter(models)

# 路由测试
test_tasks = [
    (TaskType.CHAT, False, None, 0),
    (TaskType.CODE, False, None, 0),
    (TaskType.REASONING, False, None, 0),
    (TaskType.TRANSLATION, True, None, 0),     # 本地优先
    (TaskType.SUMMARY, False, 0.001, 0),         # 成本限制
    (TaskType.CREATIVE, False, None, 0.9),       # 质量要求高
]

print(f"路由结果:")
for task, local, cost, quality in test_tasks:
    selected = router.route(task, prefer_local=local, max_cost=cost, min_quality=quality)
    constraints = []
    if local: constraints.append("本地优先")
    if cost: constraints.append(f"成本<{cost}")
    if quality: constraints.append(f"质量>{quality}")
    c_str = f" ({', '.join(constraints)})" if constraints else ""
    print(f"  {task.value:<12}{c_str:<20} → {selected.name}")

# ============================================================================
# 4. 降级与容错
# ============================================================================
print("\n--- 4. 降级容错 ---")

class ResilientLLMClient:
    """带降级能力的 LLM 客户端"""

    def __init__(self, router: LLMRouter):
        self.router = router

    def call(self, messages: list, task_type: TaskType,
             max_retries: int = 3) -> dict:
        """带降级重试的 LLM 调用"""
        errors = []
        tried_models = set()

        for attempt in range(max_retries):
            try:
                model = self.router.route(task_type)
                if model.name in tried_models:
                    # 标记不可用，选下一个
                    model.status = "unavailable"
                    model = self.router.route(task_type)

                tried_models.add(model.name)

                # 调用 LLM
                if model.provider == "ollama":
                    resp = httpx.post(f"{model.base_url}/api/chat", json={
                        "model": model.name,
                        "messages": messages,
                        "stream": False,
                        "options": {"num_predict": 200}
                    }, timeout=15.0)
                    reply = resp.json().get("message", {}).get("content", "")
                else:
                    reply = f"[{model.name}] 模拟回答（{model.provider}API）"

                # 恢复状态
                for m in self.router.models.values():
                    m.status = "available"

                return {
                    "reply": reply,
                    "model": model.name,
                    "attempt": attempt + 1,
                    "fallback": attempt > 0,
                }

            except Exception as e:
                errors.append(f"{model.name}: {type(e).__name__}")
                continue

        # 恢复状态
        for m in self.router.models.values():
            m.status = "available"

        return {"reply": "[所有模型不可用]", "errors": errors}

resilient = ResilientLLMClient(router)
result = resilient.call(
    [{"role": "user", "content": "你好"}],
    TaskType.CHAT
)
print(f"弹性调用:")
print(f"  模型: {result.get('model')}, 尝试次数: {result.get('attempt')}")
print(f"  降级: {result.get('fallback', False)}")
print(f"  回复: {result.get('reply', '')[:60]}...")

# ============================================================================
# 5. 成本控制
# ============================================================================
print("\n--- 5. 成本控制 ---")

class CostTracker:
    """成本追踪器"""

    def __init__(self, daily_budget: float = 10.0):
        self.daily_budget = daily_budget
        self.usage = []

    def record(self, model: str, prompt_tokens: int, completion_tokens: int):
        cost_per_1k = models.get(model, ModelConfig("", "")).cost_per_1k
        cost = (prompt_tokens + completion_tokens) / 1000 * cost_per_1k
        self.usage.append({
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": cost,
            "time": time.time(),
        })
        return cost

    @property
    def total_cost(self):
        return sum(u["cost"] for u in self.usage)

    @property
    def remaining_budget(self):
        return self.daily_budget - self.total_cost

    def can_afford(self, model: str, estimated_tokens: int) -> bool:
        cost_per_1k = models.get(model, ModelConfig("", "")).cost_per_1k
        estimated_cost = estimated_tokens / 1000 * cost_per_1k
        return self.remaining_budget >= estimated_cost

    def summary(self) -> dict:
        by_model = {}
        for u in self.usage:
            m = u["model"]
            by_model.setdefault(m, {"calls": 0, "tokens": 0, "cost": 0})
            by_model[m]["calls"] += 1
            by_model[m]["tokens"] += u["prompt_tokens"] + u["completion_tokens"]
            by_model[m]["cost"] += u["cost"]
        return {
            "total_cost": round(self.total_cost, 4),
            "remaining": round(self.remaining_budget, 4),
            "by_model": by_model,
        }

tracker = CostTracker(daily_budget=10.0)

# 模拟使用
for model, pt, ct in [("gpt-4o", 500, 300), ("gpt-4o-mini", 1000, 500),
                       ("gpt-4o-mini", 800, 400), ("qwen2.5:7b", 1000, 600)]:
    cost = tracker.record(model, pt, ct)

summary = tracker.summary()
print(f"成本统计:")
print(f"  总费用: ${summary['total_cost']}")
print(f"  剩余预算: ${summary['remaining']}")
for m, info in summary["by_model"].items():
    print(f"  {m}: {info['calls']}次, {info['tokens']}tokens, ${info['cost']:.4f}")

# ============================================================================
# 6. 多模型管理
# ============================================================================
print("\n--- 6. 模型管理 ---")
print("""
生产环境模型管理：

1. 健康检查
   定期 ping 每个模型，标记不可用的
   ```python
   async def health_check():
       for model in models.values():
           try:
               await call_model(model, "ping", timeout=5)
               model.status = "available"
           except:
               model.status = "unavailable"
   ```

2. 模型热切换
   通过配置文件/API 动态调整路由规则
   无需重启服务

3. A/B 测试
   10% 流量用新模型，90% 用老模型
   对比效果后再全量切换

4. 模型版本管理
   记录每个请求用的模型版本
   方便回溯和问题排查

路由使用统计:
""")

usage = router.get_usage_summary()
for model, count in usage.items():
    print(f"  {model}: {count} 次")

print("\n" + "=" * 60)
print("[完成] 第4课完成！你已经学会了：")
print("  [v] LLM 路由概念与价值")
print("  [v] 模型注册与配置")
print("  [v] 任务路由（按类型/成本/质量）")
print("  [v] 降级容错（自动重试/切换模型）")
print("  [v] 成本追踪与预算控制")
print("  [v] 多模型管理（健康检查/热切换/A/B测试）")
print("=" * 60)
print("\n下一课：05_observability.py - 可观测性")
