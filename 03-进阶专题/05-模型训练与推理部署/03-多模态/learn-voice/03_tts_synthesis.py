import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：语音合成 TTS（edge-tts / OpenAI TTS / VITS）
==============================================================================

TTS = Text-to-Speech（文字转语音）

本课学习三种主流 TTS 方案：
1. edge-tts：微软免费在线TTS（推荐入门）
2. OpenAI TTS API：高质量6种声音
3. 开源模型（VITS/ChatTTS）概览

本课内容：
1. edge-tts 快速上手
2. OpenAI TTS API
3. SSML 语音控制
4. 开源 TTS 模型
5. 语音参数调节
6. 批量文本转语音
==============================================================================
"""

import json
import os
import tempfile
import asyncio

print("=" * 60)
print("第3课：语音合成 TTS")
print("=" * 60)

# ============================================================================
# 1. edge-tts 快速上手
# ============================================================================
print("\n--- 1. edge-tts ---")
print("""
edge-tts 使用微软 Edge 浏览器的在线 TTS 服务。
免费、高质量、支持中文。

安装：pip install edge-tts

```python
import edge_tts
import asyncio

async def text_to_speech(text, output_file, voice="zh-CN-XiaoxiaoNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

# 运行
asyncio.run(text_to_speech("你好，欢迎学习语音合成！", "output.mp3"))
```

常用中文声音：
┌─────────────────────────┬────────┬──────────────────────┐
│  声音ID                  │  性别  │  特点                 │
├─────────────────────────┼────────┼──────────────────────┤
│  zh-CN-XiaoxiaoNeural   │  女    │  温柔甜美（最常用）   │
│  zh-CN-XiaoYiNeural     │  女    │  活泼可爱             │
│  zh-CN-YunxiNeural      │  男    │  年轻阳光             │
│  zh-CN-YunjianNeural    │  男    │  沉稳播音             │
│  zh-CN-XiaochenNeural   │  女    │  知性温和             │
│  zh-CN-YunyangNeural    │  男    │  新闻播报             │
│  zh-TW-HsiaoChenNeural  │  女    │  台湾口音             │
│  zh-HK-HiuMaanNeural    │  女    │  粤语                 │
└─────────────────────────┴────────┴──────────────────────┘

英文声音：
  en-US-JennyNeural (女)  en-US-GuyNeural (男)
  en-GB-SoniaNeural (女)  en-GB-RyanNeural (男)
""")

# 实际测试 edge-tts
output_dir = tempfile.mkdtemp(prefix="tts_")

try:
    import edge_tts

    async def demo_edge_tts():
        text = "你好，我是小晓，欢迎学习语音合成技术！"
        output = os.path.join(output_dir, "edge_tts_demo.mp3")
        communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
        await communicate.save(output)
        size = os.path.getsize(output)
        print(f"  ✅ 生成成功: {output}")
        print(f"     大小: {size/1024:.1f} KB")
        return output

    result = asyncio.run(demo_edge_tts())

    # 列出可用声音
    async def list_voices():
        voices = await edge_tts.list_voices()
        zh_voices = [v for v in voices if v["Locale"].startswith("zh-")]
        return zh_voices

    zh_voices = asyncio.run(list_voices())
    print(f"\n  可用中文声音: {len(zh_voices)} 个")
    for v in zh_voices[:5]:
        print(f"    {v['ShortName']:30s} {v['Gender']:8s} {v['Locale']}")

except ImportError:
    print("  edge-tts 未安装 (pip install edge-tts)")
except Exception as e:
    print(f"  edge-tts 错误: {e}")

# ============================================================================
# 2. OpenAI TTS API
# ============================================================================
print("\n--- 2. OpenAI TTS API ---")
print("""
OpenAI 提供高质量 TTS API。

```python
from openai import OpenAI
client = OpenAI()

# 基本使用
response = client.audio.speech.create(
    model="tts-1",         # tts-1（快）或 tts-1-hd（高质量）
    voice="alloy",         # 声音选择
    input="Hello, this is a test of OpenAI TTS.",
    speed=1.0,             # 语速 0.25-4.0
    response_format="mp3", # mp3/opus/aac/flac/wav/pcm
)

# 保存文件
response.stream_to_file("output.mp3")

# 流式输出（实时播放）
with client.audio.speech.with_streaming_response.create(
    model="tts-1",
    voice="nova",
    input="Streaming TTS test",
) as response:
    response.stream_to_file("stream_output.mp3")
```

