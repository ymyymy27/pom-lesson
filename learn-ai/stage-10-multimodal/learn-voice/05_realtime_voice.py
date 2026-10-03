import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：实时语音交互（流式 ASR / TTS / VAD）
==============================================================================

实时语音交互 = 像打电话一样与 AI 对话。
核心挑战：低延迟（<500ms 端到端）。

关键技术：
- VAD（Voice Activity Detection）：检测用户何时开始/结束说话
- 流式 ASR：边听边转文字
- 流式 LLM：边生成边输出
- 流式 TTS：边合成边播放

本课内容：
1. 实时语音交互架构
2. VAD 语音活动检测
3. 流式 ASR
4. 流式 TTS
5. 全双工对话
6. GPT-4o Realtime API
==============================================================================
"""

import json
import numpy as np
import time

print("=" * 60)
print("第5课：实时语音交互")
print("=" * 60)

# ============================================================================
# 1. 实时语音交互架构
# ============================================================================
print("\n--- 1. 实时语音架构 ---")
print("""
传统方案（串行，延迟高）：
  录音(3s) → ASR(1s) → LLM(2s) → TTS(1s) → 播放
  总延迟: 7秒+  ❌ 体验差

优化方案（流式并行，延迟低）：
  ┌─────────────────────────────────────────────────────┐
  │  麦克风                                              │
  │    ↓                                                 │
  │  VAD（检测说话开始/结束）                            │
  │    ↓                                                 │
  │  流式 ASR（边听边转，~200ms 延迟）                   │
  │    ↓                                                 │
  │  流式 LLM（边生成边输出，~300ms 首token）            │
  │    ↓                                                 │
  │  流式 TTS（边合成边播放，~100ms 首音节）             │
  │    ↓                                                 │
  │  扬声器                                              │
  └─────────────────────────────────────────────────────┘
  总延迟: ~600ms  ✅ 接近真人对话

最新方案（端到端，延迟最低）：
  GPT-4o Realtime API：音频直接进出，无需ASR/TTS中转
  总延迟: ~300ms  ✅ 最佳体验
""")

# ============================================================================
# 2. VAD 语音活动检测
# ============================================================================
print("\n--- 2. VAD ---")
print("""
VAD = 检测音频中是否有人在说话

核心功能：
- 检测说话开始 → 开始录音/识别
- 检测说话结束 → 停止录音，触发处理
- 过滤背景噪音

主流方案：
┌─────────────────┬──────────┬──────────────────────────┐
│  方案            │  类型    │  特点                     │
├─────────────────┼──────────┼──────────────────────────┤
│  WebRTC VAD     │  传统    │  最快，CPU即可，精度一般   │
│  Silero VAD     │  深度学习│  精度高，速度快，推荐     │
│  Energy VAD     │  简单    │  基于音量阈值，最简单     │
└─────────────────┴──────────┴──────────────────────────┘
""")

# 简单的能量 VAD
def energy_vad(audio: np.ndarray, threshold: float = 0.02,
               frame_ms: int = 30, sr: int = 16000) -> list:
    """基于能量的简单 VAD"""
    frame_size = int(sr * frame_ms / 1000)
    results = []

    for i in range(0, len(audio) - frame_size, frame_size):
        frame = audio[i:i + frame_size].astype(np.float32) / 32768.0
        energy = np.sqrt(np.mean(frame ** 2))  # RMS 能量
        is_speech = energy > threshold
        results.append({
            "start_ms": i * 1000 // sr,
            "energy": round(float(energy), 4),
            "is_speech": is_speech,
        })

    return results

# 模拟一段包含说话和静音的音频
sr = 16000
silence = np.zeros(sr, dtype=np.int16)  # 1秒静音
speech = (np.sin(2 * np.pi * 300 * np.linspace(0, 1, sr)) * 16000).astype(np.int16)
audio = np.concatenate([silence, speech, silence[:sr//2], speech, silence])

vad_results = energy_vad(audio, threshold=0.1)
speech_frames = sum(1 for r in vad_results if r["is_speech"])
print(f"Energy VAD 演示:")
print(f"  音频时长: {len(audio)/sr:.1f}s")
print(f"  帧数: {len(vad_results)}")
print(f"  语音帧: {speech_frames}, 静音帧: {len(vad_results)-speech_frames}")

print("""
Silero VAD 使用：
```python
import torch

model, utils = torch.hub.load(
    'snakers4/silero-vad', 'silero_vad', force_reload=False
)
(get_speech_timestamps, _, read_audio, _, _) = utils

audio = read_audio('audio.wav', sampling_rate=16000)
timestamps = get_speech_timestamps(audio, model, sampling_rate=16000)
# [{'start': 1000, 'end': 48000}, ...]
```
""")

# ============================================================================
# 3. 流式 ASR
# ============================================================================
print("\n--- 3. 流式 ASR ---")
print("""
流式 ASR = 边说边识别，不需要等说完。

FunASR 流式识别：
```python
from funasr import AutoModel

model = AutoModel(model="paraformer-zh-streaming")

# 模拟流式输入
chunk_size = [0, 10, 5]  # 流式参数
cache = {}

for audio_chunk in get_audio_chunks():
    result = model.generate(
        input=audio_chunk,
        cache=cache,
        is_final=False,
        chunk_size=chunk_size,
    )
    if result[0]["text"]:
        print(result[0]["text"], end="", flush=True)

# 最终确认
result = model.generate(input="", cache=cache, is_final=True, chunk_size=chunk_size)
print(result[0]["text"])
```

