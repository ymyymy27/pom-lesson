import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：索引管道（分块 → Embedding → 存储）
==============================================================================

索引管道 = RAG 的离线阶段
把原始文档变成可检索的向量索引

本课内容：
1. 索引管道概述
2. 文本分块
3. Embedding 生成
4. ChromaDB 存储
5. 完整索引管道
6. 增量索引
==============================================================================
"""

import json
import hashlib
import time
import re
import numpy as np
import tempfile
import shutil

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

print("=" * 60)
print("第3课：索引管道")
print("=" * 60)

# ============================================================================
# 1. 索引管道概述
# ============================================================================
print("\n--- 1. 概述 ---")
print("""
索引管道的三个步骤：

  原始文档
      ↓
  ┌──────────────┐
  │  1. 分块     │  大文档 → 小段落（300-800字）
  │  (Chunking)  │  保持语义完整，添加重叠
  └──────┬───────┘
         ↓
  ┌──────────────┐
  │  2. Embedding│  文本 → 向量（768/1024/1536维）
  │              │  使用 Embedding 模型
  └──────┬───────┘
         ↓
  ┌──────────────┐
  │  3. 存储     │  向量 + 文本 + 元数据 → 向量数据库
  │  (Storage)   │  ChromaDB / FAISS / Milvus
  └──────────────┘

关键决策：
  chunk_size: 300-800（太小语义碎片，太大检索不精确）
  Embedding 模型: nomic / bge / OpenAI
  向量数据库: ChromaDB（原型）/ Milvus（生产）
""")

# ============================================================================
# 2. 文本分块
# ============================================================================
print("\n--- 2. 文本分块 ---")

class TextChunker:
    """递归字符文本分块器"""

    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", "。", "！", "？", ".", " "]

    def split(self, text: str) -> list:
        chunks = self._recursive_split(text)
        return [c for c in chunks if c.strip()]

    def _recursive_split(self, text: str) -> list:
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        for sep in self.separators:
            if sep not in text:
                continue
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

    def split_with_metadata(self, text: str, base_metadata: dict = None) -> list:
        chunks = self.split(text)
        return [{
            "text": chunk,
            "metadata": {
                **(base_metadata or {}),
                "chunk_id": i,
                "chunk_total": len(chunks),
                "char_count": len(chunk),
            }
        } for i, chunk in enumerate(chunks)]

chunker = TextChunker(chunk_size=300, chunk_overlap=30)

sample_text = """人工智能（AI）是计算机科学的一个分支，致力于创建能模拟人类智能的系统。

机器学习是 AI 的核心子领域，让计算机从数据中学习。监督学习使用标注数据，无监督学习发现隐藏模式，强化学习通过奖励信号优化决策。

深度学习是机器学习的子集，使用多层神经网络。卷积神经网络（CNN）擅长图像处理，循环神经网络（RNN）处理序列数据，Transformer 架构革新了自然语言处理。

大语言模型（LLM）基于 Transformer，通过海量文本预训练获得强大的语言能力。GPT-4、Claude、Gemini 等模型能完成翻译、写作、编程等多种任务。

