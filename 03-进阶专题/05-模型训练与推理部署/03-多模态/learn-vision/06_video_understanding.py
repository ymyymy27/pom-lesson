import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第6课：视频理解（关键帧 / 摘要 / 多模态分析）
==============================================================================

视频 = 连续的图像帧 + 音频
视频理解的核心：从大量帧中提取有意义的信息。

方案：
1. 关键帧提取 + 视觉 LLM 分析（最实用）
2. 专用视频模型（Video-LLaVA / Gemini 1.5）
3. 视频目标检测/跟踪（YOLO + tracking）

本课内容：
1. 视频处理基础（OpenCV）
2. 关键帧提取策略
3. 关键帧 + LLM 视频摘要
4. 视频目标检测与跟踪
5. 视频问答（VideoQA）
6. 实时视频流分析
==============================================================================
"""

import json
import os
import tempfile

print("=" * 60)
print("第6课：视频理解")
print("=" * 60)

# ============================================================================
# 1. 视频处理基础
# ============================================================================
print("\n--- 1. 视频处理基础 ---")
print("""
使用 OpenCV 处理视频：

```python
import cv2

# 打开视频
cap = cv2.VideoCapture("video.mp4")

# 视频信息
fps = cap.get(cv2.CAP_PROP_FPS)           # 帧率
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 总帧数
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
duration = total_frames / fps              # 时长（秒）

print(f"{width}x{height}, {fps}fps, {duration:.1f}秒, {total_frames}帧")

# 逐帧读取
while cap.isOpened():
    ret, frame = cap.read()  # frame: numpy array (H, W, 3)
    if not ret:
        break
    # 处理 frame...

cap.release()
```

视频数据量：
  1080p × 30fps × 60秒 = 1920×1080×3×30×60 ≈ 11.2 GB（原始）
  → 不可能把所有帧都送给 LLM
  → 需要关键帧提取！
""")

# ============================================================================
# 2. 关键帧提取策略
# ============================================================================
print("\n--- 2. 关键帧提取策略 ---")
print("""
从视频中选择有代表性的帧：

策略1：均匀采样（最简单）
  每隔 N 帧取一帧，或每秒取 1 帧

策略2：场景变化检测（推荐）
  计算相邻帧的差异，差异大的地方取帧
  → 捕获场景切换的关键时刻

策略3：基于内容（最精确）
  用 CLIP 嵌入聚类，每个聚类取一帧
  → 确保多样性

策略4：混合策略
  均匀采样 + 场景变化 + 去重
""")

import numpy as np

def uniform_sample_frames(total_frames: int, n_samples: int) -> list[int]:
    """均匀采样帧"""
    if n_samples >= total_frames:
        return list(range(total_frames))
    step = total_frames / n_samples
    return [int(i * step) for i in range(n_samples)]

def scene_change_detect(frame_diffs: list[float], threshold: float = 0.3) -> list[int]:
    """基于帧差异的场景变化检测"""
    changes = [0]  # 第一帧始终包含
    for i, diff in enumerate(frame_diffs):
        if diff > threshold:
            changes.append(i + 1)
    return changes

# 演示
print("均匀采样（100帧中取10帧）:")
samples = uniform_sample_frames(100, 10)
print(f"  帧号: {samples}")

print("\n场景变化检测:")
mock_diffs = [0.05, 0.03, 0.02, 0.45, 0.04, 0.03, 0.60, 0.02, 0.01, 0.35]
changes = scene_change_detect(mock_diffs, threshold=0.3)
print(f"  帧差异: {mock_diffs}")
print(f"  场景变化帧: {changes}")

# ============================================================================
# 3. 关键帧 + LLM 视频摘要
# ============================================================================
print("\n--- 3. 关键帧 + LLM 视频摘要 ---")
print("""
最实用的视频理解方案：

  视频 → 提取关键帧 → 每帧送 LLM 描述 → 汇总为视频摘要

```python
import cv2, base64

def extract_keyframes(video_path, interval_sec=2):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    interval = int(fps * interval_sec)
    frames = []
    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if count % interval == 0:
            # 转 Base64
            _, buffer = cv2.imencode('.jpg', frame)
            b64 = base64.b64encode(buffer).decode()
            frames.append({
                "frame_num": count,
                "timestamp": count / fps,
                "base64": b64
            })
        count += 1
    cap.release()
    return frames

def summarize_video(frames):
    # 1. 描述每个关键帧
    descriptions = []
    for f in frames:
        desc = llm_vision(f"描述这个视频帧的内容（时间{f['timestamp']:.1f}秒）",
                          f["base64"])
        descriptions.append(f"[{f['timestamp']:.1f}s] {desc}")
    
    # 2. 汇总为视频摘要
    all_desc = "\\n".join(descriptions)
    summary = llm.invoke(f"以下是视频各关键帧的描述，请生成视频摘要：\\n{all_desc}")
    return summary
```
""")

# 模拟视频摘要
mock_frame_descriptions = [
    {"timestamp": 0.0, "description": "一个人坐在办公桌前打开电脑"},
    {"timestamp": 3.0, "description": "屏幕上显示代码编辑器，正在写Python代码"},
    {"timestamp": 8.0, "description": "切换到终端，运行了一个命令"},
    {"timestamp": 12.0, "description": "浏览器打开，显示一个Web应用"},
    {"timestamp": 18.0, "description": "回到代码编辑器，修改了一些代码"},
    {"timestamp": 22.0, "description": "再次运行，终端显示'测试通过'"},
    {"timestamp": 25.0, "description": "人物面带微笑，竖起大拇指"},
]

print("模拟视频关键帧描述:")
for f in mock_frame_descriptions:
    print(f"  [{f['timestamp']:5.1f}s] {f['description']}")

print(f"""
视频摘要（LLM 汇总）：
  这是一段编程工作的录屏视频（约25秒）。视频中一位开发者
  在编写Python代码，通过终端运行测试，在浏览器中查看Web应用
  效果，修复了一些问题后测试通过，最后表示满意。
