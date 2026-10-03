import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：图像搜索与 CLIP 嵌入
==============================================================================

CLIP（Contrastive Language-Image Pre-training）是 OpenAI 发布的
文本-图像对齐模型，将文本和图像映射到同一个向量空间。

核心能力：
- 以文搜图：用文字描述搜索相似图片
- 以图搜图：用一张图片搜索相似图片
- 零样本分类：不需要训练就能分类
- 图文相似度：判断文字和图片的匹配程度

本课内容：
1. CLIP 原理
2. CLIP 嵌入生成
3. 以文搜图
4. 以图搜图
5. 零样本图像分类
6. 构建图像搜索引擎
==============================================================================
"""

import json
import numpy as np

print("=" * 60)
print("第5课：图像搜索与 CLIP 嵌入")
print("=" * 60)

# ============================================================================
# 1. CLIP 原理
# ============================================================================
print("\n--- 1. CLIP 原理 ---")
print("""
CLIP 的训练方式（对比学习）：

  用 4 亿对（图像, 文字描述）训练：
  - 匹配的图文对 → 向量距离拉近
  - 不匹配的图文对 → 向量距离推远

  训练后：
  ┌──────────┐                    ┌──────────┐
  │ 文本编码器│  "一只橘猫"  ──→  │  向量    │ ←── 距离近！
  └──────────┘                    │ [0.2,..] │
                                  └──────────┘
  ┌──────────┐                    ┌──────────┐
  │ 图像编码器│  🐱图片     ──→  │  向量    │ ←── 距离近！
  └──────────┘                    │ [0.2,..] │
                                  └──────────┘

  文本和图像在同一个向量空间中！
  → 可以用文本向量搜索图像向量
  → 可以用图像向量搜索图像向量
  → 可以计算任意文本-图像的相似度

CLIP 模型版本：
┌─────────────────┬──────────┬────────────────────┐
│  模型            │  维度    │  说明               │
├─────────────────┼──────────┼────────────────────┤
│  ViT-B/32       │  512     │  基础版，速度快      │
│  ViT-B/16       │  512     │  更精确              │
│  ViT-L/14       │  768     │  大模型，最准确      │
│  ViT-L/14@336px │  768     │  高分辨率            │
└─────────────────┴──────────┴────────────────────┘
""")

# ============================================================================
# 2. CLIP 嵌入生成
# ============================================================================
print("\n--- 2. CLIP 嵌入生成 ---")
print("""
使用 HuggingFace transformers 加载 CLIP：

```python
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

# 加载模型
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# 图像嵌入
image = Image.open("photo.jpg")
inputs = processor(images=image, return_tensors="pt")
image_embedding = model.get_image_features(**inputs)
# image_embedding.shape = (1, 512)

# 文本嵌入
inputs = processor(text=["一只猫", "一条狗"], return_tensors="pt", padding=True)
text_embeddings = model.get_text_features(**inputs)
# text_embeddings.shape = (2, 512)

# 归一化
image_embedding = image_embedding / image_embedding.norm(dim=-1, keepdim=True)
text_embeddings = text_embeddings / text_embeddings.norm(dim=-1, keepdim=True)
```

也可以用 OpenAI API 获取嵌入（但目前不支持图像嵌入，仅文本）。
CLIP 嵌入需要本地运行。
""")

# 模拟 CLIP 嵌入（用于演示搜索逻辑）
def mock_clip_embed(text_or_id: str, dim: int = 512) -> np.ndarray:
    """模拟 CLIP 嵌入（实际用 transformers 生成）"""
    np.random.seed(hash(text_or_id) % 2**32)
    vec = np.random.randn(dim).astype(np.float32)
    return vec / np.linalg.norm(vec)  # L2 归一化

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))

# ============================================================================
# 3. 以文搜图
# ============================================================================
print("\n--- 3. 以文搜图 ---")
print("""
用文字描述搜索匹配的图片：
  "日落时的海滩" → 搜索图片库 → 返回最相似的图片

流程：
  1. 预先计算所有图片的 CLIP 嵌入 → 存入向量数据库
  2. 用户输入文字 → 计算文字的 CLIP 嵌入
  3. 在向量数据库中搜索最近邻 → 返回相似图片
""")

# 模拟图片库
image_library = [
    {"id": "img_001", "description": "日落时的海滩，金色阳光"},
    {"id": "img_002", "description": "城市夜景，高楼大厦灯火通明"},
    {"id": "img_003", "description": "雪山风景，蓝天白云"},
    {"id": "img_004", "description": "一只橘猫在沙发上睡觉"},
    {"id": "img_005", "description": "办公室里的程序员在写代码"},
    {"id": "img_006", "description": "早餐桌上的咖啡和面包"},
    {"id": "img_007", "description": "秋天的枫叶，红黄相间"},
    {"id": "img_008", "description": "小狗在草地上奔跑"},
    {"id": "img_009", "description": "古镇水乡，小桥流水"},
    {"id": "img_010", "description": "演唱会现场，人群欢呼"},
]

# 预计算图片嵌入
for img in image_library:
    img["embedding"] = mock_clip_embed(img["description"])

def text_search_images(query: str, top_k: int = 3) -> list:
    """以文搜图"""
    query_emb = mock_clip_embed(query)
    results = []
    for img in image_library:
        sim = cosine_similarity(query_emb, img["embedding"])
        results.append({"id": img["id"], "description": img["description"], "score": sim})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

# 测试
queries = ["海边的日落", "可爱的宠物", "城市风光"]
for q in queries:
    results = text_search_images(q)
    print(f"\n  搜索: \"{q}\"")
    for r in results:
        print(f"    {r['score']:.4f} | {r['id']} | {r['description'][:30]}...")

# ============================================================================
# 4. 以图搜图
# ============================================================================
print("\n\n--- 4. 以图搜图 ---")
print("""
用一张图片搜索相似图片：
  上传图片 → CLIP 图像嵌入 → 搜索最近邻 → 返回相似图片

