import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第1课：Embedding 原理与相似度计算
==============================================================================

Embedding = 把文本变成数字向量
语义相近的文本 → 向量距离近
语义不同的文本 → 向量距离远

这是 RAG、语义搜索、推荐系统的基础。

本课内容：
1. 什么是 Embedding
2. 向量空间直觉
3. 距离度量方法
4. 相似度计算实践
5. Embedding 的应用场景
6. Ollama Embedding 使用
==============================================================================
"""

import numpy as np
import httpx
import json

OLLAMA_URL = "http://localhost:11434"

print("=" * 60)
print("第1课：Embedding 原理")
print("=" * 60)

# ============================================================================
# 1. 什么是 Embedding
# ============================================================================
print("\n--- 1. 什么是 Embedding ---")
print("""
Embedding = 文本 → 固定长度的浮点数向量

  "机器学习是AI的分支" → [0.12, -0.34, 0.56, ..., 0.78]  (768维)
  "深度学习属于人工智能" → [0.11, -0.32, 0.55, ..., 0.80]  (语义近→距离近)
  "今天天气很好"        → [0.89, 0.23, -0.67, ..., 0.12]  (语义远→距离远)

关键特性：
  ✅ 固定维度（不管文本长短，输出都是同样维度）
  ✅ 稠密（每个维度都有值，不像 one-hot 那样稀疏）
  ✅ 语义编码（相近含义→相近向量）
  ✅ 可计算（可以做加减乘除、距离计算）

经典例子：
  king - man + woman ≈ queen （词向量算术）

维度选择：
  384维:  轻量级（all-MiniLM-L6-v2）
  768维:  标准（nomic-embed-text, bge-base）
  1024维: 高精度（bge-large）
  1536维: OpenAI text-embedding-3-small
  3072维: OpenAI text-embedding-3-large
""")

# ============================================================================
# 2. 向量空间直觉
# ============================================================================
print("\n--- 2. 向量空间 ---")

# 用 2D 向量演示
vectors_2d = {
    "猫":   np.array([0.9, 0.1]),
    "狗":   np.array([0.8, 0.15]),
    "鱼":   np.array([0.7, -0.3]),
    "汽车": np.array([-0.5, 0.8]),
    "飞机": np.array([-0.4, 0.9]),
    "苹果": np.array([0.2, -0.7]),
}

print("2D 向量空间演示（简化）:")
print(f"  {'词':<6} {'x':>6} {'y':>6}")
print(f"  {'-'*20}")
for word, vec in vectors_2d.items():
    print(f"  {word:<6} {vec[0]:>6.2f} {vec[1]:>6.2f}")

print("""
  观察：
  • 猫和狗 靠近（都是宠物）
  • 汽车和飞机 靠近（都是交通工具）
  • 猫和汽车 距离远（语义不相关）

  真实 Embedding 是 768~3072 维，无法可视化，
  但距离关系是一样的。
""")

# ============================================================================
# 3. 距离度量
# ============================================================================
print("\n--- 3. 距离度量 ---")

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """余弦相似度：衡量方向相似性，[-1, 1]"""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """欧氏距离：衡量绝对距离，[0, ∞)"""
    return float(np.linalg.norm(a - b))

def dot_product(a: np.ndarray, b: np.ndarray) -> float:
    """点积：向量归一化后等价于余弦相似度"""
    return float(np.dot(a, b))

def manhattan_distance(a: np.ndarray, b: np.ndarray) -> float:
    """曼哈顿距离：L1距离"""
    return float(np.sum(np.abs(a - b)))

print("""
┌──────────────────┬──────────────┬──────────────────────────────┐
│  度量             │  范围         │  说明                         │
├──────────────────┼──────────────┼──────────────────────────────┤
│  余弦相似度      │  [-1, 1]     │  最常用！衡量方向相似性      │
│  (Cosine)        │  1=完全相同  │  不受向量长度影响            │
├──────────────────┼──────────────┼──────────────────────────────┤
│  欧氏距离        │  [0, ∞)      │  衡量绝对距离               │
│  (L2/Euclidean)  │  0=完全相同  │  受向量长度影响             │
├──────────────────┼──────────────┼──────────────────────────────┤
│  点积            │  (-∞, ∞)     │  归一化后=余弦相似度        │
│  (Dot Product)   │              │  计算最快                    │
├──────────────────┼──────────────┼──────────────────────────────┤
│  曼哈顿距离      │  [0, ∞)      │  L1距离，各维差值之和       │
│  (Manhattan/L1)  │  0=完全相同  │  对异常值不敏感             │
└──────────────────┴──────────────┴──────────────────────────────┘

