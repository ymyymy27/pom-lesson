import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第4课：声音克隆与个性化
==============================================================================

声音克隆 = 用少量参考音频复制某人的声音特征，
然后让 AI 用这个声音说任何话。

主流方案：
1. GPT-SoVITS：5秒参考音频即可克隆（中文最佳）
2. CosyVoice：阿里开源，高质量克隆
3. VALL-E / Bark：零样本克隆（英文）
4. ElevenLabs：商用云服务（英文最佳）

本课内容：
1. 声音克隆原理
2. GPT-SoVITS 使用
3. CosyVoice 使用
4. ElevenLabs 云服务
5. 声音克隆的伦理与安全
6. 个性化语音助手
==============================================================================
"""

import json

print("=" * 60)
print("第4课：声音克隆与个性化")
print("=" * 60)

# ============================================================================
# 1. 声音克隆原理
# ============================================================================
print("\n--- 1. 声音克隆原理 ---")
print("""
声音克隆的核心流程：

  参考音频（3-30秒）→ 提取声音特征（音色/语调/节奏）→ 声音嵌入向量
                                                            ↓
  待合成文本 → TTS 模型 + 声音嵌入 → 目标声音的语音

技术路线：
┌────────────────────────────────────────────────────────────┐
│  1. Speaker Embedding 方式（经典）                          │
│     参考音频 → Speaker Encoder → 说话人向量                │
│     文本 + 说话人向量 → TTS 模型 → 语音                    │
│     优点: 快速, 适合固定说话人                              │
│     缺点: 需要较多参考音频（分钟级）                        │
│                                                            │
│  2. In-Context Learning 方式（新一代）                      │
│     参考音频作为"上下文"直接输入模型                        │
│     模型在推理时"学会"目标声音                              │
│     优点: 只需几秒参考音频                                  │
│     缺点: 推理较慢                                          │
│     代表: GPT-SoVITS, CosyVoice, VALL-E                   │
│                                                            │
│  3. Fine-tuning 方式（最高质量）                            │
│     用目标说话人数据微调模型                                │
│     优点: 质量最高, 个性化最好                              │
│     缺点: 需要大量数据（30分钟+）, 训练时间长              │
└────────────────────────────────────────────────────────────┘
""")

# ============================================================================
# 2. GPT-SoVITS
# ============================================================================
print("\n--- 2. GPT-SoVITS ---")
print("""
GPT-SoVITS 是目前中文声音克隆最好的开源方案。
只需 5 秒参考音频即可克隆声音！

项目地址：https://github.com/RVC-Boss/GPT-SoVITS

安装和使用：
```bash
# 1. 克隆仓库
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS

# 2. 安装依赖
pip install -r requirements.txt

# 3. 下载预训练模型（自动下载或手动）
# 放到 GPT_SoVITS/pretrained_models/ 下

# 4. 启动 WebUI
python webui.py
```

WebUI 使用流程：

  Step 1: 上传参考音频（5-30秒，清晰的人声）
  Step 2: 输入参考音频的文字内容
  Step 3: 输入要合成的新文本
  Step 4: 点击生成 → 得到克隆声音的语音

API 调用：
```python
import httpx

# GPT-SoVITS 提供 HTTP API
response = httpx.post("http://localhost:9880/tts", json={
    "text": "你好，我是用声音克隆生成的语音",
    "text_lang": "zh",
    "ref_audio_path": "reference.wav",
    "prompt_text": "参考音频的文字内容",
    "prompt_lang": "zh",
})

with open("cloned_output.wav", "wb") as f:
    f.write(response.content)
```

效果评价：
- 中文克隆质量: ★★★★★（最佳）
- 少样本能力: 5秒即可（极好）
- 推理速度: 中等（GPU推荐）
- 情感保持: ★★★★
""")

# ============================================================================
# 3. CosyVoice
# ============================================================================
print("\n--- 3. CosyVoice ---")
print("""
CosyVoice 是阿里通义实验室开源的语音合成模型。
支持声音克隆、跨语言合成、情感控制。

项目地址：https://github.com/FunAudioLLM/CosyVoice