```python
# 计算查询图片的嵌入
query_image = Image.open("query.jpg")
inputs = processor(images=query_image, return_tensors="pt")
query_emb = model.get_image_features(**inputs)
query_emb = query_emb / query_emb.norm(dim=-1, keepdim=True)

# 与图片库中所有嵌入计算相似度
similarities = query_emb @ image_embeddings.T  # 余弦相似度
top_indices = similarities.argsort(descending=True)[:5]
```
""")

def image_search_images(query_id: str, top_k: int = 3) -> list:
    """以图搜图"""
    query_img = next((i for i in image_library if i["id"] == query_id), None)
    if not query_img:
        return []
    results = []
    for img in image_library:
        if img["id"] == query_id:
            continue
        sim = cosine_similarity(query_img["embedding"], img["embedding"])
        results.append({"id": img["id"], "description": img["description"], "score": sim})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

print("以图搜图（用 img_001 海滩图搜索）:")
results = image_search_images("img_001")
for r in results:
    print(f"  {r['score']:.4f} | {r['id']} | {r['description'][:30]}...")

# ============================================================================
# 5. 零样本图像分类
# ============================================================================
print("\n--- 5. 零样本分类 ---")
print("""
不需要训练，直接用 CLIP 分类！

原理：
  图片嵌入 vs 每个类别的文本嵌入 → 最相似的类别

```python
# 定义类别
categories = ["猫", "狗", "鸟", "鱼", "兔子"]
text_inputs = processor(
    text=[f"a photo of a {c}" for c in categories],
    return_tensors="pt", padding=True
)
text_embs = model.get_text_features(**text_inputs)

# 计算相似度
image_emb = model.get_image_features(...)
similarities = (image_emb @ text_embs.T).softmax(dim=-1)
predicted = categories[similarities.argmax()]
```
""")

def zero_shot_classify(image_desc: str, categories: list) -> list:
    """零样本分类"""
    img_emb = mock_clip_embed(image_desc)
    results = []
    for cat in categories:
        cat_emb = mock_clip_embed(f"a photo of {cat}")
        sim = cosine_similarity(img_emb, cat_emb)
        results.append({"category": cat, "score": sim})
    results.sort(key=lambda x: x["score"], reverse=True)
    # softmax 归一化
    scores = np.array([r["score"] for r in results])
    exp_scores = np.exp(scores - scores.max())
    probs = exp_scores / exp_scores.sum()
    for i, r in enumerate(results):
        r["probability"] = float(probs[i])
    return results

print("零样本分类演示:")
categories = ["猫", "狗", "城市", "自然风景", "食物", "人物"]
for desc in ["橘猫在沙发", "城市夜景高楼"]:
    results = zero_shot_classify(desc, categories)
    print(f"\n  图片: \"{desc}\"")
    for r in results[:3]:
        print(f"    {r['category']}: {r['probability']:.1%}")

# ============================================================================
# 6. 构建图像搜索引擎
# ============================================================================
print("\n--- 6. 图像搜索引擎架构 ---")
print("""
生产环境的图像搜索引擎：

  ┌────────────┐    ┌──────────┐    ┌──────────────┐
  │ 图片上传   │ →  │ CLIP     │ →  │ 向量数据库   │
  │            │    │ 编码器   │    │ (Chroma/     │
  └────────────┘    └──────────┘    │  Milvus/     │
                                     │  Pinecone)   │
  ┌────────────┐    ┌──────────┐    └──────┬───────┘
  │ 搜索请求   │ →  │ CLIP     │ →  相似度搜索 → 结果
  │ 文字/图片  │    │ 编码器   │          │
  └────────────┘    └──────────┘          ↓
                                    Top-K 最近邻

```python
# 使用 ChromaDB 构建图像搜索
import chromadb

client = chromadb.Client()
collection = client.create_collection(
    "image_search",
    metadata={"hnsw:space": "cosine"}
)

# 索引图片
for img_path in image_paths:
    embedding = clip_encode_image(img_path)
    collection.add(
        embeddings=[embedding.tolist()],
        ids=[img_path],
        metadatas=[{"path": img_path}]
    )

# 以文搜图
query_emb = clip_encode_text("日落海滩")
results = collection.query(
    query_embeddings=[query_emb.tolist()],
    n_results=5
)
```
""")

print("\n" + "=" * 60)
print("[完成] 第5课完成！你已经学会了：")
print("  [v] CLIP 原理（文本-图像对齐）")
print("  [v] CLIP 嵌入生成")
print("  [v] 以文搜图")
print("  [v] 以图搜图")
print("  [v] 零样本图像分类")
print("  [v] 图像搜索引擎架构")
print("=" * 60)
print("\n下一课：06_video_understanding.py - 视频理解")
