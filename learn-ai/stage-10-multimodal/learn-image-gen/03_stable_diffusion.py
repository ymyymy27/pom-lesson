import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：Stable Diffusion 本地部署与使用
==============================================================================

Stable Diffusion 是最重要的开源图像生成模型。
本课学习如何用 Python（diffusers库）在本地运行。

部署方式：
1. diffusers（Python代码，本课重点）
2. ComfyUI（节点式 GUI，生产推荐）
3. A1111 WebUI（经典 GUI）
4. Fooocus（最简单 GUI）

本课内容：
1. diffusers 基本用法
2. txt2img 文生图
3. img2img 图生图
4. Inpainting 局部重绘
5. 模型加载与切换
6. 性能优化
==============================================================================
"""

import json

print("=" * 60)
print("第3课：Stable Diffusion 本地部署")
print("=" * 60)

# ============================================================================
# 1. diffusers 基本用法
# ============================================================================
print("\n--- 1. diffusers 基本用法 ---")
print("""
diffusers 是 HuggingFace 的扩散模型库。

安装：
  pip install diffusers transformers accelerate torch

```python
from diffusers import StableDiffusionPipeline
import torch

# 加载模型（首次下载约4GB）
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,    # 半精度省显存
).to("cuda")                     # GPU

# 生成图像
image = pipe(
    prompt="a cute cat sitting on a windowsill, sunset, watercolor",
    num_inference_steps=30,    # 去噪步数（越多越精细）
    guidance_scale=7.5,        # CFG 值（提示词遵循度）
    height=512,
    width=512,
).images[0]

image.save("output.png")
```

常用模型 ID：
  SD 1.5:  runwayml/stable-diffusion-v1-5
  SD 2.1:  stabilityai/stable-diffusion-2-1
  SDXL:    stabilityai/stable-diffusion-xl-base-1.0
  SD 3:    stabilityai/stable-diffusion-3-medium-diffusers
""")

# ============================================================================
# 2. txt2img 文生图
# ============================================================================
print("\n--- 2. txt2img 文生图 ---")
print("""
```python
from diffusers import StableDiffusionXLPipeline
import torch

# SDXL（推荐，1024×1024）
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    variant="fp16",
    use_safetensors=True,
).to("cuda")

# 生成
image = pipe(
    prompt="a majestic dragon flying over a medieval castle, "
           "epic fantasy art, highly detailed, 8k",
    negative_prompt="blurry, low quality, distorted, watermark",
    num_inference_steps=30,
    guidance_scale=7.5,
    height=1024,
    width=1024,
    generator=torch.Generator("cuda").manual_seed(42),  # 固定种子=可复现
).images[0]

image.save("dragon.png")
```

关键参数：
┌──────────────────────┬──────────────────────────────────┐
│  参数                 │  说明                             │
├──────────────────────┼──────────────────────────────────┤
│  prompt              │  正向提示词（要什么）             │
│  negative_prompt     │  负向提示词（不要什么）           │
│  num_inference_steps │  去噪步数，20-50，越多越细       │
│  guidance_scale      │  CFG，5-15，越高越遵循提示词     │
│  height / width      │  输出尺寸                         │
│  generator.seed      │  随机种子，固定可复现             │
│  num_images_per_prompt│ 每次生成几张                     │
└──────────────────────┴──────────────────────────────────┘
""")

# 模拟生成参数测试
configs = [
    {"steps": 20, "cfg": 7.0, "desc": "标准配置（快速）"},
    {"steps": 30, "cfg": 7.5, "desc": "推荐配置（均衡）"},
    {"steps": 50, "cfg": 10.0, "desc": "高质量（慢）"},
    {"steps": 30, "cfg": 3.0, "desc": "低CFG（更自由/抽象）"},
    {"steps": 30, "cfg": 15.0, "desc": "高CFG（严格遵循/可能过饱和）"},
]

print("参数配置对比:")
for c in configs:
    print(f"  steps={c['steps']:3d}, CFG={c['cfg']:5.1f} → {c['desc']}")

# ============================================================================
# 3. img2img 图生图
# ============================================================================
print("\n--- 3. img2img 图生图 ---")
print("""
以一张图为基础，结合提示词生成新图。

```python
from diffusers import StableDiffusionImg2ImgPipeline
from PIL import Image

pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
).to("cuda")

# 加载参考图
init_image = Image.open("sketch.png").resize((512, 512))

image = pipe(
    prompt="a beautiful landscape painting, vibrant colors, oil painting",
    image=init_image,
    strength=0.7,       # 0-1，越大变化越大
    num_inference_steps=30,
    guidance_scale=7.5,
).images[0]

image.save("img2img_output.png")
```

strength 参数的影响：
  0.1-0.3: 微调（保留大部分原图）
  0.4-0.6: 中度变化（结构保留，细节改变）
  0.7-0.9: 大幅变化（只保留大致构图）
  1.0:     完全重新生成（等同 txt2img）

