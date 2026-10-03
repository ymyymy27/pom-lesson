import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第7课：完整项目 - 多模态智能助手
==============================================================================

整合前6课 + learn-vision + learn-voice + learn-image-gen 的全部知识，
构建一个全能多模态智能助手。

能力：
1. 看（图像理解/OCR/检测）
2. 听（语音识别/音频分析）
3. 说（语音合成）
4. 画（图像生成/编辑）
5. 想（多模态推理/RAG）
6. 做（工具调用/Agent）

架构：
  多模态输入 → 感知层 → 推理层 → 行动层 → 多模态输出
==============================================================================
"""

import json
import os
import tempfile
import asyncio
import numpy as np
import base64
from io import BytesIO
from datetime import datetime

print("=" * 60)
print("第7课：完整项目 - 多模态智能助手")
print("=" * 60)

import httpx

OLLAMA_URL = "http://localhost:11434"

# ============================================================================
# 1. 感知模块
# ============================================================================
print("\n--- 1. 感知模块 ---")

class PerceptionModule:
    """多模态感知层：处理各种输入模态"""

    def perceive_text(self, text: str) -> dict:
        return {"modality": "text", "content": text, "language": "zh"}

    def perceive_image(self, image_b64: str) -> dict:
        try:
            from PIL import Image
            img_bytes = base64.b64decode(image_b64)
            img = Image.open(BytesIO(img_bytes))
            return {
                "modality": "image",
                "size": img.size,
                "format": img.format or "PNG",
                "base64": image_b64,
            }
        except:
            return {"modality": "image", "base64": image_b64, "size": "unknown"}

    def perceive_audio(self, audio_path: str = None) -> dict:
        if audio_path and os.path.exists(audio_path):
            size = os.path.getsize(audio_path)
            return {"modality": "audio", "path": audio_path, "size_kb": size / 1024}
        return {"modality": "audio", "status": "simulated"}

    def detect_modalities(self, **inputs) -> list:
        """检测输入中包含哪些模态"""
        modalities = []
        if inputs.get("text"):
            modalities.append("text")
        if inputs.get("image"):
            modalities.append("image")
        if inputs.get("audio"):
            modalities.append("audio")
        if inputs.get("video"):
            modalities.append("video")
        return modalities

perception = PerceptionModule()
print("感知模块: 支持 text / image / audio / video")

# ============================================================================
# 2. 推理模块
# ============================================================================
print("\n--- 2. 推理模块 ---")

class ReasoningModule:
    """多模态推理层：理解+决策"""

    def __init__(self):
        self.history = []

    def classify_intent(self, text: str, modalities: list) -> dict:
        """意图分类 + 任务规划"""
        t = text.lower()
        tasks = []

        # 根据文字内容判断意图
        if any(w in t for w in ["描述", "看看", "什么图", "分析"]):
            tasks.append({"action": "vision_analyze", "desc": "图像分析"})
        if any(w in t for w in ["文字", "ocr", "识别文字", "票据", "发票"]):
            tasks.append({"action": "ocr_extract", "desc": "OCR文字提取"})
        if any(w in t for w in ["检测", "物体", "目标"]):
            tasks.append({"action": "object_detect", "desc": "目标检测"})
        if any(w in t for w in ["生成", "画", "创建图"]):
            tasks.append({"action": "image_generate", "desc": "图像生成"})
        if any(w in t for w in ["编辑", "修改图", "风格", "重绘"]):
            tasks.append({"action": "image_edit", "desc": "图像编辑"})
        if any(w in t for w in ["搜索", "找图", "相似"]):
            tasks.append({"action": "image_search", "desc": "图像搜索"})
        if any(w in t for w in ["翻译", "转录", "语音识别"]):
            tasks.append({"action": "asr", "desc": "语音识别"})
        if any(w in t for w in ["朗读", "播报", "说出来"]):
            tasks.append({"action": "tts", "desc": "语音合成"})

        # 如果有图片但没有明确指令，默认分析
        if "image" in modalities and not tasks:
            tasks.append({"action": "vision_analyze", "desc": "图像分析"})

        # 通用对话
        if not tasks:
            tasks.append({"action": "chat", "desc": "对话"})

        return {"intent": tasks[0]["action"] if tasks else "chat", "tasks": tasks}

    def chat(self, messages: list) -> str:
        """调用 LLM 对话"""
        try:
            resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
                "model": "qwen2.5:7b",
                "messages": messages,
                "stream": False,
            }, timeout=30.0)
            return resp.json().get("message", {}).get("content", "思考中...")
        except:
            return "[模拟回答] 好的，我来帮你处理这个问题。"

    def vision_chat(self, prompt: str, image_b64: str) -> str:
        """视觉 LLM 对话"""
        try:
            resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
                "model": "llava:7b",
                "messages": [{"role": "user", "content": prompt, "images": [image_b64]}],
                "stream": False,
            }, timeout=60.0)
            return resp.json().get("message", {}).get("content", "分析中...")
        except:
            return "[模拟] 这是一张图片，包含丰富的视觉元素。"

reasoning = ReasoningModule()
print("推理模块: 意图分类 + LLM对话 + 视觉LLM")

# ============================================================================
# 3. 行动模块
# ============================================================================
print("\n--- 3. 行动模块 ---")

class ActionModule:
    """多模态行动层：执行具体任务"""

    def __init__(self):
        self.output_dir = tempfile.mkdtemp(prefix="multimodal_")

    def vision_analyze(self, image_b64: str, prompt: str) -> dict:
        result = reasoning.vision_chat(prompt, image_b64)
        return {"action": "vision_analyze", "result": result}

    def ocr_extract(self, image_b64: str) -> dict:
        result = reasoning.vision_chat("识别图片中的所有文字", image_b64)
        return {"action": "ocr", "text": result}

    def object_detect(self, image_b64: str) -> dict:
        result = reasoning.vision_chat(
            "列出图中所有物体及其大致位置(JSON数组)", image_b64)
        return {"action": "detect", "detections": result}

    def image_generate(self, prompt: str) -> dict:
        return {
            "action": "generate",
            "status": "success",
            "description": f"根据'{prompt[:30]}'生成图像",
            "note": "实际使用 DALL-E 3 或 SD 生成",
        }

    def image_edit(self, image_b64: str, instruction: str) -> dict:
        return {
            "action": "edit",
            "instruction": instruction,
            "status": "success",
            "note": "实际使用 SD Inpainting / img2img",
        }

    def image_search(self, query: str) -> dict:
        return {
            "action": "search",
            "query": query,
            "results": [
                {"id": "img_001", "score": 0.92, "desc": "最相似的图片"},
                {"id": "img_002", "score": 0.85, "desc": "第二相似"},
            ],
        }

    def asr(self, audio_path: str = None) -> dict:
        return {"action": "asr", "text": "[模拟] 你好，请帮我分析这张图片。"}

    def tts(self, text: str) -> dict:
        try:
            import edge_tts
            output = os.path.join(self.output_dir, f"tts_{hash(text) % 100000}.mp3")

            async def _syn():
                comm = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
                await comm.save(output)

            asyncio.run(_syn())
            return {"action": "tts", "path": output, "size_kb": os.path.getsize(output) / 1024}
        except:
            return {"action": "tts", "status": "simulated", "text": text[:50]}

    def chat(self, text: str, history: list) -> dict:
        history.append({"role": "user", "content": text})
        reply = reasoning.chat(history)
        history.append({"role": "assistant", "content": reply})
        return {"action": "chat", "reply": reply}

action = ActionModule()
print("行动模块: 视觉分析/OCR/检测/生成/编辑/搜索/ASR/TTS/对话")

# ============================================================================
# 4. 多模态智能助手
# ============================================================================
print("\n--- 4. 构建助手 ---")

class MultimodalAssistant:
    """多模态智能助手：整合感知+推理+行动"""

    def __init__(self):
        self.perception = perception
        self.reasoning = reasoning
        self.action = action
        self.chat_history = []
        self.session_log = []

    def process(self, text: str = "", image_b64: str = None,
                audio_path: str = None, verbose: bool = True) -> dict:
        """统一处理入口"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 1. 感知：检测输入模态
        modalities = self.perception.detect_modalities(
            text=text, image=image_b64, audio=audio_path)
        if verbose:
            print(f"    模态: {modalities}")

        # 2. 推理：意图分类
        intent_result = self.reasoning.classify_intent(text, modalities)
        tasks = intent_result["tasks"]
        if verbose:
            print(f"    意图: {intent_result['intent']}")
            print(f"    任务: {[t['desc'] for t in tasks]}")

        # 3. 行动：执行任务
        results = []
        for task in tasks:
            act = task["action"]
            if act == "vision_analyze" and image_b64:
                r = self.action.vision_analyze(image_b64, text or "详细描述这张图片")
            elif act == "ocr_extract" and image_b64:
                r = self.action.ocr_extract(image_b64)
            elif act == "object_detect" and image_b64:
                r = self.action.object_detect(image_b64)
            elif act == "image_generate":
                r = self.action.image_generate(text)
            elif act == "image_edit" and image_b64:
                r = self.action.image_edit(image_b64, text)
            elif act == "image_search":
                r = self.action.image_search(text)
            elif act == "asr":
                r = self.action.asr(audio_path)
            elif act == "tts":
                r = self.action.tts(text.replace("朗读", "").replace("播报", "").strip())
            elif act == "chat":
                r = self.action.chat(text, self.chat_history)
            else:
                r = self.action.chat(text, self.chat_history)
            results.append(r)
            if verbose:
                print(f"    执行: {act} → 完成")

        # 4. 记录
        entry = {
            "timestamp": timestamp,
            "input_modalities": modalities,
            "intent": intent_result["intent"],
            "tasks": [t["desc"] for t in tasks],
            "results": results,
        }
        self.session_log.append(entry)

        return entry

    def get_stats(self) -> dict:
        return {
            "total_interactions": len(self.session_log),
            "chat_turns": len(self.chat_history) // 2,
            "modality_counts": self._count_modalities(),
        }

    def _count_modalities(self) -> dict:
        counts = {}
        for entry in self.session_log:
            for m in entry["input_modalities"]:
                counts[m] = counts.get(m, 0) + 1
        return counts

