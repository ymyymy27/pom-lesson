import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第4课：检索策略（向量 / BM25 / 混合 / 重排序）
==============================================================================

检索是 RAG 最关键的环节——检索不到好文档，LLM 再强也没用。

本课内容：
1. 检索策略概览
2. 向量检索
3. BM25 关键词检索
4. 混合检索与 RRF 融合
5. 重排序（Reranking）
6. 检索参数调优
==============================================================================
"""

import json
import re
import math
import numpy as np
from collections import Counter

import httpx

OLLAMA_URL = "http://localhost:11434"

def embed(texts: list) -> list:
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/embed", json={
            "model": "qwen3-embedding:4b", "input": texts,
        }, timeout=180.0)
        return resp.json().get("embeddings", [])
    except:
        np.random.seed(hash(str(texts)) % 2**31)
        return [np.random.randn(2560).tolist() for _ in texts]

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / norm) if norm > 0 else 0

print("=" * 60)
print("第4课：检索策略")
print("=" * 60)

# 构建知识库
knowledge = [
    "Python 是一种高级通用编程语言，由 Guido van Rossum 创建。以简洁优雅的语法著称。",
    "Django 是 Python 的 Web 框架，采用 MTV 架构，适合快速开发大型 Web 应用。",
    "Flask 是轻量级 Python Web 框架，灵活且易于扩展，适合小型项目和 API 开发。",
    "机器学习让计算机从数据中学习模式。监督学习、无监督学习和强化学习是三大范式。",
    "深度学习使用多层神经网络。CNN 处理图像，RNN 处理序列，Transformer 处理文本。",
    "RAG 检索增强生成让 LLM 基于检索到的文档回答，有效减少幻觉，支持私域知识问答。",
    "ChromaDB 是轻量级开源向量数据库，支持持久化存储和元数据过滤，适合 RAG 原型开发。",
    "FAISS 是 Facebook 开源的高性能向量检索库，支持十亿级向量搜索，适合大规模场景。",
    "向量数据库存储文本的 Embedding 向量，通过余弦相似度等指标进行语义搜索。",
    "Transformer 架构是现代 LLM 的基础，其自注意力机制能捕捉长距离依赖关系。",
    "GPT-4o 是 OpenAI 的多模态大模型，支持文本、图像和音频的理解与生成。",
    "Ollama 是本地运行开源 LLM 的工具，支持 Qwen、LLaMA 等模型的一键部署和推理。",
]

doc_embeddings = embed(knowledge)

# ============================================================================
# 1. 检索策略概览
# ============================================================================
print("\n--- 1. 概览 ---")
print("""
┌──────────────┬──────────────────────────────────────────┐
│  策略         │  特点                                     │
├──────────────┼──────────────────────────────────────────┤
│  向量检索    │  理解语义（"退钱"→"退款"）              │
│              │  可能遗漏精确关键词匹配                  │
├──────────────┼──────────────────────────────────────────┤
│  BM25        │  精确关键词匹配（"GPT-4o"→精确命中）    │
│              │  不理解语义                              │
├──────────────┼──────────────────────────────────────────┤
│  混合检索    │  向量 + BM25 结合，取长补短              │
│  (推荐！)    │  RRF 融合两者排名                        │
├──────────────┼──────────────────────────────────────────┤
│  重排序      │  粗检索(Top-50) → 精排序(Top-5)         │
│  (Reranking) │  Cross-Encoder 精确评分                  │
└──────────────┴──────────────────────────────────────────┘