应用场景：
- 草稿→成品：手绘草图变精美插画
- 风格转换：照片变水彩/油画/动漫
- 季节变换：夏天→冬天
- 时间变换：白天→夜晚
""")

# ============================================================================
# 4. Inpainting 局部重绘
# ============================================================================
print("\n--- 4. Inpainting ---")
print("""
只修改图像的指定区域，其余保持不变。

```python
from diffusers import StableDiffusionInpaintPipeline
from PIL import Image

pipe = StableDiffusionInpaintPipeline.from_pretrained(
    "runwayml/stable-diffusion-inpainting",
    torch_dtype=torch.float16,
).to("cuda")

# 原图和遮罩
image = Image.open("photo.png").resize((512, 512))
mask = Image.open("mask.png").resize((512, 512))
# mask: 白色=需要重绘, 黑色=保持不变

result = pipe(
    prompt="a cute golden retriever puppy",
    image=image,
    mask_image=mask,
    num_inference_steps=30,
    guidance_scale=7.5,
).images[0]

result.save("inpainted.png")
```

创建遮罩的方式：
1. Pillow 手动绘制
2. SAM 自动分割生成
3. GUI 工具（ComfyUI/A1111 内置）

```python
# 用 Pillow 创建圆形遮罩
from PIL import Image, ImageDraw

mask = Image.new("RGB", (512, 512), "black")
draw = ImageDraw.Draw(mask)
draw.ellipse([150, 150, 350, 350], fill="white")
mask.save("mask.png")
```
""")

# ============================================================================
# 5. 模型加载与切换
# ============================================================================
print("\n--- 5. 模型管理 ---")
print("""
社区模型（Civitai / HuggingFace）：
  SD 社区有大量微调模型，擅长不同风格。

```python
# 从 HuggingFace 加载
pipe = StableDiffusionPipeline.from_pretrained("模型ID")

# 从本地 safetensors 文件加载
pipe = StableDiffusionPipeline.from_single_file(
    "path/to/model.safetensors",
    torch_dtype=torch.float16,
)

# LoRA（轻量微调模型，叠加使用）
pipe.load_lora_weights("path/to/lora.safetensors")
pipe.fuse_lora(lora_scale=0.8)  # 强度 0-1

# 卸载 LoRA
pipe.unfuse_lora()
pipe.unload_lora_weights()
```

常用社区模型风格：
┌──────────────────┬──────────────────────────────────┐
│  模型             │  风格                             │
├──────────────────┼──────────────────────────────────┤
│  DreamShaper     │  通用高质量                       │
│  RealisticVision │  照片级真实感                     │
│  Anything V5     │  动漫二次元                       │
│  RevAnimated     │  半真实风格                       │
│  Deliberate      │  通用艺术                         │
└──────────────────┴──────────────────────────────────┘
""")

# ============================================================================
# 6. 性能优化
# ============================================================================
print("\n--- 6. 性能优化 ---")
print("""
优化策略（显存不够/速度太慢时）：

1. 半精度 (fp16)：显存减半
   pipe = pipe.to(torch_dtype=torch.float16)

2. 注意力优化：
   pipe.enable_xformers_memory_efficient_attention()  # xformers
   # 或
   pipe.enable_attention_slicing()  # 通用，不需要额外库

3. VAE 切片：大图显存优化
   pipe.enable_vae_slicing()
   pipe.enable_vae_tiling()

4. CPU 卸载：显存极度不足时
   pipe.enable_model_cpu_offload()    # 推荐
   pipe.enable_sequential_cpu_offload()  # 更省但更慢

5. Scheduler 优化（减少步数）：
   from diffusers import DPMSolverMultistepScheduler
   pipe.scheduler = DPMSolverMultistepScheduler.from_config(
       pipe.scheduler.config
   )
   # DPM-Solver: 20步即可达到50步的效果

6. TensorRT / ONNX 加速：
   # 推理速度提升 2-5 倍

速度参考（RTX 3060 12GB，SDXL，30步）：
  无优化: ~30秒
  fp16 + xformers: ~15秒
  + DPM-Solver 20步: ~10秒
  + TensorRT: ~5秒

常用 Scheduler：
┌────────────────────────────┬──────────────────────────┐
│  Scheduler                 │  特点                     │
├────────────────────────────┼──────────────────────────┤
│  DDPM                      │  原始，1000步，太慢       │
│  DDIM                      │  减少到50步              │
│  DPM-Solver++              │  20步即可，推荐          │
│  Euler                     │  快速，通用              │
│  Euler Ancestral           │  更多随机性/创意         │
│  UniPC                     │  10步即可，最快          │
└────────────────────────────┴──────────────────────────┘
""")

print("\n" + "=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] diffusers 库基本用法")
print("  [v] txt2img 文生图（参数调优）")
print("  [v] img2img 图生图（strength 控制）")
print("  [v] Inpainting 局部重绘")
print("  [v] 模型加载与 LoRA")
print("  [v] 性能优化（显存/速度）")
print("=" * 60)
print("\n下一课：04_prompt_engineering.py - 图像生成 Prompt 工程")
