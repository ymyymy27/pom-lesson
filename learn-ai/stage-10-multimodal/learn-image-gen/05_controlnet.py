import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：ControlNet 精确控制生成
==============================================================================

ControlNet 让你精确控制图像生成的构图和细节。
通过各种条件图（线稿/深度图/姿态/边缘）引导生成。

没有 ControlNet：只能靠文字描述（不够精确）
有 ControlNet：  提供参考结构 → 精确控制生成

本课内容：
1. ControlNet 原理
2. Canny 边缘控制
3. Depth 深度图控制
4. OpenPose 姿态控制
5. 其他条件类型
6. 多 ControlNet 叠加
==============================================================================
"""

import json
import numpy as np

print("=" * 60)
print("第5课：ControlNet 精确控制")
print("=" * 60)

# ============================================================================
# 1. ControlNet 原理
# ============================================================================
print("\n--- 1. ControlNet 原理 ---")
print("""
ControlNet 的核心思想：

  在 SD 的 UNet 旁边添加一个"控制网络"
  输入条件图 → 控制网络提取特征 → 注入到 UNet → 引导生成

  ┌────────────────────────────────────────────────┐
  │  条件图（线稿/深度/姿态）                       │
  │       ↓                                         │
  │  ControlNet（冻结原模型权重 + 新增控制分支）    │
  │       ↓（特征注入）                             │
  │  SD UNet（正常去噪）                            │
  │       ↓                                         │
  │  生成结果（遵循条件图的结构）                   │
  └────────────────────────────────────────────────┘

优势：
- 不修改原模型，即插即用
- 可以叠加多个 ControlNet
- 通过 control_scale 调节控制强度
- 社区大量预训练 ControlNet 模型
""")

# ============================================================================
# 2. Canny 边缘控制
# ============================================================================
print("\n--- 2. Canny 边缘控制 ---")
print("""
Canny 边缘 = 从图像中提取轮廓线
用于保持原图的结构/形状

```python
from diffusers import (
    StableDiffusionControlNetPipeline,
    ControlNetModel,
)
from diffusers.utils import load_image
import cv2, torch
from PIL import Image
import numpy as np

# 1. 提取 Canny 边缘
image = load_image("input.jpg")
image_np = np.array(image)
canny = cv2.Canny(image_np, 100, 200)  # 低阈值, 高阈值
canny_image = Image.fromarray(canny)

# 2. 加载 ControlNet
controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/sd-controlnet-canny",
    torch_dtype=torch.float16,
)

# 3. 创建 Pipeline
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnet,
    torch_dtype=torch.float16,
).to("cuda")

# 4. 生成
result = pipe(
    prompt="a beautiful watercolor painting of the scene",
    image=canny_image,             # 条件图
    num_inference_steps=30,
    controlnet_conditioning_scale=1.0,  # 控制强度 0-2
).images[0]

result.save("canny_output.png")
```

controlnet_conditioning_scale 的影响：
  0.0: 完全忽略边缘（等同无 ControlNet）
  0.5: 轻微参考边缘结构
  1.0: 严格遵循边缘（默认）
  1.5+: 过度遵循（可能影响质量）
""")

# 模拟 Canny 边缘提取
print("Canny 边缘提取演示:")
# 创建简单的测试图像数据
test_img = np.zeros((100, 100), dtype=np.uint8)
test_img[20:80, 20:80] = 255  # 白色方块

# 简单的边缘检测（模拟 Canny）
def simple_edge_detect(img):
    """简化版边缘检测"""
    edges = np.zeros_like(img)
    # 水平梯度
    edges[:-1, :] += np.abs(img[1:, :].astype(int) - img[:-1, :].astype(int))
    # 垂直梯度
    edges[:, :-1] += np.abs(img[:, 1:].astype(int) - img[:, :-1].astype(int))
    return (edges > 50).astype(np.uint8) * 255

edges = simple_edge_detect(test_img)
edge_pixels = np.sum(edges > 0)
print(f"  原图: {test_img.shape}, 白色区域占比: {np.mean(test_img > 0):.1%}")
print(f"  边缘: {edges.shape}, 边缘像素数: {edge_pixels}")

# ============================================================================
# 3. Depth 深度图控制
# ============================================================================
print("\n--- 3. Depth 深度控制 ---")
print("""
深度图 = 图像中每个像素的距离信息
近处白色，远处黑色（或反过来）

用途：保持原图的空间关系/前后遮挡