RAG（检索增强生成）让 LLM 基于检索到的外部知识回答问题，有效减少幻觉，实现私域知识问答。"""

chunks = chunker.split_with_metadata(sample_text, {"source": "ai_intro.md"})
print(f"分块结果: {len(chunks)} 块")
for c in chunks:
    print(f"  [{c['metadata']['chunk_id']}] ({c['metadata']['char_count']}字) {c['text'][:50]}...")

# ============================================================================
# 3. Embedding 生成
# ============================================================================
print("\n--- 3. Embedding ---")

class EmbeddingService:
    """Embedding 服务（带缓存和批量处理）"""

    def __init__(self, batch_size: int = 32):
        self.batch_size = batch_size
        self.cache = {}
        self.stats = {"calls": 0, "cached": 0}

    def embed_batch(self, texts: list) -> list:
        results = [None] * len(texts)
        uncached = []
        uncached_idx = []

        for i, text in enumerate(texts):
            key = hashlib.md5(text.encode()).hexdigest()
            if key in self.cache:
                results[i] = self.cache[key]
                self.stats["cached"] += 1
            else:
                uncached.append(text)
                uncached_idx.append(i)

        # 批量处理未缓存的
        for batch_start in range(0, len(uncached), self.batch_size):
            batch = uncached[batch_start:batch_start + self.batch_size]
            embeddings = embed(batch)
            for j, emb in enumerate(embeddings):
                global_idx = uncached_idx[batch_start + j]
                results[global_idx] = emb
                key = hashlib.md5(uncached[batch_start + j].encode()).hexdigest()
                self.cache[key] = emb

        self.stats["calls"] += 1
        return results

emb_service = EmbeddingService()
chunk_texts = [c["text"] for c in chunks]
embeddings = emb_service.embed_batch(chunk_texts)
print(f"Embedding: {len(embeddings)} 条, 维度: {len(embeddings[0]) if embeddings else 0}")
print(f"  缓存命中: {emb_service.stats['cached']}")

# 再次 embed 相同文本（测试缓存）
embeddings2 = emb_service.embed_batch(chunk_texts)
print(f"  再次embed: 缓存命中 {emb_service.stats['cached']}")

# ============================================================================
# 4. ChromaDB 存储
# ============================================================================
print("\n--- 4. 存储 ---")

try:
    import chromadb

    temp_db = tempfile.mkdtemp(prefix="rag_db_")
    client = chromadb.PersistentClient(path=temp_db)

    collection = client.get_or_create_collection(
        name="knowledge_base",
        metadata={"hnsw:space": "cosine"},
    )

    # 添加数据
    collection.add(
        documents=[c["text"] for c in chunks],
        embeddings=embeddings,
        ids=[f"chunk_{c['metadata']['chunk_id']}" for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )
    print(f"ChromaDB 存储: {collection.count()} 条")

    # 检索测试
    results = collection.query(
        query_embeddings=[embed(["什么是深度学习"])[0]],
        n_results=2,
    )
    print(f"检索测试:")
    for doc, dist in zip(results["documents"][0], results["distances"][0]):
        print(f"  ({dist:.4f}) {doc[:50]}...")

    shutil.rmtree(temp_db, ignore_errors=True)

except ImportError:
    print("chromadb 未安装，使用内存向量存储演示")

    class SimpleVectorStore:
        """简单向量存储"""
        def __init__(self):
            self.documents = []
            self.embeddings = []
            self.metadatas = []

        def add(self, documents, embeddings, metadatas=None):
            self.documents.extend(documents)
            self.embeddings.extend(embeddings)
            self.metadatas.extend(metadatas or [{}] * len(documents))

        def query(self, query_embedding, top_k=5):
            scores = []
            q = np.array(query_embedding)
            for i, emb in enumerate(self.embeddings):
                e = np.array(emb)
                sim = float(np.dot(q, e) / (np.linalg.norm(q) * np.linalg.norm(e)))
                scores.append((i, sim))
            scores.sort(key=lambda x: x[1], reverse=True)
            return [(self.documents[i], s, self.metadatas[i]) for i, s in scores[:top_k]]

        def count(self):
            return len(self.documents)

    store = SimpleVectorStore()
    store.add([c["text"] for c in chunks], embeddings, [c["metadata"] for c in chunks])
    print(f"内存存储: {store.count()} 条")

    q_emb = embed(["什么是深度学习"])[0]
    results = store.query(q_emb, 2)
    print(f"检索测试:")
    for doc, sim, meta in results:
        print(f"  ({sim:.4f}) {doc[:50]}...")

# ============================================================================
# 5. 完整索引管道
# ============================================================================
print("\n--- 5. 完整管道 ---")

class IndexingPipeline:
    """完整索引管道"""

    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50):
        self.chunker = TextChunker(chunk_size, chunk_overlap)
        self.emb_service = EmbeddingService()
        self.store = SimpleVectorStore() if 'SimpleVectorStore' in dir() else None
        self.doc_hashes = set()

    def ingest(self, text: str, metadata: dict = None) -> dict:
        """索引一个文档"""
        # 去重
        doc_hash = hashlib.md5(text.encode()).hexdigest()
        if doc_hash in self.doc_hashes:
            return {"status": "duplicate", "chunks": 0}
        self.doc_hashes.add(doc_hash)

        # 分块
        chunks = self.chunker.split_with_metadata(text, metadata)

        # Embedding
        texts = [c["text"] for c in chunks]
        embeddings = self.emb_service.embed_batch(texts)

        # 存储
        if self.store:
            self.store.add(texts, embeddings, [c["metadata"] for c in chunks])

        return {"status": "ok", "chunks": len(chunks), "total": self.store.count() if self.store else 0}

    def search(self, query: str, top_k: int = 3) -> list:
        q_emb = self.emb_service.embed_batch([query])[0]
        if self.store:
            return self.store.query(q_emb, top_k)
        return []

pipeline = IndexingPipeline(chunk_size=300)

# 批量索引
docs_to_index = [
    ("Python 是高级编程语言，广泛用于Web开发、数据分析和AI。Django和Flask是常用的Web框架。", {"source": "python.md"}),
    ("向量数据库存储高维向量。ChromaDB适合原型，FAISS性能最高，Milvus适合生产环境。", {"source": "vectordb.md"}),
    ("RAG让LLM基于检索到的文档回答，减少幻觉。核心流程：分块→Embedding→检索→生成。", {"source": "rag.md"}),
]

print("批量索引:")
for text, meta in docs_to_index:
    result = pipeline.ingest(text, meta)
    print(f"  {meta['source']}: {result}")

# 测试检索
print(f"\n检索测试:")
for q in ["Python Web框架", "向量数据库选型", "RAG怎么减少幻觉"]:
    results = pipeline.search(q, 2)
    print(f"  Q: {q}")
    for doc, score, meta in results:
        print(f"    ({score:.4f}) [{meta.get('source','')}] {doc[:40]}...")

# ============================================================================
# 6. 增量索引
# ============================================================================
print("\n--- 6. 增量索引 ---")
print("""
增量索引 = 只索引新增/修改的文档

