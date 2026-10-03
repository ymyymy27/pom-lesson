import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第4课：多模态 RAG（图文混合检索与生成）
==============================================================================

传统 RAG：纯文本检索 + 文本生成
多模态 RAG：图文/音频/视频混合检索 + 多模态生成

应用场景：
- 产品手册问答（包含图片/表格/流程图）
- 医学影像+病历联合检索
- 技术文档搜索（代码+截图+文字）
- 多媒体知识库

本课内容：
1. 多模态 RAG 架构
2. 多模态嵌入（CLIP/多模态Embedding）
3. 图文混合索引
4. 多模态检索策略
5. 多模态生成（图+文回答）
6. 完整多模态 RAG 流水线
==============================================================================
"""

import json
import numpy as np
from datetime import datetime

print("=" * 60)
print("第4课：多模态 RAG")
print("=" * 60)

# ============================================================================
# 1. 多模态 RAG 架构
# ============================================================================
print("\n--- 1. 架构 ---")
print("""
传统 RAG：
  问题(文本) → 文本嵌入 → 文本向量库 → 检索文本 → LLM → 文本回答

多模态 RAG：
  ┌──────────────────────────────────────────────────────┐
  │  索引阶段                                            │
  │  文档 → 解析（文字+图片+表格）                       │
  │       → 多模态嵌入（CLIP/多模态Embedding）           │
  │       → 向量数据库（ChromaDB/Milvus）                │
  └──────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────┐
  │  检索阶段                                            │
  │  用户问题 → 问题嵌入 → 向量检索                      │
  │          → 检索到：[文本块, 图片, 表格]               │
  └──────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────┐
  │  生成阶段                                            │
  │  问题 + 检索到的[文本+图片] → 多模态LLM → 回答       │
  └──────────────────────────────────────────────────────┘

三种多模态 RAG 策略：

策略1: 图片→文本→纯文本RAG
  图片 → VLM描述为文本 → 文本嵌入 → 文本向量库
  简单，但丢失视觉细节

策略2: 多模态嵌入RAG
  图片 → CLIP图像嵌入 → 多模态向量库
  文本 → CLIP文本嵌入 → 多模态向量库
  检索时：文本查询可以匹配到图片

策略3: 混合RAG（推荐）
  图片 → CLIP嵌入 + VLM文本描述 → 双重索引
  检索时：向量匹配 + 文本匹配 → 重排序
""")

# ============================================================================
# 2. 多模态嵌入
# ============================================================================
print("\n--- 2. 多模态嵌入 ---")
print("""
关键：文本和图像在同一个向量空间

CLIP 嵌入（最通用）：
```python
from transformers import CLIPProcessor, CLIPModel

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# 图像嵌入
inputs = processor(images=image, return_tensors="pt")
image_emb = model.get_image_features(**inputs)  # (1, 512)

# 文本嵌入
inputs = processor(text=["一只猫"], return_tensors="pt", padding=True)
text_emb = model.get_text_features(**inputs)    # (1, 512)

# 归一化后可以计算余弦相似度
image_emb = image_emb / image_emb.norm(dim=-1, keepdim=True)
text_emb = text_emb / text_emb.norm(dim=-1, keepdim=True)
similarity = (text_emb @ image_emb.T).item()
```

其他多模态嵌入模型：
┌─────────────────────┬──────────┬──────────────────────┐
│  模型                │  维度    │  特点                 │
├─────────────────────┼──────────┼──────────────────────┤
│  CLIP ViT-B/32      │  512     │  最通用，速度快       │
│  CLIP ViT-L/14      │  768     │  更准确              │
│  Chinese-CLIP       │  512/768 │  中文优化            │
│  SigLIP             │  768     │  Google，更好的对齐  │
│  Jina CLIP v2       │  1024    │  多语言，89种语言    │
│  Voyage Multimodal  │  1024    │  商用API，高质量     │
└─────────────────────┴──────────┴──────────────────────┘
""")

# 模拟多模态嵌入
def mock_multimodal_embed(content: str, modality: str = "text",
                          dim: int = 512) -> np.ndarray:
    """模拟多模态嵌入（实际用 CLIP 生成）"""
    np.random.seed(hash(f"{modality}:{content}") % 2**32)
    vec = np.random.randn(dim).astype(np.float32)
    return vec / np.linalg.norm(vec)

def cosine_sim(a, b):
    return float(np.dot(a, b))

# ============================================================================
# 3. 图文混合索引
# ============================================================================
print("\n--- 3. 图文混合索引 ---")
print("""
使用 ChromaDB 构建多模态向量库：

