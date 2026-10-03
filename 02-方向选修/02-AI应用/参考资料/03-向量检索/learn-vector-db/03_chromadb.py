import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：ChromaDB 完整使用指南
==============================================================================

ChromaDB = 最简单的开源向量数据库
零配置、嵌入式、支持持久化

本课内容：
1. ChromaDB 基础操作
2. 集合管理
3. 增删改查
4. 元数据过滤
5. 自定义 Embedding
6. 持久化存储
==============================================================================
"""

import json
import numpy as np
import tempfile
import shutil

print("=" * 60)
print("第3课：ChromaDB")
print("=" * 60)

# ============================================================================
# 1. 基础操作
# ============================================================================
print("\n--- 1. 基础操作 ---")
print("""
ChromaDB 两种模式：

  内存模式（测试/临时）：
    client = chromadb.Client()

  持久化模式（数据保存到磁盘）：
    client = chromadb.PersistentClient(path="./chroma_data")

  客户端/服务器模式（多进程共享）：
    # 服务端: chroma run --host localhost --port 8000
    client = chromadb.HttpClient(host="localhost", port=8000)
""")

try:
    import chromadb

    # 使用临时目录避免污染工作目录
    temp_dir = tempfile.mkdtemp(prefix="chroma_")
    client = chromadb.PersistentClient(path=temp_dir)
    print(f"ChromaDB 客户端创建成功（持久化: {temp_dir}）")

    # ========================================================================
    # 2. 集合管理
    # ========================================================================
    print("\n--- 2. 集合管理 ---")

    # 创建集合
    collection = client.create_collection(
        name="documents",
        metadata={"hnsw:space": "cosine"},  # 距离度量
    )
    print(f"创建集合: {collection.name}")

    # 获取或创建
    collection2 = client.get_or_create_collection("faq")
    print(f"获取或创建: {collection2.name}")

    # 列出所有集合
    collections = client.list_collections()
    print(f"所有集合: {[c.name for c in collections]}")

    # ========================================================================
    # 3. 增删改查
    # ========================================================================
    print("\n--- 3. CRUD 操作 ---")

    # 添加文档（ChromaDB 自动生成 embedding）
    collection.add(
        documents=[
            "Python 是一种通用编程语言，以简洁著称",
            "JavaScript 是 Web 前端的核心语言",
            "Rust 是一种注重安全性和性能的系统语言",
            "Go 是 Google 开发的高并发编程语言",
            "TypeScript 是 JavaScript 的超集，添加了类型系统",
            "Java 是企业级应用最常用的编程语言",
            "C++ 是高性能计算和游戏开发的首选",
            "机器学习是人工智能的一个重要分支",
            "深度学习使用多层神经网络处理复杂数据",
            "自然语言处理让计算机理解人类语言",
        ],
        ids=[f"doc_{i}" for i in range(10)],
        metadatas=[
            {"category": "language", "difficulty": "easy"},
            {"category": "language", "difficulty": "medium"},
            {"category": "language", "difficulty": "hard"},
            {"category": "language", "difficulty": "medium"},
            {"category": "language", "difficulty": "medium"},
            {"category": "language", "difficulty": "medium"},
            {"category": "language", "difficulty": "hard"},
            {"category": "ai", "difficulty": "medium"},
            {"category": "ai", "difficulty": "hard"},
            {"category": "ai", "difficulty": "hard"},
        ],
    )
    print(f"添加 {collection.count()} 条文档")

    # 查询（语义搜索）
    results = collection.query(
        query_texts=["高性能编程语言"],
        n_results=3,
    )
    print(f"\n查询: '高性能编程语言'")
    for i, (doc, dist) in enumerate(zip(results["documents"][0], results["distances"][0])):
        print(f"  [{i+1}] ({dist:.4f}) {doc}")

    # 更新
    collection.update(
        ids=["doc_0"],
        documents=["Python 是全球最流行的编程语言，广泛用于AI、Web和数据分析"],
    )
    print(f"\n更新 doc_0 成功")

    # 获取指定文档
    item = collection.get(ids=["doc_0"])
    print(f"获取 doc_0: {item['documents'][0][:40]}...")

    # 删除
    collection.delete(ids=["doc_6"])
    print(f"删除 doc_6，剩余: {collection.count()} 条")

    # ========================================================================
    # 4. 元数据过滤
    # ========================================================================
    print("\n--- 4. 元数据过滤 ---")

    # 精确匹配
    results = collection.query(
        query_texts=["编程语言"],
        n_results=5,
        where={"category": "language"},
    )
    print(f"过滤 category=language:")
    for doc, dist in zip(results["documents"][0], results["distances"][0]):
        print(f"  ({dist:.4f}) {doc[:40]}...")

    # 复合条件
    results = collection.query(
        query_texts=["入门编程"],
        n_results=5,
        where={
            "$and": [
                {"category": "language"},
                {"difficulty": {"$ne": "hard"}},
            ]
        },
    )
    print(f"\n过滤 language + 非hard:")
    for doc in results["documents"][0]:
        print(f"  {doc[:40]}...")

    # 文档内容过滤
    results = collection.query(
        query_texts=["AI技术"],
        n_results=5,
        where_document={"$contains": "神经网络"},
    )
    print(f"\n文档包含'神经网络':")
    for doc in results["documents"][0]:
        print(f"  {doc[:40]}...")

    print("""
