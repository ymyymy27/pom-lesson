import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第6课：高级搜索（混合检索 / 重排序 / 过滤）
==============================================================================

基础向量搜索不够用时，需要高级技术：
  混合检索 = 向量搜索 + 关键词搜索
  重排序 = 粗检索 + 精排序
  过滤 = 元数据约束

本课内容：
1. 混合检索（Hybrid Search）
2. 关键词搜索（BM25）
3. 重排序（Reranking）
4. 查询改写
5. 多路召回与融合
6. 搜索效果评估
==============================================================================
"""

import json
import re
import math
import numpy as np
from collections import Counter, defaultdict

import httpx

OLLAMA_URL = "http://localhost:11434"

print("=" * 60)
print("第6课：高级搜索")
print("=" * 60)

# ============================================================================
# 1. 混合检索
# ============================================================================
print("\n--- 1. 混合检索 ---")
print("""
向量搜索的局限：
  ❌ 专有名词/编号（"订单号12345"）→ 向量不精确
  ❌ 精确关键词匹配（"Python 3.12 新特性"）
  ❌ 稀有术语（训练数据中很少出现的词）

关键词搜索（BM25）的局限：
  ❌ 同义词（"退款" vs "退钱"）
  ❌ 语义理解（"怎么学编程" vs "编程入门指南"）

混合检索 = 两者结合，取长补短：
  向量搜索：理解语义，找到意思相近的内容
  关键词搜索：精确匹配，找到包含特定词的内容
  融合：把两者结果合并排序

  ┌─────────┐     ┌────────────┐
  │ 用户查询 │────→│ 向量搜索    │──→ 结果A
  │         │     └────────────┘
  │         │     ┌────────────┐
  │         │────→│ BM25搜索   │──→ 结果B
  └─────────┘     └────────────┘
                        ↓
                  ┌────────────┐
                  │ RRF 融合   │──→ 最终结果
                  └────────────┘
""")

# ============================================================================
# 2. BM25 关键词搜索
# ============================================================================
print("\n--- 2. BM25 ---")

class BM25:
    """BM25 关键词搜索"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.docs = []
        self.doc_freqs = {}  # 词→出现在几篇文档中
        self.doc_lens = []
        self.avg_len = 0
        self.n_docs = 0

    def _tokenize(self, text: str) -> list:
        """简单中文分词（按字符/标点切分）"""
        # 提取中文词（2-4字）和英文词
        words = re.findall(r'[\u4e00-\u9fff]{1,4}|[a-zA-Z]+\d*', text.lower())
        return words

    def index(self, documents: list):
        self.docs = documents
        self.n_docs = len(documents)
        self.doc_lens = []
        tf_per_doc = []

        for doc in documents:
            tokens = self._tokenize(doc)
            self.doc_lens.append(len(tokens))
            tf = Counter(tokens)
            tf_per_doc.append(tf)
            for word in set(tokens):
                self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1

        self.avg_len = sum(self.doc_lens) / self.n_docs if self.n_docs else 1
        self.tf_per_doc = tf_per_doc

    def search(self, query: str, top_k: int = 5) -> list:
        query_tokens = self._tokenize(query)
        scores = []

        for i in range(self.n_docs):
            score = 0
            for token in query_tokens:
                if token not in self.doc_freqs:
                    continue
                df = self.doc_freqs[token]
                idf = math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1)
                tf = self.tf_per_doc[i].get(token, 0)
                doc_len = self.doc_lens[i]
                tf_norm = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_len))
                score += idf * tf_norm
            scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

# 测试数据
documents = [
    "Python 是一种通用编程语言，广泛用于数据分析和机器学习",
    "JavaScript 是 Web 前端开发的核心语言，支持浏览器端编程",
    "机器学习是人工智能的一个分支，让计算机从数据中学习",
    "深度学习使用多层神经网络处理图像、语音等复杂数据",
    "自然语言处理（NLP）让计算机理解和生成人类语言",
    "Rust 语言注重内存安全和高性能，适合系统编程",
    "Docker 容器技术简化了应用部署和环境管理",
    "Kubernetes 是容器编排平台，管理大规模容器集群",
    "向量数据库存储和检索高维向量，是RAG的核心组件",
    "Transformer 架构是现代大语言模型的基础",
]

bm25 = BM25()
bm25.index(documents)

query = "Python 机器学习"
results = bm25.search(query, top_k=3)
print(f"BM25 搜索: \"{query}\"")
for idx, score in results:
    print(f"  [{score:.2f}] {documents[idx][:50]}...")

# ============================================================================
# 3. 混合检索实现
# ============================================================================
print("\n--- 3. 混合检索 ---")

