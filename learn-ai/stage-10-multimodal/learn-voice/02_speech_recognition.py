import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：语音识别 ASR（Whisper / FunASR）
==============================================================================

ASR = Automatic Speech Recognition（自动语音识别）
语音 → 文字

本课学习三种 ASR 方案：
1. OpenAI Whisper（本地模型）
2. OpenAI Whisper API（云端）
3. FunASR（达摩院，中文最强）

本课内容：
1. Whisper 本地使用
2. Whisper API 调用
3. FunASR 中文识别
4. 流式语音识别
5. 长音频分段识别
6. 识别结果后处理
==============================================================================
"""

import json
import os
import tempfile
import numpy as np

print("=" * 60)
print("第2课：语音识别 ASR")
print("=" * 60)

# ============================================================================
# 1. Whisper 本地使用
# ============================================================================
print("\n--- 1. Whisper 本地 ---")
print("""
OpenAI Whisper 是目前最通用的 ASR 模型。

安装：pip install openai-whisper
还需要安装 ffmpeg（音频格式转换）

```python
import whisper

# 加载模型
model = whisper.load_model("base")  # tiny/base/small/medium/large

# 识别音频文件
result = model.transcribe("audio.wav")

print(result["text"])           # 完整文本
print(result["language"])       # 检测到的语言
print(result["segments"])       # 分段（带时间戳）

# 带时间戳的分段
for seg in result["segments"]:
    start = seg["start"]       # 开始时间（秒）
    end = seg["end"]           # 结束时间（秒）
    text = seg["text"]         # 文本
    print(f"[{start:.1f}s-{end:.1f}s] {text}")
```

模型大小和性能：
┌──────────┬────────┬──────────┬───────────────────────┐
│  模型     │  参数  │  VRAM    │  相对速度              │
├──────────┼────────┼──────────┼───────────────────────┤
│  tiny    │  39M   │  ~1GB    │  ~32x（最快）          │
│  base    │  74M   │  ~1GB    │  ~16x                 │
│  small   │  244M  │  ~2GB    │  ~6x                  │
│  medium  │  769M  │  ~5GB    │  ~2x                  │
│  large   │  1.5B  │  ~10GB   │  1x（最准）            │
└──────────┴────────┴──────────┴───────────────────────┘

推荐：
- 快速转写 → tiny/base
- 中文识别 → small 以上（small 即可）
- 最高精度 → large-v3
""")

# 生成模拟音频用于演示
def generate_test_audio(filename: str, duration: float = 3.0, sr: int = 16000):
    """生成测试音频文件"""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # 简单的正弦波
    audio = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.5).astype(np.int16)
    try:
        import soundfile as sf
        sf.write(filename, audio, sr)
        return True
    except ImportError:
        # 手动写 WAV
        import struct
        with open(filename, 'wb') as f:
            n_samples = len(audio)
            data_size = n_samples * 2
            f.write(b'RIFF')
            f.write(struct.pack('<I', 36 + data_size))
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write(struct.pack('<IHHIIHH', 16, 1, 1, sr, sr * 2, 2, 16))
            f.write(b'data')
            f.write(struct.pack('<I', data_size))
            f.write(audio.tobytes())
        return True

test_wav = os.path.join(tempfile.gettempdir(), "test_asr.wav")
generate_test_audio(test_wav)
print(f"测试音频: {test_wav}")

# 尝试使用 Whisper
try:
    import whisper
    print("\n[Whisper 本地识别]")
    model = whisper.load_model("tiny")
    result = model.transcribe(test_wav)
    print(f"  语言: {result.get('language', '?')}")
    print(f"  文本: {result.get('text', '(无)')[:100]}")
    print(f"  分段数: {len(result.get('segments', []))}")
except ImportError:
    print("\n  Whisper 未安装 (pip install openai-whisper)")
except Exception as e:
    print(f"\n  Whisper 错误: {e}")

# ============================================================================
# 2. Whisper API（云端）
# ============================================================================
print("\n--- 2. Whisper API ---")
print("""
OpenAI 提供 Whisper 的云端 API（不需要 GPU）。

```python
from openai import OpenAI
client = OpenAI()

# 基本转写
with open("audio.wav", "rb") as f:
    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=f,
        language="zh",              # 指定语言（可选）
        response_format="verbose_json",  # 详细JSON（带时间戳）
    )

print(result.text)

# 翻译（任何语言 → 英文）
with open("chinese_audio.wav", "rb") as f:
    result = client.audio.translations.create(
        model="whisper-1",
        file=f,
    )
print(result.text)  # 英文翻译
```

response_format 选项：
- "text": 纯文本
- "json": JSON（含text字段）
- "verbose_json": 详细JSON（含segments时间戳）
- "srt": SRT字幕格式
- "vtt": VTT字幕格式

价格：$0.006/分钟（非常便宜）
限制：文件最大 25MB
""")

# ============================================================================
# 3. FunASR 中文识别
# ============================================================================
print("\n--- 3. FunASR（达摩院）---")
print("""
FunASR 是阿里达摩院的语音识别框架，中文识别最强。

安装：pip install funasr modelscope

```python
from funasr import AutoModel

# 语音识别（Paraformer 模型）
model = AutoModel(
    model="paraformer-zh",              # 中文识别
    vad_model="fsmn-vad",               # 语音活动检测
    punc_model="ct-punc",               # 标点恢复
    spk_model="cam++",                  # 说话人识别（可选）
)

result = model.generate(input="audio.wav")
print(result[0]["text"])

# 流式识别
model_streaming = AutoModel(model="paraformer-zh-streaming")
# 分块送入音频...
```

