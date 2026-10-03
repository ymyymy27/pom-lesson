import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：音频-语言模型（语音对话 / 音频理解）
==============================================================================

音频-语言模型 = 直接理解音频内容的 LLM

传统方案：音频 → ASR(转文字) → LLM(处理) → 丢失语调/情感/环境音
原生方案：音频 → 音频-语言模型 → 保留所有声音信息

本课内容：
1. 音频-语言模型原理
2. GPT-4o 音频能力
3. Qwen2-Audio 开源模型
4. 语音对话流水线
5. 音频场景理解
6. 音频+文本联合推理
==============================================================================
"""

import json
import numpy as np

print("=" * 60)
print("第3课：音频-语言模型")
print("=" * 60)

# ============================================================================
# 1. 音频-语言模型原理
# ============================================================================
print("\n--- 1. 原理 ---")
print("""
音频-语言模型的架构：

  音频波形 → 音频编码器(Whisper/音频ViT) → 音频token → LLM → 文本

与纯 ASR 的区别：
  ASR:  音频 → 文字（只提取语言内容）
  ALM:  音频 → 理解（语言+语调+情感+环境+音乐+...）

GPT-4o 能理解的音频信息：
  ✅ 语言内容（说了什么）
  ✅ 语调语气（开心/生气/犹豫/...）
  ✅ 说话人特征（性别/年龄/口音）
  ✅ 背景声音（音乐/噪音/自然声）
  ✅ 多人对话（区分不同说话人）
  ✅ 音乐内容（乐器/节奏/风格）

Qwen2-Audio 能理解的音频信息：
  ✅ 多语言语音
  ✅ 环境声音分类
  ✅ 音乐分析
  ✅ 声音事件检测
""")

# ============================================================================
# 2. GPT-4o 音频能力
# ============================================================================
print("\n--- 2. GPT-4o 音频 ---")
print("""
GPT-4o 的音频输入（通过 Realtime API 或 Audio API）：

```python
from openai import OpenAI
import base64

client = OpenAI()

# 音频文件 → Base64
with open("speech.wav", "rb") as f:
    audio_b64 = base64.b64encode(f.read()).decode()

# GPT-4o-audio-preview 模型
response = client.chat.completions.create(
    model="gpt-4o-audio-preview",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "分析这段音频的内容和说话人的情感"},
            {"type": "input_audio", "input_audio": {
                "data": audio_b64,
                "format": "wav"  # wav/mp3
            }}
        ]
    }]
)

print(response.choices[0].message.content)
```

GPT-4o 音频输出（生成语音回复）：
```python
response = client.chat.completions.create(
    model="gpt-4o-audio-preview",
    modalities=["text", "audio"],  # 同时输出文本和音频
    audio={"voice": "alloy", "format": "wav"},
    messages=[{"role": "user", "content": "用欢快的语气说：今天天气真好！"}]
)

# 获取音频回复
audio_data = base64.b64decode(response.choices[0].message.audio.data)
with open("response.wav", "wb") as f:
    f.write(audio_data)

# 同时获取文本
print(response.choices[0].message.audio.transcript)
```
""")

# ============================================================================
# 3. Qwen2-Audio
# ============================================================================
print("\n--- 3. Qwen2-Audio ---")
print("""
Qwen2-Audio 是阿里开源的音频-语言模型。
可以理解语音、音乐、环境声音。

```python
from transformers import Qwen2AudioForConditionalGeneration, AutoProcessor
import librosa

# 加载模型
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-Audio-7B-Instruct")
model = Qwen2AudioForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-Audio-7B-Instruct",
    torch_dtype=torch.float16,
).to("cuda")

# 加载音频
audio, sr = librosa.load("audio.wav", sr=processor.feature_extractor.sampling_rate)

# 构建多模态消息
messages = [{
    "role": "user",
    "content": [
        {"type": "audio", "audio_url": "audio.wav"},
        {"type": "text", "text": "这段音频说了什么？分析说话人的情感。"}
    ]
}]

# 处理
text = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
inputs = processor(text=text, audios=[audio], return_tensors="pt").to("cuda")

output_ids = model.generate(**inputs, max_new_tokens=256)
response = processor.batch_decode(output_ids, skip_special_tokens=True)[0]
print(response)
```

Qwen2-Audio 的独特能力：
  "这段音频中有哪些声音？"
  → "背景中有鸟叫声和流水声，一个女性在用普通话说话。"

  "分析这段音乐的风格"
  → "这是一首古典钢琴曲，节奏较慢，C大调，有肖邦的风格。"
""")

# ============================================================================
# 4. 语音对话流水线
# ============================================================================
print("\n--- 4. 语音对话流水线 ---")
print("""
三种语音对话方案：

方案1: 拼接式（ASR + LLM + TTS）
  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐
  │ 语音  │ →  │Whisper│ →  │ LLM  │ →  │ TTS  │ → 语音
  │ 输入  │    │ ASR  │    │ 对话 │    │ 合成 │
  └──────┘    └──────┘    └──────┘    └──────┘
  延迟: ~5秒  信息损失: 高  成本: 中等

方案2: 半原生（Audio LLM + TTS）
  ┌──────┐    ┌─────────────┐    ┌──────┐
  │ 语音  │ →  │ GPT-4o-audio│ →  │ TTS  │ → 语音
  │ 输入  │    │ (理解音频)  │    │ 合成 │
  └──────┘    └─────────────┘    └──────┘
  延迟: ~3秒  信息损失: 低  成本: 高

