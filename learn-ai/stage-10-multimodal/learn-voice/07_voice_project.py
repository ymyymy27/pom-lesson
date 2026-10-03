import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第7课：完整项目 - 语音对话助手
==============================================================================

整合前6课知识，构建完整的语音对话助手：

  用户说话 → ASR(语音转文字) → LLM(对话) → TTS(文字转语音) → 播放

功能：
1. 语音输入（Whisper ASR）
2. 智能对话（Ollama LLM）
3. 语音输出（edge-tts）
4. 情感分析
5. 多轮对话记忆
6. 语音指令（播放/暂停/切换声音）
==============================================================================
"""

import json
import os
import tempfile
import asyncio
import numpy as np
from datetime import datetime

print("=" * 60)
print("第7课：完整项目 - 语音对话助手")
print("=" * 60)

# ============================================================================
# 1. 模块定义
# ============================================================================
print("\n--- 1. 定义核心模块 ---")

import httpx

OLLAMA_URL = "http://localhost:11434"
LLM_MODEL = "qwen2.5:7b"

# ----- ASR 模块 -----
class ASRModule:
    """语音识别模块"""

    def __init__(self, model_name: str = "tiny"):
        self.model_name = model_name
        self.model = None

    def load(self):
        try:
            import whisper
            self.model = whisper.load_model(self.model_name)
            return True
        except ImportError:
            print("    Whisper 未安装，使用模拟模式")
            return False

    def transcribe(self, audio_path: str = None, audio_array: np.ndarray = None) -> dict:
        if self.model and audio_path:
            result = self.model.transcribe(audio_path, language="zh")
            return {
                "text": result["text"],
                "language": result.get("language", "zh"),
                "segments": result.get("segments", []),
            }
        # 模拟模式
        return {"text": "[模拟输入] 你好，今天天气怎么样？", "language": "zh", "segments": []}

    def transcribe_text(self, text: str) -> dict:
        """文字模拟语音输入（用于测试）"""
        return {"text": text, "language": "zh", "segments": []}

# ----- TTS 模块 -----
class TTSModule:
    """语音合成模块"""

    VOICES = {
        "小晓": "zh-CN-XiaoxiaoNeural",
        "云希": "zh-CN-YunxiNeural",
        "云健": "zh-CN-YunjianNeural",
        "小忆": "zh-CN-XiaoYiNeural",
    }

    def __init__(self, voice_name: str = "小晓"):
        self.voice_name = voice_name
        self.voice_id = self.VOICES.get(voice_name, "zh-CN-XiaoxiaoNeural")
        self.output_dir = tempfile.mkdtemp(prefix="voice_assistant_")

    def set_voice(self, voice_name: str):
        if voice_name in self.VOICES:
            self.voice_name = voice_name
            self.voice_id = self.VOICES[voice_name]
            return True
        return False

    def synthesize(self, text: str) -> str:
        """合成语音，返回文件路径"""
        try:
            import edge_tts
            output = os.path.join(self.output_dir, f"tts_{hash(text) % 100000}.mp3")

            async def _syn():
                comm = edge_tts.Communicate(text, self.voice_id)
                await comm.save(output)

            asyncio.run(_syn())
            return output
        except ImportError:
            return f"[模拟TTS] 使用 {self.voice_name} 合成: {text[:30]}..."
        except Exception as e:
            return f"[TTS错误] {e}"

    def list_voices(self) -> dict:
        return self.VOICES.copy()

# ----- LLM 模块 -----
class LLMModule:
    """对话模块"""

    def __init__(self, model: str = LLM_MODEL):
        self.model = model
        self.system_prompt = """你是"小智"，一个友好的语音助手。
