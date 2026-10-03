import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：图像理解（GPT-4o / Qwen-VL 视觉问答）
==============================================================================

本课学习如何用多模态 LLM 理解图像内容。

核心能力：
- 看图说话（图像描述）
- 视觉问答（VQA）
- 图像对比分析
- 多图理解

支持的方式：
1. OpenAI GPT-4o（最强，需要API Key）
2. Ollama LLaVA / Qwen2-VL（免费本地）
3. LangChain 统一封装

本课内容：
1. OpenAI Vision API
2. Ollama 本地视觉模型
3. LangChain 多模态消息
4. 图像描述与场景理解
5. 视觉问答（VQA）
6. 多图对比分析
==============================================================================
"""

import json
import os
import base64
from io import BytesIO

print("=" * 60)
print("第2课：图像理解")
print("=" * 60)

# ============================================================================
# 1. OpenAI Vision API
# ============================================================================
print("\n--- 1. OpenAI Vision API ---")
print("""
GPT-4o 原生支持图像输入，通过 content 数组传入文本+图像。

```python
from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "描述这张图片"},
            {"type": "image_url", "image_url": {
                "url": "data:image/png;base64,iVBOR...",
                "detail": "auto"  # low/high/auto
            }}
        ]
    }]
)
print(response.choices[0].message.content)
```

detail 参数影响：
- low:  固定 85 tokens，适合快速分类
- high: 最多 1445 tokens，适合细节分析
- auto: 模型自动选择
""")

# 创建测试图像（用于后续演示）
try:
    from PIL import Image, ImageDraw, ImageFont

    def create_test_image(text="Hello AI", size=(300, 200), bg_color=(66, 135, 245)):
        """创建带文字的测试图像"""
        img = Image.new("RGB", size, color=bg_color)
        draw = ImageDraw.Draw(img)
        # 简单文字
        draw.text((size[0]//4, size[1]//3), text, fill=(255, 255, 255))
        draw.rectangle([20, 20, size[0]-20, size[1]-20], outline=(255, 255, 255), width=2)
        return img

    def image_to_base64(img, format="PNG"):
        """PIL Image → Base64 字符串"""
        buffer = BytesIO()
        img.save(buffer, format=format)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    test_img = create_test_image("Test Image")
    test_b64 = image_to_base64(test_img)
    print(f"测试图像: {test_img.size}, Base64 长度: {len(test_b64)}")
    HAS_PIL = True

except ImportError:
    print("  Pillow 未安装，使用模拟数据")
    HAS_PIL = False
    test_b64 = "iVBORw0KGgoAAAANSUhEUg..."  # 模拟

# ============================================================================
# 2. Ollama 本地视觉模型
# ============================================================================
print("\n--- 2. Ollama 本地视觉模型 ---")
print("""
Ollama 支持多个视觉模型：
  ollama pull llava:7b       # LLaVA 7B
  ollama pull llava:13b      # LLaVA 13B（更准确）
  ollama pull bakllava       # BakLLaVA

Ollama Vision API（原生）：
```python
import httpx

response = httpx.post("http://localhost:11434/api/chat", json={
    "model": "llava:7b",
    "messages": [{
        "role": "user",
        "content": "描述这张图片",
        "images": ["<base64编码的图片>"]  # Ollama用images字段
    }],
    "stream": False
})
print(response.json()["message"]["content"])
```

注意 Ollama 和 OpenAI 的区别：
- OpenAI: content 数组，image_url 对象
- Ollama: content 文本，images 数组（Base64列表）
""")

import httpx

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llava:7b"  # 需要先 ollama pull llava:7b

def ollama_vision(prompt: str, image_b64: str, model: str = OLLAMA_MODEL) -> str:
    """Ollama 视觉模型调用"""
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": model,
            "messages": [{
                "role": "user",
                "content": prompt,
                "images": [image_b64],
            }],
            "stream": False,
        }, timeout=60.0)
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "无回复")
    except httpx.ConnectError:
        return "❌ 无法连接 Ollama，请确保已运行 ollama serve 并下载 llava 模型"
    except Exception as e:
        return f"❌ 错误: {e}"

# 测试
print("\n[测试: Ollama Vision]")
result = ollama_vision("用中文简要描述这张图片的内容", test_b64)
print(f"  回答: {result[:150]}...")

# ============================================================================
# 3. LangChain 多模态消息
# ============================================================================
print("\n\n--- 3. LangChain 多模态消息 ---")
print("""
LangChain 统一了多模态消息格式，一套代码适配多个模型。