推荐：
  语义搜索 → 余弦相似度（cosine）
  向量归一化后 → 点积（最快）
""")

# 距离计算演示
pairs = [("猫", "狗"), ("猫", "汽车"), ("汽车", "飞机"), ("猫", "鱼")]
print("距离计算演示:")
print(f"  {'词对':<12} {'余弦相似':>8} {'欧氏距离':>8} {'点积':>8}")
print(f"  {'-'*40}")
for w1, w2 in pairs:
    v1, v2 = vectors_2d[w1], vectors_2d[w2]
    cos = cosine_similarity(v1, v2)
    euc = euclidean_distance(v1, v2)
    dot = dot_product(v1, v2)
    print(f"  {w1+'-'+w2:<12} {cos:>7.4f} {euc:>8.4f} {dot:>7.4f}")

# ============================================================================
# 4. 相似度矩阵
# ============================================================================
print("\n--- 4. 相似度矩阵 ---")

words = list(vectors_2d.keys())
n = len(words)
sim_matrix = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        sim_matrix[i][j] = cosine_similarity(vectors_2d[words[i]], vectors_2d[words[j]])

print("余弦相似度矩阵:")
header = "      " + "".join(f"{w:>6}" for w in words)
print(header)
for i, w in enumerate(words):
    row = f"  {w:<4}" + "".join(f"{sim_matrix[i][j]:>6.2f}" for j in range(n))
    print(row)

# ============================================================================
# 5. 应用场景
# ============================================================================
print("\n--- 5. 应用场景 ---")
print("""
┌──────────────────┬──────────────────────────────────────┐
│  场景             │  怎么用 Embedding                     │
├──────────────────┼──────────────────────────────────────┤
│  语义搜索        │  query → embedding → 找最近的文档   │
│  RAG             │  检索相关段落 → 送给 LLM 回答       │
│  文本分类        │  文本 → embedding → 分类器          │
│  聚类分析        │  所有文本 → embedding → K-means     │
│  去重检测        │  相似度 > 阈值 → 判定为重复         │
│  推荐系统        │  用户兴趣embedding ↔ 商品embedding  │
│  异常检测        │  离群点 = 与所有向量距离都远的点    │
└──────────────────┴──────────────────────────────────────┘
""")

# ============================================================================
# 6. Ollama Embedding
# ============================================================================
print("\n--- 6. Ollama Embedding ---")

def ollama_embed(texts: list) -> list:
    """使用 Ollama 获取 Embedding"""
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/embed", json={
            "model": "nomic-embed-text",
            "input": texts,
        }, timeout=30.0)
        return resp.json().get("embeddings", [])
    except:
        # 模拟 embedding
        np.random.seed(hash(str(texts)) % 2**31)
        return [np.random.randn(768).tolist() for _ in texts]

# 真实 embedding 演示
sentences = [
    "机器学习是人工智能的一个重要分支",
    "深度学习使用多层神经网络处理数据",
    "今天天气非常好，适合出去散步",
    "Python 是最流行的编程语言之一",
    "神经网络是深度学习的基础技术",
]

print("Embedding 演示:")
embeddings = ollama_embed(sentences)
if embeddings:
    dim = len(embeddings[0])
    print(f"  维度: {dim}")
    print(f"  句子数: {len(embeddings)}")

    # 计算相似度
    emb_array = np.array(embeddings)
    print(f"\n  语义相似度（余弦）:")
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            sim = cosine_similarity(emb_array[i], emb_array[j])
            marker = "★" if sim > 0.7 else " "
            print(f"  {marker} \"{sentences[i][:15]}...\" ↔ \"{sentences[j][:15]}...\": {sim:.4f}")

    # 语义搜索演示
    print(f"\n  语义搜索演示:")
    query = "什么是深度学习？"
    query_emb = ollama_embed([query])
    if query_emb:
        query_vec = np.array(query_emb[0])
        scores = [(i, cosine_similarity(query_vec, emb_array[i])) for i in range(len(sentences))]
        scores.sort(key=lambda x: x[1], reverse=True)
        print(f"  查询: \"{query}\"")
        for idx, score in scores:
            print(f"    [{score:.4f}] {sentences[idx]}")

print("\n" + "=" * 60)
print("[完成] 第1课完成！你已经学会了：")
print("  [v] Embedding 的概念和特性")
print("  [v] 向量空间直觉（语义近→距离近）")
print("  [v] 四种距离度量（余弦/欧氏/点积/曼哈顿）")
print("  [v] 相似度矩阵计算")
print("  [v] Embedding 的六大应用场景")
print("  [v] Ollama Embedding 使用与语义搜索")
print("=" * 60)
print("\n下一课：02_embedding_models.py - Embedding 模型对比")