6种声音：
┌──────────┬──────────────────────────────────┐
│  Voice   │  特点                             │
├──────────┼──────────────────────────────────┤
│  alloy   │  中性、平衡                       │
│  echo    │  男声、沉稳                       │
│  fable   │  英式、温暖                       │
│  onyx    │  男声、深沉有力                   │
│  nova    │  女声、年轻活泼                   │
│  shimmer │  女声、温柔清亮                   │
└──────────┴──────────────────────────────────┘

模型对比：
- tts-1: 延迟低，适合实时（$15/1M字符）
- tts-1-hd: 质量高，适合预生成（$30/1M字符）
""")

# ============================================================================
# 3. SSML 语音控制
# ============================================================================
print("\n--- 3. SSML 语音控制 ---")
print("""
SSML（Speech Synthesis Markup Language）= 语音合成标记语言
精细控制语音的停顿、语调、语速、音量等。

Azure TTS 和部分 edge-tts 支持 SSML。

```xml
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
       xml:lang="zh-CN">
    <voice name="zh-CN-XiaoxiaoNeural">
        <!-- 停顿 -->
        你好！<break time="500ms"/> 欢迎来到语音课程。
        
        <!-- 语速控制 -->
        <prosody rate="slow">这句话说得慢一些。</prosody>
        <prosody rate="fast">这句话说得快一些。</prosody>
        
        <!-- 音量控制 -->
        <prosody volume="loud">大声说！</prosody>
        <prosody volume="soft">小声说。</prosody>
        
        <!-- 音调控制 -->
        <prosody pitch="high">高音调。</prosody>
        <prosody pitch="low">低音调。</prosody>
        
        <!-- 强调 -->
        这是一个<emphasis level="strong">非常重要</emphasis>的功能。
        
        <!-- 数字读法 -->
        <say-as interpret-as="digits">12345</say-as>  <!-- 一二三四五 -->
        <say-as interpret-as="cardinal">12345</say-as> <!-- 一万两千三百四十五 -->
    </voice>
</speak>
```

edge-tts SSML 使用：
```python
import edge_tts

ssml = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
<voice name="zh-CN-XiaoxiaoNeural">
    你好！<break time="300ms"/>今天天气<prosody rate="slow">真不错</prosody>。
</voice>
</speak>'''

communicate = edge_tts.Communicate(ssml, voice="zh-CN-XiaoxiaoNeural")
await communicate.save("ssml_output.mp3")
```
""")

# ============================================================================
# 4. 开源 TTS 模型
# ============================================================================
print("\n--- 4. 开源 TTS 模型 ---")
print("""
┌─────────────────┬──────────────────────────────────────────┐
│  模型            │  特点                                    │
├─────────────────┼──────────────────────────────────────────┤
│  ChatTTS        │  最自然的中文TTS，支持笑声/停顿/语气     │
│                 │  https://github.com/2noise/ChatTTS        │
│                 │  需要GPU，适合预生成                      │
├─────────────────┼──────────────────────────────────────────┤
│  CosyVoice      │  阿里开源，支持声音克隆+多语言           │
│                 │  https://github.com/FunAudioLLM/CosyVoice│
│                 │  中文质量极高                             │
├─────────────────┼──────────────────────────────────────────┤
│  FishSpeech     │  轻量快速TTS，支持多语言                 │
│                 │  https://github.com/fishaudio/fish-speech │
│                 │  推理速度快                               │
├─────────────────┼──────────────────────────────────────────┤
│  VITS           │  经典端到端TTS                            │
│                 │  学术经典，社区模型丰富                   │
│                 │  适合学习TTS原理                          │
├─────────────────┼──────────────────────────────────────────┤
│  Bark           │  Suno AI，支持多语言+笑声+音乐           │
│                 │  pip install suno-bark                    │
│                 │  英文好，中文一般                         │
└─────────────────┴──────────────────────────────────────────┘

