import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第4课：图像生成 Prompt 工程
==============================================================================

图像生成的 Prompt 工程与文本 LLM 完全不同。
好的提示词 = 高质量图像。

DALL-E 3 vs SD 的提示词风格差异：
- DALL-E 3: 自然语言描述即可，模型会自动优化
- SD/SDXL: 需要结构化的关键词组合，标签式

本课内容：
1. 提示词基本结构
2. 正向提示词模板
3. 负向提示词
4. 风格关键词大全
5. 权重语法
6. DALL-E 3 vs SD 提示词差异
==============================================================================
"""

import json

print("=" * 60)
print("第4课：图像生成 Prompt 工程")
print("=" * 60)

# ============================================================================
# 1. 提示词基本结构
# ============================================================================
print("\n--- 1. 提示词结构 ---")
print("""
SD/SDXL 提示词的标准结构：

  [主体] + [环境/场景] + [风格] + [质量修饰] + [光影/色调]

示例：
  "a cute cat, sitting on a windowsill, sunset background,
   watercolor painting style, masterpiece, best quality,
   warm lighting, golden hour"

各部分详解：
┌──────────────┬──────────────────────────────────────────┐
│  部分         │  示例                                     │
├──────────────┼──────────────────────────────────────────┤
│  主体         │  a cute cat, a girl with red hair        │
│  动作/姿态   │  sitting, running, looking at viewer      │
│  环境/场景   │  in a forest, city street, studio         │
│  风格         │  oil painting, anime, photorealistic     │
│  质量修饰    │  masterpiece, best quality, 8k, detailed │
│  光影         │  dramatic lighting, golden hour, neon    │
│  色调         │  warm colors, pastel, vibrant            │
│  镜头         │  close-up, wide angle, bird's eye view   │
│  艺术家      │  by Monet, in the style of Ghibli        │
└──────────────┴──────────────────────────────────────────┘
""")

# ============================================================================
# 2. 正向提示词模板
# ============================================================================
print("\n--- 2. 正向提示词模板 ---")

prompt_templates = {
    "人像照片": {
        "template": "portrait of {subject}, {expression}, {clothing}, {background}, "
                    "photorealistic, 8k uhd, dslr, soft lighting, high quality, film grain",
        "example": "portrait of a young woman, gentle smile, white dress, garden background, "
                   "photorealistic, 8k uhd, dslr, soft lighting, high quality, film grain",
    },
    "动漫插画": {
        "template": "{character}, {action}, {scene}, anime style, "
                    "masterpiece, best quality, detailed, vibrant colors",
        "example": "a girl with blue hair, holding a sword, standing on a cliff, anime style, "
                   "masterpiece, best quality, detailed, vibrant colors",
    },
    "风景画": {
        "template": "{scene description}, {time of day}, {weather}, {art style}, "
                    "masterpiece, breathtaking, highly detailed",
        "example": "majestic mountain lake, golden sunset, clear sky, oil painting, "
                   "masterpiece, breathtaking, highly detailed",
    },
    "概念设计": {
        "template": "{object/creature}, {design details}, concept art, "
                    "digital painting, artstation, detailed, sharp focus",
        "example": "futuristic spaceship, sleek design with blue neon lights, concept art, "
                   "digital painting, artstation, detailed, sharp focus",
    },
    "产品图": {
        "template": "{product}, {material/color}, product photography, "
                    "studio lighting, white background, commercial, 4k",
        "example": "wireless headphones, matte black, product photography, "
                   "studio lighting, white background, commercial, 4k",
    },
}

for name, info in prompt_templates.items():
    print(f"\n  [{name}]")
    print(f"  模板: {info['template'][:70]}...")
    print(f"  示例: {info['example'][:70]}...")

# ============================================================================
# 3. 负向提示词
# ============================================================================
print("\n\n--- 3. 负向提示词 ---")
print("""
负向提示词告诉模型"不要生成什么"。

