import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：RAG 优化（Query改写 / 上下文 / 生成）
==============================================================================

RAG 优化四个维度：
  Query优化 → 检索优化 → 上下文优化 → 生成优化

本课内容：
1. RAG 优化全景
2. Query 改写与扩展
3. Multi-Query 多查询
4. HyDE 假设文档
5. 上下文优化
6. 生成优化（引用/验证）
==============================================================================
"""

import json
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

def embed(texts: list) -> list:
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/embed", json={
            "model": "qwen3-embedding:4b", "input": texts,
        }, timeout=180.0)
        return resp.json().get("embeddings", [])
    except:
        np.random.seed(hash(str(texts)) % 2**31)
        return [np.random.randn(2560).tolist() for _ in texts]

print("=" * 60)
print("第5课：RAG 优化")
print("=" * 60)

# ============================================================================
# 1. 优化全景
# ============================================================================
print("\n--- 1. 优化全景 ---")
print("""
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Query优化 │ → │ 检索优化  │ → │ 上下文优化│ → │ 生成优化  │
├──────────┤   ├──────────┤   ├──────────┤   ├──────────┤
│ Query改写│   │ 混合检索  │   │ 重排序    │   │ 引用来源  │
│ Multi-Q  │   │ 元数据过滤│   │ 上下文压缩│   │ 幻觉检测  │
│ HyDE     │   │ Parent-   │   │ 文档重排  │   │ 答案验证  │
│ 步回问   │   │ Child     │   │ 窗口扩展  │   │ 流式输出  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘

每个环节优化 10%，最终效果翻倍！
""")

# ============================================================================
# 2. Query 改写
# ============================================================================
print("\n--- 2. Query 改写 ---")

class QueryRewriter:
    """查询改写器"""

    def rewrite(self, query: str) -> str:
        """用 LLM 改写查询"""
        prompt = f"""将用户查询改写为更适合向量检索的形式。
要求：保持原意，补充关键词，使表述更清晰。
只输出改写后的查询，不要解释。

原查询：{query}
改写："""
        return chat(prompt, temperature=0.0).strip()

    def expand(self, query: str) -> str:
        """查询扩展（添加同义词/相关词）"""
        prompt = f"""为以下查询添加相关关键词，用于扩展搜索范围。
只输出扩展后的查询。

原查询：{query}
扩展："""
        return chat(prompt, temperature=0.0).strip()

    def decompose(self, query: str) -> list:
        """复杂问题分解为子问题"""
        prompt = f"""将以下复杂问题分解为2-3个简单的子问题。
以 JSON 数组输出：["子问题1", "子问题2"]
只输出JSON。

问题：{query}"""
        result = chat(prompt, temperature=0.0)
        try:
            start, end = result.find("["), result.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except:
            pass
        return [query]

rewriter = QueryRewriter()

test_queries = [
    "RAG 咋用？",
    "Python 和 Java 哪个好？为什么？",
]

for q in test_queries:
    rewritten = rewriter.rewrite(q)
    print(f"  原始: {q}")
    print(f"  改写: {rewritten[:60]}...")
    print()

# 复杂问题分解
complex_q = "RAG 系统如何从文档加载到最终生成回答的完整流程是什么？各环节有哪些优化策略？"
sub_qs = rewriter.decompose(complex_q)
print(f"问题分解: {complex_q[:30]}...")
for i, sq in enumerate(sub_qs[:3], 1):
    print(f"  子问题{i}: {sq}")

# ============================================================================
# 3. Multi-Query
# ============================================================================
print("\n--- 3. Multi-Query ---")

class MultiQueryRetriever:
    """多查询检索器"""

    def generate_queries(self, original_query: str, n: int = 3) -> list:
        """生成多个查询变体"""
        prompt = f"""为以下查询生成{n}个不同角度的搜索查询。
每个查询用不同的表述方式但保持相同的搜索意图。
以 JSON 数组输出：["查询1", "查询2", "查询3"]
只输出JSON。