```python
from cosyvoice.cli.cosyvoice import CosyVoice
from cosyvoice.utils.file_utils import load_wav
import torchaudio

# 加载模型
cosyvoice = CosyVoice("pretrained_models/CosyVoice-300M")

# 1. 零样本克隆（提供参考音频）
prompt_speech = load_wav("reference.wav", 16000)
output = cosyvoice.inference_zero_shot(
    tts_text="你好，这是声音克隆测试",
    prompt_text="参考音频的文字",
    prompt_speech_16k=prompt_speech,
)
torchaudio.save("output.wav", output["tts_speech"], 22050)

# 2. 跨语言克隆（用中文声音说英文）
output = cosyvoice.inference_cross_lingual(
    tts_text="Hello, this is a cross-lingual test.",
    prompt_speech_16k=prompt_speech,
)

# 3. 指令控制
output = cosyvoice.inference_instruct(
    tts_text="今天天气真好",
    spk_id="中文女",
    instruct_text="用开心的语气说",  # 情感控制指令
)
```

CosyVoice 特色：
- 零样本克隆 + 跨语言
- 自然语言指令控制情感/风格
- 支持中/英/日/粤/韩
- 流式输出
""")

# ============================================================================
# 4. ElevenLabs 云服务
# ============================================================================
print("\n--- 4. ElevenLabs ---")
print("""
ElevenLabs 是商用声音克隆云服务（英文最佳）。

```python
from elevenlabs import generate, clone, set_api_key

set_api_key("your-api-key")

# 1. 使用预设声音
audio = generate(
    text="Hello! This is ElevenLabs TTS.",
    voice="Rachel",
    model="eleven_monolingual_v1"
)

# 2. 克隆声音
voice = clone(
    name="my_voice",
    files=["sample1.wav", "sample2.wav"],  # 上传参考音频
)

audio = generate(
    text="This is my cloned voice!",
    voice=voice,
)

# 3. 保存
with open("output.mp3", "wb") as f:
    f.write(audio)
```

特点：
- 英文质量极高
- API 简单易用
- 有免费额度（每月 10000 字符）
- 中文支持一般
""")

# ============================================================================
# 5. 伦理与安全
# ============================================================================
print("\n--- 5. 伦理与安全 ---")
print("""
⚠️ 声音克隆技术的伦理风险

┌──────────────────────────────────────────────────────────┐
│  风险类型       │  说明                                   │
├──────────────────────────────────────────────────────────┤
│  身份伪造       │  冒充他人声音进行诈骗                   │
│  虚假内容       │  伪造名人/政客的语音                    │
│  隐私侵犯       │  未经授权使用他人声音                   │
│  版权问题       │  声音的知识产权归属                     │
└──────────────────────────────────────────────────────────┘

安全措施：
1. 知情同意：使用他人声音前必须获得授权
2. 水印标记：在生成的语音中嵌入不可见水印
3. 检测技术：开发 AI 语音鉴伪工具
4. 法律法规：多国已立法限制深度伪造

开发者守则：
✅ 只克隆自己的声音或已授权的声音
✅ 标注"AI 生成"标签
✅ 不用于欺骗、诈骗、冒充
✅ 遵守当地法律法规
❌ 不未经同意克隆他人声音
❌ 不生成虚假的名人/政客语音
""")

# ============================================================================
# 6. 个性化语音助手
# ============================================================================
print("\n--- 6. 个性化语音助手 ---")
print("""
结合 ASR + LLM + TTS(克隆声音) 构建个性化语音助手：

  用户语音 → ASR(Whisper) → 文字
                              ↓
                           LLM(对话)
                              ↓
  播放 ← TTS(克隆声音) ← 回复文字

```python
import whisper
import edge_tts  # 或 GPT-SoVITS
from openai import OpenAI

# ASR
whisper_model = whisper.load_model("small")
result = whisper_model.transcribe("user_input.wav")
user_text = result["text"]

# LLM
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
response = client.chat.completions.create(
    model="qwen2.5:7b",
    messages=[
        {"role": "system", "content": "你是一个友好的助手"},
        {"role": "user", "content": user_text}
    ]
)
reply = response.choices[0].message.content

# TTS（用克隆的声音）
# GPT-SoVITS API
import httpx
audio = httpx.post("http://localhost:9880/tts", json={
    "text": reply,
    "text_lang": "zh",
    "ref_audio_path": "my_voice_ref.wav",
    "prompt_text": "参考音频文字",
}).content
```
""")

print("\n" + "=" * 60)
print("[完成] 第4课完成！你已经学会了：")
print("  [v] 声音克隆三种技术路线")
print("  [v] GPT-SoVITS（5秒克隆，中文最佳）")
print("  [v] CosyVoice（跨语言+情感控制）")
print("  [v] ElevenLabs 云服务")
print("  [v] 伦理与安全准则")
print("  [v] 个性化语音助手架构")
print("=" * 60)
print("\n下一课：05_realtime_voice.py - 实时语音交互")
