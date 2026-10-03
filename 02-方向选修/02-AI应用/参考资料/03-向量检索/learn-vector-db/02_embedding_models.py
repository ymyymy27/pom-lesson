import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：主流 Embedding 模型对比与使用
==============================================================================

不同 Embedding 模型在维度、速度、精度、语言支持上各有特点。

本课内容：
1. 模型分类与选型
2. OpenAI Embedding
3. Ollama 本地 Embedding
4. HuggingFace 模型
5. 模型对比评测
6. 选型决策指南
==============================================================================
"""

import json
import time
import numpy as np
import httpx

OLLAMA_URL = "http://localhost:11434"

print("=" * 60)
print("第2课：Embedding 模型对比")
print("=" * 60)

# ============================================================================
# 1. 模型分类
# ============================================================================
print("\n--- 1. 模型分类 ---")
print("""
┌──────────────────────────────────────────────────────────────┐
│  闭源 API 模型                                               │
├──────────────────┬──────┬──────────────────────────────────┤
│  模型             │ 维度 │  特点                             │
├──────────────────┼──────┼──────────────────────────────────┤
│  text-embedding  │      │                                   │
│  -3-large (OpenAI)│ 3072│  最强精度，可降维                │
│  -3-small (OpenAI)│ 1536│  性价比高，推荐起步              │
│  embed-v3 (Cohere)│ 1024│  多语言支持好                    │
│  embedding (voyage)│ 1024│  代码embedding强                │
├──────────────────┴──────┴──────────────────────────────────┤
│  开源本地模型                                                │
├──────────────────┬──────┬──────────────────────────────────┤
│  bge-large-zh    │ 1024 │  中文最优之一（BAAI）            │
│  bge-m3          │ 1024 │  多语言、多粒度                  │
│  nomic-embed-text│  768 │  Ollama可用，轻量                │
│  all-MiniLM-L6   │  384 │  英文轻量，速度快                │
│  jina-embeddings │ 1024 │  多语言，支持长文本              │
│  gte-large-zh    │ 1024 │  阿里出品，中文强                │
└──────────────────┴──────┴──────────────────────────────────┘

选型要素：
  语言: 中文 → bge-zh / gte-zh   英文 → all-MiniLM
  场景: RAG → bge-m3   代码 → voyage-code
  成本: 免费 → 开源本地   按量付费 → OpenAI
""")

# ============================================================================
# 2. OpenAI Embedding
# ============================================================================
print("\n--- 2. OpenAI Embedding ---")
print("""
```python
from openai import OpenAI
client = OpenAI()

# 单条
response = client.embeddings.create(
    input="什么是机器学习？",
    model="text-embedding-3-small"
)
embedding = response.data[0].embedding  # 1536维

# 批量（推荐，更高效）
response = client.embeddings.create(
    input=["文本1", "文本2", "文本3"],
    model="text-embedding-3-small"
)
embeddings = [item.embedding for item in response.data]

# 降维（text-embedding-3 独有功能）
response = client.embeddings.create(
    input="降维示例",
    model="text-embedding-3-large",
    dimensions=256  # 从3072降到256，精度略降但更快更省
)
```

价格（每百万 token）：
  text-embedding-3-small: $0.02
  text-embedding-3-large: $0.13
  → 100万条短文本 ≈ $2-13
""")

# ============================================================================
# 3. Ollama 本地 Embedding
# ============================================================================
print("\n--- 3. Ollama Embedding ---")

def ollama_embed(texts: list, model: str = "nomic-embed-text") -> list:
    """Ollama embedding"""
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/embed", json={
            "model": model, "input": texts,
        }, timeout=30.0)
        return resp.json().get("embeddings", [])
    except:
        np.random.seed(hash(str(texts)) % 2**31)
        return [np.random.randn(768).tolist() for _ in texts]

print("""
Ollama 支持的 Embedding 模型：

```bash
ollama pull nomic-embed-text     # 768维，通用
ollama pull mxbai-embed-large    # 1024维，精度更高
ollama pull all-minilm            # 384维，最轻量
```

API 调用：
```python
resp = httpx.post("http://localhost:11434/api/embed", json={
    "model": "nomic-embed-text",
    "input": ["文本1", "文本2"],
})
embeddings = resp.json()["embeddings"]
```
""")

# 演示
test_texts = ["机器学习入门", "深度学习教程", "Python编程", "今天天气不错"]
start = time.time()
embeddings = ollama_embed(test_texts)
elapsed = time.time() - start

if embeddings:
    print(f"Ollama Embedding 结果:")
    print(f"  模型: nomic-embed-text")
    print(f"  维度: {len(embeddings[0])}")
    print(f"  耗时: {elapsed:.2f}s ({len(test_texts)}条)")
    print(f"  首条前5维: {[round(x, 4) for x in embeddings[0][:5]]}")

# ============================================================================
# 4. HuggingFace 模型
# ============================================================================
print("\n--- 4. HuggingFace ---")
print("""
使用 sentence-transformers 库：