通用负向（几乎所有场景都适用）：
  "lowres, bad anatomy, bad hands, text, error, missing fingers,
   extra digit, fewer digits, cropped, worst quality, low quality,
   normal quality, jpeg artifacts, signature, watermark, username, blurry"

人像专用负向：
  "deformed, ugly, disfigured, bad proportions, extra limbs,
   mutation, mutated hands, poorly drawn face, extra fingers,
   bad eyes, crossed eyes"

动漫专用负向：
  "lowres, bad anatomy, bad hands, error, missing fingers,
   extra digit, fewer digits, cropped, worst quality, low quality"

真实感专用负向：
  "cartoon, anime, illustration, painting, drawing, sketch,
   3d render, cgi, unrealistic"

提示：
- DALL-E 3 不支持负向提示词（模型自动处理）
- SD/SDXL 强烈建议使用负向提示词
- 不要放太多，20-50 个词足够
""")

# 负向提示词库
negative_presets = {
    "通用": "lowres, bad anatomy, bad hands, text, error, missing fingers, "
            "extra digit, fewer digits, cropped, worst quality, low quality, "
            "jpeg artifacts, signature, watermark, blurry",
    "人像": "deformed, ugly, disfigured, bad proportions, extra limbs, "
            "mutation, mutated hands, poorly drawn face, cross-eyed",
    "真实感": "cartoon, anime, illustration, painting, drawing, 3d render, cgi",
    "动漫": "lowres, bad anatomy, bad hands, error, ugly, "
            "worst quality, low quality, normal quality",
}

print("预设负向提示词:")
for name, neg in negative_presets.items():
    print(f"  [{name}] {neg[:60]}...")

# ============================================================================
# 4. 风格关键词大全
# ============================================================================
print("\n--- 4. 风格关键词 ---")
print("""
艺术风格：
  oil painting, watercolor, acrylic, pencil sketch, charcoal drawing,
  digital art, pixel art, vector art, collage, mosaic

照片风格：
  photorealistic, cinematic, film photography, Polaroid, vintage,
  lomography, tilt-shift, macro, bokeh, long exposure

动漫/插画：
  anime, manga, chibi, cel shading, Ghibli style, Makoto Shinkai,
  light novel illustration, visual novel

3D 风格：
  3d render, octane render, unreal engine, blender, c4d,
  isometric, low poly, voxel

特殊风格：
  steampunk, cyberpunk, art nouveau, art deco, baroque,
  minimalist, surrealist, impressionist, pop art

光影关键词：
  golden hour, blue hour, dramatic lighting, rim lighting,
  volumetric lighting, god rays, neon, moody, studio lighting

镜头/构图：
  close-up, medium shot, wide angle, bird's eye view, dutch angle,
  portrait, landscape, panoramic, fish-eye, macro
""")

# ============================================================================
# 5. 权重语法
# ============================================================================
print("\n--- 5. 权重语法 ---")
print("""
SD/SDXL 支持对关键词设置权重，控制其影响力。

语法（A1111 WebUI / ComfyUI）：
  (keyword:1.5)    → 权重1.5（更强调）
  (keyword:0.5)    → 权重0.5（弱化）
  (keyword)        → 等同 (keyword:1.1)
  ((keyword))      → 等同 (keyword:1.21)
  [keyword]        → 等同 (keyword:0.9)

示例：
  "a (beautiful:1.3) girl with (red hair:1.5), (blue eyes:0.8)"
  → 强调"beautiful"和"red hair"，弱化"blue eyes"

diffusers 中的权重：
```python
from compel import Compel

compel = Compel(tokenizer=pipe.tokenizer, text_encoder=pipe.text_encoder)

prompt_embeds = compel("a (beautiful:1.3) landscape with (mountains:1.5)")
image = pipe(prompt_embeds=prompt_embeds).images[0]
```