```python
import chromadb

client = chromadb.Client()
collection = client.create_collection(
    "multimodal_docs",
    metadata={"hnsw:space": "cosine"}
)

# 索引文本块
collection.add(
    ids=["text_001"],
    embeddings=[text_embedding.tolist()],
    documents=["这是一段关于猫的描述..."],
    metadatas=[{"type": "text", "source": "doc1.pdf", "page": 1}]
)

# 索引图片（用 CLIP 嵌入）
collection.add(
    ids=["img_001"],
    embeddings=[image_embedding.tolist()],
    documents=["[图片] 一只橘猫的照片"],  # VLM 生成的描述
    metadatas=[{"type": "image", "source": "doc1.pdf", "page": 2,
                "image_path": "images/cat.jpg"}]
)

# 索引表格（截图+描述）
collection.add(
    ids=["table_001"],
    embeddings=[table_embedding.tolist()],
    documents=["[表格] 2024年Q1销售数据，总计1200万"],
    metadatas=[{"type": "table", "source": "report.pdf", "page": 5}]
)
```
""")

# 构建模拟多模态索引
class MultimodalIndex:
    """模拟多模态向量索引"""

    def __init__(self):
        self.items = []

    def add(self, id: str, content: str, modality: str,
            metadata: dict = None):
        emb = mock_multimodal_embed(content, modality)
        self.items.append({
            "id": id, "content": content, "modality": modality,
            "embedding": emb, "metadata": metadata or {},
        })

    def search(self, query: str, top_k: int = 3) -> list:
        q_emb = mock_multimodal_embed(query, "text")
        results = []
        for item in self.items:
            score = cosine_sim(q_emb, item["embedding"])
            results.append({**item, "score": score})
        results.sort(key=lambda x: x["score"], reverse=True)
        for r in results:
            del r["embedding"]
        return results[:top_k]

index = MultimodalIndex()

# 添加多模态文档
docs = [
    ("text_01", "猫是一种常见的家养宠物，以独立性格著称", "text",
     {"source": "pets.pdf", "page": 1}),
    ("text_02", "Python是一种通用编程语言，简洁易学", "text",
     {"source": "coding.pdf", "page": 1}),
    ("img_01", "[图片] 一只橘色猫咪在阳台晒太阳", "image",
     {"source": "pets.pdf", "page": 2, "path": "cat_sunbathing.jpg"}),
    ("img_02", "[图片] Python代码编辑器的截图", "image",
     {"source": "coding.pdf", "page": 3, "path": "code_editor.png"}),
    ("table_01", "[表格] 2024年各品种猫的饲养数量统计", "table",
     {"source": "pets.pdf", "page": 5}),
    ("text_03", "深度学习使用神经网络处理复杂数据", "text",
     {"source": "ai.pdf", "page": 1}),
    ("img_03", "[图片] 神经网络架构图", "image",
     {"source": "ai.pdf", "page": 2, "path": "nn_arch.png"}),
    ("text_04", "猫咪的日常饮食需要蛋白质和脂肪的平衡", "text",
     {"source": "pets.pdf", "page": 3}),
]

for id, content, mod, meta in docs:
    index.add(id, content, mod, meta)
print(f"多模态索引: {len(index.items)} 个文档（文本+图片+表格）")

# ============================================================================
# 4. 多模态检索
# ============================================================================
print("\n--- 4. 多模态检索 ---")

queries = ["猫的饮食", "编程语言入门", "AI神经网络"]
for q in queries:
    results = index.search(q, top_k=3)
    print(f"\n  查询: \"{q}\"")
    for r in results:
        icon = {"text": "📄", "image": "🖼️", "table": "📊"}.get(r["modality"], "?")
        print(f"    {icon} {r['score']:.3f} [{r['modality']:5s}] {r['content'][:40]}...")

# ============================================================================
# 5. 多模态生成
# ============================================================================
print("\n\n--- 5. 多模态生成 ---")
print("""
检索到图文混合内容后，用多模态 LLM 生成回答：