assistant = MultimodalAssistant()
print("多模态智能助手构建完成 ✓")

# ============================================================================
# 5. 功能测试
# ============================================================================
print("\n--- 5. 功能测试 ---")

# 创建测试图像
try:
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (300, 150), color=(66, 135, 245))
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "Hello AI\nMultimodal Test", fill=(255, 255, 255))
    draw.rectangle([10, 10, 290, 140], outline=(255, 255, 255), width=2)
    buf = BytesIO()
    img.save(buf, format="PNG")
    test_img_b64 = base64.b64encode(buf.getvalue()).decode()
    print(f"  测试图像: {img.size} ✓")
except ImportError:
    test_img_b64 = "mock_base64"
    print("  Pillow 未安装，使用模拟数据")

# 测试场景
tests = [
    # (描述, 文字输入, 图片, 音频)
    ("纯文字对话", "你好，介绍一下多模态AI", None, None),
    ("图像分析", "描述这张图片的内容", test_img_b64, None),
    ("OCR识别", "识别图中的文字", test_img_b64, None),
    ("目标检测", "检测图中的物体", test_img_b64, None),
    ("图像生成", "帮我生成一张日落海滩的图片", None, None),
    ("图像搜索", "搜索类似风格的图片", None, None),
    ("语音合成", "朗读：今天天气真好", None, None),
]