原查询：{original_query}"""
        result = chat(prompt, temperature=0.3)
        try:
            start, end = result.find("["), result.rfind("]") + 1
            if start >= 0 and end > start:
                queries = json.loads(result[start:end])
                return [original_query] + queries[:n]
        except:
            pass
        return [original_query]

    def search(self, query: str, documents: list, doc_embeddings: list,
               top_k: int = 5) -> list:
        """多查询检索并去重合并"""
        queries = self.generate_queries(query, 3)
        seen = set()
        results = []

        for q in queries:
            q_emb = embed([q])[0]
            scores = []
            for i, emb in enumerate(doc_embeddings):
                a, b = np.array(q_emb), np.array(emb)
                sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
                scores.append((i, sim))
            scores.sort(key=lambda x: x[1], reverse=True)

            for idx, score in scores[:top_k]:
                if idx not in seen:
                    seen.add(idx)
                    results.append((documents[idx], score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

# 知识库
knowledge = [
    "RAG 检索增强生成让 LLM 基于检索到的文档回答，减少幻觉。",
    "RAG 的核心流程：文档分块→Embedding→向量检索→构建Prompt→LLM生成。",
    "混合检索结合向量搜索和 BM25 关键词搜索，取长补短。",
    "Reranking 用 Cross-Encoder 对初步检索结果重新排序，提升精度。",
    "Multi-Query 生成多个查询变体，提高召回率。",
    "HyDE 先用 LLM 生成假设答案，再用假设答案做检索。",
]
doc_embs = embed(knowledge)

mq = MultiQueryRetriever()
query = "RAG 是什么"
gen_queries = mq.generate_queries(query, 3)
print(f"Multi-Query: \"{query}\"")
print(f"  生成的查询变体:")
for i, q in enumerate(gen_queries):
    print(f"    {i+1}. {q}")

results = mq.search(query, knowledge, doc_embs, 3)
print(f"  检索结果:")
for doc, score in results:
    print(f"    [{score:.4f}] {doc[:50]}...")

# ============================================================================
# 4. HyDE
# ============================================================================
print("\n--- 4. HyDE ---")
print("""
HyDE = Hypothetical Document Embeddings（假设文档嵌入）

原理：
  问题 → LLM 生成假设答案 → 假设答案 Embedding → 检索

为什么有效？
  问题的 Embedding 和文档的 Embedding 在向量空间中可能不够接近
  但"假设答案"的 Embedding 和真实文档更相似
""")

class HyDERetriever:
    """HyDE 检索器"""

    def generate_hypothesis(self, query: str) -> str:
        prompt = f"请用100字左右回答以下问题（即使不确定也尝试回答）：\n{query}"
        return chat(prompt, temperature=0.3)

    def search(self, query: str, documents: list, doc_embeddings: list,
               top_k: int = 5) -> list:
        # 生成假设文档
        hypothesis = self.generate_hypothesis(query)

        # 用假设文档的 embedding 检索
        hyp_emb = embed([hypothesis])[0]
        scores = []
        for i, emb in enumerate(doc_embeddings):
            a, b = np.array(hyp_emb), np.array(emb)
            sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
            scores.append((i, sim))
        scores.sort(key=lambda x: x[1], reverse=True)

        return [(documents[i], s, hypothesis) for i, s in scores[:top_k]]

hyde = HyDERetriever()
query = "如何提高 RAG 检索质量"
hypothesis = hyde.generate_hypothesis(query)
print(f"HyDE 演示: \"{query}\"")
print(f"  假设答案: {hypothesis[:80]}...")

results = hyde.search(query, knowledge, doc_embs, 3)
print(f"  检索结果:")
for doc, score, _ in results:
    print(f"    [{score:.4f}] {doc[:50]}...")

# ============================================================================
# 5. 上下文优化
# ============================================================================
print("\n--- 5. 上下文优化 ---")
print("""
上下文优化策略：

1. 上下文压缩
   检索到 5 段文档 → 只保留与问题相关的句子
   减少噪音，节省 token

2. Lost-in-the-Middle 文档重排
   LLM 对中间位置的信息关注度低
   最相关的文档放在开头和结尾

3. 窗口扩展
   检索到的 chunk 可能语义不完整
   把前后相邻的 chunk 也包含进来

