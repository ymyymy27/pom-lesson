import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第4课：目标检测与图像分割
==============================================================================

目标检测：识别图像中物体的位置和类别
图像分割：像素级别的区域划分

主流方案：
1. YOLO 系列（v8/v10）→ 最快的实时检测
2. SAM（Segment Anything）→ 最强的通用分割
3. Grounding DINO → 开放词汇检测（文字描述→检测）
4. 多模态 LLM → 粗粒度定位（灵活但不精确）

本课内容：
1. 目标检测基础概念
2. YOLOv8 实战
3. SAM 图像分割
4. Grounding DINO 开放词汇检测
5. LLM 辅助的视觉定位
6. 检测结果后处理
==============================================================================
"""

import json

print("=" * 60)
print("第4课：目标检测与图像分割")
print("=" * 60)

# ============================================================================
# 1. 目标检测基础概念
# ============================================================================
print("\n--- 1. 目标检测基础 ---")
print("""
目标检测的输出：
  每个检测到的物体 = (类别, 置信度, 边界框)

  边界框格式：
  ┌────────────────────┐
  │  (x1,y1)           │
  │     ┌──────────┐   │
  │     │  person   │   │  class: "person"
  │     │  0.95     │   │  confidence: 0.95
  │     └──────────┘   │  bbox: [x1, y1, x2, y2]
  │            (x2,y2) │
  └────────────────────┘

检测 vs 分类 vs 分割：
┌──────────────┬────────────────────────────────────────┐
│  任务         │  输出                                   │
├──────────────┼────────────────────────────────────────┤
│  图像分类     │  整图一个标签: "猫"                     │
│  目标检测     │  多个框+标签: [(猫,框1),(狗,框2)]       │
│  语义分割     │  每个像素一个类别标签                    │
│  实例分割     │  每个像素属于哪个物体实例                │
│  全景分割     │  语义+实例结合                          │
└──────────────┴────────────────────────────────────────┘
""")

# ============================================================================
# 2. YOLOv8 实战
# ============================================================================
print("\n--- 2. YOLOv8 实战 ---")
print("""
YOLO（You Only Look Once）是最快的目标检测框架。

安装：pip install ultralytics

```python
from ultralytics import YOLO

# 加载预训练模型
model = YOLO("yolov8n.pt")  # nano版（最快）
# model = YOLO("yolov8s.pt")  # small版
# model = YOLO("yolov8m.pt")  # medium版
# model = YOLO("yolov8x.pt")  # extra large版（最准）

# 检测图像
results = model("photo.jpg")

# 解析结果
for result in results:
    for box in result.boxes:
        cls = result.names[int(box.cls)]  # 类别名
        conf = float(box.conf)            # 置信度
        xyxy = box.xyxy[0].tolist()       # [x1,y1,x2,y2]
        print(f"{cls}: {conf:.2f} at {xyxy}")

# 保存标注后的图像
results[0].save("result.jpg")

# 视频检测
results = model("video.mp4", stream=True)
for result in results:
    # 每帧的检测结果
    ...
```

YOLOv8 支持的任务：
- 目标检测: model("photo.jpg")
- 实例分割: YOLO("yolov8n-seg.pt")
- 姿态估计: YOLO("yolov8n-pose.pt")
- 分类:     YOLO("yolov8n-cls.pt")

性能参考（640×640 图像）：
┌──────────────┬──────────┬──────────┬──────────┐
│  模型         │  参数量  │  mAP     │  速度     │
├──────────────┼──────────┼──────────┼──────────┤
│  YOLOv8n     │  3.2M    │  37.3%   │  1.2ms   │
│  YOLOv8s     │  11.2M   │  44.9%   │  2.1ms   │
│  YOLOv8m     │  25.9M   │  50.2%   │  5.0ms   │
│  YOLOv8x     │  68.2M   │  53.9%   │  12.1ms  │
└──────────────┴──────────┴──────────┴──────────┘
""")

# 模拟 YOLO 检测结果
mock_yolo_results = [
    {"class": "person", "confidence": 0.96, "bbox": [120, 50, 280, 400]},
    {"class": "car", "confidence": 0.89, "bbox": [350, 200, 550, 350]},
    {"class": "dog", "confidence": 0.82, "bbox": [30, 300, 150, 420]},
    {"class": "traffic light", "confidence": 0.75, "bbox": [500, 10, 530, 60]},
]

print("模拟 YOLO 检测结果:")
for det in mock_yolo_results:
    print(f"  {det['class']:15s} 置信度:{det['confidence']:.2f}  框:{det['bbox']}")

# ============================================================================
# 3. SAM 图像分割
# ============================================================================
print("\n--- 3. SAM（Segment Anything）---")
print("""
SAM 是 Meta 发布的"分割一切"模型。
给定一个点/框/文本提示，自动分割对应区域。

安装：pip install segment-anything

```python
from segment_anything import sam_model_registry, SamPredictor

# 加载模型
sam = sam_model_registry["vit_h"](checkpoint="sam_vit_h.pth")
predictor = SamPredictor(sam)

# 设置图像
predictor.set_image(image_array)

# 方式1: 点提示（点击一个点）
masks, scores, logits = predictor.predict(
    point_coords=np.array([[500, 375]]),  # 点坐标
    point_labels=np.array([1]),           # 1=前景, 0=背景
)

# 方式2: 框提示（画一个框）
masks, scores, logits = predictor.predict(
    box=np.array([100, 50, 400, 300]),  # [x1,y1,x2,y2]
)

# masks[0] 就是分割掩码（H×W 的 bool 数组）
```

