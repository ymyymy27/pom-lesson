import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：DALL-E / API 方式生成图像
==============================================================================

使用 API 生成图像是最简单的方式，无需 GPU。

主流 API：
1. OpenAI DALL-E 3（最强提示词理解）
2. Stability AI（Stable Diffusion 云端）
3. Replicate（各种开源模型的云端 API）

本课内容：
1. DALL-E 3 API 基本使用
2. 图像尺寸与质量选项
3. 图像编辑 API
4. 图像变体生成
5. Stability AI API
6. 批量生成与成本控制
==============================================================================
"""

import json
import os
import base64
from io import BytesIO

print("=" * 60)
print("第2课：DALL-E / API 生成图像")
print("=" * 60)

# ============================================================================
# 1. DALL-E 3 API
# ============================================================================
print("\n--- 1. DALL-E 3 API ---")
print("""
DALL-E 3 是 OpenAI 的图像生成模型，提示词理解能力最强。

```python
from openai import OpenAI
client = OpenAI()

# 基本生成
response = client.images.generate(
    model="dall-e-3",
    prompt="一只橘猫坐在窗台上看日落，水彩画风格",
    size="1024x1024",     # 尺寸
    quality="standard",    # standard 或 hd
    n=1,                   # 生成数量（DALL-E 3 只能=1）
)

# 获取结果
image_url = response.data[0].url           # 图片URL（1小时有效）
revised_prompt = response.data[0].revised_prompt  # 模型修改后的提示词

print(f"图片URL: {image_url}")
print(f"实际使用的提示词: {revised_prompt}")

# 下载保存
import httpx
img_data = httpx.get(image_url).content
with open("generated.png", "wb") as f:
    f.write(img_data)
```

DALL-E 3 特点：
- 自动优化提示词（revised_prompt）
- 文字渲染能力强
- 不需要复杂的提示词工程
- 但无法精确控制构图
""")

# 模拟 DALL-E 调用
def mock_dalle_generate(prompt: str, size: str = "1024x1024",
                        quality: str = "standard") -> dict:
    """模拟 DALL-E API 调用"""
    return {
        "url": f"https://oaidalleapiprodscus.blob.core.windows.net/mock/{hash(prompt) % 10000}.png",
        "revised_prompt": f"A detailed illustration of: {prompt[:50]}... rendered in high quality digital art style.",
        "size": size,
        "quality": quality,
        "estimated_cost": 0.04 if quality == "standard" else 0.08,
    }

result = mock_dalle_generate("一只橘猫坐在窗台上看日落，水彩画风格")
print(f"模拟生成:")
print(f"  URL: {result['url'][:60]}...")
print(f"  修改后的提示词: {result['revised_prompt'][:60]}...")
print(f"  预估成本: ${result['estimated_cost']}")

# ============================================================================
# 2. 尺寸与质量
# ============================================================================
print("\n--- 2. 尺寸与质量 ---")
print("""
DALL-E 3 支持的选项：

尺寸：
┌──────────────┬──────────┬──────────┐
│  尺寸         │  比例    │  用途     │
├──────────────┼──────────┼──────────┤
│  1024×1024   │  1:1     │  通用     │
│  1792×1024   │  16:9    │  横屏壁纸 │
│  1024×1792   │  9:16    │  手机壁纸 │
└──────────────┴──────────┴──────────┘

质量：
┌──────────────┬──────────┬──────────────────┐
│  选项         │  价格    │  说明             │
├──────────────┼──────────┼──────────────────┤
│  standard    │  $0.040  │  标准质量         │
│  hd          │  $0.080  │  高清（细节更丰富）│
└──────────────┴──────────┴──────────────────┘

DALL-E 2 支持的选项（更便宜但质量低）：
  256×256: $0.016  |  512×512: $0.018  |  1024×1024: $0.020

返回格式：
  response_format="url"     → 返回图片URL（默认，1小时过期）
  response_format="b64_json" → 返回Base64编码（适合直接处理）

```python
# Base64 方式（直接获取图像数据）
response = client.images.generate(
    model="dall-e-3",
    prompt="...",
    response_format="b64_json",
)
img_b64 = response.data[0].b64_json
img_bytes = base64.b64decode(img_b64)
```
""")

# ============================================================================
# 3. 图像编辑 API
# ============================================================================
print("\n--- 3. 图像编辑 ---")
print("""
DALL-E 2 支持图像编辑（DALL-E 3 暂不支持）：