推荐组合：混合检索 + 重排序
""")

# ============================================================================
# 2. 向量检索
# ============================================================================
print("\n--- 2. 向量检索 ---")

class VectorRetriever:
    """向量检索器"""

    def __init__(self, documents: list, embeddings: list):
        self.documents = documents
        self.embeddings = embeddings

    def search(self, query: str, top_k: int = 5, threshold: float = 0.0) -> list:
        q_emb = embed([query])[0]
        scores = [(i, cosine_sim(q_emb, emb)) for i, emb in enumerate(self.embeddings)]
        scores.sort(key=lambda x: x[1], reverse=True)
        results = [(self.documents[i], s) for i, s in scores[:top_k] if s >= threshold]
        return results

vec_retriever = VectorRetriever(knowledge, doc_embeddings)

queries = ["Python Web开发", "什么是注意力机制", "本地运行AI模型"]
print("向量检索:")
for q in queries:
    results = vec_retriever.search(q, 3)
    print(f"\n  Q: {q}")
    for doc, score in results:
        print(f"    [{score:.4f}] {doc[:50]}...")

# ============================================================================
# 3. BM25 检索
# ============================================================================
print("\n\n--- 3. BM25 ---")

class BM25Retriever:
    """BM25 关键词检索器"""

    def __init__(self, documents: list, k1: float = 1.5, b: float = 0.75):
        self.documents = documents
        self.k1, self.b = k1, b
        self.doc_freqs = {}
        self.tf_per_doc = []
        self.doc_lens = []

        for doc in documents:
            tokens = self._tokenize(doc)
            self.doc_lens.append(len(tokens))
            tf = Counter(tokens)
            self.tf_per_doc.append(tf)
            for word in set(tokens):
                self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1

        self.avg_len = sum(self.doc_lens) / len(self.doc_lens)
        self.n = len(documents)

    def _tokenize(self, text: str) -> list:
        return re.findall(r'[\u4e00-\u9fff]{1,4}|[a-zA-Z]+[\-]?[a-zA-Z]*\d*', text.lower())

    def search(self, query: str, top_k: int = 5) -> list:
        tokens = self._tokenize(query)
        scores = []
        for i in range(self.n):
            score = 0
            for t in tokens:
                df = self.doc_freqs.get(t, 0)
                if df == 0:
                    continue
                idf = math.log((self.n - df + 0.5) / (df + 0.5) + 1)
                tf = self.tf_per_doc[i].get(t, 0)
                dl = self.doc_lens[i]
                score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avg_len))
            scores.append((i, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [(self.documents[i], s) for i, s in scores[:top_k] if s > 0]

bm25_retriever = BM25Retriever(knowledge)

print("BM25 检索:")
for q in queries:
    results = bm25_retriever.search(q, 3)
    print(f"\n  Q: {q}")
    for doc, score in results:
        print(f"    [{score:.2f}] {doc[:50]}...")

# ============================================================================
# 4. 混合检索
# ============================================================================
print("\n\n--- 4. 混合检索 ---")

class HybridRetriever:
    """混合检索器（向量 + BM25 + RRF 融合）"""

    def __init__(self, documents: list, embeddings: list):
        self.documents = documents
        self.vec = VectorRetriever(documents, embeddings)
        self.bm25 = BM25Retriever(documents)

    def search(self, query: str, top_k: int = 5,
               alpha: float = 0.5, k: int = 60) -> list:
        """RRF 融合搜索"""
        # 向量排名
        vec_results = self.vec.search(query, top_k=len(self.documents))
        vec_ranks = {}
        for rank, (doc, _) in enumerate(vec_results):
            idx = self.documents.index(doc)
            vec_ranks[idx] = rank

        # BM25 排名
        bm25_results = self.bm25.search(query, top_k=len(self.documents))
        bm25_ranks = {}
        for rank, (doc, _) in enumerate(bm25_results):
            idx = self.documents.index(doc)
            bm25_ranks[idx] = rank

        # RRF 融合
        rrf_scores = {}
        for i in range(len(self.documents)):
            vec_score = alpha / (k + vec_ranks.get(i, 999))
            bm25_score = (1 - alpha) / (k + bm25_ranks.get(i, 999))
            rrf_scores[i] = vec_score + bm25_score

        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [(self.documents[i], score) for i, score in sorted_results[:top_k]]

hybrid = HybridRetriever(knowledge, doc_embeddings)

print("混合检索 vs 单独检索:")
test_queries = [
    "GPT-4o 多模态",       # 关键词明确 → BM25 强
    "如何让模型理解语义",   # 语义查询 → 向量强
    "Python Flask API",     # 混合
]

for q in test_queries:
    vec_r = vec_retriever.search(q, 2)
    bm25_r = bm25_retriever.search(q, 2)
    hybrid_r = hybrid.search(q, 2)

    print(f"\n  Q: {q}")
    print(f"    向量:  {[d[:25]+'...' for d, _ in vec_r]}")
    print(f"    BM25:  {[d[:25]+'...' for d, _ in bm25_r]}")
    print(f"    混合:  {[d[:25]+'...' for d, _ in hybrid_r]}")

# ============================================================================
# 5. 重排序
# ============================================================================
print("\n\n--- 5. 重排序 ---")
print("""
重排序 = 二次精排

