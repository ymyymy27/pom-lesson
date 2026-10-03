import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第6课：音频处理（降噪 / 分离 / 情感分析）
==============================================================================

音频处理是语音 AI 的底层基础。
本课学习常见的音频处理技术。

本课内容：
1. 音频读写与格式转换
2. 音频降噪
3. 人声分离（背景音乐去除）
4. 语音情感分析
5. 声纹识别（说话人验证）
6. 音频特征提取（MFCC/Mel谱）
==============================================================================
"""

import json
import numpy as np
import os
import tempfile

print("=" * 60)
print("第6课：音频处理")
print("=" * 60)

# ============================================================================
# 1. 音频读写与格式转换
# ============================================================================
print("\n--- 1. 音频读写 ---")
print("""
Python 音频处理库：

基础读写：
  soundfile:  读写 WAV/FLAC/OGG（推荐）
  wave:       Python 内置，只支持 WAV
  scipy.io:   读写 WAV

高级处理：
  pydub:      格式转换/剪切/拼接/混音（需要ffmpeg）
  librosa:    音频分析/特征提取（学术标准）
  torchaudio: PyTorch 生态音频处理

```python
# soundfile（推荐）
import soundfile as sf
audio, sr = sf.read("input.wav")    # 返回 numpy + 采样率
sf.write("output.wav", audio, sr)

# pydub（格式转换）
from pydub import AudioSegment
audio = AudioSegment.from_mp3("input.mp3")
audio.export("output.wav", format="wav")

# 常用转换
audio = audio.set_frame_rate(16000)     # 改采样率
audio = audio.set_channels(1)           # 改为单声道
audio = audio.set_sample_width(2)       # 16bit
audio = audio + 10                      # 音量+10dB
audio = audio - 5                       # 音量-5dB

# 剪切拼接
segment = audio[1000:5000]              # 1-5秒
merged = audio1 + audio2               # 拼接
mixed = audio1.overlay(audio2)         # 混音
```
""")

# 生成测试音频
sr = 16000
duration = 3.0
t = np.linspace(0, duration, int(sr * duration), endpoint=False)

# 模拟语音信号（多频率叠加）
speech = np.sin(2 * np.pi * 200 * t) * 0.5
speech += np.sin(2 * np.pi * 400 * t) * 0.3
speech += np.sin(2 * np.pi * 800 * t) * 0.1

# 添加噪声
noise = np.random.randn(len(t)) * 0.1
noisy_speech = speech + noise

print(f"测试音频生成:")
print(f"  采样率: {sr} Hz, 时长: {duration}s")
print(f"  纯净语音 RMS: {np.sqrt(np.mean(speech**2)):.4f}")
print(f"  噪声 RMS: {np.sqrt(np.mean(noise**2)):.4f}")
print(f"  带噪语音 RMS: {np.sqrt(np.mean(noisy_speech**2)):.4f}")
print(f"  信噪比 SNR: {10*np.log10(np.mean(speech**2)/np.mean(noise**2)):.1f} dB")

# ============================================================================
# 2. 音频降噪
# ============================================================================
print("\n--- 2. 音频降噪 ---")
print("""
降噪方案：

┌─────────────────┬──────────────────────────────────────┐
│  方案            │  说明                                 │
├─────────────────┼──────────────────────────────────────┤
│  谱减法          │  传统方法，估计噪声谱并减去           │
│  noisereduce    │  Python库，基于谱门控                 │
│  DeepFilterNet  │  深度学习降噪，效果最好               │
│  RNNoise        │  RNN降噪，速度快                      │
│  DTLN           │  双信号Transformer，实时降噪          │
└─────────────────┴──────────────────────────────────────┘

noisereduce 使用：
```python
import noisereduce as nr

# 降噪
reduced = nr.reduce_noise(
    y=noisy_audio,
    sr=16000,
    prop_decrease=0.8,  # 降噪程度 0-1
)
```