SAM2（2024更新）：
- 支持视频分割
- 速度更快
- pip install sam-2
""")

# ============================================================================
# 4. Grounding DINO
# ============================================================================
print("\n--- 4. Grounding DINO ---")
print("""
Grounding DINO = 开放词汇目标检测
用文字描述要检测什么，不限于固定类别！

传统检测: 只能检测训练过的80类（person/car/dog...）
Grounding DINO: 用文字描述任意物体都能检测

```python
from groundingdino.util.inference import load_model, predict

model = load_model("config.py", "weights.pth")

# 用文字描述要检测的物体
boxes, logits, phrases = predict(
    model=model,
    image=image,
    caption="red car. person with hat. traffic sign.",  # 文字描述
    box_threshold=0.35,
    text_threshold=0.25,
)

# boxes: 检测框, phrases: 匹配的文字
for box, logit, phrase in zip(boxes, logits, phrases):
    print(f"{phrase}: {logit:.2f} at {box.tolist()}")
```

Grounding DINO + SAM = 最强组合：
  文字描述 → Grounding DINO 检测框 → SAM 精确分割
  "把图中的红色汽车分割出来"
""")

# ============================================================================
# 5. LLM 辅助的视觉定位
# ============================================================================
print("\n--- 5. LLM 辅助视觉定位 ---")
print("""
多模态 LLM 也能做粗粒度的物体定位：

```python
prompt = '''看这张图片，找出所有的人物，
用JSON格式输出他们的大致位置：
[{"object": "...", "position": "左上/中间/右下等"}]'''

response = llm.invoke([HumanMessage(content=[
    {"type": "text", "text": prompt},
    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
])])
```

LLM vs 专用模型：
┌──────────────┬──────────────────┬──────────────────┐
│              │  LLM             │  YOLO/SAM        │
├──────────────┼──────────────────┼──────────────────┤
│  精度        │  粗粒度（方向）  │  像素级精确       │
│  速度        │  慢（秒级）      │  快（毫秒级）     │
│  灵活性      │  任意文字描述    │  固定/开放类别     │
│  适用场景    │  理解分析        │  精确定位          │
│  批量处理    │  不适合          │  非常适合          │
└──────────────┴──────────────────┴──────────────────┘

最佳实践：LLM 理解意图 → 专用模型精确执行
""")

# ============================================================================
# 6. 检测结果后处理
# ============================================================================
print("\n--- 6. 检测结果后处理 ---")
print("""
原始检测结果通常需要后处理。
""")

def non_max_suppression(detections: list, iou_threshold: float = 0.5) -> list:
    """非极大值抑制（NMS）：去除重叠的检测框"""
    if not detections:
        return []

    # 按置信度排序
    sorted_dets = sorted(detections, key=lambda d: d["confidence"], reverse=True)
    kept = []

    while sorted_dets:
        best = sorted_dets.pop(0)
        kept.append(best)

        remaining = []
        for det in sorted_dets:
            if compute_iou(best["bbox"], det["bbox"]) < iou_threshold:
                remaining.append(det)
        sorted_dets = remaining

    return kept

def compute_iou(box1, box2):
    """计算两个框的交并比 IoU"""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0

# NMS 演示
raw_detections = [
    {"class": "person", "confidence": 0.96, "bbox": [100, 50, 280, 400]},
    {"class": "person", "confidence": 0.85, "bbox": [110, 55, 275, 395]},  # 重叠！
    {"class": "car", "confidence": 0.89, "bbox": [350, 200, 550, 350]},
]

print("NMS 前:", len(raw_detections), "个检测")
for d in raw_detections:
    print(f"  {d['class']} {d['confidence']:.2f} {d['bbox']}")

filtered = non_max_suppression(raw_detections)
print(f"\nNMS 后: {len(filtered)} 个检测（去除重叠框）")
for d in filtered:
    print(f"  {d['class']} {d['confidence']:.2f} {d['bbox']}")

# IoU 计算
iou = compute_iou([100, 50, 280, 400], [110, 55, 275, 395])
print(f"\n两个 person 框的 IoU: {iou:.4f}（高度重叠，NMS 去除低置信度的）")

print("""
常用后处理：
1. NMS（非极大值抑制）→ 去除重叠框
2. 置信度过滤 → 去除低置信度检测
3. 类别过滤 → 只保留感兴趣的类别
4. 区域过滤 → 只保留特定区域内的检测
5. 跟踪关联 → 视频中跨帧关联同一物体
""")

print("\n" + "=" * 60)
print("[完成] 第4课完成！你已经学会了：")
print("  [v] 目标检测基础（框/类别/置信度）")
print("  [v] YOLOv8 实战（检测/分割/姿态）")
print("  [v] SAM 通用分割（点/框提示）")
print("  [v] Grounding DINO 开放词汇检测")
print("  [v] LLM 辅助视觉定位")
print("  [v] NMS 与 IoU 后处理")
print("=" * 60)
print("\n下一课：05_image_search.py - 图像搜索与 CLIP 嵌入")