```python
# 使用 MiDaS 或 Depth-Anything 生成深度图
from transformers import pipeline

depth_estimator = pipeline("depth-estimation", model="Intel/dpt-large")
depth = depth_estimator("input.jpg")
depth_image = depth["depth"]  # PIL Image

# 或使用 Depth-Anything V2（更准确）
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

processor = AutoImageProcessor.from_pretrained("depth-anything/Depth-Anything-V2-Small-hf")
model = AutoModelForDepthEstimation.from_pretrained("depth-anything/Depth-Anything-V2-Small-hf")

# 使用深度 ControlNet
controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/sd-controlnet-depth",
    torch_dtype=torch.float16,
)

pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnet,
    torch_dtype=torch.float16,
).to("cuda")

result = pipe(
    prompt="a futuristic cityscape, cyberpunk, neon lights",
    image=depth_image,
    num_inference_steps=30,
).images[0]
```

场景：同一个深度结构，不同风格
  深度图 + "古代中国城市" → 古风
  深度图 + "赛博朋克城市" → 科幻
  深度图 + "水彩画风景" → 水彩
""")

# ============================================================================
# 4. OpenPose 姿态控制
# ============================================================================
print("\n--- 4. OpenPose 姿态控制 ---")
print("""
OpenPose = 人体关键点检测
控制人物的姿态/动作

18个关键点：头/颈/肩/肘/手/臀/膝/脚

```python
from controlnet_aux import OpenposeDetector

# 提取姿态
openpose = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
pose_image = openpose(input_image)

# 使用姿态 ControlNet
controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/sd-controlnet-openpose",
    torch_dtype=torch.float16,
)

pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnet,
    torch_dtype=torch.float16,
).to("cuda")

result = pipe(
    prompt="a dancer in a red dress, elegant, studio",
    image=pose_image,
    num_inference_steps=30,
).images[0]
```

也可以手动绘制姿态骨架图来指定任意姿势！
""")

# ============================================================================
# 5. 其他条件类型
# ============================================================================
print("\n--- 5. 其他 ControlNet 类型 ---")
print("""
┌─────────────────┬──────────────────────────────────────┐
│  类型            │  用途                                 │
├─────────────────┼──────────────────────────────────────┤
│  Canny          │  边缘轮廓，保持形状                   │
│  Depth          │  深度图，保持空间关系                 │
│  OpenPose       │  人体姿态，控制动作                   │
│  Scribble       │  涂鸦/草稿，自由绘制                 │
│  SoftEdge       │  柔和边缘（比Canny更自然）           │
│  NormalMap      │  法线图，控制3D表面方向               │
│  MLSD           │  直线检测，适合建筑/室内              │
│  Lineart        │  线稿，适合插画上色                   │
│  Segmentation   │  语义分割图，控制区域内容             │
│  Tile           │  图块/超分，细节增强                  │
│  IP-Adapter     │  参考图风格/角色迁移                  │
│  Reference-Only │  参考图风格（无需额外模型）           │
│  Inpaint        │  局部重绘控制                         │
│  QR Code        │  生成含二维码的艺术图                 │
└─────────────────┴──────────────────────────────────────┘

常用组合：
- 建筑设计：MLSD（直线）+ Depth（空间）
- 人物插画：OpenPose（姿态）+ Canny（轮廓）
- 风格迁移：IP-Adapter（风格）+ Depth（结构）
- 上色：Lineart（线稿）→ 提示词描述颜色
""")

# ============================================================================
# 6. 多 ControlNet 叠加
# ============================================================================
print("\n--- 6. 多 ControlNet 叠加 ---")
print("""
可以同时使用多个 ControlNet，综合控制！

```python
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel

# 加载多个 ControlNet
controlnets = [
    ControlNetModel.from_pretrained("lllyasviel/sd-controlnet-canny",
                                    torch_dtype=torch.float16),
    ControlNetModel.from_pretrained("lllyasviel/sd-controlnet-openpose",
                                    torch_dtype=torch.float16),
]

pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnets,        # 传入列表！
    torch_dtype=torch.float16,
).to("cuda")

result = pipe(
    prompt="a elegant woman in a garden",
    image=[canny_image, pose_image],  # 对应的条件图列表
    controlnet_conditioning_scale=[0.8, 1.0],  # 各自的强度
    num_inference_steps=30,
).images[0]
```

多 ControlNet 技巧：
- 控制强度分开设置，避免冲突
- 条件图之间不要矛盾（如边缘和姿态应一致）
- 通常2-3个就够，太多会降低质量

SDXL ControlNet：
```python
controlnet = ControlNetModel.from_pretrained(
    "diffusers/controlnet-canny-sdxl-1.0",
    torch_dtype=torch.float16,
)
# 使用 StableDiffusionXLControlNetPipeline
```
""")

print("\n" + "=" * 60)
print("[完成] 第5课完成！你已经学会了：")
print("  [v] ControlNet 原理（条件注入）")
print("  [v] Canny 边缘控制")
print("  [v] Depth 深度图控制")
print("  [v] OpenPose 姿态控制")
print("  [v] 各种条件类型总览")
print("  [v] 多 ControlNet 叠加使用")
print("=" * 60)
print("\n下一课：06_image_editing.py - 图像编辑")