流程：
  混合检索(Top-20) → Reranker 精排 → Top-5

Reranker 模型：
  ┌────────────────────┬──────────────────────────────────┐
  │  模型               │  特点                             │
  ├────────────────────┼──────────────────────────────────┤
  │  Cohere Rerank     │  API 调用，效果好，付费          │
  │  bge-reranker-v2   │  开源，本地部署                  │
  │  jina-reranker     │  多语言支持好                    │
  │  LLM-as-Reranker   │  用 LLM 打分，最灵活            │
  └────────────────────┴──────────────────────────────────┘
""")

class SimpleReranker:
    """简单重排序器（基于关键词密度+位置）"""

    def rerank(self, query: str, documents: list, top_n: int = 3) -> list:
        q_words = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]+', query.lower()))
        scored = []
        for i, (doc, orig_score) in enumerate(documents):
            d_words = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]+', doc.lower()))
            overlap = len(q_words & d_words)
            density = overlap / max(len(q_words), 1)
            rerank_score = 0.6 * orig_score + 0.4 * density
            scored.append((doc, rerank_score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

reranker = SimpleReranker()
query = "RAG 如何减少 LLM 的幻觉问题"
candidates = hybrid.search(query, 5)
reranked = reranker.rerank(query, candidates, 3)

print(f"重排序演示: \"{query}\"")
print(f"  混合检索 Top-5:")
for doc, score in candidates:
    print(f"    [{score:.4f}] {doc[:50]}...")
print(f"  重排序 Top-3:")
for doc, score in reranked:
    print(f"    [{score:.4f}] {doc[:50]}...")

# ============================================================================
# 6. 参数调优
# ============================================================================
print("\n--- 6. 参数调优 ---")
print("""
检索参数调优指南：

top_k 选择：
  top_k=3:  精确场景（FAQ问答）
  top_k=5:  通用场景（推荐）
  top_k=10: 复杂问题（需要多个角度信息）

相似度阈值：
  过滤低相关结果，避免噪音
  余弦相似度: >0.7 通常较相关
  建议: 不设太高阈值，让 reranker 去过滤

混合检索权重（alpha）：
  alpha=0.7: 偏语义（通用问答）
  alpha=0.5: 均衡（推荐起步）
  alpha=0.3: 偏关键词（专业术语多时）

Reranker:
  粗检索 top_k=20 → reranker top_n=5
  确保粗检索阶段召回率足够高
""")

# alpha 对比
print("alpha 参数对比:")
test_q = "ChromaDB 向量数据库"
for alpha in [0.2, 0.5, 0.8]:
    r = hybrid.search(test_q, 3, alpha=alpha)
    docs_str = " | ".join(d[:25] for d, _ in r)
    print(f"  alpha={alpha}: {docs_str}")

print("\n" + "=" * 60)
print("[完成] 第4课完成！你已经学会了：")
print("  [v] 四种检索策略（向量/BM25/混合/重排序）")
print("  [v] 向量检索（余弦相似度）")
print("  [v] BM25 关键词检索（TF-IDF变体）")
print("  [v] 混合检索 + RRF 融合算法")
print("  [v] 重排序（Reranking）")
print("  [v] 检索参数调优（top_k/阈值/alpha）")
print("=" * 60)
print("\n下一课：05_rag_optimization.py - RAG 优化")
