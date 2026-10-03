import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：视觉-语言模型（图文理解 / VQA / 文档分析）
==============================================================================

视觉-语言模型（VLM）= 同时理解图像和文本

核心能力：
- 看图说话：描述图像内容
- 视觉问答：针对图像回答问题
- 文档理解：理解图表/PDF/幻灯片
- OCR+理解：不仅识别文字，还理解含义

本课内容：
1. VLM 架构原理
2. GPT-4o 视觉能力
3. 开源 VLM（Qwen2-VL/LLaVA）
4. 文档与图表理解
5. LangChain 多模态消息
6. 多图对比分析
==============================================================================
"""

import json
import base64
from io import BytesIO

print("=" * 60)
print("第2课：视觉-语言模型")
print("=" * 60)

# ============================================================================
# 1. VLM 架构
# ============================================================================
print("\n--- 1. VLM 架构 ---")
print("""
视觉-语言模型的三种架构：

1. 编码器-解码器（BLIP-2 / InstructBLIP）
   图像 → ViT编码 → Q-Former桥接 → LLM解码 → 文本
   优点：训练成本低（只训练桥接层）
   缺点：图像信息可能损失

2. 视觉token直接注入（LLaVA / Qwen-VL）
   图像 → ViT编码 → 线性投影为token → 与文本token拼接 → LLM
   优点：信息保留完整
   缺点：token数量大，推理慢

3. 原生多模态（GPT-4o）
   图像+文本 → 统一tokenizer → 同一个Transformer
   优点：最强理解力
   缺点：训练成本极高

LLaVA 的具体流程：
  ┌────────┐    ┌──────────┐    ┌───────────────────┐
  │ 图像   │ →  │ CLIP ViT │ →  │ 576个视觉token    │
  │ 336px  │    │ 编码器   │    │ (24×24 patches)   │
  └────────┘    └──────────┘    └────────┬──────────┘
                                         │ 拼接
  ┌────────┐    ┌──────────┐    ┌────────▼──────────┐
  │ 文本   │ →  │ Tokenizer│ →  │ 文本token         │
  │ Prompt │    │          │    │                    │
  └────────┘    └──────────┘    └────────┬──────────┘
                                         │
                                  ┌──────▼──────┐
                                  │  LLM (如    │
                                  │  Vicuna/    │
                                  │  Qwen)      │
                                  └──────┬──────┘
                                         │
                                    回答文本
""")

# ============================================================================
# 2. GPT-4o 视觉能力
# ============================================================================
print("\n--- 2. GPT-4o 视觉 ---")
print("""
GPT-4o 的视觉能力是目前最强的。

```python
from openai import OpenAI
client = OpenAI()

# 方式1: URL 图片
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "描述这张图片"},
            {"type": "image_url", "image_url": {
                "url": "https://example.com/photo.jpg",
                "detail": "high"  # low/high/auto
            }}
        ]
    }]
)

# 方式2: Base64 图片
with open("photo.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "这张图片里有什么？"},
            {"type": "image_url", "image_url": {
                "url": f"data:image/jpeg;base64,{b64}"
            }}
        ]
    }]
)

# 方式3: 多图对比
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "比较这两张图片的异同"},
            {"type": "image_url", "image_url": {"url": url1}},
            {"type": "image_url", "image_url": {"url": url2}},
        ]
    }]
)
```

detail 参数：
  low:  512px处理，65 token，快速概览
  high: 最大2048px，按512切片，精细理解
  auto: 自动选择
""")

# ============================================================================
# 3. 开源 VLM
# ============================================================================
print("\n--- 3. 开源 VLM ---")
print("""
通过 Ollama 使用开源视觉模型：

```bash
# 下载视觉模型
ollama pull llava:7b          # LLaVA 7B
ollama pull llava:13b         # LLaVA 13B
ollama pull llava-llama3      # LLaVA + Llama3
ollama pull minicpm-v         # MiniCPM-V（中文优秀）
```

```python
import httpx, base64

def ollama_vision(image_b64: str, prompt: str,
                  model: str = "llava:7b") -> str:
    resp = httpx.post("http://localhost:11434/api/chat", json={
        "model": model,
        "messages": [{
            "role": "user",
            "content": prompt,
            "images": [image_b64]
        }],
        "stream": False,
    }, timeout=60.0)
    return resp.json()["message"]["content"]

# 使用
with open("photo.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

result = ollama_vision(b64, "详细描述这张图片")
print(result)
```