""")

# ============================================================================
# 4. 视频目标检测与跟踪
# ============================================================================
print("\n--- 4. 视频目标检测与跟踪 ---")
print("""
视频中的目标跟踪 = 逐帧检测 + 跨帧关联

```python
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

# 方式1: 视频文件
results = model.track("video.mp4", persist=True, stream=True)
for result in results:
    for box in result.boxes:
        track_id = int(box.id)    # 跟踪ID（跨帧同一物体）
        cls = result.names[int(box.cls)]
        print(f"Track {track_id}: {cls}")

# 方式2: 实时摄像头
results = model.track(source=0, show=True, stream=True)
```

跟踪算法：
- ByteTrack（YOLOv8默认，最稳定）
- BoT-SORT（更准确）
- DeepSORT（经典，带外观特征）

应用场景：
- 客流统计（商场/门店）
- 车辆计数（交通）
- 运动分析（体育）
- 安防监控
""")

# ============================================================================
# 5. 视频问答（VideoQA）
# ============================================================================
print("\n--- 5. 视频问答 ---")
print("""
直接用 LLM 回答关于视频的问题。

方案1：关键帧 + LLM（目前最实用）
  提取关键帧 → 连同问题一起送给 LLM

方案2：专用视频模型
  - Gemini 1.5 Pro: 原生支持视频输入（最长1小时）
  - Video-LLaVA: 开源视频理解模型
  - LLaVA-NeXT-Video: 改进版

方案3：字幕+帧描述+LLM
  视频 → 语音转文字(ASR) + 关键帧描述 → 合并为文本 → LLM回答

```python
# Gemini 方式（原生视频）
import google.generativeai as genai

model = genai.GenerativeModel("gemini-1.5-pro")
video_file = genai.upload_file("video.mp4")
response = model.generate_content([
    video_file,
    "这个视频讲了什么？列出关键信息。"
])
```
""")

# 模拟 VideoQA
print("视频问答演示（基于关键帧描述）:")
video_context = "\n".join([f"[{f['timestamp']}s] {f['description']}" for f in mock_frame_descriptions])

qa_pairs = [
    ("这个视频的主要内容是什么？", "这是一段编程工作的录屏，展示了代码编写、测试和调试的过程。"),
    ("视频中的人在用什么编程语言？", "从关键帧描述中可以看到是Python代码。"),
    ("最终测试结果如何？", "测试通过了，视频中人物在最后竖起大拇指表示满意。"),
]

for q, a in qa_pairs:
    print(f"  Q: {q}")
    print(f"  A: {a}")
    print()

# ============================================================================
# 6. 实时视频流分析
# ============================================================================
print("\n--- 6. 实时视频流分析 ---")
print("""
实时处理摄像头或视频流：

```python
import cv2
from ultralytics import YOLO

model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)  # 摄像头

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # YOLO 检测
    results = model(frame, verbose=False)
    
    # 每 N 帧用 LLM 分析一次（LLM太慢不能每帧）
    frame_count += 1
    if frame_count % 30 == 0:  # 每秒1次
        b64 = frame_to_base64(frame)
        analysis = llm_vision("场景有异常吗？", b64)
    
    # 绘制检测结果
    annotated = results[0].plot()
    cv2.imshow("Live", annotated)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
```

分层处理策略（平衡速度和智能）：
┌──────────────┬──────────┬──────────────────────────┐
│  层级        │  频率    │  处理                     │
├──────────────┼──────────┼──────────────────────────┤
│  L1 检测     │  每帧    │  YOLO 实时检测（<10ms）   │
│  L2 跟踪     │  每帧    │  ByteTrack 跟踪关联       │
│  L3 分析     │  每秒    │  规则判断（越界/计数）     │
│  L4 理解     │  每10秒  │  LLM 深度分析             │
└──────────────┴──────────┴──────────────────────────┘
""")

print("\n" + "=" * 60)
print("[完成] 第6课完成！你已经学会了：")
print("  [v] 视频处理基础（OpenCV）")
print("  [v] 关键帧提取策略（均匀/场景变化/聚类）")
print("  [v] 关键帧 + LLM 视频摘要")
print("  [v] 视频目标检测与跟踪（YOLO + ByteTrack）")
print("  [v] 视频问答（VideoQA）")
print("  [v] 实时视频流分层分析")
print("=" * 60)
print("\n下一课：07_vision_project.py - 完整项目：智能图像分析助手")