FunASR 的优势：
- 中文识别精度超过 Whisper
- 支持实时流式识别
- 内置 VAD（语音活动检测）
- 内置标点恢复
- 支持说话人分离
- 完全离线运行
""")

# ============================================================================
# 4. 流式语音识别
# ============================================================================
print("\n--- 4. 流式识别 ---")
print("""
实时场景需要流式（Streaming）识别：
  麦克风 → 分块 → 实时识别 → 逐字输出

非流式 vs 流式：
  非流式: 录完整段音频 → 一次性识别 → 返回完整结果
  流式:   边录边识别 → 实时返回部分结果 → 最终确认

```python
# FunASR 流式识别
import sounddevice as sd
from funasr import AutoModel

model = AutoModel(model="paraformer-zh-streaming")

chunk_size = [0, 10, 5]  # 流式参数 [首帧, 中间帧, 尾帧] (单位:秒/60)

def callback(indata, frames, time, status):
    # 麦克风回调
    audio_chunk = indata[:, 0]  # 单声道
    result = model.generate(
        input=audio_chunk,
        chunk_size=chunk_size,
        is_final=False
    )
    if result and result[0]["text"]:
        print(result[0]["text"], end="", flush=True)

# 开始录音
with sd.InputStream(callback=callback, samplerate=16000, channels=1):
    input("按回车停止...")
```

流式识别的关键概念：
- 中间结果（partial）：实时显示，可能会修改
- 最终结果（final）：确认后不再修改
- VAD（语音活动检测）：检测何时开始/结束说话
""")

# ============================================================================
# 5. 长音频分段识别
# ============================================================================
print("\n--- 5. 长音频处理 ---")
print("""
长音频（>30分钟）的处理策略：

策略1：VAD 分段
  用 VAD 检测静音段 → 按句子/段落切分 → 逐段识别

策略2：固定窗口滑动
  每30秒切一段（前后有重叠）→ 逐段识别 → 合并去重

策略3：Whisper 内置分段
  Whisper 本身支持长音频，内部会自动分段

```python
# 策略1: VAD + 分段识别
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

audio = AudioSegment.from_wav("long_audio.wav")

# 检测非静音段
chunks = detect_nonsilent(audio, 
    min_silence_len=500,    # 静音阈值（毫秒）
    silence_thresh=-40      # 静音音量阈值（dB）
)

for i, (start, end) in enumerate(chunks):
    chunk = audio[start:end]
    chunk.export(f"chunk_{i}.wav", format="wav")
    result = whisper_model.transcribe(f"chunk_{i}.wav")
    print(f"[{start/1000:.1f}s-{end/1000:.1f}s] {result['text']}")
```
""")

# 模拟 VAD 分段
mock_vad_segments = [
    {"start": 0.0, "end": 3.5, "text": "大家好，欢迎来到今天的技术分享"},
    {"start": 4.2, "end": 8.1, "text": "今天我们要讲的主题是语音识别技术"},
    {"start": 9.0, "end": 14.5, "text": "首先来了解一下 Whisper 模型的基本原理"},
    {"start": 15.2, "end": 20.0, "text": "Whisper 是 OpenAI 在 2022 年发布的多语言语音识别模型"},
]

print("模拟 VAD 分段识别结果:")
for seg in mock_vad_segments:
    print(f"  [{seg['start']:5.1f}s - {seg['end']:5.1f}s] {seg['text']}")

# ============================================================================
# 6. 识别结果后处理
# ============================================================================
print("\n--- 6. 后处理 ---")
print("""
ASR 原始输出通常需要后处理：

1. 标点恢复
   原始: "大家好欢迎来到今天的分享今天讲语音识别"
   处理: "大家好，欢迎来到今天的分享。今天讲语音识别。"

2. 数字/日期格式化
   原始: "二零二四年三月十五号下午两点"
   处理: "2024年3月15号下午2点"

3. 敏感词过滤

4. 说话人标注
   [Speaker 1] 你好，请问有什么可以帮你？
   [Speaker 2] 我想咨询一下产品信息。

5. 生成字幕（SRT/VTT）
""")

def add_punctuation(text: str) -> str:
    """简单的标点恢复（实际用 LLM 或专用模型）"""
    # 简化版：基于关键词添加标点
    import re
    text = re.sub(r'(大家好)', r'\1，', text)
    text = re.sub(r'(欢迎)', r'\1', text)
    text = re.sub(r'(今天)', r'。\1', text)
    if not text.endswith(('。', '！', '？')):
        text += '。'
    return text

def generate_srt(segments: list) -> str:
    """生成 SRT 字幕"""
    srt = ""
    for i, seg in enumerate(segments, 1):
        start = format_srt_time(seg["start"])
        end = format_srt_time(seg["end"])
        srt += f"{i}\n{start} --> {end}\n{seg['text']}\n\n"
    return srt

def format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

srt_output = generate_srt(mock_vad_segments)
print("SRT 字幕输出:")
print(srt_output[:300])

# 清理
if os.path.exists(test_wav):
    os.unlink(test_wav)

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] Whisper 本地识别（加载/转写/时间戳）")
print("  [v] Whisper API 云端调用")
print("  [v] FunASR 中文识别（Paraformer）")
print("  [v] 流式语音识别")
print("  [v] 长音频 VAD 分段处理")
print("  [v] 后处理（标点/字幕/说话人）")
print("=" * 60)
print("\n下一课：03_tts_synthesis.py - 语音合成 TTS")
