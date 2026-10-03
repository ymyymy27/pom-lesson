> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# ChromaDB 入门

## 学习目标

- 掌握 ChromaDB 的安装和基本操作
- 学会创建集合、存储和查询向量
- 理解元数据过滤和持久化存储

## 1. ChromaDB 简介

ChromaDB 是一个轻量级的开源向量数据库，特点：
- 开箱即用，无需额外服务
- 支持持久化和内存模式
- 内置 Embedding 函数
- 元数据过滤
- 与 LangChain 深度集成

```bash
pip install chromadb
```

## 2. 基本操作

```python
import chromadb

# 内存模式
client = chromadb.Client()

# 持久化模式（数据保存到磁盘）
client = chromadb.PersistentClient(path="./chroma_data")

# 创建集合
collection = client.create_collection(
    name="my_documents",
    metadata={"hnsw:space": "cosine"},  # 距离度量：cosine / l2 / ip
)

# 或获取已有集合
collection = client.get_or_create_collection("my_documents")
```

## 3. 添加数据

```python
# 添加文档（自动生成 Embedding）
collection.add(
    documents=["机器学习是AI的分支", "深度学习使用神经网络", "Python是编程语言"],
    ids=["doc1", "doc2", "doc3"],
    metadatas=[
        {"source": "textbook", "chapter": 1},
        {"source": "textbook", "chapter": 2},
        {"source": "tutorial", "chapter": 1},
    ]
)

# 添加预计算的 Embedding
collection.add(
    embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
    documents=["文本1", "文本2"],
    ids=["id1", "id2"],
)

# 更新
collection.update(
    ids=["doc1"],
    documents=["机器学习（ML）是人工智能的核心分支"],
)

# 删除
collection.delete(ids=["doc3"])
```

## 4. 查询

```python
# 语义搜索
results = collection.query(
    query_texts=["什么是人工智能？"],
    n_results=3,
)
print(results["documents"])     # 最相关的文档
print(results["distances"])     # 距离分数
print(results["metadatas"])     # 元数据

# 带元数据过滤
results = collection.query(
    query_texts=["深度学习"],
    n_results=5,
    where={"source": "textbook"},                    # 精确匹配
    where_document={"$contains": "神经网络"},          # 文档内容包含
)

# 复合条件
results = collection.query(
    query_texts=["机器学习"],
    where={
        "$and": [
            {"source": "textbook"},
            {"chapter": {"$gte": 2}},
        ]
    },
    n_results=3,
)

# 获取所有数据
all_data = collection.get()
print(f"总文档数: {collection.count()}")
```

## 5. 自定义 Embedding 函数

```python
from chromadb.utils.embedding_functions import (
    OpenAIEmbeddingFunction,
    SentenceTransformerEmbeddingFunction,
    OllamaEmbeddingFunction,
)

# OpenAI
openai_ef = OpenAIEmbeddingFunction(
    api_key="sk-xxx",
    model_name="text-embedding-3-small"
)

# Sentence Transformers（本地）
st_ef = SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-large-zh-v1.5"
)

# Ollama（本地）
ollama_ef = OllamaEmbeddingFunction(
    model_name="nomic-embed-text",
    url="http://localhost:11434/api/embeddings"
)

# 创建集合时指定
collection = client.create_collection(
    name="my_docs",
    embedding_function=st_ef,
)
```

## 6. 实战：文档语义搜索引擎

```python
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

class SemanticSearch:
    def __init__(self, collection_name="documents"):
        self.client = chromadb.PersistentClient(path="./search_db")
        self.ef = SentenceTransformerEmbeddingFunction(
            model_name="BAAI/bge-large-zh-v1.5"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, texts: list[str], metadatas: list[dict] = None):
        ids = [f"doc_{i}" for i in range(self.collection.count(),
                                          self.collection.count() + len(texts))]
        self.collection.add(
            documents=texts,
            ids=ids,
            metadatas=metadatas,
        )
        print(f"已添加 {len(texts)} 条文档，总计 {self.collection.count()} 条")

    def search(self, query: str, top_k: int = 5, **filters) -> list[dict]:
        kwargs = {"query_texts": [query], "n_results": top_k}
        if filters:
            kwargs["where"] = filters

        results = self.collection.query(**kwargs)

        output = []
        for i in range(len(results["documents"][0])):
            output.append({
                "text": results["documents"][0][i],
                "distance": results["distances"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            })
        return output

# 使用
search = SemanticSearch()
search.add_documents([
    "PyTorch 是一个深度学习框架",
    "TensorFlow 由 Google 开发",
    "Scikit-learn 用于传统机器学习",
    "Pandas 是数据分析利器",
])

results = search.search("深度学习框架有哪些？", top_k=2)
for r in results:
    print(f"[{r['distance']:.4f}] {r['text']}")
```

## 练习

1. 用 ChromaDB 创建一个持久化的文档集合，添加 50 条数据
2. 实现带元数据过滤的语义搜索
3. 对比不同 Embedding 模型在搜索准确度上的差异
4. 构建一个完整的文档搜索引擎（支持添加、搜索、删除）

## 下一节

→ [03-FAISS与Milvus](<03-FAISS 与 Milvus.md>)
