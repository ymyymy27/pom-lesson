import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第6课：图像编辑（Inpainting / Outpainting / 风格迁移）
==============================================================================

AI 图像编辑 = 在已有图像基础上进行智能修改。

编辑类型：
- Inpainting：局部重绘（修改指定区域）
- Outpainting：画布扩展（向外延伸图像）
- 风格迁移：保持内容，改变风格
- 超分辨率：低分辨率→高分辨率
- 背景替换：保留主体，更换背景
- 物体移除：擦除不需要的元素

本课内容：
1. Inpainting 进阶
2. Outpainting 画布扩展
3. 风格迁移（IP-Adapter）
4. 超分辨率放大
5. 背景替换
6. 智能物体移除
==============================================================================
"""

import json
import numpy as np

print("=" * 60)
print("第6课：图像编辑")
print("=" * 60)

# ============================================================================
# 1. Inpainting 进阶
# ============================================================================
print("\n--- 1. Inpainting 进阶 ---")
print("""
Inpainting = 局部重绘，只修改遮罩区域。

进阶技巧：

1. 遮罩羽化（柔和边缘过渡）
```python
from PIL import Image, ImageFilter

mask = Image.open("mask.png")
# 高斯模糊使边缘柔和
mask = mask.filter(ImageFilter.GaussianBlur(radius=10))
```

2. 扩大遮罩区域（避免接缝）
```python
# 膨胀遮罩
from scipy.ndimage import binary_dilation
mask_array = np.array(mask) > 128
dilated = binary_dilation(mask_array, iterations=5)
mask = Image.fromarray((dilated * 255).astype(np.uint8))
```

3. 只重绘遮罩区域（节省计算）
```python
result = pipe(
    prompt="a beautiful flower",
    image=original,
    mask_image=mask,
    num_inference_steps=30,
    strength=0.8,          # 重绘强度
    guidance_scale=7.5,
).images[0]
```

4. Differential Diffusion（渐变强度）
   遮罩不是非黑即白，灰度=渐变重绘强度
   白色=完全重绘，灰色=部分重绘，黑色=不变

SDXL Inpainting（推荐）：
```python
from diffusers import AutoPipelineForInpainting

pipe = AutoPipelineForInpainting.from_pretrained(
    "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
    torch_dtype=torch.float16,
).to("cuda")
```
""")

# ============================================================================
# 2. Outpainting 画布扩展
# ============================================================================
print("\n--- 2. Outpainting ---")
print("""
Outpainting = 向外扩展图像画布

原理：将原图放在大画布中央，周围用遮罩标记，执行 Inpainting。

```python
from PIL import Image

def outpaint_prepare(image, expand_pixels=256):
    w, h = image.size
    new_w = w + expand_pixels * 2
    new_h = h + expand_pixels * 2
    
    # 新画布
    canvas = Image.new("RGB", (new_w, new_h), (128, 128, 128))
    canvas.paste(image, (expand_pixels, expand_pixels))
    
    # 遮罩（扩展区域为白色）
    mask = Image.new("L", (new_w, new_h), 255)  # 全白
    mask.paste(Image.new("L", (w, h), 0),         # 原图区域黑色
               (expand_pixels, expand_pixels))
    
    return canvas, mask

# 使用
canvas, mask = outpaint_prepare(original_image, expand_pixels=256)

result = pipe(
    prompt="继续扩展这个场景，保持风格一致",
    image=canvas,
    mask_image=mask,
    num_inference_steps=30,
).images[0]
```

技巧：
- 分步扩展（每次扩展一个方向）效果更好
- 在遮罩边缘做渐变过渡，避免接缝
- 提示词要描述整体场景，不只是扩展部分

DALL-E 2 Outpainting：
```python
# DALL-E 2 直接支持
response = client.images.edit(
    model="dall-e-2",
    image=open("canvas.png", "rb"),  # 带透明区域的图
    mask=open("mask.png", "rb"),
    prompt="extend the beautiful landscape",
)
```
""")

# ============================================================================
# 3. 风格迁移（IP-Adapter）
# ============================================================================
print("\n--- 3. 风格迁移 ---")
print("""
IP-Adapter = 用参考图的风格/角色来引导生成

传统风格迁移 vs IP-Adapter：
  传统：内容图 + 风格图 → 神经风格迁移（NST）
  IP-Adapter：参考图 → 提取风格特征 → 注入到SD生成

```python
from diffusers import StableDiffusionPipeline
from transformers import CLIPVisionModelWithProjection

# 加载 IP-Adapter
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
).to("cuda")

pipe.load_ip_adapter(
    "h94/IP-Adapter",
    subfolder="models",
    weight_name="ip-adapter_sd15.bin"
)

# 设置风格强度
pipe.set_ip_adapter_scale(0.6)  # 0-1

# 生成（参考图风格 + 文字内容）
result = pipe(
    prompt="a cat in the garden",
    ip_adapter_image=style_reference_image,  # 风格参考图
    num_inference_steps=30,
).images[0]
```

IP-Adapter 变体：
┌──────────────────────┬──────────────────────────────────┐
│  变体                 │  用途                             │
├──────────────────────┼──────────────────────────────────┤
│  IP-Adapter          │  通用风格迁移                     │
│  IP-Adapter-FaceID   │  人脸一致性（换脸/角色一致）     │
│  IP-Adapter-Plus     │  更强的风格提取                   │
│  IP-Adapter-Full     │  完整图像特征（几乎复制）        │
└──────────────────────┴──────────────────────────────────┘
""")

# ============================================================================
# 4. 超分辨率放大
# ============================================================================
print("\n--- 4. 超分辨率 ---")
print("""
低分辨率图像 → 高分辨率（保持/增强细节）