def ollama_embed(texts: list) -> list:
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/embed", json={
            "model": "nomic-embed-text", "input": texts,
        }, timeout=30.0)
        return resp.json().get("embeddings", [])
    except:
        np.random.seed(hash(str(texts)) % 2**31)
        return [np.random.randn(768).tolist() for _ in texts]

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

class HybridSearch:
    """混合检索引擎"""

    def __init__(self, documents: list, alpha: float = 0.5):
        self.documents = documents
        self.alpha = alpha  # 向量权重（1-alpha = BM25权重）

        # BM25 索引
        self.bm25 = BM25()
        self.bm25.index(documents)

        # 向量索引
        self.embeddings = ollama_embed(documents)

    def search(self, query: str, top_k: int = 5) -> list:
        # BM25 搜索
        bm25_results = self.bm25.search(query, top_k=len(self.documents))
        bm25_scores = {idx: score for idx, score in bm25_results}
        max_bm25 = max(bm25_scores.values()) if bm25_scores else 1

        # 向量搜索
        query_emb = ollama_embed([query])
        if not query_emb:
            return []
        vec_scores = {}
        for i, emb in enumerate(self.embeddings):
            vec_scores[i] = cosine_sim(query_emb[0], emb)

        # 融合（归一化后加权）
        combined = {}
        for i in range(len(self.documents)):
            bm25_norm = bm25_scores.get(i, 0) / max_bm25 if max_bm25 > 0 else 0
            vec_norm = (vec_scores.get(i, 0) + 1) / 2  # [-1,1] → [0,1]
            combined[i] = self.alpha * vec_norm + (1 - self.alpha) * bm25_norm

        sorted_results = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        return [(idx, score) for idx, score in sorted_results[:top_k]]

    def search_rrf(self, query: str, top_k: int = 5, k: int = 60) -> list:
        """Reciprocal Rank Fusion（RRF）融合"""
        # BM25 排名
        bm25_results = self.bm25.search(query, top_k=len(self.documents))
        bm25_ranks = {idx: rank for rank, (idx, _) in enumerate(bm25_results)}

        # 向量排名
        query_emb = ollama_embed([query])
        if not query_emb:
            return []
        vec_scores = [(i, cosine_sim(query_emb[0], emb)) for i, emb in enumerate(self.embeddings)]
        vec_scores.sort(key=lambda x: x[1], reverse=True)
        vec_ranks = {idx: rank for rank, (idx, _) in enumerate(vec_scores)}

        # RRF 融合：score = Σ 1/(k + rank)
        rrf_scores = {}
        for i in range(len(self.documents)):
            rrf_scores[i] = (1 / (k + bm25_ranks.get(i, 999)) +
                             1 / (k + vec_ranks.get(i, 999)))

        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

hybrid = HybridSearch(documents, alpha=0.5)

# 对比
test_queries = [
    "Python 数据分析",          # 关键词明确
    "如何让程序自己学习",        # 语义搜索更好
    "Docker Kubernetes 部署",   # 专有名词
]

for q in test_queries:
    print(f"\n查询: \"{q}\"")
    bm25_r = bm25.search(q, 3)
    hybrid_r = hybrid.search(q, 3)
    rrf_r = hybrid.search_rrf(q, 3)

    print(f"  BM25:   {[documents[i][:25]+'...' for i, _ in bm25_r]}")
    print(f"  混合:   {[documents[i][:25]+'...' for i, _ in hybrid_r]}")
    print(f"  RRF:    {[documents[i][:25]+'...' for i, _ in rrf_r]}")

# ============================================================================
# 4. 重排序
# ============================================================================
print("\n\n--- 4. 重排序 ---")
print("""
重排序 = 粗检索(Top-50) → 精排序(Top-5)

原理：
  1. 粗检索：向量搜索快速召回 Top-50（速度优先）
  2. 精排序：用更强的模型对 50 个结果重新打分（精度优先）

重排序模型：
  Cohere Rerank API：最简单，效果好
  bge-reranker：开源，本地部署
  Cross-Encoder：HuggingFace，精度最高

```python
# Cohere Rerank
import cohere
co = cohere.Client("api-key")
results = co.rerank(
    query="什么是机器学习",
    documents=["机器学习是...", "今天天气...", "ML是AI的分支..."],
    top_n=3,
    model="rerank-multilingual-v3.0"
)

# HuggingFace Cross-Encoder
from sentence_transformers import CrossEncoder
model = CrossEncoder("BAAI/bge-reranker-large")
scores = model.predict([
    ["查询", "文档1"],
    ["查询", "文档2"],
])
```
""")

