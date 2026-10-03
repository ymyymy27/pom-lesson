import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第6课：Prompt 优化与评估
==============================================================================

写 Prompt 不是一次到位的，需要：
  设计 → 测试 → 评估 → 优化 → 重测 → 上线

本课内容：
1. Prompt 评估指标
2. A/B 测试框架
3. 常见失败模式与修复
4. Token 成本优化
5. 延迟优化
6. Prompt 版本管理
==============================================================================
"""

import json
import time
import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"

def chat(prompt: str, system: str = "", temperature: float = 0.3,
         max_tokens: int = 500) -> tuple:
    """返回 (结果, 耗时ms)"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    start = time.time()
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL, "messages": messages, "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens}
        }, timeout=30.0)
        elapsed = int((time.time() - start) * 1000)
        content = resp.json().get("message", {}).get("content", "")
        return content, elapsed
    except:
        return "[模拟回答]", 0

print("=" * 60)
print("第6课：Prompt 优化与评估")
print("=" * 60)

# ============================================================================
# 1. 评估指标
# ============================================================================
print("\n--- 1. 评估指标 ---")
print("""
Prompt 评估的五大维度：

┌──────────────────┬──────────────────────────────────────┐
│  维度             │  评估方法                             │
├──────────────────┼──────────────────────────────────────┤
│  准确性          │  输出是否正确（人工/自动评测）       │
│  一致性          │  多次运行结果是否稳定               │
│  格式合规        │  输出是否符合指定格式               │
│  完整性          │  是否包含所有要求的信息             │
│  安全性          │  是否违规/幻觉/泄露                 │
├──────────────────┼──────────────────────────────────────┤
│  效率             │                                       │
│  Token 数量      │  输入+输出的 token 总数              │
│  延迟            │  首字节时间 + 总时间                 │
│  成本            │  每次调用的费用                      │
└──────────────────┴──────────────────────────────────────┘

自动化评估方法：
1. 精确匹配：输出 == 标准答案
2. 包含检查：输出中包含关键信息
3. JSON 解析：能否成功解析为指定格式
4. LLM 评判：用另一个 LLM 打分（LLM-as-Judge）
""")

# ============================================================================
# 2. A/B 测试框架
# ============================================================================
print("\n--- 2. A/B 测试 ---")

class PromptEvaluator:
    """Prompt A/B 测试框架"""

    def __init__(self):
        self.results = []

    def evaluate(self, name: str, prompt: str, system: str,
                 test_cases: list, criteria: dict) -> dict:
        """评估单个 Prompt"""
        scores = {"accuracy": 0, "format_ok": 0, "latency_ms": 0}
        details = []

        for tc in test_cases:
            input_text = tc["input"]
            expected = tc.get("expected", "")
            full_prompt = prompt.replace("{input}", input_text)

            result, latency = chat(full_prompt, system=system)
            scores["latency_ms"] += latency

            # 格式检查
            format_ok = True
            if criteria.get("json_required"):
                try:
                    json.loads(result.strip().strip("`").replace("json\n", ""))
                    format_ok = True
                except:
                    # 尝试提取 JSON
                    start = result.find("{")
                    end = result.rfind("}")
                    if start != -1 and end != -1:
                        try:
                            json.loads(result[start:end+1])
                        except:
                            format_ok = False
                    else:
                        format_ok = False

            if format_ok:
                scores["format_ok"] += 1

            # 准确性（简单的关键词匹配）
            if expected:
                if any(kw in result for kw in expected.split("|")):
                    scores["accuracy"] += 1

            details.append({
                "input": input_text[:30],
                "output": result[:60],
                "format_ok": format_ok,
                "latency": latency,
            })

        n = len(test_cases)
        report = {
            "name": name,
            "accuracy": scores["accuracy"] / n if n else 0,
            "format_rate": scores["format_ok"] / n if n else 0,
            "avg_latency": scores["latency_ms"] / n if n else 0,
            "details": details,
        }
        self.results.append(report)
        return report

evaluator = PromptEvaluator()

# 定义测试用例
test_cases = [
    {"input": "这家餐厅太好吃了，强烈推荐！", "expected": "positive|正面"},
    {"input": "等了一个小时才上菜，太差了", "expected": "negative|负面"},
    {"input": "味道一般，价格还行", "expected": "neutral|中性"},
    {"input": "环境很好但服务态度恶劣", "expected": "negative|负面|mixed"},
]

# Prompt A：简单版
report_a = evaluator.evaluate(
    name="Prompt A (简单)",
    prompt="判断以下评论的情感（positive/negative/neutral）：\n{input}",
    system="",
    test_cases=test_cases,
    criteria={"json_required": False}
)