方案：
┌──────────────────┬──────────┬──────────────────────────┐
│  方案             │  倍数    │  特点                     │
├──────────────────┼──────────┼──────────────────────────┤
│  Real-ESRGAN     │  2x/4x   │  最通用，速度快           │
│  SD Upscaler     │  2x/4x   │  可以加细节（tile方式）   │
│  Swin2SR         │  2x/4x   │  学术级质量              │
│  DALL-E 变体     │  2x      │  保持风格一致             │
│  Topaz Gigapixel │  2-6x    │  商用软件，效果极好      │
└──────────────────┴──────────┴──────────────────────────┘

Real-ESRGAN（推荐）：
```python
# pip install realesrgan
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet

model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                num_block=23, num_grow_ch=32, scale=4)

upsampler = RealESRGANer(
    scale=4,
    model_path="RealESRGAN_x4plus.pth",
    model=model,
    half=True,
)

output, _ = upsampler.enhance(input_image, outscale=4)
# 512×512 → 2048×2048
```

SD Tile ControlNet 超分（增加细节）：
```python
from diffusers import ControlNetModel

controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/control_v11f1e_sd15_tile",
    torch_dtype=torch.float16,
)
# 先放大图片（双线性），再用 tile ControlNet 添加细节
```
""")

# ============================================================================
# 5. 背景替换
# ============================================================================
print("\n--- 5. 背景替换 ---")
print("""
保留主体（人/物），替换背景。

流程：
  原图 → SAM分割主体 → 生成遮罩 → Inpainting新背景

```python
from segment_anything import sam_model_registry, SamPredictor
from diffusers import AutoPipelineForInpainting
from PIL import Image
import numpy as np

# 1. SAM 分割主体
sam = sam_model_registry["vit_h"](checkpoint="sam_vit_h.pth")
predictor = SamPredictor(sam)
predictor.set_image(np.array(image))
masks, _, _ = predictor.predict(point_coords=np.array([[x, y]]),
                                 point_labels=np.array([1]))

# 2. 反转遮罩（主体=黑色/保留，背景=白色/重绘）
bg_mask = Image.fromarray((~masks[0] * 255).astype(np.uint8))

# 3. Inpainting 新背景
pipe = AutoPipelineForInpainting.from_pretrained(...)
result = pipe(
    prompt="beautiful beach sunset background",
    image=image,
    mask_image=bg_mask,
).images[0]
```

简单方案（无需SAM）：
  rembg 库自动去除背景
```python
from rembg import remove
from PIL import Image

output = remove(Image.open("photo.png"))
# output 是带透明背景的 RGBA 图像
# 然后合成到新背景上
```
""")

# ============================================================================
# 6. 智能物体移除
# ============================================================================
print("\n--- 6. 物体移除 ---")
print("""
从图像中擦除不需要的元素（电线/路人/水印...）

方案1：SD Inpainting
  选中要移除的区域 → Inpainting 用周围内容填充

方案2：LaMa（专用修复模型）
  专门训练的图像修复模型，擦除+填充

```python
# LaMa
# pip install simple-lama-inpainting
from simple_lama_inpainting import SimpleLama

lama = SimpleLama()
result = lama(image, mask)  # mask: 白色=要移除的区域
result.save("cleaned.png")
```

方案3：Generative Fill（生成式填充）
  Adobe Photoshop 的"生成式填充"底层也是类似技术

物体移除的关键：
- 遮罩要比物体稍大（包含阴影/倒影）
- 简单背景效果最好
- 复杂纹理区域可能需要多次迭代
""")

# 编辑操作总结
print("\n--- 图像编辑技术总结 ---")
print("""
┌──────────────────┬───────────────────┬──────────────────┐
│  操作             │  核心技术          │  推荐方案         │
├──────────────────┼───────────────────┼──────────────────┤
│  局部重绘        │  Inpainting        │  SDXL Inpaint    │
│  画布扩展        │  Outpainting       │  SDXL + 遮罩     │
│  风格迁移        │  IP-Adapter        │  IP-Adapter Plus │
│  超分辨率        │  Super Resolution  │  Real-ESRGAN     │
│  背景替换        │  SAM + Inpaint     │  rembg + Inpaint │
│  物体移除        │  Image Inpainting  │  LaMa            │
│  换脸            │  Face Swap         │  IP-Adapter Face │
│  上色            │  Colorization      │  ControlNet Line │
└──────────────────┴───────────────────┴──────────────────┘
""")

print("\n" + "=" * 60)
print("[完成] 第6课完成！你已经学会了：")
print("  [v] Inpainting 进阶（羽化/膨胀/渐变强度）")
print("  [v] Outpainting 画布扩展")
print("  [v] 风格迁移（IP-Adapter）")
print("  [v] 超分辨率放大（Real-ESRGAN）")
print("  [v] 背景替换（SAM + Inpaint / rembg）")
print("  [v] 智能物体移除（LaMa）")
print("=" * 60)
print("\n下一课：07_image_gen_project.py - 完整项目：AI 绘画工作站")