DeepFilterNet（最佳效果）：
```python
from df import enhance, init_df

model, df_state, _ = init_df()
enhanced = enhance(model, df_state, noisy_audio)
```
""")

# 简单的谱减法降噪
def spectral_subtraction(noisy, sr, noise_frames=10):
    """简单谱减法降噪"""
    frame_len = int(sr * 0.025)  # 25ms 帧
    hop_len = int(sr * 0.010)    # 10ms 步长

    # 估计噪声谱（取前几帧的平均）
    noise_est = np.zeros(frame_len)
    for i in range(noise_frames):
        frame = noisy[i*hop_len:i*hop_len+frame_len]
        if len(frame) == frame_len:
            noise_est += np.abs(np.fft.fft(frame))
    noise_est /= noise_frames

    # 谱减
    enhanced = np.zeros_like(noisy)
    for i in range(0, len(noisy) - frame_len, hop_len):
        frame = noisy[i:i+frame_len]
        spec = np.fft.fft(frame)
        mag = np.abs(spec) - noise_est * 0.8
        mag = np.maximum(mag, 0.01 * np.abs(spec))  # 保留最小值
        phase = np.angle(spec)
        enhanced_frame = np.real(np.fft.ifft(mag * np.exp(1j * phase)))
        enhanced[i:i+frame_len] += enhanced_frame

    return enhanced

enhanced = spectral_subtraction(noisy_speech, sr)
print(f"谱减法降噪:")
print(f"  降噪前 RMS: {np.sqrt(np.mean(noisy_speech**2)):.4f}")
print(f"  降噪后 RMS: {np.sqrt(np.mean(enhanced**2)):.4f}")

# ============================================================================
# 3. 人声分离
# ============================================================================
print("\n--- 3. 人声分离 ---")
print("""
人声分离 = 将音乐和人声分开

主流方案：
┌─────────────────┬──────────────────────────────────────┐
│  模型            │  说明                                 │
├─────────────────┼──────────────────────────────────────┤
│  Demucs(Meta)   │  最强音源分离，分出人声/鼓/贝斯/其他 │
│  Spleeter       │  Deezer开源，速度快                   │
│  UVR            │  桌面端工具，多模型可选               │
└─────────────────┴──────────────────────────────────────┘

Demucs 使用：
```python
import torchaudio
from demucs.pretrained import get_model
from demucs.apply import apply_model

model = get_model("htdemucs")
wav, sr = torchaudio.load("song.mp3")
wav = wav.unsqueeze(0)  # 添加 batch 维度

sources = apply_model(model, wav)
# sources[0]: drums  鼓
# sources[1]: bass   贝斯
# sources[2]: other  其他乐器
# sources[3]: vocals 人声

torchaudio.save("vocals.wav", sources[0, 3], sr)
torchaudio.save("instrumental.wav",
    sources[0, 0] + sources[0, 1] + sources[0, 2], sr)
```

命令行方式：
```bash
pip install demucs
demucs song.mp3 --out separated/
# 输出: separated/htdemucs/song/vocals.wav 等
```
""")

# ============================================================================
# 4. 语音情感分析
# ============================================================================
print("\n--- 4. 语音情感分析 ---")
print("""
从声音中识别说话人的情绪。

方案1：音频特征 + 分类器
  提取特征（MFCC/能量/基频）→ SVM/神经网络 → 情感类别

方案2：端到端模型
  音频 → 预训练模型 → 情感类别

方案3：多模态（推荐）
  ASR(语音→文字) + 文本情感分析 + 音频特征 → 综合判断

```python
# 使用 HuggingFace 情感识别模型
from transformers import pipeline

classifier = pipeline(
    "audio-classification",
    model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
)

result = classifier("audio.wav")
# [{'label': 'happy', 'score': 0.85}, {'label': 'neutral', 'score': 0.10}, ...]
```
""")

# 基于音频特征的简单情感分析
def analyze_audio_features(audio: np.ndarray, sr: int) -> dict:
    """提取基础音频特征用于情感分析"""
    # 能量（响度）
    rms = np.sqrt(np.mean(audio ** 2))

    # 过零率（语速/频率相关）
    zero_crossings = np.sum(np.abs(np.diff(np.sign(audio)))) / (2 * len(audio))

    # 频谱中心（音色亮暗）
    fft = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(len(audio), 1/sr)
    spectral_centroid = np.sum(freqs * fft) / (np.sum(fft) + 1e-10)

    # 简单情感推断
    if rms > 0.3 and zero_crossings > 0.1:
        emotion = "激动/开心"
    elif rms < 0.1:
        emotion = "平静/悲伤"
    elif spectral_centroid > 2000:
        emotion = "紧张/焦虑"
    else:
        emotion = "中性"

    return {
        "rms_energy": round(float(rms), 4),
        "zero_crossing_rate": round(float(zero_crossings), 4),
        "spectral_centroid_hz": round(float(spectral_centroid), 1),
        "estimated_emotion": emotion,
    }

features = analyze_audio_features(speech, sr)
print(f"音频特征分析:")
for k, v in features.items():
    print(f"  {k}: {v}")

# ============================================================================
# 5. 声纹识别
# ============================================================================
print("\n--- 5. 声纹识别 ---")
print("""
声纹识别 = 通过声音特征验证/识别说话人身份