# Prompt B：结构化版
report_b = evaluator.evaluate(
    name="Prompt B (结构化)",
    prompt='分析评论情感，输出JSON：{"sentiment":"positive/negative/neutral","confidence":0.0-1.0}\n只输出JSON。\n评论：{input}',
    system="你是情感分析专家，只输出JSON。",
    test_cases=test_cases,
    criteria={"json_required": True}
)

# Prompt C：Few-shot版
report_c = evaluator.evaluate(
    name="Prompt C (Few-shot)",
    prompt="""判断评论情感，输出JSON。

示例：
"好吃" → {"sentiment":"positive","confidence":0.95}
"太差" → {"sentiment":"negative","confidence":0.90}
"还行" → {"sentiment":"neutral","confidence":0.70}

评论：{input}
只输出JSON：""",
    system="",
    test_cases=test_cases,
    criteria={"json_required": True}
)

# 对比报告
print("\nA/B 测试结果:")
print(f"{'名称':<25} {'准确率':>8} {'格式率':>8} {'延迟ms':>8}")
print("-" * 55)
for r in [report_a, report_b, report_c]:
    print(f"{r['name']:<25} {r['accuracy']:>7.0%} {r['format_rate']:>7.0%} {r['avg_latency']:>7.0f}")

# ============================================================================
# 3. 常见失败与修复
# ============================================================================
print("\n--- 3. 常见失败 ---")
print("""
┌──────────────────────┬──────────────────────────────────┐
│  失败模式             │  修复方法                         │
├──────────────────────┼──────────────────────────────────┤
│  输出格式不稳定      │  用 JSON Schema + format="json"  │
│  忽略部分指令        │  关键指令放最后 + 加粗/大写      │
│  编造事实(幻觉)      │  要求"不确定就说不知道" + 低temp│
│  输出太长            │  明确字数限制 + max_tokens        │
│  输出太短            │  "请详细解释" + "至少包含3点"    │
│  中英文混杂          │  "全部用中文回答"                │
│  不遵循角色          │  System Prompt 开头强调角色       │
│  答非所问            │  "先复述问题，再回答"            │
│  逻辑错误            │  CoT + "请检查推理过程"          │
│  重复啰嗦            │  frequency_penalty + "简洁"      │
└──────────────────────┴──────────────────────────────────┘

修复优先级：
1. 先调 Prompt 文本（最快）
2. 再调参数（temperature/max_tokens）
3. 最后换模型（最后手段）
""")

# 幻觉防护对比
print("幻觉防护对比:")
question = "量子计算机目前最大的量子比特数是多少？"

# 无防护
result1, _ = chat(question)
print(f"  无防护: {result1[:100]}...")

# 有防护
result2, _ = chat(
    f"{question}\n\n要求：如果你不确定具体数字，请明确说明'我不确定最新数据'，不要编造具体数字。",
    temperature=0.0
)
print(f"  有防护: {result2[:100]}...")

# ============================================================================
# 4. Token 成本优化
# ============================================================================
print("\n--- 4. 成本优化 ---")
print("""
Token 成本 = (输入token + 输出token) × 单价

优化策略：
┌──────────────────────┬──────────────────────────────────┐
│  策略                 │  效果                             │
├──────────────────────┼──────────────────────────────────┤
│  精简 System Prompt  │  减少每次调用的固定输入token     │
│  限制 max_tokens     │  控制输出长度上限                 │
│  使用小模型          │  gpt-4o-mini 比 gpt-4o 便宜20倍 │
│  缓存相同请求        │  完全避免重复调用                 │
│  批量处理            │  减少 System Prompt 重复          │
│  分级处理            │  简单任务用小模型，复杂用大模型   │
│  压缩上下文          │  只传必要信息，不传完整历史      │
└──────────────────────┴──────────────────────────────────┘

价格参考（每百万token，2024）：
  gpt-4o:        输入$2.5  输出$10.0
  gpt-4o-mini:   输入$0.15 输出$0.6
  Claude 3.5:    输入$3.0  输出$15.0
  DeepSeek:      输入$0.27 输出$1.1
  本地 Ollama:   免费（电费+GPU）
""")

