import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第6课：评估与对比（指标 / LLM-Judge / A/B 测试）
==============================================================================

微调后必须系统化评估：
  "微调真的让模型变好了吗？好了多少？哪些方面好了？"

本课内容：
1. 评估方法论
2. 自动化指标
3. LLM-as-Judge 评估
4. 人工评估框架
5. A/B 对比测试
6. 评估最佳实践
==============================================================================
"""

import json
import numpy as np
from collections import defaultdict

import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"

def chat(prompt: str, system: str = "", temperature: float = 0.0) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL, "messages": messages, "stream": False,
            "options": {"temperature": temperature, "num_predict": 500}
        }, timeout=30.0)
        return resp.json().get("message", {}).get("content", "")
    except:
        return "[模拟回答]"

print("=" * 60)
print("第6课：评估与对比")
print("=" * 60)

# ============================================================================
# 1. 评估方法论
# ============================================================================
print("\n--- 1. 评估方法论 ---")
print("""
微调评估的三层体系：

  ┌──────────────────────────────────────────────────────┐
  │  层级1: 训练指标（Training Metrics）                  │
  │  → loss 曲线、eval loss、perplexity                  │
  │  → 判断训练是否正常                                  │
  └──────────────────────┬──────────────────────────────┘
                         ↓
  ┌──────────────────────────────────────────────────────┐
  │  层级2: 自动评估（Automatic Evaluation）              │
  │  → ROUGE、BLEU、Exact Match、F1                      │
  │  → 大规模快速评估                                    │
  └──────────────────────┬──────────────────────────────┘
                         ↓
  ┌──────────────────────────────────────────────────────┐
  │  层级3: 人工/LLM评估（Human/LLM Evaluation）         │
  │  → LLM-as-Judge、人工打分、偏好对比                  │
  │  → 最准确，但最慢/最贵                               │
  └──────────────────────────────────────────────────────┘

评估原则：
  ✅ 一定要有"基线"（微调前的表现）
  ✅ 测试集不能出现在训练集中
  ✅ 多维度评估（不只看一个指标）
  ✅ 人工抽检（自动指标不够可靠）
""")

# ============================================================================
# 2. 自动化指标
# ============================================================================
print("\n--- 2. 自动指标 ---")

class AutoMetrics:
    """自动评估指标"""

    @staticmethod
    def exact_match(pred: str, ref: str) -> float:
        return 1.0 if pred.strip() == ref.strip() else 0.0

    @staticmethod
    def contains_match(pred: str, keywords: list) -> float:
        hits = sum(1 for kw in keywords if kw in pred)
        return hits / len(keywords) if keywords else 0.0

    @staticmethod
    def rouge_l(pred: str, ref: str) -> float:
        """简化版 ROUGE-L（最长公共子序列）"""
        pred_chars = list(pred)
        ref_chars = list(ref)
        m, n = len(pred_chars), len(ref_chars)
        if m == 0 or n == 0:
            return 0.0

        # LCS 长度
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if pred_chars[i-1] == ref_chars[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])

        lcs = dp[m][n]
        precision = lcs / m
        recall = lcs / n
        if precision + recall == 0:
            return 0.0
        f1 = 2 * precision * recall / (precision + recall)
        return f1

    @staticmethod
    def length_ratio(pred: str, ref: str) -> float:
        """长度比率（接近1.0最好）"""
        if len(ref) == 0:
            return 0.0
        return len(pred) / len(ref)

metrics = AutoMetrics()

# 评估演示
test_cases = [
    {
        "question": "退款需要多久？",
        "reference": "退款通常在3-5个工作日内到账。如果超过5个工作日，请联系客服。",
        "model_a": "退款3-5个工作日到账，超过请联系客服。",
        "model_b": "退款会在一段时间后到账的，具体看情况吧。",
    },
    {
        "question": "能开发票吗？",
        "reference": "可以的。请在订单页面选择申请发票，支持电子发票和纸质发票。",
        "model_a": "支持开发票。在订单页申请，电子和纸质都可以。",
        "model_b": "嗯可以的。",
    },
]

print("自动指标对比:")
print(f"  {'问题':<15} {'指标':<10} {'模型A(微调)':>12} {'模型B(原始)':>12}")
print(f"  {'-'*55}")
for tc in test_cases:
    rouge_a = metrics.rouge_l(tc["model_a"], tc["reference"])
    rouge_b = metrics.rouge_l(tc["model_b"], tc["reference"])
    kw = ["退款", "工作日", "客服"] if "退款" in tc["question"] else ["发票", "电子", "纸质"]
    contain_a = metrics.contains_match(tc["model_a"], kw)
    contain_b = metrics.contains_match(tc["model_b"], kw)
    print(f"  {tc['question']:<15} {'ROUGE-L':<10} {rouge_a:>11.2f} {rouge_b:>11.2f}")
    print(f"  {'':<15} {'关键词':<10} {contain_a:>11.2f} {contain_b:>11.2f}")

# ============================================================================
# 3. LLM-as-Judge
# ============================================================================
print("\n--- 3. LLM-as-Judge ---")
print("""
用一个强大的 LLM（如 GPT-4o）作为评委打分。

