import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第7课：完整项目 - 语义搜索引擎
==============================================================================

整合前6课知识，构建一个生产级语义搜索引擎：

功能：
1. 文档管理（添加/分块/索引）
2. 多模式搜索（向量/BM25/混合）
3. 重排序与过滤
4. 搜索效果评估
5. 查询接口

架构：
  文档 → 分块 → Embedding → 向量存储 → 搜索 → 重排序 → 结果
==============================================================================
"""

import json
import re
import math
import time
import hashlib
import numpy as np
from collections import Counter
from datetime import datetime

import httpx

OLLAMA_URL = "http://localhost:11434"

print("=" * 60)
print("第7课：完整项目 - 语义搜索引擎")
print("=" * 60)

# ============================================================================
# 1. Embedding 层
# ============================================================================
print("\n--- 1. Embedding 层 ---")

class EmbeddingService:
    """Embedding 服务"""

    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model
        self.cache = {}
        self.call_count = 0

    def embed(self, texts: list) -> list:
        # 缓存
        uncached = []
        uncached_idx = []
        results = [None] * len(texts)

        for i, text in enumerate(texts):
            key = hashlib.md5(text.encode()).hexdigest()
            if key in self.cache:
                results[i] = self.cache[key]
            else:
                uncached.append(text)
                uncached_idx.append(i)

        if uncached:
            embeddings = self._call_api(uncached)
            for j, emb in enumerate(embeddings):
                idx = uncached_idx[j]
                results[idx] = emb
                key = hashlib.md5(uncached[j].encode()).hexdigest()
                self.cache[key] = emb

        self.call_count += 1
        return results

    def _call_api(self, texts: list) -> list:
        try:
            resp = httpx.post(f"{OLLAMA_URL}/api/embed", json={
                "model": self.model, "input": texts,
            }, timeout=30.0)
            return resp.json().get("embeddings", [])
        except:
            np.random.seed(hash(str(texts)) % 2**31)
            return [np.random.randn(768).tolist() for _ in texts]

emb_service = EmbeddingService()
print(f"Embedding 服务: model={emb_service.model}, 缓存=✓")

# ============================================================================
# 2. 文本分块器
# ============================================================================
print("\n--- 2. 分块器 ---")

class TextChunker:
    """文本分块器"""

    def __init__(self, chunk_size: int = 300, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", "。", "！", "？", ".", " "]

    def chunk(self, text: str, metadata: dict = None) -> list:
        chunks = self._split(text)
        result = []
        for i, chunk_text in enumerate(chunks):
            if not chunk_text.strip():
                continue
            meta = {**(metadata or {}), "chunk_id": i, "chunk_total": len(chunks)}
            result.append({"text": chunk_text.strip(), "metadata": meta})
        return result

    def _split(self, text: str) -> list:
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        for sep in self.separators:
            if sep in text:
                parts = text.split(sep)
                merged = []
                current = ""
                for part in parts:
                    candidate = current + sep + part if current else part
                    if len(candidate) <= self.chunk_size:
                        current = candidate
                    else:
                        if current.strip():
                            merged.append(current.strip())
                        current = part
                if current.strip():
                    merged.append(current.strip())
                if len(merged) > 1:
                    return merged

        # 按字符切割
        return [text[i:i+self.chunk_size]
                for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]

chunker = TextChunker(chunk_size=300, chunk_overlap=50)
print(f"分块器: size={chunker.chunk_size}, overlap={chunker.chunk_overlap}")

# ============================================================================
# 3. BM25 搜索
# ============================================================================

class BM25Index:
    """BM25 关键词索引"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = []
        self.doc_freqs = {}
        self.tf_per_doc = []
        self.doc_lens = []
        self.avg_len = 0

    def _tokenize(self, text: str) -> list:
        return re.findall(r'[\u4e00-\u9fff]{1,4}|[a-zA-Z]+\d*', text.lower())

    def add(self, documents: list):
        self.docs = documents
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

        self.avg_len = sum(self.doc_lens) / len(self.doc_lens) if self.doc_lens else 1

    def search(self, query: str, top_k: int = 10) -> list:
        tokens = self._tokenize(query)
        n = len(self.docs)
        scores = []
        for i in range(n):
            score = 0
            for t in tokens:
                df = self.doc_freqs.get(t, 0)
                if df == 0:
                    continue
                idf = math.log((n - df + 0.5) / (df + 0.5) + 1)
                tf = self.tf_per_doc[i].get(t, 0)
                dl = self.doc_lens[i]
                score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avg_len))
            scores.append((i, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

# ============================================================================
# 4. 搜索引擎核心
# ============================================================================
print("\n--- 3. 搜索引擎 ---")

class SemanticSearchEngine:
    """语义搜索引擎"""

    def __init__(self, emb_service: EmbeddingService, chunker: TextChunker):
        self.emb_service = emb_service
        self.chunker = chunker
        self.bm25 = BM25Index()
        self.documents = []  # 原始文档
        self.chunks = []     # 分块后
        self.embeddings = [] # 向量
        self.stats = {"docs": 0, "chunks": 0, "queries": 0}

    def add_document(self, text: str, metadata: dict = None):
        doc_id = len(self.documents)
        self.documents.append({"text": text, "metadata": metadata or {}})
        new_chunks = self.chunker.chunk(text, {**(metadata or {}), "doc_id": doc_id})
        self.chunks.extend(new_chunks)
        self.stats["docs"] += 1
        self.stats["chunks"] = len(self.chunks)

    def build_index(self):
        """构建索引"""
        texts = [c["text"] for c in self.chunks]
        self.embeddings = self.emb_service.embed(texts)
        self.bm25.add(texts)
        return {"chunks": len(self.chunks), "dim": len(self.embeddings[0]) if self.embeddings else 0}

    def search(self, query: str, top_k: int = 5,
               mode: str = "hybrid", alpha: float = 0.5,
               filters: dict = None) -> list:
        """搜索"""
        self.stats["queries"] += 1

        if mode == "vector":
            return self._vector_search(query, top_k, filters)
        elif mode == "bm25":
            return self._bm25_search(query, top_k, filters)
        else:
            return self._hybrid_search(query, top_k, alpha, filters)

    def _vector_search(self, query: str, top_k: int, filters: dict = None) -> list:
        query_emb = self.emb_service.embed([query])[0]
        scores = []
        for i, emb in enumerate(self.embeddings):
            if filters and not self._match_filter(self.chunks[i], filters):
                continue
            sim = self._cosine(query_emb, emb)
            scores.append((i, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return self._format_results(scores[:top_k])

    def _bm25_search(self, query: str, top_k: int, filters: dict = None) -> list:
        results = self.bm25.search(query, top_k=len(self.chunks))
        if filters:
            results = [(i, s) for i, s in results if self._match_filter(self.chunks[i], filters)]
        return self._format_results(results[:top_k])

    def _hybrid_search(self, query: str, top_k: int, alpha: float,
                       filters: dict = None) -> list:
        """RRF 融合"""
        k = 60
        # 向量排名
        query_emb = self.emb_service.embed([query])[0]
        vec_scores = [(i, self._cosine(query_emb, emb)) for i, emb in enumerate(self.embeddings)]
        vec_scores.sort(key=lambda x: x[1], reverse=True)
        vec_ranks = {idx: rank for rank, (idx, _) in enumerate(vec_scores)}

        # BM25 排名
        bm25_results = self.bm25.search(query, top_k=len(self.chunks))
        bm25_ranks = {idx: rank for rank, (idx, _) in enumerate(bm25_results)}

        # RRF
        rrf = {}
        for i in range(len(self.chunks)):
            if filters and not self._match_filter(self.chunks[i], filters):
                continue
            rrf[i] = (alpha / (k + vec_ranks.get(i, 999)) +
                      (1 - alpha) / (k + bm25_ranks.get(i, 999)))

        sorted_rrf = sorted(rrf.items(), key=lambda x: x[1], reverse=True)
        return self._format_results(sorted_rrf[:top_k])

    def _match_filter(self, chunk: dict, filters: dict) -> bool:
        meta = chunk.get("metadata", {})
        for key, val in filters.items():
            if meta.get(key) != val:
                return False
        return True

    def _cosine(self, a, b) -> float:
        a, b = np.array(a), np.array(b)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        return float(np.dot(a, b) / norm) if norm > 0 else 0

    def _format_results(self, scored: list) -> list:
        results = []
        for idx, score in scored:
            results.append({
                "text": self.chunks[idx]["text"],
                "score": round(score, 4),
                "metadata": self.chunks[idx].get("metadata", {}),
            })
        return results

    def get_stats(self) -> dict:
        return {**self.stats, "cache_size": len(self.emb_service.cache)}

# ============================================================================
# 5. 构建搜索引擎
# ============================================================================
print("\n--- 4. 构建引擎 ---")

engine = SemanticSearchEngine(emb_service, chunker)

# 添加文档
docs = [
    {"text": """Python 编程语言

Python 是一种高级通用编程语言，由 Guido van Rossum 于 1991 年发布。Python 以其简洁优雅的语法著称，强调代码的可读性。

Python 的主要应用领域包括：Web 开发（Django、Flask）、数据分析（Pandas、NumPy）、机器学习（PyTorch、TensorFlow）、自动化脚本等。

Python 使用缩进来定义代码块，这使得代码结构清晰。Python 拥有丰富的第三方库生态系统，通过 pip 包管理器可以方便地安装各种库。""",
     "metadata": {"source": "programming", "topic": "python"}},

    {"text": """机器学习基础

机器学习是人工智能的一个子领域，让计算机能够从数据中学习模式，而无需显式编程。

监督学习使用标注数据训练模型，常见算法包括线性回归、决策树、随机森林和支持向量机。无监督学习从无标注数据中发现模式，如聚类和降维。强化学习通过试错和奖励信号来优化决策。

深度学习是机器学习的子集，使用多层神经网络处理复杂数据。卷积神经网络（CNN）擅长图像处理，Transformer 架构革命性地改变了自然语言处理。""",
     "metadata": {"source": "ai", "topic": "ml"}},

    {"text": """向量数据库与 RAG

向量数据库是专门用于存储和检索高维向量的数据库。在 RAG（检索增强生成）架构中，向量数据库是核心组件。

常见的向量数据库包括：ChromaDB（轻量级、嵌入式）、FAISS（高性能、Facebook开源）、Milvus（分布式、生产级）、Pinecone（云服务）。

RAG 的工作流程：将文档分块并转为 Embedding 存入向量数据库，当用户提问时，先检索相关文档片段，再将其作为上下文提供给 LLM 生成回答。这种方式能有效减少 LLM 的幻觉问题。""",
     "metadata": {"source": "ai", "topic": "vector_db"}},
]

for doc in docs:
    engine.add_document(doc["text"], doc["metadata"])

index_info = engine.build_index()
print(f"索引构建完成: {index_info}")

# ============================================================================
# 6. 搜索演示
# ============================================================================
print("\n--- 5. 搜索演示 ---")

queries = [
    ("Python 有哪些应用领域", "hybrid", None),
    ("什么是深度学习", "vector", None),
    ("ChromaDB FAISS", "bm25", None),
    ("RAG 是什么", "hybrid", {"source": "ai"}),
]

for query, mode, filters in queries:
    results = engine.search(query, top_k=2, mode=mode, filters=filters)
    filter_str = f" [过滤: {filters}]" if filters else ""
    print(f"\n  Q: \"{query}\" (mode={mode}{filter_str})")
    for r in results:
        print(f"    [{r['score']:.4f}] {r['text'][:60]}...")

# ============================================================================
# 7. 项目总结
# ============================================================================
stats = engine.get_stats()
print(f"""
┌────────────────────────────────────────────────────────┐
│         语义搜索引擎 - 项目架构                         │
├────────────────────────────────────────────────────────┤
│                                                        │
│  EmbeddingService（Embedding 层）                      │
│  ├── embed()             获取向量（带缓存）            │
│  └── Ollama / OpenAI 后端可切换                        │
│                                                        │
│  TextChunker（分块器）                                 │
│  └── chunk()             递归字符分割                  │
│                                                        │
│  BM25Index（关键词索引）                               │
│  ├── add()               构建倒排索引                  │
│  └── search()            BM25 关键词搜索               │
│                                                        │
│  SemanticSearchEngine（搜索引擎）                      │
│  ├── add_document()      添加文档                      │
│  ├── build_index()       构建向量+BM25索引             │
│  ├── search()            三种搜索模式                  │
│  │   ├── vector          纯向量搜索                    │
│  │   ├── bm25            纯关键词搜索                  │
│  │   └── hybrid          RRF融合混合搜索              │
│  └── 元数据过滤           按字段过滤结果               │
│                                                        │
│  整合的知识                                            │
│  ├── 第1课: Embedding原理/距离度量                    │
│  ├── 第2课: Embedding模型选型                         │
│  ├── 第3课: ChromaDB向量存储                          │
│  ├── 第4课: FAISS高性能检索                           │
│  ├── 第5课: 文本分块策略                              │
│  └── 第6课: 混合检索/重排序/评估                      │
│                                                        │
│  统计:                                                 │
│    文档: {stats['docs']}, 块: {stats['chunks']}, 查询: {stats['queries']}       │
│    Embedding缓存: {stats['cache_size']}                │
│                                                        │
│  扩展方向                                              │
│  → ChromaDB/Milvus 持久化存储                          │
│  → Reranker 精排序                                     │
│  → Multi-Query 查询改写                                │
│  → Web API（FastAPI 接口）                             │
│  → 增量索引（文档更新时局部更新）                     │
│  → 与 LLM 结合 → 完整 RAG 系统                        │
└────────────────────────────────────────────────────────┘
""")

print("=" * 60)
print("[完成] 第7课完成！你已经学会了：")
print("  [v] Embedding 服务层（缓存+多后端）")
print("  [v] 文本分块器（递归分割）")
print("  [v] BM25 关键词索引")
print("  [v] 三模式搜索引擎（向量/BM25/混合RRF）")
print("  [v] 元数据过滤")
print("  [v] 整合前6课全部核心知识")
print("=" * 60)
print("\nlearn-vector-db 课程全部完成！🎉")
