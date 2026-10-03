import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第7课：完整项目 - 智能图像分析助手
==============================================================================

整合前6课知识，构建一个多功能的图像分析助手：

功能：
1. 图像描述（多粒度）
2. OCR 文字提取
3. 目标检测（模拟 YOLO）
4. 图像搜索（CLIP 嵌入）
5. 视觉问答（VQA）
6. 图像对比分析

架构：
  用户上传图片+问题 → 意图识别 → 路由到对应处理器 → 返回结果
==============================================================================
"""

import json
import base64
import numpy as np
from io import BytesIO
from datetime import datetime

print("=" * 60)
print("第7课：完整项目 - 智能图像分析助手")
print("=" * 60)

# ============================================================================
# 1. 工具定义
# ============================================================================
print("\n--- 1. 定义分析工具 ---")

import httpx

OLLAMA_URL = "http://localhost:11434"
VISION_MODEL = "llava:7b"

def call_vision_llm(prompt: str, image_b64: str) -> str:
    """调用视觉 LLM"""
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": VISION_MODEL,
            "messages": [{"role": "user", "content": prompt, "images": [image_b64]}],
            "stream": False,
        }, timeout=60.0)
        return resp.json().get("message", {}).get("content", "无回复")
    except:
        return "[模拟回答] 这是一张测试图片，包含蓝色背景和白色文字。"

def call_text_llm(prompt: str) -> str:
    """调用文本 LLM"""
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": "qwen2.5:7b",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }, timeout=30.0)
        return resp.json().get("message", {}).get("content", "无回复")
    except:
        return "[模拟回答]"

# 工具集
class VisionTools:
    """图像分析工具集"""

    @staticmethod
    def describe_image(image_b64: str, detail: str = "detailed") -> dict:
        """图像描述"""
        prompts = {
            "brief": "用一句话简要描述这张图片。",
            "detailed": "详细描述这张图片的内容，包括场景、物体、颜色、布局。",
            "structured": '用JSON格式描述: {"scene":"场景","objects":["物体"],"colors":["颜色"],"mood":"氛围"}',
        }
        prompt = prompts.get(detail, prompts["detailed"])
        result = call_vision_llm(prompt, image_b64)
        return {"tool": "describe", "detail_level": detail, "description": result}

    @staticmethod
    def ocr_extract(image_b64: str, doc_type: str = "general") -> dict:
        """OCR 文字提取"""
        prompts = {
            "general": "识别图片中的所有文字，按顺序输出。",
            "invoice": "识别发票信息，输出JSON: {type,number,date,amount,seller,buyer}",
            "card": "识别名片信息，输出JSON: {name,title,company,phone,email}",
            "table": "识别表格，以Markdown表格格式输出。",
        }
        prompt = prompts.get(doc_type, prompts["general"])
        result = call_vision_llm(prompt, image_b64)
        return {"tool": "ocr", "doc_type": doc_type, "text": result}

    @staticmethod
    def detect_objects(image_b64: str) -> dict:
        """目标检测（LLM辅助）"""
        prompt = """识别图片中的所有物体，用JSON数组输出：