回答要求：
1. 简洁（不超过3句话，适合语音播报）
2. 自然口语化
3. 中文回答"""

    def chat(self, messages: list) -> str:
        full_messages = [{"role": "system", "content": self.system_prompt}] + messages
        try:
            resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
                "model": self.model,
                "messages": full_messages,
                "stream": False,
            }, timeout=30.0)
            return resp.json().get("message", {}).get("content", "抱歉，我没有听清。")
        except:
            return "[模拟回答] 你好！今天天气不错，适合出门走走。"

# ----- 情感分析模块 -----
class EmotionModule:
    """简单情感分析"""

    EMOTION_KEYWORDS = {
        "开心": ["开心", "高兴", "快乐", "哈哈", "太好了", "棒", "赞"],
        "悲伤": ["难过", "伤心", "哭", "失望", "遗憾", "可惜"],
        "生气": ["生气", "愤怒", "烦", "讨厌", "气死", "什么鬼"],
        "焦虑": ["担心", "紧张", "害怕", "焦虑", "怎么办", "完了"],
    }

    def analyze(self, text: str) -> str:
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return emotion
        return "中性"

print("核心模块:")
print("  ✅ ASRModule (语音识别)")
print("  ✅ TTSModule (语音合成)")
print("  ✅ LLMModule (对话)")
print("  ✅ EmotionModule (情感分析)")

# ============================================================================
# 2. 语音助手引擎
# ============================================================================
print("\n--- 2. 构建语音助手 ---")

class VoiceAssistant:
    """语音对话助手"""

    def __init__(self):
        self.asr = ASRModule()
        self.tts = TTSModule()
        self.llm = LLMModule()
        self.emotion = EmotionModule()
        self.history = []          # 对话历史
        self.max_history = 20      # 最多保留轮数

    def process_text(self, user_text: str, verbose: bool = True) -> dict:
        """处理文字输入（核心流程）"""
        # 1. 语音指令检测
        cmd = self._check_command(user_text)
        if cmd:
            return cmd

        # 2. 情感分析
        emotion = self.emotion.analyze(user_text)
        if verbose:
            print(f"    情感: {emotion}")

        # 3. 构建对话消息
        self.history.append({"role": "user", "content": user_text})
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        # 4. LLM 对话
        reply = self.llm.chat(self.history)
        self.history.append({"role": "assistant", "content": reply})
        if verbose:
            print(f"    LLM: {reply[:80]}...")

        # 5. TTS 合成
        audio_path = self.tts.synthesize(reply)
        if verbose:
            print(f"    TTS: {str(audio_path)[:60]}...")

        return {
            "user_text": user_text,
            "emotion": emotion,
            "reply": reply,
            "audio_path": audio_path,
        }

    def process_audio(self, audio_path: str, verbose: bool = True) -> dict:
        """处理语音输入"""
        # ASR
        asr_result = self.asr.transcribe(audio_path)
        user_text = asr_result["text"]
        if verbose:
            print(f"    ASR: {user_text}")
        return self.process_text(user_text, verbose)

    def _check_command(self, text: str) -> dict:
        """检查语音指令"""
        if "切换声音" in text or "换个声音" in text:
            voices = list(self.tts.VOICES.keys())
            current = voices.index(self.tts.voice_name) if self.tts.voice_name in voices else 0
            next_voice = voices[(current + 1) % len(voices)]
            self.tts.set_voice(next_voice)
            return {"reply": f"好的，已切换为 {next_voice} 的声音", "command": "switch_voice"}

        if "清除记忆" in text or "重新开始" in text:
            self.history.clear()
            return {"reply": "好的，已清除对话记忆", "command": "clear_history"}

        if "当前声音" in text or "你是谁" in text:
            return {
                "reply": f"我是小智，当前使用 {self.tts.voice_name} 的声音",
                "command": "info",
            }

        return None

    def get_stats(self) -> dict:
        return {
            "total_turns": len(self.history) // 2,
            "voice": self.tts.voice_name,
            "llm_model": self.llm.model,
        }

assistant = VoiceAssistant()
assistant.asr.load()
print("语音助手构建完成 ✓")

# ============================================================================
# 3. 功能测试
# ============================================================================
print("\n--- 3. 功能测试 ---")

tests = [
    "你好，请介绍一下你自己",
    "今天天气怎么样？",
    "给我讲个笑话",
    "Python 和 Java 哪个好？",
    "我今天好开心啊！",
]

for text in tests:
    print(f"\n  🎤 用户: {text}")
    result = assistant.process_text(text)
    print(f"  🤖 助手: {result['reply'][:100]}...")
    if result.get("emotion") != "中性":
        print(f"  💭 情感: {result['emotion']}")

# ============================================================================
# 4. 语音指令测试
# ============================================================================
print("\n\n--- 4. 语音指令 ---")

commands = ["当前声音", "切换声音", "当前声音"]
for cmd in commands:
    print(f"\n  🎤 指令: {cmd}")
    result = assistant.process_text(cmd, verbose=False)
    print(f"  🤖 回应: {result['reply']}")

# ============================================================================
# 5. 多轮对话测试
# ============================================================================
print("\n\n--- 5. 多轮对话 ---")

assistant.history.clear()
conversation = [
    "我想学编程，应该从哪里开始？",
    "Python 难学吗？",
    "有什么推荐的学习资源吗？",
    "谢谢你的建议！",
]

for text in conversation:
    print(f"\n  🎤 用户: {text}")
    result = assistant.process_text(text, verbose=False)
    print(f"  🤖 助手: {result['reply'][:120]}...")

# ============================================================================
# 6. 完整交互循环
# ============================================================================
print("\n\n--- 6. 交互循环代码 ---")
print("""
完整的语音交互循环（需要麦克风和扬声器）：