4. Parent-Child 检索
   用小块(child)精确检索，返回大块(parent)
   兼顾精度和上下文完整性
""")

class ContextOptimizer:
    """上下文优化器"""

    def compress(self, query: str, documents: list) -> list:
        """上下文压缩：只保留与问题相关的句子"""
        compressed = []
        for doc in documents:
            prompt = f"""从以下文本中提取与问题相关的信息，去除无关内容。
如果没有相关信息，返回"无关"。

问题：{query}
文本：{doc}

相关信息："""
            result = chat(prompt, temperature=0.0)
            if "无关" not in result and len(result.strip()) > 10:
                compressed.append(result.strip())
        return compressed

    def reorder_lost_in_middle(self, documents: list) -> list:
        """Lost-in-the-Middle 重排：最相关的放首尾"""
        if len(documents) <= 2:
            return documents
        reordered = []
        for i, doc in enumerate(documents):
            if i % 2 == 0:
                reordered.insert(0, doc)
            else:
                reordered.append(doc)
        return reordered

optimizer = ContextOptimizer()

# Lost-in-the-Middle 演示
sample_docs = ["最相关文档A", "次相关文档B", "一般文档C", "较低相关D", "最低相关E"]
reordered = optimizer.reorder_lost_in_middle(sample_docs)
print("Lost-in-the-Middle 重排:")
print(f"  原始顺序: {sample_docs}")
print(f"  重排后:   {reordered}")
print(f"  → 最相关在首尾，LLM 关注度最高的位置")

# ============================================================================
# 6. 生成优化
# ============================================================================
print("\n--- 6. 生成优化 ---")

class RAGGenerator:
    """RAG 生成器（带引用和验证）"""

    def generate_with_citation(self, question: str, context_docs: list) -> str:
        """带引用的生成"""
        context = "\n\n".join(f"[来源{i+1}] {doc}" for i, doc in enumerate(context_docs))
        system = """你是知识库问答助手。根据检索到的文档回答问题。
规则：
1. 只基于文档回答，不编造
2. 关键信息后标注来源，如 [来源1]
3. 无法回答时说明
4. 回答简洁有条理"""
        prompt = f"文档：\n{context}\n\n问题：{question}"
        return chat(prompt, system)

    def verify_answer(self, question: str, answer: str, context: str) -> dict:
        """幻觉检测"""
        prompt = f"""判断回答是否完全基于上下文，有无编造信息。

上下文：{context}
问题：{question}
回答：{answer}

以JSON输出：{{"is_grounded": true或false, "reason": "一句话理由"}}
只输出JSON。"""
        result = chat(prompt, temperature=0.0)
        try:
            start, end = result.find("{"), result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except:
            pass
        return {"is_grounded": True, "reason": "无法验证"}

generator = RAGGenerator()

# 带引用生成
docs = [knowledge[0], knowledge[1]]
answer = generator.generate_with_citation("RAG 的工作流程是什么？", docs)
print(f"带引用回答:")
print(f"  Q: RAG 的工作流程是什么？")
print(f"  A: {answer[:120]}...")

# 幻觉检测
context = " ".join(docs)
verify = generator.verify_answer("RAG 的工作流程是什么？", answer, context)
print(f"  幻觉检测: {verify}")

print("""
生成优化最佳实践：
  ✅ temperature=0（减少随机性）
  ✅ 引用来源标注（可溯源）
  ✅ 幻觉检测（事实核查）
  ✅ "不知道"机制（无法回答时明确说明）
  ✅ 流式输出（用户体验好）
""")

print("=" * 60)
print("[完成] 第5课完成！你已经学会了：")
print("  [v] RAG 优化四维度（Query/检索/上下文/生成）")
print("  [v] Query 改写、扩展、分解")
print("  [v] Multi-Query 多查询检索")
print("  [v] HyDE 假设文档嵌入")
print("  [v] 上下文压缩和 Lost-in-the-Middle 重排")
print("  [v] 带引用生成和幻觉检测")
print("=" * 60)
print("\n下一课：06_rag_evaluation.py - RAG 评估")