# 模拟重排序
class SimpleReranker:
    """简单的 LLM 重排序"""

    def rerank(self, query: str, documents: list, top_n: int = 3) -> list:
        """基于关键词重叠度重排序（模拟 Cross-Encoder）"""
        query_words = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]+', query.lower()))
        scored = []
        for i, doc in enumerate(documents):
            doc_words = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]+', doc.lower()))
            overlap = len(query_words & doc_words)
            total = len(query_words | doc_words)
            score = overlap / total if total > 0 else 0
            scored.append((i, score, doc))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

reranker = SimpleReranker()
query = "向量数据库在RAG中的作用"
candidates = documents  # 假设这是粗检索的结果
reranked = reranker.rerank(query, candidates, 3)
print(f"重排序: \"{query}\"")
for idx, score, doc in reranked:
    print(f"  [{score:.2f}] {doc[:50]}...")

# ============================================================================
# 5. 查询改写
# ============================================================================
print("\n--- 5. 查询改写 ---")
print("""
用户查询往往不完美，改写可以提升检索效果：

策略1: 查询扩展（Query Expansion）
  "Python学习" → "Python 编程 学习 入门 教程"

策略2: 多查询生成（Multi-Query）
  "Python学习" → ["Python入门教程", "如何学Python", "Python学习路线"]

策略3: HyDE（Hypothetical Document Embedding）
  用 LLM 生成一个"假文档"，用假文档做检索
  查询: "Python学习" → LLM生成: "Python是一种编程语言..."

```python
# Multi-Query 示例
def multi_query(original_query: str) -> list:
    prompt = f'''为以下查询生成3个不同角度的搜索查询：
原查询：{original_query}
以 JSON 数组输出：["查询1", "查询2", "查询3"]'''
    result = llm.chat(prompt)
    return json.loads(result)

# HyDE 示例
def hyde(query: str) -> str:
    prompt = f"请写一段100字的文本来回答以下问题：{query}"
    hypothetical_doc = llm.chat(prompt)
    return hypothetical_doc  # 用这个做 embedding 检索
```
""")

# ============================================================================
# 6. 评估
# ============================================================================
print("\n--- 6. 搜索评估 ---")

class SearchEvaluator:
    """搜索效果评估"""

    @staticmethod
    def recall_at_k(retrieved: list, relevant: list, k: int) -> float:
        """召回率@K"""
        retrieved_k = set(retrieved[:k])
        relevant_set = set(relevant)
        return len(retrieved_k & relevant_set) / len(relevant_set) if relevant_set else 0

    @staticmethod
    def precision_at_k(retrieved: list, relevant: list, k: int) -> float:
        """精确率@K"""
        retrieved_k = set(retrieved[:k])
        relevant_set = set(relevant)
        return len(retrieved_k & relevant_set) / k if k > 0 else 0

    @staticmethod
    def mrr(retrieved: list, relevant: list) -> float:
        """MRR (Mean Reciprocal Rank)"""
        relevant_set = set(relevant)
        for rank, item in enumerate(retrieved, 1):
            if item in relevant_set:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def ndcg_at_k(retrieved: list, relevant: list, k: int) -> float:
        """NDCG@K"""
        retrieved_k = retrieved[:k]
        relevant_set = set(relevant)
        dcg = sum(1.0 / math.log2(i + 2) for i, item in enumerate(retrieved_k) if item in relevant_set)
        ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant_set), k)))
        return dcg / ideal if ideal > 0 else 0

evaluator = SearchEvaluator()

# 模拟评估
retrieved = [0, 2, 5, 3, 1]
relevant = [0, 2, 3]

print(f"评估指标:")
print(f"  检索结果: {retrieved}")
print(f"  相关文档: {relevant}")
for k in [1, 3, 5]:
    r = evaluator.recall_at_k(retrieved, relevant, k)
    p = evaluator.precision_at_k(retrieved, relevant, k)
    print(f"  @{k}: Recall={r:.2f}, Precision={p:.2f}")
print(f"  MRR: {evaluator.mrr(retrieved, relevant):.2f}")
print(f"  NDCG@5: {evaluator.ndcg_at_k(retrieved, relevant, 5):.2f}")

print("\n" + "=" * 60)
print("[完成] 第6课完成！你已经学会了：")
print("  [v] 混合检索（向量+BM25）")
print("  [v] BM25 关键词搜索原理")
print("  [v] RRF 融合算法")
print("  [v] 重排序（Reranking）")
print("  [v] 查询改写（Multi-Query/HyDE）")
print("  [v] 搜索评估指标（Recall/Precision/MRR/NDCG）")
print("=" * 60)
print("\n下一课：07_vector_db_project.py - 语义搜索引擎项目")