DALL-E 3 不支持权重语法，但可以通过描述的详细程度来控制。
""")

# 权重效果演示
print("权重效果演示:")
weighted_prompts = [
    ("默认", "a girl with red hair, blue eyes, in a garden"),
    ("强调头发", "a girl with (red hair:1.8), blue eyes, in a garden"),
    ("强调眼睛", "a girl with red hair, (blue eyes:1.8), in a garden"),
    ("强调背景", "a girl with red hair, blue eyes, in a (garden:1.8)"),
    ("弱化背景", "a girl with red hair, blue eyes, in a (garden:0.3)"),
]
for name, prompt in weighted_prompts:
    print(f"  [{name:6s}] {prompt}")

# ============================================================================
# 6. DALL-E 3 vs SD 提示词
# ============================================================================
print("\n--- 6. DALL-E 3 vs SD ---")
print("""
两者的提示词风格完全不同！

DALL-E 3（自然语言，像跟人说话）：
  "画一只橘色的猫咪，它坐在窗台上望向外面的日落，
   旁边有一杯还在冒热气的咖啡。整体是温暖的水彩画
   风格，色调偏暖黄色。"

SD/SDXL（关键词标签式）：
  "orange cat, sitting on windowsill, looking at sunset,
   coffee cup, steam, warm colors, watercolor painting,
   masterpiece, best quality, detailed, golden hour lighting"
  
  Negative: "lowres, bad anatomy, blurry, worst quality"

转换技巧：
  DALL-E → SD: 提取关键词，添加质量修饰和负向
  SD → DALL-E: 组织成自然语言句子，去掉质量标签

用 LLM 自动转换：
```python
prompt = llm.invoke(
    "将以下 SD 提示词转为 DALL-E 3 的自然语言描述：\\n"
    "orange cat, sitting on windowsill, sunset, watercolor"
)
```
""")

# 提示词生成器
def generate_prompt(subject: str, style: str = "通用",
                    mood: str = "温暖") -> dict:
    """生成提示词"""
    style_map = {
        "通用": "digital art, detailed, sharp focus",
        "照片": "photorealistic, 8k, dslr, film grain",
        "动漫": "anime style, cel shading, vibrant colors",
        "油画": "oil painting, thick brushstrokes, rich colors",
        "水彩": "watercolor painting, soft edges, flowing colors",
    }
    mood_map = {
        "温暖": "warm lighting, golden hour, cozy atmosphere",
        "冷酷": "cold blue tones, dramatic shadows, moody",
        "梦幻": "ethereal, soft glow, dreamy atmosphere, pastel",
        "黑暗": "dark, ominous, dramatic lighting, high contrast",
    }

    positive = f"{subject}, {style_map.get(style, style_map['通用'])}, " \
               f"{mood_map.get(mood, mood_map['温暖'])}, " \
               f"masterpiece, best quality"
    negative = negative_presets["通用"]

    return {"positive": positive, "negative": negative}

print("\n提示词生成器:")
for subject, style, mood in [
    ("a cat on a rooftop", "照片", "温暖"),
    ("a warrior princess", "动漫", "冷酷"),
    ("a peaceful village", "水彩", "梦幻"),
]:
    result = generate_prompt(subject, style, mood)
    print(f"\n  主题: {subject} | 风格: {style} | 氛围: {mood}")
    print(f"  正向: {result['positive'][:70]}...")
    print(f"  负向: {result['negative'][:50]}...")

print("\n" + "=" * 60)
print("[完成] 第4课完成！你已经学会了：")
print("  [v] 提示词结构（主体+场景+风格+质量+光影）")
print("  [v] 正向提示词模板（人像/动漫/风景/产品）")
print("  [v] 负向提示词预设")
print("  [v] 风格关键词大全")
print("  [v] 权重语法（强调/弱化）")
print("  [v] DALL-E 3 vs SD 提示词差异")
print("=" * 60)
print("\n下一课：05_controlnet.py - ControlNet 精确控制")