三种评判模式：

模式1: 单独评分
  "给这个回答打分（1-5）"

模式2: 对比评判
  "A和B哪个更好？"

模式3: 参考评分
  "参考标准答案，给这个回答打分"
""")

class LLMJudge:
    """LLM 评委"""

    def score_single(self, question: str, answer: str,
                     criteria: str = "准确性、完整性、专业性") -> dict:
        prompt = f"""请评估以下问答的质量。

问题：{question}
回答：{answer}

评估标准：{criteria}

请以 JSON 格式输出：
{{"score": 1到5的整数, "reason": "评分理由(一句话)"}}
只输出JSON。"""

        result = chat(prompt, temperature=0.0)
        try:
            # 提取 JSON
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except:
            pass
        return {"score": 3, "reason": "无法解析评分"}

    def compare(self, question: str, answer_a: str, answer_b: str) -> dict:
        prompt = f"""比较以下两个回答，判断哪个更好。

问题：{question}

回答A：{answer_a}

回答B：{answer_b}

请以 JSON 格式输出：
{{"winner": "A"或"B"或"tie", "reason": "理由(一句话)"}}
只输出JSON。"""

        result = chat(prompt, temperature=0.0)
        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except:
            pass
        return {"winner": "tie", "reason": "无法判断"}

    def score_with_reference(self, question: str, answer: str,
                             reference: str) -> dict:
        prompt = f"""参考标准答案，评估模型回答的质量。

问题：{question}
标准答案：{reference}
模型回答：{answer}

评分维度（每项1-5分）：
1. 准确性：信息是否正确
2. 完整性：是否覆盖关键信息
3. 简洁性：是否简洁不啰嗦

以 JSON 输出：{{"accuracy":1-5,"completeness":1-5,"conciseness":1-5,"total":1-5,"reason":"一句话"}}
只输出JSON。"""

        result = chat(prompt, temperature=0.0)
        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except:
            pass
        return {"accuracy": 3, "completeness": 3, "conciseness": 3, "total": 3, "reason": "解析失败"}

judge = LLMJudge()

print("LLM-as-Judge 评估:")
for tc in test_cases:
    # 对比评判
    comparison = judge.compare(tc["question"], tc["model_a"], tc["model_b"])
    print(f"\n  Q: {tc['question']}")
    print(f"  A(微调): {tc['model_a'][:50]}...")
    print(f"  B(原始): {tc['model_b'][:50]}...")
    print(f"  判定: {comparison.get('winner', '?')} | {comparison.get('reason', '')[:60]}")

# ============================================================================
# 4. 人工评估框架
# ============================================================================
print("\n\n--- 4. 人工评估 ---")
print("""
人工评估虽然慢，但最准确。

评估表设计：
┌────┬──────────────┬───────────┬──────┬──────┬──────┬──────────┐
│ ID │ 问题         │ 模型回答  │ 准确 │ 完整 │ 风格 │ 总分(1-5)│
├────┼──────────────┼───────────┼──────┼──────┼──────┼──────────┤
│  1 │ 退款多久？   │ 3-5天...  │  5   │  4   │  5   │    5     │
│  2 │ 怎么改地址？ │ 步骤...   │  4   │  5   │  4   │    4     │
└────┴──────────────┴───────────┴──────┴──────┴──────┴──────────┘

盲评（推荐）：
  评估者不知道哪个是微调前/后
  随机打乱顺序
  减少评估偏见

评估人数：
  至少 2 人评估（计算一致性）
  有分歧时第 3 人仲裁

Cohen's Kappa（评估者一致性）：
  κ > 0.8: 高度一致
  κ 0.6-0.8: 较一致
  κ < 0.6: 需要改进评估标准