策略：
  1. 文档指纹（MD5）去重
  2. 修改时间追踪
  3. 差异更新（只更新变化的块）

```python
class IncrementalIndexer:
    def __init__(self):
        self.doc_hashes = {}  # path → hash

    def should_index(self, path, content):
        new_hash = md5(content)
        old_hash = self.doc_hashes.get(path)
        if new_hash == old_hash:
            return False  # 未变化
        self.doc_hashes[path] = new_hash
        return True  # 需要重新索引

    def index_directory(self, dir_path):
        for file in scan_files(dir_path):
            content = read_file(file)
            if self.should_index(file, content):
                pipeline.ingest(content, {"source": file})
                print(f"  索引更新: {file}")
            else:
                print(f"  跳过(未变): {file}")
```

生产建议：
  • 定时任务（每天/每小时）扫描文件变更
  • 文件监控（watchdog）实时索引
  • 版本号管理（每次索引记录版本）
""")

# 增量演示
result = pipeline.ingest(docs_to_index[0][0], docs_to_index[0][1])  # 重复文档
print(f"重复文档: {result}")  # status=duplicate

print("\n" + "=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] 索引管道三步骤（分块→Embedding→存储）")
print("  [v] 递归字符文本分块器")
print("  [v] Embedding 批量处理与缓存")
print("  [v] ChromaDB / 内存向量存储")
print("  [v] 完整索引管道（去重+分块+向量化+存储）")
print("  [v] 增量索引策略")
print("=" * 60)
print("\n下一课：04_retrieval_strategies.py - 检索策略")