for desc, text, img, audio in tests:
    print(f"\n  📋 {desc}")
    print(f"  输入: {text[:40]}{'...' if len(text) > 40 else ''}"
          f"{' + 📷' if img else ''}{' + 🎤' if audio else ''}")
    result = assistant.process(text, img, audio, verbose=False)
    intent = result["intent"]
    tasks = result["tasks"]
    print(f"  意图: {intent} | 任务: {tasks}")

# ============================================================================
# 6. 多模态对话测试
# ============================================================================
print("\n\n--- 6. 多轮对话 ---")

assistant.chat_history.clear()
conversation = [
    ("你能做什么？", None),
    ("帮我分析一下这张图片", test_img_b64),
    ("图中的文字是什么？", test_img_b64),
    ("画一张类似风格但是红色背景的", None),
    ("谢谢！", None),
]

for text, img in conversation:
    icon = "🎤+📷" if img else "🎤"
    print(f"\n  [{icon}] 用户: {text}")
    result = assistant.process(text, img, verbose=False)
    # 获取回复
    reply = ""
    for r in result["results"]:
        if "reply" in r:
            reply = r["reply"]
        elif "result" in r:
            reply = str(r["result"])
        elif "text" in r:
            reply = r["text"]
        elif "description" in r:
            reply = r["description"]
    print(f"  [🤖] 助手: {str(reply)[:100]}...")