```python
import sounddevice as sd
import soundfile as sf

assistant = VoiceAssistant()
assistant.asr.load()

print("语音助手已启动！说'退出'结束。")

while True:
    # 1. 录音（按键说话或 VAD 自动检测）
    print("🎤 正在听...")
    recording = sd.rec(int(5 * 16000), samplerate=16000, channels=1)
    sd.wait()
    
    # 保存临时文件
    temp_wav = "temp_input.wav"
    sf.write(temp_wav, recording, 16000)
    
    # 2. 处理
    result = assistant.process_audio(temp_wav)
    
    if "退出" in result["user_text"]:
        print("再见！")
        break
    
    print(f"🤖 {result['reply']}")
    
    # 3. 播放回复语音
    if os.path.exists(str(result.get("audio_path", ""))):
        # 使用 pydub 或 playsound 播放
        from pydub import AudioSegment
        from pydub.playback import play
        audio = AudioSegment.from_mp3(result["audio_path"])
        play(audio)
```
""")

# ============================================================================
# 7. 项目架构总结
# ============================================================================
print("\n--- 7. 项目架构总结 ---")
stats = assistant.get_stats()
print(f"""
┌────────────────────────────────────────────────────────┐
│           语音对话助手 - 项目架构                        │
├────────────────────────────────────────────────────────┤
│                                                        │
│  VoiceAssistant（主控）                                │
│  ├── process_text()    文字输入处理                    │
│  ├── process_audio()   语音输入处理                    │
│  ├── _check_command()  语音指令检测                    │
│  └── get_stats()       状态统计                        │
│                                                        │
│  ASRModule（语音识别）                                 │
│  ├── Whisper tiny/base/small                          │
│  └── transcribe() 语音→文字                           │
│                                                        │
│  LLMModule（对话引擎）                                 │
│  ├── Ollama qwen2.5:7b                                │
│  └── chat() 多轮对话                                  │
│                                                        │
│  TTSModule（语音合成）                                 │
│  ├── edge-tts（4种中文声音）                           │
│  ├── synthesize() 文字→语音                           │
│  └── set_voice() 切换声音                             │
│                                                        │
│  EmotionModule（情感分析）                             │
│  └── analyze() 关键词情感识别                         │
│                                                        │
│  整合的知识点                                          │
│  ├── 第1课: 语音AI概述+音频基础                       │
│  ├── 第2课: ASR（Whisper）                            │
│  ├── 第3课: TTS（edge-tts）                           │
│  ├── 第4课: 声音克隆（个性化声音）                    │
│  ├── 第5课: 实时交互（VAD+流式）                      │
│  └── 第6课: 音频处理（降噪+特征）                     │
│                                                        │
│  统计: {stats['total_turns']} 轮对话, 声音:{stats['voice']}, 模型:{stats['llm_model']}│
│                                                        │
│  扩展方向                                              │
│  → 接入 GPT-SoVITS 实现声音克隆                       │
│  → 接入 Silero VAD 实现实时检测                        │
│  → 接入 FunASR 流式识别                               │
│  → 部署为 Web 服务（WebSocket 实时音频流）             │
│  → 接入 GPT-4o Realtime API                           │
└────────────────────────────────────────────────────────┘
""")

# 清理
import shutil
shutil.rmtree(assistant.tts.output_dir, ignore_errors=True)

print("=" * 60)
print("[完成] 第7课完成！你已经学会了：")
print("  [v] ASR + LLM + TTS 完整流水线")
print("  [v] 多轮对话记忆")
print("  [v] 语音指令系统")
print("  [v] 情感分析集成")
print("  [v] 多声音切换")
print("  [v] 整合前6课所有核心知识")
print("=" * 60)
print("\nlearn-voice 语音课程全部完成！🎉")
