import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第6课：RAG 评估（忠实度 / 相关性 / 召回率）
==============================================================================

RAG 系统的效果评估分两层：
  检索评估：检索到的文档是否相关
  生成评估：生成的回答是否忠实、相关、完整

本课内容：
1. RAG 评估维度
2. 检索评估指标
3. 生成评估指标
4. LLM-as-Judge 评估
5. 端到端评估
6. 评估最佳实践
==============================================================================
"""

import json
import math
import numpy as np
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
        }, timeout=180.0)
        return resp.json().get("message", {}).get("content", "")
    except:
        return "[模拟回答]"

print("=" * 60)
print("第6课：RAG 评估")
print("=" * 60)

# ============================================================================
# 1. 评估维度
# ============================================================================
print("\n--- 1. 评估维度 ---")
print("""
RAG 评估四大维度：

┌──────────────────┬──────────────────────────────────────┐
│  维度             │  衡量什么                             │
├──────────────────┼──────────────────────────────────────┤
│  Context Precision│  检索到的文档中有多少是相关的？      │
│  (上下文精确率)  │  高 = 检索结果噪音少                 │
├──────────────────┼──────────────────────────────────────┤
│  Context Recall  │  所有相关文档是否都被检索到了？       │
│  (上下文召回率)  │  高 = 没有遗漏重要文档               │
├──────────────────┼──────────────────────────────────────┤
│  Faithfulness    │  回答是否完全基于检索到的文档？       │
│  (忠实度)        │  高 = 没有幻觉/编造                  │
├──────────────────┼──────────────────────────────────────┤
│  Answer Relevancy│  回答是否切题回答了用户的问题？       │
│  (答案相关性)    │  高 = 回答与问题匹配                 │
└──────────────────┴──────────────────────────────────────┘

评估工具：
  RAGAS：最流行的 RAG 评估框架
  DeepEval：开源 LLM 评估框架
  LLM-as-Judge：用 LLM 打分（灵活通用）
""")

# ============================================================================
# 2. 检索评估
# ============================================================================
print("\n--- 2. 检索评估 ---")

class RetrievalEvaluator:
    """检索评估器"""

    @staticmethod
    def precision_at_k(retrieved: list, relevant: list, k: int) -> float:
        """精确率@K：Top-K 中有多少是相关的"""
        retrieved_k = retrieved[:k]
        hits = sum(1 for doc in retrieved_k if doc in relevant)
        return hits / k if k > 0 else 0

    @staticmethod
    def recall_at_k(retrieved: list, relevant: list, k: int) -> float:
        """召回率@K：相关文档中有多少被检索到"""
        retrieved_k = set(retrieved[:k])
        relevant_set = set(relevant)
        hits = len(retrieved_k & relevant_set)
        return hits / len(relevant_set) if relevant_set else 0

    @staticmethod
    def mrr(retrieved: list, relevant: list) -> float:
        """MRR：第一个相关结果的排名倒数"""
        relevant_set = set(relevant)
        for rank, doc in enumerate(retrieved, 1):
            if doc in relevant_set:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def ndcg_at_k(retrieved: list, relevant: list, k: int) -> float:
        """NDCG@K：考虑位置的排序质量"""
        retrieved_k = retrieved[:k]
        relevant_set = set(relevant)
        dcg = sum(1.0 / math.log2(i + 2) for i, doc in enumerate(retrieved_k) if doc in relevant_set)
        ideal_count = min(len(relevant_set), k)
        idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_count))
        return dcg / idcg if idcg > 0 else 0

    @staticmethod
    def hit_rate(retrieved: list, relevant: list) -> float:
        """命中率：是否至少检索到一个相关文档"""
        return 1.0 if set(retrieved) & set(relevant) else 0.0

eval_retrieval = RetrievalEvaluator()

# 测试数据
retrieved = ["doc_A", "doc_B", "doc_C", "doc_D", "doc_E"]
relevant = ["doc_A", "doc_C", "doc_F"]

print(f"检索结果: {retrieved}")
print(f"相关文档: {relevant}")
print(f"\n指标计算:")
for k in [1, 3, 5]:
    p = eval_retrieval.precision_at_k(retrieved, relevant, k)
    r = eval_retrieval.recall_at_k(retrieved, relevant, k)
    ndcg = eval_retrieval.ndcg_at_k(retrieved, relevant, k)
    print(f"  @{k}: Precision={p:.2f}, Recall={r:.2f}, NDCG={ndcg:.2f}")
print(f"  MRR: {eval_retrieval.mrr(retrieved, relevant):.2f}")
print(f"  Hit Rate: {eval_retrieval.hit_rate(retrieved, relevant):.2f}")

# ============================================================================
# 3. 生成评估
# ============================================================================
print("\n--- 3. 生成评估 ---")

class GenerationEvaluator:
    """生成评估器"""

    @staticmethod
    def keyword_overlap(answer: str, reference: str) -> float:
        """关键词重叠度"""
        import re
        a_words = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]+', answer.lower()))
        r_words = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]+', reference.lower()))
        if not r_words:
            return 0
        return len(a_words & r_words) / len(r_words)

    @staticmethod
    def answer_completeness(answer: str, key_points: list) -> float:
        """答案完整度：覆盖了多少关键点"""
        covered = sum(1 for point in key_points if point.lower() in answer.lower())
        return covered / len(key_points) if key_points else 0

    @staticmethod
    def answer_length_ratio(answer: str, min_len: int = 20, max_len: int = 500) -> float:
        """答案长度合理性"""
        length = len(answer)
        if length < min_len:
            return length / min_len
        elif length > max_len:
            return max_len / length
        return 1.0

eval_gen = GenerationEvaluator()

answer = "RAG 是检索增强生成技术，通过检索外部文档为 LLM 提供上下文，减少幻觉，支持私域知识问答。"
reference = "RAG 检索增强生成让 LLM 基于检索到的文档回答问题，有效减少幻觉，实现私域知识问答。"
key_points = ["检索", "增强生成", "文档", "幻觉", "私域"]

print(f"生成评估:")
print(f"  答案: {answer[:60]}...")
print(f"  参考: {reference[:60]}...")
print(f"  关键词重叠: {eval_gen.keyword_overlap(answer, reference):.2f}")
print(f"  关键点覆盖: {eval_gen.answer_completeness(answer, key_points):.2f}")
print(f"  长度合理性: {eval_gen.answer_length_ratio(answer):.2f}")

# ============================================================================
# 4. LLM-as-Judge
# ============================================================================
print("\n--- 4. LLM-as-Judge ---")

class LLMJudge:
    """LLM 评估器"""

    def evaluate_faithfulness(self, answer: str, context: str) -> dict:
        """忠实度评估：回答是否基于上下文"""
        prompt = f"""评估以下回答是否完全基于给定的上下文。