两种任务：
- 说话人验证：这段语音是张三说的吗？（1:1比对）
- 说话人识别：这段语音是谁说的？（1:N搜索）

```python
# 使用 speechbrain（推荐）
from speechbrain.inference.speaker import SpeakerRecognition

model = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb"
)

# 说话人验证
score, prediction = model.verify_files(
    "speaker1_sample1.wav",
    "speaker1_sample2.wav"
)
print(f"相似度: {score:.4f}, 同一人: {prediction}")

# 提取声纹嵌入
embedding = model.encode_batch(waveform)
# embedding.shape = (1, 192)  → 存入数据库用于比对
```

FunASR 说话人分离：
```python
from funasr import AutoModel

model = AutoModel(
    model="paraformer-zh",
    spk_model="cam++",  # 说话人识别模型
)

result = model.generate(input="meeting.wav")
# 输出带说话人标签的结果
```
""")

# ============================================================================
# 6. 音频特征提取（MFCC / Mel 谱）
# ============================================================================
print("\n--- 6. 音频特征提取 ---")
print("""
MFCC（梅尔频率倒谱系数）是最经典的音频特征。

音频 → 分帧 → FFT → Mel滤波器组 → 对数 → DCT → MFCC

```python
import librosa

# 加载音频
audio, sr = librosa.load("audio.wav", sr=16000)

# MFCC
mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
# mfcc.shape = (13, n_frames)

# Mel 频谱图
mel_spec = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=80)
mel_db = librosa.power_to_db(mel_spec, ref=np.max)

# 基频（F0）
f0, voiced_flag, voiced_probs = librosa.pyin(audio, fmin=50, fmax=500, sr=sr)

# 色度特征（音乐分析）
chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
```

特征用途：
┌──────────────────┬──────────────────────────────────┐
│  特征             │  用途                             │
├──────────────────┼──────────────────────────────────┤
│  MFCC            │  语音识别、说话人识别             │
│  Mel频谱图       │  深度学习模型输入                 │
│  基频F0          │  语调分析、情感识别               │
│  能量/RMS        │  音量检测、VAD                    │
│  过零率          │  有声/无声分类                    │
│  频谱中心        │  音色分析                         │
│  色度            │  音乐分析、和弦识别               │
└──────────────────┴──────────────────────────────────┘
""")

# 手动计算简化版 MFCC
def simple_mfcc(audio, sr, n_mfcc=13, frame_ms=25, hop_ms=10):
    """简化版 MFCC 计算"""
    frame_len = int(sr * frame_ms / 1000)
    hop_len = int(sr * hop_ms / 1000)
    n_frames = (len(audio) - frame_len) // hop_len + 1

    mfccs = []
    for i in range(min(n_frames, 100)):
        frame = audio[i*hop_len:i*hop_len+frame_len]
        # 加窗
        frame = frame * np.hamming(frame_len)
        # FFT
        spec = np.abs(np.fft.rfft(frame))
        # 对数能量
        log_spec = np.log(spec + 1e-10)
        # DCT（简化）
        mfcc_frame = np.fft.rfft(log_spec).real[:n_mfcc]
        mfccs.append(mfcc_frame)

    return np.array(mfccs).T  # (n_mfcc, n_frames)

mfcc = simple_mfcc(speech, sr)
print(f"\n简化 MFCC 计算:")
print(f"  形状: {mfcc.shape} (n_mfcc, n_frames)")
print(f"  MFCC[0] 均值: {mfcc[0].mean():.4f}")
print(f"  MFCC[1] 均值: {mfcc[1].mean():.4f}")

print("\n" + "=" * 60)
print("[完成] 第6课完成！你已经学会了：")
print("  [v] 音频读写与格式转换（soundfile/pydub）")
print("  [v] 音频降噪（谱减法/noisereduce/DeepFilterNet）")
print("  [v] 人声分离（Demucs）")
print("  [v] 语音情感分析")
print("  [v] 声纹识别（说话人验证/识别）")
print("  [v] 音频特征提取（MFCC/Mel谱/F0）")
print("=" * 60)
print("\n下一课：07_voice_project.py - 完整项目：语音对话助手")