""")

# 模拟人工评估
print("模拟人工评估结果:")
human_eval = [
    {"id": 1, "question": "退款多久", "before": 3.5, "after": 4.8},
    {"id": 2, "question": "改地址", "before": 3.0, "after": 4.5},
    {"id": 3, "question": "开发票", "before": 2.5, "after": 4.7},
    {"id": 4, "question": "会员优惠", "before": 3.2, "after": 4.3},
    {"id": 5, "question": "质量问题", "before": 3.8, "after": 4.6},
]

before_avg = np.mean([e["before"] for e in human_eval])
after_avg = np.mean([e["after"] for e in human_eval])
improvement = (after_avg - before_avg) / before_avg * 100

print(f"  {'问题':<12} {'微调前':>8} {'微调后':>8} {'提升':>8}")
print(f"  {'-'*40}")
for e in human_eval:
    delta = e["after"] - e["before"]
    print(f"  {e['question']:<12} {e['before']:>7.1f} {e['after']:>7.1f} {'+' if delta>0 else ''}{delta:>6.1f}")
print(f"  {'平均':<12} {before_avg:>7.1f} {after_avg:>7.1f} +{improvement:.0f}%")

# ============================================================================
# 5. A/B 对比
# ============================================================================
print("\n--- 5. A/B 对比 ---")

class ABComparator:
    """A/B 对比测试"""

    def __init__(self, judge: LLMJudge):
        self.judge = judge

    def run_comparison(self, test_data: list) -> dict:
        results = {"A_wins": 0, "B_wins": 0, "ties": 0, "details": []}

        for tc in test_data:
            comp = self.judge.compare(tc["question"], tc["model_a"], tc["model_b"])
            winner = comp.get("winner", "tie")
            if winner == "A":
                results["A_wins"] += 1
            elif winner == "B":
                results["B_wins"] += 1
            else:
                results["ties"] += 1

            results["details"].append({
                "question": tc["question"][:20],
                "winner": winner,
                "reason": comp.get("reason", "")[:40],
            })

        total = len(test_data)
        results["A_rate"] = results["A_wins"] / total if total else 0
        results["B_rate"] = results["B_wins"] / total if total else 0
        return results

comparator = ABComparator(judge)
ab_result = comparator.run_comparison(test_cases)

print("A/B 对比结果:")
print(f"  模型A(微调后): {ab_result['A_wins']}胜 ({ab_result['A_rate']:.0%})")
print(f"  模型B(微调前): {ab_result['B_wins']}胜 ({ab_result['B_rate']:.0%})")
print(f"  平局: {ab_result['ties']}")
for d in ab_result["details"]:
    print(f"    {d['question']}: {d['winner']} | {d['reason']}")

# ============================================================================
# 6. 最佳实践
# ============================================================================
print("\n--- 6. 最佳实践 ---")
print("""
完整评估流程：

  1. 准备测试集（20-50条，不在训练集中）
  2. 生成基线结果（微调前模型）
  3. 生成微调结果（微调后模型）
  4. 自动指标快速筛选（ROUGE/关键词匹配）
  5. LLM-as-Judge 详细评分
  6. 人工抽检（10-20条盲评）
  7. 生成评估报告

评估报告模板：
┌─────────────────────────────────────────────┐
│  微调评估报告                                │
│                                              │
│  模型: Qwen2.5-7B + LoRA (r=16)            │
│  数据: 500条客服QA, 3 epochs                │
│  测试集: 50条                                │
│                                              │
│  自动指标:                                   │
│    ROUGE-L:  0.72 → 0.85 (+18%)            │
│    关键词匹配: 0.65 → 0.88 (+35%)          │
│                                              │
│  LLM评分 (GPT-4o):                          │
│    准确性: 3.2 → 4.5                        │
│    完整性: 3.0 → 4.3                        │
│    风格:   2.8 → 4.7                        │
│                                              │
│  人工评估 (3人):                             │
│    平均分: 3.2 → 4.5 (+41%)                │
│    一致性 κ: 0.82                            │
│                                              │
│  结论: 微调显著提升各维度表现，推荐上线      │
└─────────────────────────────────────────────┘
""")

print("=" * 60)
print("[完成] 第6课完成！你已经学会了：")
print("  [v] 三层评估体系（训练指标/自动/人工）")
print("  [v] 自动化指标（ROUGE-L/关键词/精确匹配）")
print("  [v] LLM-as-Judge（单独评分/对比/参考评分）")
print("  [v] 人工评估框架（盲评/一致性）")
print("  [v] A/B 对比测试")
print("  [v] 完整评估流程与报告模板")
print("=" * 60)
print("\n下一课：07_fine_tuning_project.py - 完整项目：领域专家微调平台")