方案3: 全原生（GPT-4o Realtime）
  ┌──────┐    ┌─────────────────┐
  │ 语音  │ ←→ │ GPT-4o Realtime │ → 语音
  │ 输入  │    │ (端到端)        │
  └──────┘    └─────────────────┘
  延迟: ~0.3秒  信息损失: 无  成本: 最高
""")

# 模拟语音对话流水线
class VoiceDialoguePipeline:
    """语音对话流水线"""

    def __init__(self, mode: str = "拼接式"):
        self.mode = mode
        self.history = []

    def process(self, user_input: str) -> dict:
        """处理用户输入（文字模拟语音）"""
        # ASR 阶段
        asr_result = {"text": user_input, "language": "zh", "emotion": "neutral"}

        # LLM 对话
        self.history.append({"role": "user", "content": user_input})
        reply = f"[{self.mode}回复] 收到你的问题：{user_input[:30]}。让我为你解答。"

        self.history.append({"role": "assistant", "content": reply})

        # TTS 信息
        tts_info = {"text": reply, "voice": "zh-CN-XiaoxiaoNeural"}

        return {
            "mode": self.mode,
            "asr": asr_result,
            "reply": reply,
            "tts": tts_info,
        }

pipeline = VoiceDialoguePipeline("拼接式")
print("\n语音对话演示:")
for q in ["今天天气怎么样？", "给我讲个故事", "你能听出我的情绪吗？"]:
    result = pipeline.process(q)
    print(f"  🎤 {q}")
    print(f"  🤖 {result['reply'][:60]}...")

# ============================================================================
# 5. 音频场景理解
# ============================================================================
print("\n\n--- 5. 音频场景理解 ---")
print("""
超越语音识别：理解音频中的"场景"

任务类型：
┌─────────────────────┬──────────────────────────────────┐
│  任务                │  示例                             │
├─────────────────────┼──────────────────────────────────┤
│  声音事件检测        │  "有玻璃碎裂声和汽车喇叭声"     │
│  声音场景分类        │  "这是咖啡厅的环境"             │
│  音乐分析            │  "G大调，120BPM，摇滚风格"      │
│  说话人情感          │  "说话人听起来焦虑且犹豫"       │
│  多说话人识别        │  "有3个人在对话"                │
│  声音异常检测        │  "检测到异常的机器运转声"       │
└─────────────────────┴──────────────────────────────────┘

Prompt 模板：
```python
prompts = {
    "场景分析": "描述这段音频中的所有声音元素和场景",
    "情感识别": "分析说话人的情绪状态",
    "音乐分析": "分析这段音乐的风格、节奏、乐器",
    "会议记录": "将这段会议录音转为会议纪要，标注每个说话人",
    "质检":     "这段机器运转声中是否有异常",
}
```
""")

# ============================================================================
# 6. 音频+文本联合推理
# ============================================================================
print("\n--- 6. 音频+文本联合 ---")
print("""
结合音频和文本上下文进行推理：

场景1: 客服质量分析
  音频(客服通话) + 文本(质检标准) → 评分和建议

  ```python
  response = audio_llm.invoke([
      SystemMessage("你是客服质量分析师，根据以下标准评分：\\n"
                    "1. 礼貌用语(20分) 2. 问题解决(30分) 3. 响应速度(20分)..."),
      HumanMessage(content=[
          {"type": "input_audio", "input_audio": {"data": call_audio_b64}},
          {"type": "text", "text": "请分析这通客服电话的质量"}
      ])
  ])
  ```

场景2: 播客/访谈分析
  音频(对话) + 文本(话题列表) → 结构化摘要

场景3: 教学评估
  音频(学生发音) + 文本(正确发音标准) → 纠正建议

场景4: 多语言翻译
  音频(源语言) + 文本(目标语言指令) → 翻译结果（保留情感语调描述）
""")

# 模拟音频+文本分析
print("音频+文本联合推理演示:")
scenarios = [
    {
        "name": "客服质量分析",
        "audio_desc": "客服接听电话，语气友好",
        "text_context": "质检标准：礼貌20分/解决30分/效率20分/专业30分",
        "result": "总分 85/100。礼貌用语良好(18/20)，问题解决及时(28/30)..."
    },
    {
        "name": "会议纪要",
        "audio_desc": "3人讨论产品需求",
        "text_context": "会议主题：Q3产品规划",
        "result": "参会人：A、B、C。主要议题：1)新功能优先级 2)上线时间..."
    },
]
for s in scenarios:
    print(f"\n  [{s['name']}]")
    print(f"  音频: {s['audio_desc']}")
    print(f"  文本: {s['text_context']}")
    print(f"  分析: {s['result'][:60]}...")

print("\n" + "=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] 音频-语言模型原理")
print("  [v] GPT-4o 音频能力（输入+输出）")
print("  [v] Qwen2-Audio 开源模型")
print("  [v] 三种语音对话方案对比")
print("  [v] 音频场景理解（声音事件/情感/音乐）")
print("  [v] 音频+文本联合推理")
print("=" * 60)
print("\n下一课：04_multimodal_rag.py - 多模态 RAG")
