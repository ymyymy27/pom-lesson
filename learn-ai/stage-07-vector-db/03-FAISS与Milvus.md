# FAISS 与 Milvus

## 学习目标

- 掌握 FAISS 高性能向量检索
- 了解 Milvus 分布式向量数据库
- 学会根据场景选择合适的向量数据库

## 1. FAISS

Facebook AI Similarity Search，高性能向量检索库。

```bash
pip install faiss-cpu    # CPU 版
# pip install faiss-gpu  # GPU 版
```

```python
import faiss
import numpy as np

# 准备数据
dim = 768                          # 向量维度
n_vectors = 10000                  # 向量数量
vectors = np.random.rand(n_vectors, dim).astype('float32')

# 1. Flat Index（精确搜索，暴力枚举）
index = faiss.IndexFlatL2(dim)     # L2 距离
# index = faiss.IndexFlatIP(dim)   # 内积（余弦相似度需先归一化）
index.add(vectors)

# 搜索
query = np.random.rand(1, dim).astype('float32')
distances, indices = index.search(query, k=5)    # Top-5
print(f"最近邻索引: {indices[0]}")
print(f"距离: {distances[0]}")

# 2. IVF Index（近似搜索，更快）
nlist = 100  # 聚类中心数
quantizer = faiss.IndexFlatL2(dim)
index_ivf = faiss.IndexIVFFlat(quantizer, dim, nlist)
index_ivf.train(vectors)          # 需要先训练
index_ivf.add(vectors)
index_ivf.nprobe = 10             # 搜索时检查的聚类数

distances, indices = index_ivf.search(query, k=5)

# 3. HNSW Index（图搜索，推荐）
index_hnsw = faiss.IndexHNSWFlat(dim, 32)  # 32 = 图的连接数
index_hnsw.add(vectors)

distances, indices = index_hnsw.search(query, k=5)
```

### 保存与加载

```python
# 保存
faiss.write_index(index, "vectors.index")

# 加载
index = faiss.read_index("vectors.index")
```

### 带 ID 映射

```python
# FAISS 默认用顺序 ID，需要自定义 ID 时：
index = faiss.IndexFlatL2(dim)
index_with_ids = faiss.IndexIDMap(index)

ids = np.array([100, 200, 300, 400, 500], dtype=np.int64)
vectors_small = np.random.rand(5, dim).astype('float32')
index_with_ids.add_with_ids(vectors_small, ids)

distances, indices = index_with_ids.search(query, k=3)
print(indices)  # 返回自定义 ID
```

## 2. Milvus

分布式向量数据库，适合生产环境大规模部署。

```bash
# Docker 部署（最简方式）
# docker-compose up -d

# 或使用轻量级 Milvus Lite
pip install pymilvus
```

```python
from pymilvus import MilvusClient

# 轻量模式（本地文件存储）
client = MilvusClient("milvus_demo.db")

# 创建集合
client.create_collection(
    collection_name="documents",
    dimension=768,
    metric_type="COSINE",
)

# 插入数据
data = [
    {"id": 1, "vector": [0.1] * 768, "text": "机器学习", "source": "book"},
    {"id": 2, "vector": [0.2] * 768, "text": "深度学习", "source": "paper"},
]
client.insert(collection_name="documents", data=data)

# 搜索
results = client.search(
    collection_name="documents",
    data=[[0.15] * 768],        # 查询向量
    limit=5,
    output_fields=["text", "source"],
)
for hits in results:
    for hit in hits:
        print(f"ID: {hit['id']}, Distance: {hit['distance']}, Text: {hit['entity']['text']}")

# 带过滤搜索
results = client.search(
    collection_name="documents",
    data=[[0.15] * 768],
    limit=5,
    filter='source == "book"',
    output_fields=["text"],
)
```

## 3. 向量数据库选型

| 特性 | ChromaDB | FAISS | Milvus | Pinecone |
|------|----------|-------|--------|----------|
| 类型 | 嵌入式 | 库 | 分布式 | 云服务 |
| 部署 | 零配置 | 零配置 | Docker/K8s | 托管 |
| 规模 | 百万级 | 十亿级 | 十亿级 | 十亿级 |
| 元数据 | ✅ | ❌（需自建） | ✅ | ✅ |
| 持久化 | ✅ | 手动 | ✅ | ✅ |
| 适用 | 原型/小项目 | 高性能检索 | 生产环境 | 免运维 |

### 选型建议

```
学习/原型开发    → ChromaDB（最简单）
高性能单机      → FAISS
生产环境大规模   → Milvus
免运维云服务    → Pinecone / Zilliz Cloud
```

## 练习

1. 用 FAISS 构建 10000 条向量的索引，对比 Flat 和 IVF 的搜索速度
2. 用 Milvus Lite 实现带元数据过滤的向量搜索
3. 将同一批数据分别存入 ChromaDB 和 FAISS，对比搜索结果
4. 测试不同索引类型（Flat、IVF、HNSW）的速度和精度

## 阶段总结

本阶段你已掌握：
- ✅ Embedding 原理与模型选择
- ✅ ChromaDB 向量存储与检索
- ✅ FAISS 高性能向量搜索
- ✅ 向量数据库选型

→ 下一阶段：[stage-08 RAG 检索增强生成](../stage-08-rag/)