```python
from langchain_core.messages import HumanMessage

def multimodal_rag_answer(question: str, retrieved_docs: list) -> str:
    # 构建多模态 prompt
    content = [{"type": "text", "text": f"根据以下资料回答问题：{question}\\n\\n"}]
    
    for doc in retrieved_docs:
        if doc["modality"] == "text":
            content.append({"type": "text", "text": f"[文本] {doc['content']}"})
        elif doc["modality"] == "image":
            # 加载图片并编码
            image_b64 = load_and_encode(doc["metadata"]["path"])
            content.append({"type": "text", "text": f"[图片描述] {doc['content']}"})
            content.append({"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{image_b64}"
            }})
        elif doc["modality"] == "table":
            content.append({"type": "text", "text": f"[表格] {doc['content']}"})
    
    message = HumanMessage(content=content)
    response = multimodal_llm.invoke([message])
    return response.content
```

关键：将检索到的图片直接传给多模态 LLM，
让模型看到原始图片而不只是文字描述。
""")

# 模拟 RAG 回答
def mock_rag_answer(question: str, docs: list) -> str:
    context_types = [d["modality"] for d in docs]
    return (f"根据检索到的 {len(docs)} 个资料"
            f"（{', '.join(context_types)}），"
            f"关于「{question}」的回答：这是一个综合了文本和视觉信息的回答。")

print("多模态 RAG 问答:")
for q in ["猫咪怎么喂养？", "什么是深度学习？"]:
    docs = index.search(q, top_k=3)
    answer = mock_rag_answer(q, docs)
    print(f"\n  Q: {q}")
    print(f"  检索: {[d['modality'] for d in docs]}")
    print(f"  A: {answer[:80]}...")

# ============================================================================
# 6. 完整流水线
# ============================================================================
print("\n--- 6. 完整流水线 ---")
print("""
生产级多模态 RAG 流水线：

  ┌─── 索引阶段 ─────────────────────────────────────┐
  │                                                    │
  │  PDF/文档 → Unstructured 解析                     │
  │    ├── 文本块 → CLIP文本嵌入 → ChromaDB            │
  │    ├── 图片   → CLIP图像嵌入 + VLM描述 → ChromaDB  │
  │    └── 表格   → 截图嵌入 + 文字提取 → ChromaDB     │
  │                                                    │
  └────────────────────────────────────────────────────┘

  ┌─── 查询阶段 ─────────────────────────────────────┐
  │                                                    │
  │  用户问题 → CLIP文本嵌入 → 向量检索               │
  │           → 重排序（Reranker）                     │
  │           → 筛选 top-K 文档                        │
  │                                                    │
  │  问题 + [文本+图片+表格] → GPT-4o → 多模态回答    │
  │                                                    │
  └────────────────────────────────────────────────────┘

推荐工具：
  文档解析: Unstructured / PyMuPDF / pdf2image
  嵌入模型: CLIP / Jina CLIP / Voyage
  向量库:   ChromaDB / Milvus / Pinecone
  重排序:   Cohere Reranker / bge-reranker
  生成:     GPT-4o / Qwen2-VL
""")

print("\n" + "=" * 60)
print("[完成] 第4课完成！你已经学会了：")
print("  [v] 多模态 RAG 三种策略")
print("  [v] CLIP 多模态嵌入")
print("  [v] 图文混合索引（ChromaDB）")
print("  [v] 多模态检索（以文搜图/搜表格）")
print("  [v] 多模态生成（图+文→回答）")
print("  [v] 生产级多模态 RAG 流水线")
print("=" * 60)
print("\n下一课：05_multimodal_agent.py - 多模态 Agent")