Whisper 流式（伪流式）：
```python
# Whisper 不原生支持流式，但可以用滑动窗口模拟
import whisper

model = whisper.load_model("tiny")
buffer = []

for chunk in audio_stream:
    buffer.append(chunk)
    if len(buffer) > 30:  # 每30个chunk识别一次
        audio = np.concatenate(buffer)
        result = model.transcribe(audio)
        print(result["text"])
```
""")

# ============================================================================
# 4. 流式 TTS
# ============================================================================
print("\n--- 4. 流式 TTS ---")
print("""
流式 TTS = 文字生成一句就合成一句，不等全部生成完。

edge-tts 流式：
```python
import edge_tts

async def stream_tts(text, voice="zh-CN-XiaoxiaoNeural"):
    communicate = edge_tts.Communicate(text, voice)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            # chunk["data"] 是音频二进制数据
            play_audio(chunk["data"])  # 实时播放
        elif chunk["type"] == "WordBoundary":
            # 字词边界信息
            print(f"  说到: {chunk['text']} at {chunk['offset']}ms")
```

OpenAI TTS 流式：
```python
from openai import OpenAI
client = OpenAI()

with client.audio.speech.with_streaming_response.create(
    model="tts-1",
    voice="nova",
    input="Hello, streaming TTS!",
) as response:
    for chunk in response.iter_bytes(chunk_size=4096):
        play_audio(chunk)  # 实时播放
```

LLM + TTS 流式联动：
```python
# LLM 流式输出 → 按句子分割 → TTS 流式合成
buffer = ""
for token in llm.stream("你好"):
    buffer += token
    # 遇到句号/问号等 → 送给 TTS
    if buffer.endswith(("。", "！", "？", "\\n")):
        await stream_tts(buffer)
        buffer = ""
```
""")

# ============================================================================
# 5. 全双工对话
# ============================================================================
print("\n--- 5. 全双工对话 ---")
print("""
全双工 = 用户说话的同时 AI 也在说话（像真人对话）

挑战：
- 打断检测：用户开始说话时，AI 要停止播放
- 回声消除：防止 AI 的输出被麦克风采集到
- 并行处理：ASR/LLM/TTS 同时运行

架构：
```
  ┌──────────────────────────────────┐
  │         全双工对话管理器          │
  │                                  │
  │  ┌────────┐    ┌────────────┐   │
  │  │ 输入流  │    │  输出流     │   │
  │  │ 麦克风  │    │  扬声器     │   │
  │  │   ↓    │    │    ↑       │   │
  │  │ VAD    │    │  TTS流式   │   │
  │  │   ↓    │    │    ↑       │   │
  │  │ ASR流式│    │  LLM流式   │   │
  │  └───┬────┘    └────┬───────┘   │
  │      └──── 对话状态 ────┘        │
  │                                  │
  │  状态机：                        │
  │  IDLE → LISTENING → PROCESSING  │
  │    ↑      → SPEAKING → IDLE     │
  │    └── INTERRUPTED ──┘          │
  └──────────────────────────────────┘
```
""")

# 对话状态机模拟
class ConversationStateMachine:
    """全双工对话状态机"""
    STATES = ["IDLE", "LISTENING", "PROCESSING", "SPEAKING"]

    def __init__(self):
        self.state = "IDLE"
        self.history = []

    def transition(self, event: str) -> str:
        transitions = {
            ("IDLE", "voice_detected"): "LISTENING",
            ("LISTENING", "silence_detected"): "PROCESSING",
            ("LISTENING", "timeout"): "IDLE",
            ("PROCESSING", "response_ready"): "SPEAKING",
            ("SPEAKING", "playback_done"): "IDLE",
            ("SPEAKING", "user_interrupt"): "LISTENING",  # 打断！
        }
        new_state = transitions.get((self.state, event))
        if new_state:
            self.history.append(f"{self.state} --{event}--> {new_state}")
            self.state = new_state
        return self.state

sm = ConversationStateMachine()
events = ["voice_detected", "silence_detected", "response_ready",
          "user_interrupt", "silence_detected", "response_ready", "playback_done"]
print("对话状态机演示:")
for event in events:
    new_state = sm.transition(event)
    print(f"  事件: {event:20s} → 状态: {new_state}")

# ============================================================================
# 6. GPT-4o Realtime API
# ============================================================================
print("\n--- 6. GPT-4o Realtime API ---")
print("""
OpenAI 的 Realtime API 是端到端语音对话方案。
音频直接输入，音频直接输出，无需 ASR/TTS 中转。

```python
import asyncio
import websockets
import json, base64

async def realtime_conversation():
    url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1",
    }
    
    async with websockets.connect(url, extra_headers=headers) as ws:
        # 配置会话
        await ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",  # 服务端 VAD
                    "threshold": 0.5,
                    "silence_duration_ms": 500,
                },
            }
        }))
        
        # 发送音频
        audio_b64 = base64.b64encode(audio_bytes).decode()
        await ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": audio_b64,
        }))
        
        # 接收响应（音频+文字同时返回）
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "response.audio.delta":
                audio_chunk = base64.b64decode(data["delta"])
                play_audio(audio_chunk)
            elif data["type"] == "response.text.delta":
                print(data["delta"], end="")
```

Realtime API 特点：
- 延迟 ~300ms（最快）
- 原生 VAD（服务端检测）
- 支持打断（全双工）
- 支持 Function Calling
- 价格：$0.06/min 输入，$0.24/min 输出
""")

print("\n" + "=" * 60)
print("[完成] 第5课完成！你已经学会了：")
print("  [v] 实时语音交互架构（流式串联）")
print("  [v] VAD 语音活动检测（Energy/Silero）")
print("  [v] 流式 ASR（FunASR Streaming）")
print("  [v] 流式 TTS（edge-tts/OpenAI 流式）")
print("  [v] 全双工对话（状态机+打断检测）")
print("  [v] GPT-4o Realtime API（端到端）")
print("=" * 60)
print("\n下一课：06_audio_processing.py - 音频处理")
