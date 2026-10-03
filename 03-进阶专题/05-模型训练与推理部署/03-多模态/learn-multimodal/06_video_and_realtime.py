import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第6课：视频理解与实时多模态交互
==============================================================================

视频 = 图像序列 + 音频，是最复杂的多模态内容。
实时交互 = 边看/边听/边说/边画，延迟要极低。

本课内容：
1. 视频理解方案
2. Gemini 1.5 视频分析
3. 关键帧+音频联合理解
4. GPT-4o Realtime 多模态
5. 实时屏幕/摄像头分析
6. 多模态流式处理架构
==============================================================================
"""

import json
import numpy as np
from datetime import datetime

print("=" * 60)
print("第6课：视频理解与实时多模态交互")
print("=" * 60)

# ============================================================================
# 1. 视频理解方案
# ============================================================================
print("\n--- 1. 视频理解方案 ---")
print("""
视频理解的三种方案：

方案1: 关键帧 + VLM（最通用）
  视频 → 提取关键帧 → 每帧送 GPT-4o/LLaVA → 汇总
  优点：兼容所有 VLM
  缺点：丢失时序信息和音频

方案2: 原生视频模型（最准确）
  视频 → Gemini 1.5 Pro（原生视频输入）→ 回答
  优点：理解时序、不丢信息
  缺点：只有 Gemini 支持

方案3: 关键帧 + ASR + VLM（推荐折中）
  视频 → 关键帧(视觉) + 音轨(ASR转文字) → 合并送 LLM
  优点：保留视觉和语言信息
  缺点：仍丢失部分时序

方案对比：
┌──────────────────┬──────────┬──────────┬──────────┐
│  方案             │  视觉    │  音频    │  时序     │
├──────────────────┼──────────┼──────────┼──────────┤
│  关键帧+VLM      │  ✅ 采样│  ❌     │  ❌      │
│  Gemini 原生     │  ✅ 全部│  ✅     │  ✅      │
│  关键帧+ASR+VLM  │  ✅ 采样│  ✅ 文字│  ⚠️ 部分 │
│  专用视频模型    │  ✅     │  ⚠️     │  ✅      │
└──────────────────┴──────────┴──────────┴──────────┘
""")

# ============================================================================
# 2. Gemini 1.5 视频分析
# ============================================================================
print("\n--- 2. Gemini 1.5 视频 ---")
print("""
Gemini 1.5 Pro 是目前唯一原生支持视频输入的商用模型。
支持最长 1 小时视频，100 万 token 上下文。

```python
import google.generativeai as genai

genai.configure(api_key="your-api-key")
model = genai.GenerativeModel("gemini-1.5-pro")

# 上传视频文件
video_file = genai.upload_file("lecture.mp4")

# 等待处理完成
import time
while video_file.state.name == "PROCESSING":
    time.sleep(5)
    video_file = genai.get_file(video_file.name)

# 视频问答
response = model.generate_content([
    video_file,
    "请详细总结这个视频的内容，列出关键信息点。"
])
print(response.text)

# 带时间戳的分析
response = model.generate_content([
    video_file,
    "列出视频中每个主要场景的时间戳和内容描述"
])

# 视频中的特定问题
response = model.generate_content([
    video_file,
    "视频中03:25处展示的图表数据是什么？"
])
```

Gemini 视频处理能力：
- 最长 1 小时视频
- 理解画面内容、文字、人物动作
- 理解音频/对话内容
- 支持时间戳定位
- 支持多视频对比
""")

# ============================================================================
# 3. 关键帧+音频联合理解
# ============================================================================
print("\n--- 3. 关键帧+音频联合 ---")
print("""
不用 Gemini 时的推荐方案：

```python
import cv2
import whisper
import base64
from openai import OpenAI

def analyze_video(video_path: str, question: str) -> str:
    # 1. 提取关键帧（每2秒一帧）
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % int(fps * 2) == 0:  # 每2秒
            _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            b64 = base64.b64encode(buf).decode()
            frames.append({
                "timestamp": frame_idx / fps,
                "base64": b64
            })
        frame_idx += 1
    cap.release()
    
    # 2. 提取音频并 ASR
    # ffmpeg 提取音频
    os.system(f'ffmpeg -i {video_path} -q:a 0 temp_audio.wav -y')
    whisper_model = whisper.load_model("small")
    asr_result = whisper_model.transcribe("temp_audio.wav")
    transcript = asr_result["text"]
    
    # 3. 合并送 GPT-4o
    client = OpenAI()
    content = [
        {"type": "text", "text": 
         f"视频转录文字：{transcript[:2000]}\\n\\n"
         f"以下是视频关键帧（共{len(frames)}帧），请结合画面和转录回答：{question}"}
    ]
    # 最多取10帧避免 token 过多
    for f in frames[:10]:
        content.append({"type": "image_url", "image_url": {
            "url": f"data:image/jpeg;base64,{f['base64']}",
            "detail": "low"
        }})
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}]
    )
    return response.choices[0].message.content
```
""")

# 模拟视频分析
mock_video_analysis = {
    "frames_extracted": 15,
    "duration": "2:30",
    "transcript": "大家好，今天我们来讨论多模态AI的最新发展...",
    "key_moments": [
        {"time": "00:05", "visual": "标题页：多模态AI入门", "audio": "开场白"},
        {"time": "00:30", "visual": "GPT-4o架构图", "audio": "介绍模型架构"},
        {"time": "01:15", "visual": "代码演示", "audio": "实操环节"},
        {"time": "02:00", "visual": "总结幻灯片", "audio": "课程总结"},
    ]
}

print("模拟视频分析结果:")
print(f"  时长: {mock_video_analysis['duration']}")
print(f"  关键帧数: {mock_video_analysis['frames_extracted']}")
print(f"  转录: {mock_video_analysis['transcript'][:40]}...")
print(f"  关键时刻:")
for m in mock_video_analysis["key_moments"]:
    print(f"    [{m['time']}] 画面:{m['visual']} | 音频:{m['audio']}")

# ============================================================================
# 4. GPT-4o Realtime 多模态
# ============================================================================
print("\n--- 4. GPT-4o Realtime ---")
print("""
GPT-4o Realtime API = 端到端实时多模态交互