Inpainting（局部重绘）：
```python
response = client.images.edit(
    model="dall-e-2",
    image=open("original.png", "rb"),  # 原图（必须PNG，正方形）
    mask=open("mask.png", "rb"),       # 遮罩（透明区域=要重绘的）
    prompt="一只蓝色的蝴蝶停在花上",
    size="1024x1024",
    n=1,
)
```

遮罩要求：
- PNG 格式，带 Alpha 通道
- 透明区域 = 需要重绘的区域
- 不透明区域 = 保持不变的区域
- 尺寸必须和原图一样

创建遮罩：
```python
from PIL import Image, ImageDraw

# 创建遮罩
mask = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
draw = ImageDraw.Draw(mask)
# 圆形透明区域（需要重绘的部分）
draw.ellipse([300, 300, 700, 700], fill=(0, 0, 0, 0))
mask.save("mask.png")
```
""")

# ============================================================================
# 4. 图像变体
# ============================================================================
print("\n--- 4. 图像变体 ---")
print("""
根据一张图生成类似的变体：

```python
response = client.images.create_variation(
    model="dall-e-2",
    image=open("input.png", "rb"),
    n=3,               # 生成3个变体
    size="1024x1024",
)

for i, data in enumerate(response.data):
    print(f"变体{i+1}: {data.url}")
```

限制：
- 只有 DALL-E 2 支持
- 输入必须是 PNG，正方形，<4MB
- 变体风格和构图会有变化
""")

# ============================================================================
# 5. Stability AI API
# ============================================================================
print("\n--- 5. Stability AI API ---")
print("""
Stability AI 提供 Stable Diffusion 系列的云端 API。

```python
import httpx

API_KEY = "sk-..."
API_HOST = "https://api.stability.ai"

# 文生图
response = httpx.post(
    f"{API_HOST}/v2beta/stable-image/generate/sd3",
    headers={"Authorization": f"Bearer {API_KEY}"},
    files={"none": ""},
    data={
        "prompt": "a beautiful sunset over the ocean, oil painting",
        "negative_prompt": "blurry, low quality",
        "output_format": "png",
        "aspect_ratio": "16:9",
        "model": "sd3-medium",
    },
)

if response.status_code == 200:
    with open("stability_output.png", "wb") as f:
        f.write(response.content)
```

支持的模型：
- sd3-medium / sd3-large: Stable Diffusion 3
- sdxl-1.0: SDXL
- stable-image-core: 快速版

图生图：
```python
response = httpx.post(
    f"{API_HOST}/v2beta/stable-image/generate/sd3",
    headers={"Authorization": f"Bearer {API_KEY}"},
    files={"image": open("input.png", "rb")},
    data={
        "prompt": "transform to anime style",
        "strength": 0.7,  # 0-1，越大变化越大
        "mode": "image-to-image",
    },
)
```
""")

# ============================================================================
# 6. 批量生成与成本
# ============================================================================
print("\n--- 6. 批量生成与成本 ---")
print("""
成本控制策略：

1. 先用 DALL-E 2 快速迭代提示词（便宜）
2. 确定后用 DALL-E 3 生成高质量版本
3. 大批量用 Stability AI（更便宜）
4. 超大批量用本地 SD（零成本，但需 GPU）

价格对比（每张图）：
┌──────────────────┬──────────┬──────────────────┐
│  方案             │  价格    │  质量             │
├──────────────────┼──────────┼──────────────────┤
│  DALL-E 2 256px  │  $0.016  │  ★★             │
│  DALL-E 2 1024px │  $0.020  │  ★★★           │
│  DALL-E 3 std    │  $0.040  │  ★★★★         │
│  DALL-E 3 hd     │  $0.080  │  ★★★★★       │
│  Stability API   │  ~$0.01  │  ★★★★         │
│  本地 SD         │  电费    │  ★★★★         │
│  Midjourney      │  ~$0.02  │  ★★★★★       │
└──────────────────┴──────────┴──────────────────┘

批量生成模板：
```python
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def generate_batch(prompts: list):
    tasks = [
        client.images.generate(model="dall-e-3", prompt=p, size="1024x1024")
        for p in prompts
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# 注意速率限制！DALL-E 3: 7张/分钟（Tier 1）
```
""")

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] DALL-E 3 API 基本使用")
print("  [v] 尺寸/质量/格式选项")
print("  [v] 图像编辑（Inpainting）")
print("  [v] 图像变体生成")
print("  [v] Stability AI API")
print("  [v] 批量生成与成本控制")
print("=" * 60)
print("\n下一课：03_stable_diffusion.py - Stable Diffusion 本地部署")