# 成本计算器
def estimate_cost(input_tokens: int, output_tokens: int,
                  model: str = "gpt-4o-mini") -> float:
    prices = {
        "gpt-4o":      {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "claude-3.5":  {"input": 3.0, "output": 15.0},
        "deepseek":    {"input": 0.27, "output": 1.1},
    }
    p = prices.get(model, prices["gpt-4o-mini"])
    return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000

print("成本估算:")
scenarios = [
    ("客服机器人(短回复)", 200, 100, 10000),
    ("文章生成(长输出)", 500, 2000, 1000),
    ("数据提取(批量)", 300, 50, 100000),
]
for name, inp, out, calls in scenarios:
    for model in ["gpt-4o", "gpt-4o-mini", "deepseek"]:
        cost = estimate_cost(inp, out, model) * calls
        print(f"  {name} × {calls:,}次 [{model:14s}]: ${cost:.2f}")
    print()

# ============================================================================
# 5. 延迟优化
# ============================================================================
print("--- 5. 延迟优化 ---")
print("""
延迟 = 首token时间(TTFT) + 生成时间

优化策略：
1. 减少输出 token 数（max_tokens）
2. 使用流式输出（用户感知更快）
3. 并行调用（多个独立任务同时执行）
4. 使用更快的模型（小模型更快）
5. 缓存（相同输入返回缓存结果）
6. 预热（避免冷启动）

流式输出：
```python
# 流式响应（用户看到第一个字就很快）
resp = httpx.post(url, json={..., "stream": True}, stream=True)
for line in resp.iter_lines():
    data = json.loads(line)
    print(data["message"]["content"], end="", flush=True)
```

并行调用：
```python
import asyncio

async def parallel_prompts(prompts):
    tasks = [async_chat(p) for p in prompts]
    return await asyncio.gather(*tasks)
# 3个独立 Prompt 同时执行 → 总延迟 ≈ 最慢的那个
```
""")

# ============================================================================
# 6. 版本管理
# ============================================================================
print("--- 6. 版本管理 ---")
print("""
生产环境的 Prompt 需要版本管理：

```python
prompt_registry = {
    "sentiment_v1": {
        "version": "1.0",
        "system": "你是情感分析专家",
        "template": "分析情感：{input}",
        "model": "gpt-4o-mini",
        "temperature": 0.0,
        "created": "2024-01-15",
        "accuracy": 0.85,
    },
    "sentiment_v2": {
        "version": "2.0",
        "system": "你是情感分析专家，只输出JSON",
        "template": "分析：{input}\\n输出JSON：{sentiment,confidence}",
        "model": "gpt-4o-mini",
        "temperature": 0.0,
        "created": "2024-02-01",
        "accuracy": 0.92,
    },
}
```

管理工具：
- LangSmith：LangChain 官方，Prompt 追踪+评估
- PromptLayer：专业 Prompt 版本管理
- Weights & Biases：实验追踪
- 自建：Git + YAML/JSON 配置文件

最佳实践：
1. 每次修改 Prompt 都记录版本号
2. 记录每个版本的评估指标
3. A/B 测试再上线
4. 保留回滚能力
5. 监控线上效果
""")

# 简单的 Prompt 注册表
class PromptRegistry:
    def __init__(self):
        self.prompts = {}

    def register(self, name: str, version: str, system: str,
                 template: str, **kwargs):
        key = f"{name}_v{version}"
        self.prompts[key] = {
            "name": name, "version": version, "system": system,
            "template": template, **kwargs
        }

    def get(self, name: str, version: str = None) -> dict:
        if version:
            return self.prompts.get(f"{name}_v{version}", {})
        # 返回最新版本
        versions = [k for k in self.prompts if k.startswith(name)]
        return self.prompts[versions[-1]] if versions else {}

    def list_all(self) -> list:
        return list(self.prompts.keys())

registry = PromptRegistry()
registry.register("sentiment", "1.0", "", "分析情感：{input}", accuracy=0.85)
registry.register("sentiment", "2.0", "情感分析专家", "JSON输出：{input}", accuracy=0.92)
registry.register("translate", "1.0", "翻译专家", "翻译：{input}", accuracy=0.90)

print("Prompt 注册表:")
for key in registry.list_all():
    p = registry.prompts[key]
    acc = p.get("accuracy", "N/A")
    print(f"  {key}: accuracy={acc}")

print("\n" + "=" * 60)
print("[完成] 第6课完成！你已经学会了：")
print("  [v] 五大评估维度（准确/一致/格式/完整/安全）")
print("  [v] A/B 测试框架")
print("  [v] 常见失败模式修复（幻觉/格式/啰嗦）")
print("  [v] Token 成本优化策略")
print("  [v] 延迟优化（流式/并行/缓存）")
print("  [v] Prompt 版本管理")
print("=" * 60)
print("\n下一课：07_prompt_project.py - 完整项目：自动化 Prompt 工程平台")
