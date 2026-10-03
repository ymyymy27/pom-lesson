> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 语音与 TTS

## 学习目标

- 掌握语音识别（ASR）和语音合成（TTS）技术
- 学会使用 Whisper、OpenAI TTS 等工具
- 实现语音交互 AI 应用

## 1. 语音识别（ASR）

### OpenAI Whisper

```python
from openai import OpenAI

client = OpenAI()

# 语音转文字
with open("audio.mp3", "rb") as f:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=f,
        language="zh",               # 指定语言
        response_format="verbose_json",  # 包含时间戳
    )

print(transcript.text)

# 带时间戳
for segment in transcript.segments:
    print(f"[{segment['start']:.1f}s - {segment['end']:.1f}s] {segment['text']}")
```

### 本地 Whisper

```bash
pip install openai-whisper
```

```python
import whisper

model = whisper.load_model("base")  # tiny/base/small/medium/large
result = model.transcribe("audio.mp3", language="zh")

print(result["text"])
for segment in result["segments"]:
    print(f"[{segment['start']:.1f}s] {segment['text']}")
```

### 实时语音识别

```python
# 使用 faster-whisper（更快的推理）
# pip install faster-whisper
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")
segments, info = model.transcribe("audio.mp3", language="zh")

for segment in segments:
    print(f"[{segment.start:.2f}s → {segment.end:.2f}s] {segment.text}")
```

## 2. 语音合成（TTS）

### OpenAI TTS

```python
from openai import OpenAI
from pathlib import Path

client = OpenAI()

# 生成语音
response = client.audio.speech.create(
    model="tts-1",           # tts-1 或 tts-1-hd
    voice="alloy",           # alloy/echo/fable/onyx/nova/shimmer
    input="你好，我是你的 AI 助手。今天有什么可以帮你的吗？",
    speed=1.0,               # 0.25 - 4.0
)

# 保存文件
speech_file = Path("output.mp3")
response.stream_to_file(speech_file)
```

### 开源 TTS（Edge TTS）

```bash
pip install edge-tts
```

```python
import edge_tts
import asyncio

async def text_to_speech(text: str, output_file: str, voice="zh-CN-XiaoxiaoNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

# 运行
asyncio.run(text_to_speech("你好世界", "output.mp3"))

# 可用中文语音
# zh-CN-XiaoxiaoNeural（女声）
# zh-CN-YunxiNeural（男声）
# zh-CN-YunyangNeural（新闻男声）
```

## 3. 语音对话 AI

```python
import whisper
import edge_tts
from openai import OpenAI
import asyncio
import tempfile

class VoiceAssistant:
    def __init__(self):
        self.whisper_model = whisper.load_model("base")
        self.llm_client = OpenAI()
        self.messages = [
            {"role": "system", "content": "你是一个友好的语音助手，回复简洁。"}
        ]

    def listen(self, audio_path: str) -> str:
        """语音转文字"""
        result = self.whisper_model.transcribe(audio_path, language="zh")
        return result["text"]

    def think(self, text: str) -> str:
        """LLM 处理"""
        self.messages.append({"role": "user", "content": text})
        response = self.llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.messages,
        )
        reply = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    async def speak(self, text: str, output_path: str):
        """文字转语音"""
        communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
        await communicate.save(output_path)

    async def process(self, audio_input: str) -> str:
        """完整流程：听 → 想 → 说"""
        user_text = self.listen(audio_input)
        print(f"用户: {user_text}")

        reply_text = self.think(user_text)
        print(f"助手: {reply_text}")

        output_path = tempfile.mktemp(suffix=".mp3")
        await self.speak(reply_text, output_path)
        return output_path

assistant = VoiceAssistant()
# output = asyncio.run(assistant.process("input_audio.mp3"))
```

## 4. 音频分析

```python
# 使用 librosa 分析音频特征
# pip install librosa soundfile
import librosa
import numpy as np

# 加载音频
y, sr = librosa.load("audio.wav", sr=16000)

# 基本信息
duration = librosa.get_duration(y=y, sr=sr)
print(f"时长: {duration:.1f}s, 采样率: {sr}")

# 静音检测
intervals = librosa.effects.split(y, top_db=30)
print(f"语音片段数: {len(intervals)}")
```

## 练习

1. 用 Whisper 实现一个会议录音转文字工具
2. 用 TTS 将一篇文章转为有声读物
3. 构建一个语音对话 AI（录音 → 识别 → LLM → TTS → 播放）
4. 实现一个语音翻译工具：中文语音 → 英文语音

## 下一节

→ [03-图像生成与多模态应用](03-图像生成与多模态应用.md)