ChatTTS 使用示例：
```python
import ChatTTS
import torch

chat = ChatTTS.Chat()
chat.load(compile=False)  # 加载模型

# 随机说话人
rand_spk = chat.sample_random_speaker()

params = ChatTTS.Chat.InferCodeParams(
    spk_emb=rand_spk,
    temperature=0.3,
)

wavs = chat.infer(["你好啊，今天心情怎么样？"], params_infer_code=params)
# wavs[0] 是 numpy 数组
```
""")

# ============================================================================
# 5. 语音参数调节
# ============================================================================
print("\n--- 5. 语音参数 ---")
print("""
TTS 可调节的参数：

┌──────────────┬──────────────┬──────────────────────────┐
│  参数        │  范围         │  说明                     │
├──────────────┼──────────────┼──────────────────────────┤
│  语速(rate)  │  0.25x~4.0x  │  正常=1.0                │
│  音调(pitch) │  -50%~+50%   │  控制声音高低             │
│  音量(volume)│  0%~200%     │  控制声音大小             │
│  停顿(break) │  0~5000ms    │  句间/段间停顿            │
│  情感(style) │  多种预设    │  如：开心/悲伤/生气       │
│  角色(role)  │  多种预设    │  如：新闻播报/讲故事      │
└──────────────┴──────────────┴──────────────────────────┘

Azure/edge-tts 情感风格（部分声音支持）：
  cheerful（开心）  sad（悲伤）  angry（生气）
  fearful（害怕）   gentle（温柔）  serious（严肃）
  
```python
# edge-tts 调节语速和音调
communicate = edge_tts.Communicate(
    text,
    voice="zh-CN-XiaoxiaoNeural",
    rate="+20%",    # 语速加快20%
    volume="-10%",  # 音量降低10%
    pitch="+5Hz",   # 音调提高
)
```
""")

# 演示不同参数
try:
    import edge_tts

    async def demo_params():
        text = "语音合成可以通过参数控制效果。"
        configs = [
            ("normal", {}),
            ("fast", {"rate": "+50%"}),
            ("slow", {"rate": "-30%"}),
            ("loud", {"volume": "+30%"}),
        ]
        for name, params in configs:
            output = os.path.join(output_dir, f"param_{name}.mp3")
            comm = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural", **params)
            await comm.save(output)
            size = os.path.getsize(output)
            print(f"  {name:8s}: {size/1024:.1f} KB  {params or '(默认)'}")

    asyncio.run(demo_params())

except ImportError:
    print("  edge-tts 未安装")
except Exception as e:
    print(f"  错误: {e}")

# ============================================================================
# 6. 批量文本转语音
# ============================================================================
print("\n--- 6. 批量转语音 ---")
print("""
将长文本或多段文本批量转为语音。

```python
import edge_tts, asyncio

async def batch_tts(texts: list, voice="zh-CN-XiaoxiaoNeural"):
    for i, text in enumerate(texts):
        output = f"output_{i:03d}.mp3"
        comm = edge_tts.Communicate(text, voice)
        await comm.save(output)
        print(f"  [{i+1}/{len(texts)}] {output}")

# 长文本自动分段
def split_text(text, max_len=200):
    sentences = text.replace('。', '。\\n').replace('！', '！\\n').split('\\n')
    chunks = []
    current = ""
    for s in sentences:
        if len(current) + len(s) > max_len:
            if current:
                chunks.append(current.strip())
            current = s
        else:
            current += s
    if current:
        chunks.append(current.strip())
    return chunks

# 使用
long_text = "这是一段很长的文本..." * 10
chunks = split_text(long_text)
asyncio.run(batch_tts(chunks))
```

有声书/播客制作流程：
  文本 → 分段 → TTS → 拼接 → 后处理 → MP3
""")

# 清理
import shutil
shutil.rmtree(output_dir, ignore_errors=True)

print("\n" + "=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] edge-tts 快速上手（免费中文TTS）")
print("  [v] OpenAI TTS API（6种声音）")
print("  [v] SSML 语音控制（停顿/语速/音调）")
print("  [v] 开源 TTS 模型概览（ChatTTS/CosyVoice）")
print("  [v] 语音参数调节")
print("  [v] 批量文本转语音")
print("=" * 60)
print("\n下一课：04_voice_cloning.py - 声音克隆")