# ============================================================================
# 7. 项目架构总结
# ============================================================================
stats = assistant.get_stats()
print(f"\n\n--- 7. 项目架构总结 ---")
print(f"""
┌────────────────────────────────────────────────────────┐
│         多模态智能助手 - 完整项目架构                    │
├────────────────────────────────────────────────────────┤
│                                                        │
│  MultimodalAssistant（主控）                           │
│  ├── process()           统一处理入口                  │
│  └── get_stats()         会话统计                      │
│                                                        │
│  PerceptionModule（感知层）                            │
│  ├── perceive_text()     文本感知                      │
│  ├── perceive_image()    图像感知                      │
│  ├── perceive_audio()    音频感知                      │
│  └── detect_modalities() 模态检测                      │
│                                                        │
│  ReasoningModule（推理层）                             │
│  ├── classify_intent()   意图分类+任务规划             │
│  ├── chat()              文本LLM对话                   │
│  └── vision_chat()       视觉LLM对话                  │
│                                                        │
│  ActionModule（行动层）                                │
│  ├── vision_analyze()    图像分析                      │
│  ├── ocr_extract()       OCR文字提取                   │
│  ├── object_detect()     目标检测                      │
│  ├── image_generate()    图像生成                      │
│  ├── image_edit()        图像编辑                      │
│  ├── image_search()      图像搜索                      │
│  ├── asr()               语音识别                      │
│  ├── tts()               语音合成                      │
│  └── chat()              对话                          │
│                                                        │
│  整合的全部知识                                        │
│  ├── learn-vision:  VLM/OCR/检测/CLIP/视频            │
│  ├── learn-voice:   ASR/TTS/克隆/实时/处理            │
│  ├── learn-image-gen: SD/DALL-E/ControlNet/编辑       │
│  └── learn-multimodal: 融合/RAG/Agent/实时            │
│                                                        │
│  统计: {stats['total_interactions']}次交互, {stats['chat_turns']}轮对话          │
│  模态: {stats['modality_counts']}                     │
│                                                        │
│  扩展方向                                              │
│  → 接入 GPT-4o Realtime（端到端语音）                  │
│  → 接入 YOLO + SAM（精确视觉）                        │
│  → 接入 CLIP + ChromaDB（多模态RAG）                  │
│  → 接入 SD/DALL-E（真实图像生成）                      │
│  → 接入 GPT-SoVITS（声音克隆）                        │
│  → 部署为 Web 服务（FastAPI + WebSocket + React）      │
│  → 添加多 Agent 协作                                  │
└────────────────────────────────────────────────────────┘
""")

# 清理
import shutil
shutil.rmtree(action.output_dir, ignore_errors=True)

print("=" * 60)
print("[完成] 第7课完成！你已经学会了：")
print("  [v] 感知层（文本/图像/音频/视频输入处理）")
print("  [v] 推理层（意图分类+多模态LLM）")
print("  [v] 行动层（9种多模态工具）")
print("  [v] 多模态对话（图文混合多轮）")
print("  [v] 完整的多模态助手架构")
print("  [v] 整合四门课程的全部核心知识")
print("=" * 60)
print("\n🎉 learn-multimodal 多模态融合课程全部完成！")
print("🎉 stage-10-multimodal 四门深讲课程全部完成！")
print("   - learn-vision (7课)")
print("   - learn-voice (7课)")
print("   - learn-image-gen (7课)")
print("   - learn-multimodal (7课)")