[{"object":"物体名","position":"位置(左上/中间/右下等)","confidence":"高/中/低"}]"""
        result = call_vision_llm(prompt, image_b64)
        return {"tool": "detect", "detections": result}

    @staticmethod
    def visual_qa(image_b64: str, question: str) -> dict:
        """视觉问答"""
        result = call_vision_llm(f"请看图回答：{question}", image_b64)
        return {"tool": "vqa", "question": question, "answer": result}

    @staticmethod
    def compare_images(img1_b64: str, img2_b64: str) -> dict:
        """图像对比"""
        try:
            resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
                "model": VISION_MODEL,
                "messages": [{"role": "user",
                    "content": "比较这两张图片的异同点，分别说明相同之处和不同之处。",
                    "images": [img1_b64, img2_b64]}],
                "stream": False,
            }, timeout=60.0)
            result = resp.json().get("message", {}).get("content", "无回复")
        except:
            result = "[模拟] 两张图片颜色不同，布局相似。"
        return {"tool": "compare", "comparison": result}

    @staticmethod
    def analyze_mood(image_b64: str) -> dict:
        """情感/氛围分析"""
        prompt = "分析这张图片传达的情感和氛围，包括色调、构图给人的感受。"
        result = call_vision_llm(prompt, image_b64)
        return {"tool": "mood", "analysis": result}

tools = VisionTools()
print("已定义 6 个分析工具:")
for name in ["describe_image", "ocr_extract", "detect_objects",
             "visual_qa", "compare_images", "analyze_mood"]:
    print(f"  🔧 {name}")

# ============================================================================
# 2. 图像搜索引擎
# ============================================================================
print("\n--- 2. 图像搜索引擎 ---")

class ImageSearchEngine:
    """基于模拟 CLIP 嵌入的图像搜索"""

    def __init__(self):
        self.images = []

    def add_image(self, image_id: str, description: str):
        np.random.seed(hash(description) % 2**32)
        emb = np.random.randn(512).astype(np.float32)
        emb = emb / np.linalg.norm(emb)
        self.images.append({"id": image_id, "description": description, "embedding": emb})

    def search_by_text(self, query: str, top_k: int = 3) -> list:
        np.random.seed(hash(query) % 2**32)
        q_emb = np.random.randn(512).astype(np.float32)
        q_emb = q_emb / np.linalg.norm(q_emb)
        results = []
        for img in self.images:
            score = float(np.dot(q_emb, img["embedding"]))
            results.append({"id": img["id"], "description": img["description"], "score": score})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

search_engine = ImageSearchEngine()
for img_id, desc in [
    ("img_001", "日落时的海滩"),
    ("img_002", "城市夜景高楼"),
    ("img_003", "雪山蓝天白云"),
    ("img_004", "橘猫在沙发睡觉"),
    ("img_005", "程序员在写代码"),
    ("img_006", "咖啡和早餐"),
    ("img_007", "秋天红色枫叶"),
    ("img_008", "小狗在草地奔跑"),
]:
    search_engine.add_image(img_id, desc)
print(f"图像搜索引擎: 已索引 {len(search_engine.images)} 张图片")

# ============================================================================
# 3. 助手引擎
# ============================================================================
print("\n--- 3. 构建助手引擎 ---")

class VisionAssistant:
    """智能图像分析助手"""

    def __init__(self):
        self.tools = VisionTools()
        self.search = search_engine
        self.history = []

    def classify_intent(self, message: str) -> str:
        """意图分类"""
        m = message.lower()
        if any(w in m for w in ["ocr", "文字", "识别文字", "票据", "发票", "名片"]):
            return "ocr"
        if any(w in m for w in ["检测", "目标", "物体", "识别物体", "有什么"]):
            return "detect"
        if any(w in m for w in ["搜索", "找图", "类似", "搜图"]):
            return "search"
        if any(w in m for w in ["对比", "比较", "区别", "差异"]):
            return "compare"
        if any(w in m for w in ["情感", "氛围", "感受", "风格"]):
            return "mood"
        if any(w in m for w in ["描述", "看看", "什么图"]):
            return "describe"
        if "?" in m or "？" in m or any(w in m for w in ["是什么", "多少", "哪里", "为什么", "怎么"]):
            return "vqa"
        return "describe"

    def process(self, message: str, image_b64: str = None,
                image2_b64: str = None, verbose: bool = True) -> str:
        """处理用户请求"""
        intent = self.classify_intent(message)
        if verbose:
            print(f"    意图: {intent}")

        if intent == "search":
            results = self.search.search_by_text(message)
            if verbose:
                print(f"    🔍 搜索图片库...")
            output = "搜索结果:\n"
            for r in results:
                output += f"  {r['score']:.3f} | {r['id']} | {r['description']}\n"
            self.history.append({"intent": intent, "message": message})
            return output

        if not image_b64:
            return "请提供一张图片进行分析。"

        if intent == "ocr":
            doc_type = "general"
            if "发票" in message or "票据" in message:
                doc_type = "invoice"
            elif "名片" in message:
                doc_type = "card"
            elif "表格" in message:
                doc_type = "table"
            if verbose:
                print(f"    🔧 ocr_extract(type={doc_type})")
            result = self.tools.ocr_extract(image_b64, doc_type)
            self.history.append({"intent": intent, "result": result})
            return result["text"]

        elif intent == "detect":
            if verbose:
                print(f"    🔧 detect_objects()")
            result = self.tools.detect_objects(image_b64)
            self.history.append({"intent": intent, "result": result})
            return result["detections"]

        elif intent == "compare":
            if image2_b64:
                if verbose:
                    print(f"    🔧 compare_images()")
                result = self.tools.compare_images(image_b64, image2_b64)
            else:
                result = {"comparison": "请提供第二张图片进行对比。"}
            self.history.append({"intent": intent, "result": result})
            return result["comparison"]

        elif intent == "mood":
            if verbose:
                print(f"    🔧 analyze_mood()")
            result = self.tools.analyze_mood(image_b64)
            self.history.append({"intent": intent, "result": result})
            return result["analysis"]

        elif intent == "vqa":
            if verbose:
                print(f"    🔧 visual_qa()")
            result = self.tools.visual_qa(image_b64, message)
            self.history.append({"intent": intent, "result": result})
            return result["answer"]

        else:
            detail = "structured" if "json" in message.lower() else "detailed"
            if verbose:
                print(f"    🔧 describe_image(detail={detail})")
            result = self.tools.describe_image(image_b64, detail)
            self.history.append({"intent": intent, "result": result})
            return result["description"]

assistant = VisionAssistant()
print("智能图像分析助手构建完成 ✓")

# ============================================================================
# 4. 创建测试图像
# ============================================================================
print("\n--- 4. 创建测试图像 ---")

try:
    from PIL import Image, ImageDraw

    def make_test_img(text, bg=(66, 135, 245), size=(300, 150)):
        img = Image.new("RGB", size, color=bg)
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), text, fill=(255, 255, 255))
        draw.rectangle([10, 10, size[0]-10, size[1]-10], outline=(255, 255, 255), width=2)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    img1 = make_test_img("Hello AI\nTest Image v1")
    img2 = make_test_img("Hello AI\nTest Image v2", bg=(245, 135, 66))
    print(f"  创建测试图像 ✓")
except ImportError:
    img1 = "test_base64_1"
    img2 = "test_base64_2"
    print("  Pillow 未安装，使用模拟数据")

# ============================================================================
# 5. 功能测试
# ============================================================================
print("\n--- 5. 功能测试 ---")

tests = [
    ("描述一下这张图片", img1, None),
    ("识别图中的文字", img1, None),
    ("图中有什么物体？", img1, None),
    ("这张图片的氛围是什么？", img1, None),
    ("这张图片是什么颜色的？", img1, None),
    ("搜索类似海滩的图片", None, None),
]

for msg, img, img2 in tests:
    print(f"\n  Q: {msg}")
    a = assistant.process(msg, img, img2)
    print(f"  A: {str(a)[:120]}...")

# ============================================================================
# 6. 图像对比测试
# ============================================================================
print("\n\n--- 6. 图像对比 ---")
print("  Q: 比较这两张图片的区别")
a = assistant.process("比较这两张图片的区别", img1, img2)
print(f"  A: {str(a)[:150]}...")

# ============================================================================
# 7. 项目架构总结
# ============================================================================
print("\n\n--- 7. 项目架构总结 ---")
print(f"""
┌────────────────────────────────────────────────────────┐
│           智能图像分析助手 - 项目架构                    │
├────────────────────────────────────────────────────────┤
│                                                        │
│  VisionAssistant（用户接口）                            │
│  ├── classify_intent()  意图分类                       │
│  └── process()          路由+执行+返回                 │
│                                                        │
│  VisionTools（分析工具集）                              │
│  ├── describe_image()   图像描述（3种粒度）            │
│  ├── ocr_extract()      OCR提取（通用/票据/名片/表格） │
│  ├── detect_objects()   目标检测（LLM辅助）            │
│  ├── visual_qa()        视觉问答                       │
│  ├── compare_images()   图像对比                       │
│  └── analyze_mood()     情感分析                       │
│                                                        │
│  ImageSearchEngine（图像搜索）                         │
│  ├── add_image()        索引图片                       │
│  └── search_by_text()   以文搜图                       │
│                                                        │
│  整合的知识点                                          │
│  ├── 第1课: 视觉AI概述+模型选型                        │
│  ├── 第2课: Vision API（GPT-4o/LLaVA）                │
│  ├── 第3课: OCR文字提取+结构化                         │
│  ├── 第4课: 目标检测（YOLO/SAM概念）                  │
│  ├── 第5课: CLIP嵌入+图像搜索                         │
│  └── 第6课: 视频理解（关键帧+摘要）                   │
│                                                        │
│  扩展方向                                              │
│  → 接入 YOLO 真实检测（像素级精度）                    │
│  → 接入 PaddleOCR（高精度中文OCR）                     │
│  → 接入 CLIP 真实嵌入（向量搜索）                      │
│  → 添加视频分析能力                                    │
│  → 部署为 Web 服务（FastAPI + 前端上传）               │
└────────────────────────────────────────────────────────┘

历史记录: {len(assistant.history)} 条分析记录
""")

print("=" * 60)
print("[完成] 第7课完成！你已经学会了：")
print("  [v] 构建多功能图像分析工具集")
print("  [v] 意图分类+工具路由")
print("  [v] 图像描述/OCR/检测/问答/对比/情感分析")
print("  [v] 图像搜索引擎（CLIP嵌入）")
print("  [v] 整合前6课所有核心知识")
print("=" * 60)
print("\nlearn-vision 视觉课程全部完成！🎉")
