# 语音识别与语音合成 从零开始深入学习教程

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 第1课 | `01_voice_overview.py` | 语音 AI 概述（ASR/TTS/发展/模型） |
| 第2课 | `02_speech_recognition.py` | 语音识别 ASR（Whisper/FunASR） |
| 第3课 | `03_tts_synthesis.py` | 语音合成 TTS（OpenAI TTS/edge-tts/VITS） |
| 第4课 | `04_voice_cloning.py` | 声音克隆与个性化（GPT-SoVITS/CosyVoice） |
| 第5课 | `05_realtime_voice.py` | 实时语音交互（流式ASR/TTS/VAD） |
| 第6课 | `06_audio_processing.py` | 音频处理（降噪/分离/情感分析） |
| 第7课 | `07_voice_project.py` | 完整项目：语音对话助手 |

## 环境配置

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Whisper 模型（语音识别）
# pip install openai-whisper  # OpenAI 官方
# 或通过 API: set OPENAI_API_KEY=sk-xxx
```

## 学习方式

按顺序学习，每个文件可直接运行：`python 01_voice_overview.py`