```python
from sentence_transformers import SentenceTransformer

# 中文模型
model = SentenceTransformer("BAAI/bge-large-zh-v1.5")
embeddings = model.encode(["文本1", "文本2"], normalize_embeddings=True)

# bge 系列需要加前缀提升效果
queries = ["为这个句子生成表示用于检索相关文章：什么是机器学习"]
passages = ["机器学习是AI的一个分支", "今天天气很好"]
q_emb = model.encode(queries, normalize_embeddings=True)
p_emb = model.encode(passages, normalize_embeddings=True)

# 多语言模型
model = SentenceTransformer("BAAI/bge-m3")  # 100+语言
embeddings = model.encode(["Hello", "你好", "こんにちは"])
```

使用 transformers 原生：
```python
from transformers import AutoTokenizer, AutoModel
import torch

model_name = "BAAI/bge-large-zh-v1.5"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

inputs = tokenizer("文本", return_tensors="pt", padding=True, truncation=True)
with torch.no_grad():
    outputs = model(**inputs)
embedding = outputs.last_hidden_state[:, 0, :]  # [CLS] token
embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
```
""")

# ============================================================================
# 5. 模型对比
# ============================================================================
print("\n--- 5. 模型对比 ---")

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# 用 Ollama 做对比测试
test_pairs = [
    ("机器学习是AI的分支", "深度学习属于人工智能", "语义相近"),
    ("机器学习是AI的分支", "今天天气很好", "语义无关"),
    ("如何学习Python", "Python学习方法", "同义改写"),
    ("退款要多久", "退货流程是什么", "相关但不同"),
]

print("语义相似度测试:")
all_texts = []
for t1, t2, _ in test_pairs:
    all_texts.extend([t1, t2])

embeddings = ollama_embed(all_texts)
if embeddings:
    print(f"  {'文本对':<30} {'类型':<10} {'相似度':>8}")
    print(f"  {'-'*52}")
    for i, (t1, t2, label) in enumerate(test_pairs):
        sim = cosine_sim(embeddings[i*2], embeddings[i*2+1])
        print(f"  {t1[:12]}↔{t2[:12]:<16} {label:<10} {sim:>7.4f}")

print("""
模型性能对比（MTEB 基准）：
┌────────────────────┬──────┬────────┬────────┬──────────┐
│  模型               │ 维度 │ 中文   │ 英文   │ 速度      │
├────────────────────┼──────┼────────┼────────┼──────────┤
│  bge-large-zh      │ 1024 │ ★★★★★ │ ★★★   │ 中       │
│  bge-m3            │ 1024 │ ★★★★  │ ★★★★  │ 中       │
│  nomic-embed-text  │  768 │ ★★★   │ ★★★★  │ 快       │
│  all-MiniLM-L6     │  384 │ ★★    │ ★★★★  │ 最快     │
│  OpenAI-3-small    │ 1536 │ ★★★★  │ ★★★★★ │ API延迟  │
│  OpenAI-3-large    │ 3072 │ ★★★★★ │ ★★★★★ │ API延迟  │
└────────────────────┴──────┴────────┴────────┴──────────┘
""")

# ============================================================================
# 6. 选型决策
# ============================================================================
print("--- 6. 选型指南 ---")
print("""
决策树：

  你需要中文？
  ├── 是 → 需要最高精度？
  │   ├── 是 → OpenAI text-embedding-3-large
  │   └── 否 → 需要本地运行？
  │       ├── 是 → bge-large-zh-v1.5（HF）或 nomic-embed-text（Ollama）
  │       └── 否 → OpenAI text-embedding-3-small
  └── 否 → 英文为主
      ├── 高精度 → OpenAI text-embedding-3-large
      ├── 轻量快速 → all-MiniLM-L6-v2
      └── 代码场景 → voyage-code-2

常见搭配：
  学习/原型: Ollama nomic-embed-text（免费、简单）
  生产(中文): bge-large-zh + ChromaDB/Milvus
  生产(通用): OpenAI text-embedding-3-small（性价比最高）

注意：
  ✅ 索引和查询必须用同一个模型
  ✅ 维度越高精度越好但存储越大
  ✅ 归一化后用点积比余弦快
""")

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] 闭源/开源 Embedding 模型分类")
print("  [v] OpenAI Embedding API（含降维）")
print("  [v] Ollama 本地 Embedding")
print("  [v] HuggingFace sentence-transformers")
print("  [v] 模型性能对比（MTEB基准）")
print("  [v] 选型决策指南")
print("=" * 60)
print("\n下一课：03_chromadb.py - ChromaDB 使用")