上下文：{context}
回答：{answer}

评分标准：
  5分：完全基于上下文，没有额外编造
  4分：基本基于上下文，有少量合理推断
  3分：部分基于上下文，有些内容无法验证
  2分：大部分内容不在上下文中
  1分：完全编造，与上下文无关

以JSON输出：{{"score": 1-5, "reason": "一句话理由"}}
只输出JSON。"""
        result = chat(prompt)
        try:
            start, end = result.find("{"), result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except:
            pass
        return {"score": 3, "reason": "评估失败"}

    def evaluate_relevancy(self, question: str, answer: str) -> dict:
        """相关性评估：回答是否切题"""
        prompt = f"""评估回答是否切题回答了用户的问题。

问题：{question}
回答：{answer}

评分标准：
  5分：完全切题，直接回答问题
  4分：基本切题，回答了主要内容
  3分：部分相关，但不够直接
  2分：大部分不相关
  1分：完全跑题

以JSON输出：{{"score": 1-5, "reason": "一句话理由"}}
只输出JSON。"""
        result = chat(prompt)
        try:
            start, end = result.find("{"), result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except:
            pass
        return {"score": 3, "reason": "评估失败"}

    def evaluate_completeness(self, question: str, answer: str) -> dict:
        """完整性评估"""
        prompt = f"""评估回答是否完整覆盖了问题的各个方面。

问题：{question}
回答：{answer}

评分标准：
  5分：完整覆盖所有方面
  4分：覆盖主要方面
  3分：覆盖部分方面
  2分：遗漏很多重要内容
  1分：几乎没有有效内容