特性：
- 音频直接输入输出（无需 ASR/TTS）
- 延迟 ~300ms
- 支持打断（全双工）
- 支持 Function Calling
- 支持发送图片（边看边聊）

```python
import asyncio, websockets, json, base64

async def realtime_multimodal():
    url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1",
    }
    
    async with websockets.connect(url, extra_headers=headers) as ws:
        # 配置
        await ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "voice": "alloy",
                "tools": [{
                    "type": "function",
                    "name": "get_weather",
                    "description": "获取天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {"city": {"type": "string"}},
                    }
                }],
                "turn_detection": {"type": "server_vad"},
            }
        }))
        
        # 发送图片（让 AI 看到画面）
        await ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{image_b64}"
                }]
            }
        }))
        
        # 发送音频 + 接收音频（双向流式）
        async for msg in ws:
            data = json.loads(msg)
            if data["type"] == "response.audio.delta":
                play_audio(base64.b64decode(data["delta"]))
            elif data["type"] == "response.function_call_arguments.done":
                # 执行工具调用
                result = execute_tool(data["name"], json.loads(data["arguments"]))
                await ws.send(json.dumps({
                    "type": "conversation.item.create",
                    "item": {"type": "function_call_output", ...}
                }))
```

Realtime 交互模式：
  用户说话 → VAD检测 → GPT-4o处理 → 语音回复 → 用户可随时打断
  同时可以发送图片/截图 → GPT-4o "看到"画面并结合语音回答
""")

# ============================================================================
# 5. 实时屏幕/摄像头分析
# ============================================================================
print("\n--- 5. 实时屏幕分析 ---")
print("""
实时捕获屏幕或摄像头 → AI 分析：

```python
import cv2, base64, time
from openai import OpenAI

client = OpenAI()
cap = cv2.VideoCapture(0)  # 摄像头

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # 每 5 秒分析一次
    if time.time() % 5 < 0.1:
        _, buf = cv2.imencode('.jpg', frame)
        b64 = base64.b64encode(buf).decode()
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "简述画面中正在发生什么"},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}",
                    "detail": "low"
                }}
            ]}],
            max_tokens=100,
        )
        print(f"[{datetime.now():%H:%M:%S}] {response.choices[0].message.content}")
    
    cv2.imshow("Live", frame)
    if cv2.waitKey(1) == 27:  # ESC
        break

cap.release()
```

应用场景：
- 视频会议实时字幕+分析
- 安防监控异常检测
- 直播内容审核
- 工业质检实时监控
- 辅助视障人士实时描述环境
""")

# ============================================================================
# 6. 多模态流式架构
# ============================================================================
print("\n--- 6. 流式架构 ---")
print("""
生产级实时多模态系统架构：

  ┌──────────────────────────────────────────────────────┐
  │                   客户端                              │
  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐    │
  │  │ 麦克风  │  │ 摄像头  │  │ 屏幕   │  │ 扬声器  │    │
  │  └──┬─────┘  └──┬─────┘  └──┬─────┘  └──▲─────┘    │
  │     │ audio     │ video     │ screen    │ audio     │
  └─────┼───────────┼───────────┼───────────┼───────────┘
        │           │           │           │
  ══════╪═══════════╪═══════════╪═══════════╪══ WebSocket
        │           │           │           │
  ┌─────▼───────────▼───────────▼───────────┼───────────┐
  │                   服务端                  │           │
  │                                          │           │
  │  ┌──────────┐  ┌──────────┐  ┌──────────▼────────┐  │
  │  │ 音频流   │  │ 视频流   │  │ TTS 流式合成      │  │
  │  │ 处理器   │  │ 处理器   │  └───────────────────┘  │
  │  │ VAD+ASR  │  │ 关键帧  │                          │
  │  └──┬──────┘  └──┬──────┘                          │
  │     │            │                                  │
  │  ┌──▼────────────▼──┐    ┌──────────────────────┐  │
  │  │ 多模态 LLM       │ ←→ │ 工具/知识库          │  │
  │  │ (GPT-4o/Qwen)   │    │ (RAG/API/数据库)     │  │
  │  └──────────────────┘    └──────────────────────┘  │
  └────────────────────────────────────────────────────┘

关键设计：
- WebSocket 双向流式通信
- 音频/视频独立处理管道
- LLM 异步调用（不阻塞流式输入）
- TTS 流式输出（边生成边播放）
- 回压控制（避免处理不过来）
""")

print("\n" + "=" * 60)
print("[完成] 第6课完成！你已经学会了：")
print("  [v] 视频理解三种方案对比")
print("  [v] Gemini 1.5 原生视频分析")
print("  [v] 关键帧+ASR 联合理解")
print("  [v] GPT-4o Realtime 多模态交互")
print("  [v] 实时屏幕/摄像头分析")
print("  [v] 生产级多模态流式架构")
print("=" * 60)
print("\n下一课：07_multimodal_project.py - 完整项目：多模态智能助手")
