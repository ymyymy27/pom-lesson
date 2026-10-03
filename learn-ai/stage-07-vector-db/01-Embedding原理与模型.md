# Embedding 原理与模型

## 学习目标

- 理解文本 Embedding 的原理
- 掌握主流 Embedding 模型的选型和使用
- 学会计算和应用语义相似度

## 1. 什么是 Embedding

Embedding 是将文本（或其他数据）映射为固定长度的稠密向量，使语义相近的文本在向量空间中距离也近。

```
"机器学习是 AI 的分支" → [0.12, -0.34, 0.56, ..., 0.78]  (维度: 768 或 1024)
"深度学习属于人工智能" → [0.11, -0.32, 0.55, ..., 0.80]  (相似 → 向量距离近)
"今天天气很好"        → [0.89, 0.23, -0.67, ..., 0.12]  (不相关 → 向量距离远)
```

### 应用场景

- **语义搜索**：用向量相似度替代关键词匹配
- **RAG**：检索相关文档片段供 LLM 回答
- **推荐系统**：基于内容相似度推荐
- **聚类/分类**：将文本按语义分组
- **去重**：发现语义相似的重复内容

## 2. 主流 Embedding 模型

### 闭源模型

| 模型 | 维度 | 特点 |
|------|------|------|
| OpenAI text-embedding-3-large | 3072 | 性能强，按量付费 |
| OpenAI text-embedding-3-small | 1536 | 性价比高 |
| Cohere embed-v3 | 1024 | 多语言支持好 |

### 开源模型

| 模型 | 维度 | 特点 |
|------|------|------|
| BAAI/bge-large-zh-v1.5 | 1024 | 中文最优之一 |
| BAAI/bge-m3 | 1024 | 多语言、多粒度 |
| nomic-embed-text | 768 | Ollama 可用，轻量 |
| sentence-transformers/all-MiniLM-L6-v2 | 384 | 英文轻量级 |
| jinaai/jina-embeddings-v3 | 1024 | 多语言，长文本 |

## 3. 使用 OpenAI Embedding

```python
from openai import OpenAI
import numpy as np

client = OpenAI()

def get_embedding(text: str, model="text-embedding-3-small") -> list[float]:
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding

# 单条文本
emb = get_embedding("什么是机器学习？")
print(f"维度: {len(emb)}")  # 1536

# 批量处理
texts = ["机器学习", "深度学习", "烹饪技巧"]
response = client.embeddings.create(input=texts, model="text-embedding-3-small")
embeddings = [item.embedding for item in response.data]
```

## 4. 使用开源 Embedding（HuggingFace）

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# 加载模型
model = SentenceTransformer("BAAI/bge-large-zh-v1.5")

# 编码文本
sentences = [
    "机器学习是人工智能的一个重要分支",
    "深度学习是机器学习的子集",
    "今天的晚餐吃什么好呢",
    "Python 是最流行的编程语言之一",
]

embeddings = model.encode(sentences, normalize_embeddings=True)
print(f"形状: {embeddings.shape}")  # (4, 1024)
```

## 5. 相似度计算

```python
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 余弦相似度
sim_matrix = cosine_similarity(embeddings)
print("相似度矩阵:")
for i, s1 in enumerate(sentences):
    for j, s2 in enumerate(sentences):
        if i < j:
            print(f"  '{s1[:15]}...' vs '{s2[:15]}...': {sim_matrix[i][j]:.4f}")

# 手动计算余弦相似度
def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# 欧氏距离
def euclidean_dist(a, b):
    return np.linalg.norm(a - b)

# 点积（适用于归一化向量）
def dot_product(a, b):
    return np.dot(a, b)
```

## 6. 使用 Ollama Embedding

```python
import requests

def ollama_embed(texts: list[str], model="nomic-embed-text") -> list[list[float]]:
    response = requests.post("http://localhost:11434/api/embed", json={
        "model": model,
        "input": texts,
    })
    return response.json()["embeddings"]

embeddings = ollama_embed(["你好世界", "Hello World"])
print(f"维度: {len(embeddings[0])}")
```

## 7. 文本分块策略

Embedding 模型有长度限制，需要对长文本进行分块。

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 递归字符分割（最常用）
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,        # 每块最大字符数
    chunk_overlap=50,      # 块之间的重叠
    separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
)

text = "很长的文档内容..."
chunks = splitter.split_text(text)

# 从文件分割
from langchain_community.document_loaders import TextLoader
loader = TextLoader("document.txt", encoding="utf-8")
docs = loader.load()
chunks = splitter.split_documents(docs)

# 每个 chunk 都可以独立 embedding
chunk_embeddings = model.encode([c.page_content for c in chunks])
```

### 分块最佳实践

```
chunk_size 选择：
- 太小（<100）：语义不完整
- 太大（>1000）：检索精度下降
- 推荐：300-800 字符

chunk_overlap：
- 通常为 chunk_size 的 10-20%
- 确保跨块信息不丢失

分割策略：
- 优先按段落分割
- 其次按句子
- 保持语义完整性
```

## 练习

1. 用 OpenAI 或开源模型获取 10 个句子的 Embedding，计算两两相似度
2. 实现一个简单的语义搜索：输入查询，返回最相似的 3 个句子
3. 对一篇长文档进行分块，并对比不同 chunk_size 的效果
4. 比较 OpenAI 和开源 Embedding 模型在中文相似度任务上的表现

## 下一节

→ [02-ChromaDB入门](02-ChromaDB入门.md)