元数据过滤操作符：
  $eq: 等于       {"field": "value"} 或 {"field": {"$eq": "value"}}
  $ne: 不等于     {"field": {"$ne": "value"}}
  $gt: 大于       {"field": {"$gt": 5}}
  $gte: 大于等于  {"field": {"$gte": 5}}
  $lt: 小于       {"field": {"$lt": 10}}
  $lte: 小于等于  {"field": {"$lte": 10}}
  $in: 在列表中   {"field": {"$in": ["a", "b"]}}
  $nin: 不在列表  {"field": {"$nin": ["a", "b"]}}

  $and: 与        {"$and": [条件1, 条件2]}
  $or:  或        {"$or": [条件1, 条件2]}

文档过滤：
  $contains:     文档包含子串
  $not_contains: 文档不包含子串
""")

    # ========================================================================
    # 5. 自定义 Embedding
    # ========================================================================
    print("--- 5. 自定义 Embedding ---")
    print("""
ChromaDB 支持多种 Embedding 后端：

```python
from chromadb.utils.embedding_functions import (
    OpenAIEmbeddingFunction,
    SentenceTransformerEmbeddingFunction,
    OllamaEmbeddingFunction,
)

# OpenAI
ef = OpenAIEmbeddingFunction(
    api_key="sk-xxx",
    model_name="text-embedding-3-small"
)

# 本地 HuggingFace
ef = SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-large-zh-v1.5"
)

# Ollama
ef = OllamaEmbeddingFunction(
    model_name="nomic-embed-text",
    url="http://localhost:11434/api/embeddings"
)

# 使用
collection = client.create_collection(
    name="custom_embedding",
    embedding_function=ef,
)
```

也可以传入预计算的 embedding：
```python
collection.add(
    embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...]],
    documents=["文本1", "文本2"],
    ids=["id1", "id2"],
)
```
""")

    # 使用预计算 embedding 演示
    custom_col = client.get_or_create_collection("custom_emb")
    np.random.seed(42)
    custom_col.add(
        embeddings=[np.random.randn(128).tolist() for _ in range(5)],
        documents=["文档A", "文档B", "文档C", "文档D", "文档E"],
        ids=["a", "b", "c", "d", "e"],
    )
    results = custom_col.query(
        query_embeddings=[np.random.randn(128).tolist()],
        n_results=3,
    )
    print(f"自定义 Embedding 查询: {results['documents'][0]}")

    # ========================================================================
    # 6. 持久化
    # ========================================================================
    print("\n--- 6. 持久化 ---")
    print(f"""
PersistentClient 自动保存数据到磁盘。

当前数据目录: {temp_dir}
集合数: {len(client.list_collections())}
documents 集合: {collection.count()} 条

重启后加载：
```python
client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_collection("documents")
# 数据全部还在！
```
""")

    # 清理
    shutil.rmtree(temp_dir, ignore_errors=True)
    print("临时数据已清理")

except ImportError:
    print("chromadb 未安装，跳过实践演示")
    print("安装: pip install chromadb")
    print("""
以上内容展示了 ChromaDB 的完整用法：
1. 创建客户端（内存/持久化/HTTP）
2. 集合管理（create/get/list/delete）
3. CRUD 操作（add/query/update/delete）
4. 元数据过滤（$eq/$gt/$and/$or...）
5. 自定义 Embedding 函数
6. 持久化存储
""")

print("\n" + "=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] ChromaDB 三种运行模式")
print("  [v] 集合创建与管理")
print("  [v] 完整 CRUD 操作")
print("  [v] 元数据过滤（精确/范围/复合/文档）")
print("  [v] 自定义 Embedding 函数")
print("  [v] 持久化存储与恢复")
print("=" * 60)
print("\n下一课：04_faiss.py - FAISS 高性能检索")