以JSON输出：{{"score": 1-5, "reason": "一句话理由"}}
只输出JSON。"""
        result = chat(prompt)
        try:
            start, end = result.find("{"), result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except:
            pass
        return {"score": 3, "reason": "评估失败"}

judge = LLMJudge()

question = "RAG 的核心工作流程是什么？"
context = "RAG 的核心流程：文档分块→Embedding→向量检索→构建Prompt→LLM生成。混合检索结合向量搜索和BM25关键词搜索。"
answer = "RAG 的核心工作流程包括：1) 文档分块 2) 将文本转为 Embedding 向量 3) 用向量检索找到相关文档 4) 构建包含检索结果的 Prompt 5) LLM 生成回答。"

print(f"LLM-as-Judge 评估:")
print(f"  Q: {question}")
print(f"  A: {answer[:60]}...")

faithfulness = judge.evaluate_faithfulness(answer, context)
relevancy = judge.evaluate_relevancy(question, answer)
completeness = judge.evaluate_completeness(question, answer)

print(f"  忠实度: {faithfulness}")
print(f"  相关性: {relevancy}")
print(f"  完整性: {completeness}")

# ============================================================================
# 5. 端到端评估
# ============================================================================
print("\n--- 5. 端到端评估 ---")

class RAGEvaluator:
    """端到端 RAG 评估"""

    def __init__(self):
        self.retrieval_eval = RetrievalEvaluator()
        self.generation_eval = GenerationEvaluator()
        self.judge = LLMJudge()

    def evaluate(self, test_cases: list) -> dict:
        """评估一组测试用例"""
        results = {
            "retrieval": {"precision": [], "recall": [], "mrr": []},
            "generation": {"faithfulness": [], "relevancy": [], "completeness": []},
        }

        for case in test_cases:
            question = case["question"]
            retrieved = case.get("retrieved", [])
            relevant = case.get("relevant", [])
            answer = case.get("answer", "")
            context = case.get("context", "")

            # 检索评估
            if retrieved and relevant:
                p = self.retrieval_eval.precision_at_k(retrieved, relevant, 3)
                r = self.retrieval_eval.recall_at_k(retrieved, relevant, 3)
                mrr = self.retrieval_eval.mrr(retrieved, relevant)
                results["retrieval"]["precision"].append(p)
                results["retrieval"]["recall"].append(r)
                results["retrieval"]["mrr"].append(mrr)

            # 生成评估（使用关键词重叠代替 LLM 评估以加速）
            if answer:
                ref = case.get("reference", "")
                if ref:
                    overlap = self.generation_eval.keyword_overlap(answer, ref)
                    results["generation"]["faithfulness"].append(overlap)
                    results["generation"]["relevancy"].append(
                        self.generation_eval.answer_completeness(answer, case.get("key_points", []))
                    )

        # 计算平均分
        summary = {}
        for category, metrics in results.items():
            summary[category] = {}
            for metric, values in metrics.items():
                summary[category][metric] = round(np.mean(values), 3) if values else 0.0

        return summary

evaluator = RAGEvaluator()

test_cases = [
    {
        "question": "RAG 是什么？",
        "retrieved": ["rag_doc", "ml_doc", "vec_doc"],
        "relevant": ["rag_doc", "vec_doc"],
        "answer": "RAG 是检索增强生成技术，通过检索外部文档辅助 LLM 回答。",
        "reference": "RAG 检索增强生成让 LLM 基于检索到的文档回答，减少幻觉。",
        "key_points": ["检索", "生成", "文档", "幻觉"],
    },
    {
        "question": "混合检索的优势？",
        "retrieved": ["hybrid_doc", "bm25_doc", "rag_doc"],
        "relevant": ["hybrid_doc", "bm25_doc"],
        "answer": "混合检索结合向量搜索的语义理解和 BM25 的精确匹配，取长补短。",
        "reference": "混合检索结合向量搜索和BM25关键词搜索，取长补短。",
        "key_points": ["向量", "bm25", "语义", "关键词"],
    },
]

result = evaluator.evaluate(test_cases)
print(f"端到端评估结果:")
for category, metrics in result.items():
    print(f"  {category}:")
    for metric, value in metrics.items():
        print(f"    {metric}: {value:.3f}")

# ============================================================================
# 6. 最佳实践
# ============================================================================
print("\n--- 6. 最佳实践 ---")
print("""
RAG 评估最佳实践：

1. 构建测试集
   • 至少 50-100 个测试问题
   • 覆盖不同难度和类型
   • 标注相关文档和参考答案

2. 分层评估
   • 先评估检索质量（Recall/Precision）
   • 再评估生成质量（Faithfulness/Relevancy）
   • 找到瓶颈环节重点优化

3. 持续监控
   • 上线后追踪用户反馈
   • 定期用新问题评估
   • A/B 测试不同配置

4. 评估工具
   • RAGAS：最流行的 RAG 评估框架
     ```python
     from ragas import evaluate
     from ragas.metrics import faithfulness, answer_relevancy
     result = evaluate(dataset, metrics=[faithfulness, answer_relevancy])
     ```
   • DeepEval：开源 LLM 评估
   • LLM-as-Judge：灵活自定义

5. 关键阈值参考
   • Faithfulness > 0.8（忠实度）
   • Context Precision > 0.7（检索精度）
   • Context Recall > 0.8（检索召回）
   • Answer Relevancy > 0.7（答案相关性）
""")

print("=" * 60)
print("[完成] 第6课完成！你已经学会了：")
print("  [v] RAG 评估四大维度")
print("  [v] 检索评估（Precision/Recall/MRR/NDCG）")
print("  [v] 生成评估（关键词重叠/完整度/长度）")
print("  [v] LLM-as-Judge（忠实度/相关性/完整性）")
print("  [v] 端到端评估框架")
print("  [v] 评估最佳实践和阈值参考")
print("=" * 60)
print("\n下一课：07_rag_project.py - 知识库问答系统项目")