```python
from langchain_core.messages import HumanMessage

# 文本 + 图像的消息
message = HumanMessage(content=[
    {"type": "text", "text": "描述这张图片"},
    {"type": "image_url", "image_url": {
        "url": f"data:image/png;base64,{base64_str}"
    }}
])

# 使用 ChatOllama（本地）
from langchain_community.chat_models import ChatOllama
llm = ChatOllama(model="llava:7b")
response = llm.invoke([message])

# 使用 ChatOpenAI（云端）
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o")
response = llm.invoke([message])
```
""")

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOllama

def langchain_vision(prompt: str, image_b64: str, model: str = "llava:7b") -> str:
    """LangChain 封装的视觉调用"""
    try:
        llm = ChatOllama(model=model)
        message = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{image_b64}"
            }}
        ])
        response = llm.invoke([message])
        return response.content
    except Exception as e:
        return f"❌ 错误: {e}"

print("[测试: LangChain Vision]")
result = langchain_vision("这张图片里有什么？用中文回答。", test_b64)
print(f"  回答: {result[:150]}...")

# ============================================================================
# 4. 图像描述与场景理解
# ============================================================================
print("\n--- 4. 图像描述场景 ---")
print("""
图像描述的不同粒度：

简要描述：一句话概括
  "这是一张城市街道的照片，有行人和汽车"

详细描述：多角度分析
  "照片中是一条繁忙的城市街道。左侧有一栋灰色的写字楼，
   街上有三辆汽车和几个行人。天气晴朗，阳光从右侧照入。
   远处可以看到一座桥。"

结构化描述：JSON输出
  {"scene": "城市街道", "objects": ["汽车","行人","写字楼"],
   "weather": "晴天", "time": "白天"}

通过 prompt 控制输出粒度：
""")

prompts = {
    "简要": "用一句话描述这张图片",
    "详细": "详细描述这张图片的内容，包括场景、物体、颜色、构图",
    "结构化": "用JSON格式描述这张图片，包含 scene/objects/colors 字段",
    "情感": "分析这张图片传达的情感和氛围",
}

print("不同 Prompt 的效果：")
for name, prompt in prompts.items():
    result = ollama_vision(prompt, test_b64)
    print(f"  [{name}] {result[:80]}...")

# ============================================================================
# 5. 视觉问答（VQA）
# ============================================================================
print("\n--- 5. 视觉问答（VQA）---")
print("""
视觉问答 = 看图回答具体问题

典型场景：
- "图中有几个人？" → 数量统计
- "这是什么品牌？" → 品牌识别
- "这道菜是什么？" → 食物识别
- "这个按钮是什么功能？" → UI理解
- "这段代码有什么问题？" → 代码截图分析
""")

vqa_questions = [
    "这张图片中有文字吗？如果有，写出文字内容。",
    "这张图片的主色调是什么？",
    "这张图片可能是用于什么场景？",
]

print("VQA 测试:")
for q in vqa_questions:
    a = ollama_vision(q, test_b64)
    print(f"  Q: {q}")
    print(f"  A: {a[:100]}...")
    print()

# ============================================================================
# 6. 多图对比分析
# ============================================================================
print("\n--- 6. 多图对比分析 ---")
print("""
多模态 LLM 支持同时传入多张图片进行对比。

OpenAI 方式（content 数组中多个 image_url）：
```python
message = HumanMessage(content=[
    {"type": "text", "text": "比较这两张图片的区别"},
    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img1}"}},
    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img2}"}},
])
```

Ollama 方式（images 数组传多张）：
```python
{"role": "user", "content": "比较区别", "images": [img1_b64, img2_b64]}
```

应用场景：
- 找不同
- 商品对比
- 前后对比（装修前/后）
- 版本对比（UI新旧版）
""")

if HAS_PIL:
    img1 = create_test_image("Version A", bg_color=(66, 135, 245))
    img2 = create_test_image("Version B", bg_color=(245, 135, 66))
    b64_1 = image_to_base64(img1)
    b64_2 = image_to_base64(img2)

    print("[测试: 多图对比]")
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": OLLAMA_MODEL,
            "messages": [{
                "role": "user",
                "content": "比较这两张图片的区别，用中文回答。",
                "images": [b64_1, b64_2],
            }],
            "stream": False,
        }, timeout=60.0)
        print(f"  回答: {resp.json().get('message', {}).get('content', '无')[:150]}...")
    except Exception as e:
        print(f"  连接失败: {e}")

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] OpenAI Vision API 调用格式")
print("  [v] Ollama 本地视觉模型（LLaVA）")
print("  [v] LangChain 多模态消息封装")
print("  [v] 不同粒度的图像描述")
print("  [v] 视觉问答（VQA）")
print("  [v] 多图对比分析")
print("=" * 60)
print("\n下一课：03_ocr_and_extraction.py - OCR 与信息提取")