模型对比：
┌──────────────────┬────────┬──────────────────────────┐
│  模型             │ 大小   │  特点                     │
├──────────────────┼────────┼──────────────────────────┤
│  llava:7b        │  4.7GB │  通用，速度快             │
│  llava:13b       │  8.0GB │  更准确                   │
│  minicpm-v       │  5.5GB │  中文最好，手机可运行     │
│  llava-llama3    │  5.5GB │  Llama3底座，英文强       │
└──────────────────┴────────┴──────────────────────────┘
""")

# ============================================================================
# 4. 文档与图表理解
# ============================================================================
print("\n--- 4. 文档理解 ---")
print("""
多模态 LLM 可以直接理解：
- PDF 页面截图
- 数据图表（柱状图/折线图/饼图）
- 表格
- 流程图/架构图
- PPT 幻灯片
- 手写笔记

```python
# 理解数据图表
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": 
             "分析这张数据图表，告诉我：\\n"
             "1. 数据的整体趋势\\n"
             "2. 最大值和最小值\\n"
             "3. 你的分析结论"},
            {"type": "image_url", "image_url": {"url": chart_url}}
        ]
    }]
)

# 理解 PDF（截图方式）
from pdf2image import convert_from_path

pages = convert_from_path("document.pdf", dpi=150)
for i, page in enumerate(pages):
    b64 = img_to_b64(page)
    analysis = gpt4o_vision(b64, f"分析第{i+1}页的内容，提取关键信息")
```

vs 传统 OCR 方案：
  传统: PDF→文字提取→LLM分析（丢失排版/图表）
  VLM:  PDF→截图→直接理解（保留所有视觉信息）
""")

# ============================================================================
# 5. LangChain 多模态消息
# ============================================================================
print("\n--- 5. LangChain 多模态 ---")
print("""
LangChain 支持多模态消息格式：

```python
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")

# 多模态消息
message = HumanMessage(content=[
    {"type": "text", "text": "分析这张图片中的数据趋势"},
    {"type": "image_url", "image_url": {
        "url": f"data:image/png;base64,{image_b64}"
    }}
])

response = llm.invoke([message])
print(response.content)

# Ollama 多模态
from langchain_community.chat_models import ChatOllama

llm = ChatOllama(model="llava:7b")
response = llm.invoke([message])
```

链式处理：
```python
from langchain_core.prompts import ChatPromptTemplate

# 图像分析链
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是图像分析专家，请用中文回答"),
    ("human", [
        {"type": "text", "text": "{question}"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,{image}"}}
    ])
])

chain = prompt | llm
result = chain.invoke({"question": "图中有什么？", "image": b64})
```
""")

# ============================================================================
# 6. 多图对比分析
# ============================================================================
print("\n--- 6. 多图对比 ---")
print("""
同时分析多张图片：

```python
# GPT-4o 多图
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "比较这三张产品图的设计差异"},
            {"type": "image_url", "image_url": {"url": url1}},
            {"type": "image_url", "image_url": {"url": url2}},
            {"type": "image_url", "image_url": {"url": url3}},
        ]
    }]
)
```

应用场景：
- 产品对比：比较不同版本的设计
- 质量检测：对比标准品和检测品
- 变化检测：比较两个时间点的卫星图
- 装修对比：多个设计方案比较

注意事项：
- GPT-4o 最多 ~20 张图（受 token 限制）
- 图片越多，准确度越低
- 建议 2-5 张为最佳
""")

# 模拟多模态分析
import httpx

def mock_vision_analysis(prompt: str, n_images: int = 1) -> str:
    """模拟视觉分析"""
    try:
        resp = httpx.post("http://localhost:11434/api/chat", json={
            "model": "qwen2.5:7b",
            "messages": [{"role": "user", "content":
                f"假设你正在分析{n_images}张图片，用户问：{prompt}。请给出分析。"}],
            "stream": False,
        }, timeout=15.0)
        return resp.json().get("message", {}).get("content", "分析完成")
    except:
        return f"[模拟] 对{n_images}张图片进行了分析，发现了主要的视觉特征和差异。"

print("多模态分析演示:")
tasks = [
    ("描述这张产品照片的设计特点", 1),
    ("比较这两张图片的颜色差异", 2),
    ("分析这三个月的销售数据图表趋势", 3),
]
for prompt, n in tasks:
    result = mock_vision_analysis(prompt, n)
    print(f"  [{n}图] {prompt}")
    print(f"        → {result[:80]}...")

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] VLM 三种架构（编码器桥接/token注入/原生）")
print("  [v] GPT-4o 视觉能力（URL/Base64/多图）")
print("  [v] 开源 VLM（LLaVA/MiniCPM-V via Ollama）")
print("  [v] 文档与图表理解")
print("  [v] LangChain 多模态消息格式")
print("  [v] 多图对比分析")
print("=" * 60)
print("\n下一课：03_audio_language.py - 音频-语言模型")
