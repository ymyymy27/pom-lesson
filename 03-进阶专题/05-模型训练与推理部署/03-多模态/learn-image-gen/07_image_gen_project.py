import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第7课：完整项目 - AI 绘画工作站
==============================================================================

整合前6课知识，构建一个多功能 AI 绘画工作站：

功能：
1. 文生图（多模型支持）
2. 图生图（风格转换）
3. 局部重绘
4. 提示词优化
5. 批量生成
6. 图像编辑工具链

架构：
  用户需求 → 提示词优化 → 选择模型/模式 → 生成/编辑 → 后处理
==============================================================================
"""

import json
import os
import tempfile
import numpy as np
from datetime import datetime

print("=" * 60)
print("第7课：完整项目 - AI 绘画工作站")
print("=" * 60)

# ============================================================================
# 1. 提示词引擎
# ============================================================================
print("\n--- 1. 提示词引擎 ---")

import httpx

OLLAMA_URL = "http://localhost:11434"

class PromptEngine:
    """提示词优化引擎"""

    STYLE_PRESETS = {
        "照片": {"positive": "photorealistic, 8k uhd, dslr, film grain, bokeh",
                 "negative": "cartoon, anime, illustration, painting, drawing"},
        "动漫": {"positive": "anime style, masterpiece, best quality, vibrant colors, cel shading",
                 "negative": "lowres, bad anatomy, worst quality, 3d render, photorealistic"},
        "油画": {"positive": "oil painting, thick brushstrokes, rich colors, canvas texture",
                 "negative": "photo, digital, smooth, blurry, low quality"},
        "水彩": {"positive": "watercolor painting, soft edges, flowing colors, wet on wet",
                 "negative": "digital, sharp lines, 3d, photo, low quality"},
        "赛博朋克": {"positive": "cyberpunk, neon lights, futuristic, dark atmosphere, rain",
                     "negative": "natural, pastoral, sunny, cartoon, low quality"},
        "幻想": {"positive": "fantasy art, magical, ethereal, epic, detailed",
                 "negative": "modern, realistic, mundane, low quality, blurry"},
    }

    QUALITY_TAGS = "masterpiece, best quality, highly detailed, sharp focus"
    BASE_NEGATIVE = ("lowres, bad anatomy, bad hands, text, error, missing fingers, "
                     "extra digit, fewer digits, cropped, worst quality, low quality, "
                     "jpeg artifacts, signature, watermark, blurry")

    def build_prompt(self, subject: str, style: str = "照片",
                     extra_positive: str = "", extra_negative: str = "") -> dict:
        preset = self.STYLE_PRESETS.get(style, self.STYLE_PRESETS["照片"])
        positive = f"{subject}, {preset['positive']}, {self.QUALITY_TAGS}"
        if extra_positive:
            positive += f", {extra_positive}"
        negative = f"{preset['negative']}, {self.BASE_NEGATIVE}"
        if extra_negative:
            negative += f", {extra_negative}"
        return {"positive": positive, "negative": negative, "style": style}

    def optimize_with_llm(self, user_input: str) -> str:
        """用 LLM 优化提示词"""
        try:
            resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
                "model": "qwen2.5:7b",
                "messages": [{"role": "user", "content":
                    f"将以下描述转为英文SD图像生成提示词（关键词标签式，不要句子）：\n{user_input}"}],
                "stream": False,
            }, timeout=20.0)
            return resp.json().get("message", {}).get("content", user_input)
        except:
            return user_input

prompt_engine = PromptEngine()
print("提示词引擎:")
for style in ["照片", "动漫", "油画", "赛博朋克"]:
    result = prompt_engine.build_prompt("a cat on a rooftop", style)
    print(f"  [{style}] {result['positive'][:65]}...")

# ============================================================================
# 2. 生成引擎
# ============================================================================
print("\n--- 2. 生成引擎 ---")

class GenerationEngine:
    """图像生成引擎（支持多后端）"""

    def __init__(self):
        self.backend = "mock"  # mock / dalle / diffusers / comfyui
        self.history = []

    def txt2img(self, positive: str, negative: str = "",
                size: tuple = (1024, 1024), steps: int = 30,
                cfg: float = 7.5, seed: int = -1) -> dict:
        """文生图"""
        if seed == -1:
            seed = np.random.randint(0, 2**32)
        result = {
            "mode": "txt2img",
            "positive": positive[:80],
            "negative": negative[:40],
            "size": f"{size[0]}x{size[1]}",
            "steps": steps, "cfg": cfg, "seed": seed,
            "backend": self.backend,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "status": "success",
        }
        self.history.append(result)
        return result

    def img2img(self, positive: str, negative: str = "",
                strength: float = 0.7, steps: int = 30) -> dict:
        """图生图"""
        result = {
            "mode": "img2img", "positive": positive[:80],
            "strength": strength, "steps": steps,
            "status": "success",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        self.history.append(result)
        return result

    def inpaint(self, positive: str, negative: str = "",
                strength: float = 0.8) -> dict:
        """局部重绘"""
        result = {
            "mode": "inpaint", "positive": positive[:80],
            "strength": strength, "status": "success",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        self.history.append(result)
        return result

    def upscale(self, scale: int = 2) -> dict:
        """超分辨率"""
        result = {
            "mode": "upscale", "scale": f"{scale}x",
            "status": "success",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        self.history.append(result)
        return result

gen_engine = GenerationEngine()
print(f"生成引擎: backend={gen_engine.backend}")

# ============================================================================
# 3. AI 绘画工作站
# ============================================================================
print("\n--- 3. 构建工作站 ---")

class AIPaintingStation:
    """AI 绘画工作站"""

    def __init__(self):
        self.prompt_engine = PromptEngine()
        self.gen_engine = GenerationEngine()
        self.projects = {}  # 项目管理

    def create_project(self, name: str) -> str:
        pid = f"proj_{len(self.projects)+1:03d}"
        self.projects[pid] = {
            "name": name, "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "images": [],
        }
        return pid

    def generate(self, prompt: str, style: str = "照片",
                 mode: str = "txt2img", project_id: str = None,
                 verbose: bool = True, **kwargs) -> dict:
        """统一生成接口"""
        # 1. 优化提示词
        prompt_result = self.prompt_engine.build_prompt(prompt, style)
        if verbose:
            print(f"    风格: {style}")
            print(f"    正向: {prompt_result['positive'][:60]}...")

        # 2. 根据模式选择生成方法
        if mode == "txt2img":
            result = self.gen_engine.txt2img(
                prompt_result["positive"], prompt_result["negative"],
                **kwargs
            )
        elif mode == "img2img":
            result = self.gen_engine.img2img(
                prompt_result["positive"], prompt_result["negative"],
                **kwargs
            )
        elif mode == "inpaint":
            result = self.gen_engine.inpaint(
                prompt_result["positive"], prompt_result["negative"],
                **kwargs
            )
        elif mode == "upscale":
            result = self.gen_engine.upscale(**kwargs)
        else:
            result = {"error": f"未知模式: {mode}"}

        # 3. 保存到项目
        if project_id and project_id in self.projects:
            self.projects[project_id]["images"].append(result)

        if verbose:
            print(f"    模式: {result.get('mode', '?')}")
            print(f"    状态: {result.get('status', '?')}")

        return result

    def batch_generate(self, prompt: str, styles: list,
                       project_id: str = None) -> list:
        """批量生成（同一主题，多种风格）"""
        results = []
        for style in styles:
            result = self.generate(prompt, style=style,
                                   project_id=project_id, verbose=False)
            results.append(result)
        return results

    def get_stats(self) -> dict:
        return {
            "projects": len(self.projects),
            "total_images": sum(len(p["images"]) for p in self.projects.values()),
            "history": len(self.gen_engine.history),
        }

station = AIPaintingStation()
print("AI 绘画工作站构建完成 ✓")

# ============================================================================
# 4. 功能测试
# ============================================================================
print("\n--- 4. 功能测试 ---")

# 创建项目
pid = station.create_project("猫咪系列")
print(f"创建项目: {pid}")

# 文生图测试
print("\n[测试1: 文生图 - 不同风格]")
for style in ["照片", "动漫", "油画", "水彩"]:
    print(f"\n  🎨 {style}风格:")
    station.generate("a cute cat sleeping on a warm windowsill", style=style, project_id=pid)

# 图生图测试
print("\n[测试2: 图生图]")
print("  🎨 风格转换:")
station.generate("convert to anime style", style="动漫", mode="img2img",
                 project_id=pid, strength=0.7)

# 局部重绘测试
print("\n[测试3: 局部重绘]")
print("  🎨 替换背景:")
station.generate("beautiful sunset beach background", style="照片",
                 mode="inpaint", project_id=pid, strength=0.8)

# 超分辨率测试
print("\n[测试4: 超分辨率]")
print("  🎨 4倍放大:")
station.generate("", mode="upscale", project_id=pid, scale=4)

# ============================================================================
# 5. 批量生成
# ============================================================================
print("\n\n--- 5. 批量生成 ---")

pid2 = station.create_project("风景系列")
styles = ["照片", "油画", "水彩", "幻想", "赛博朋克"]

print(f"批量生成 5 种风格的风景图:")
results = station.batch_generate(
    "a majestic mountain lake at sunrise", styles, project_id=pid2
)
for r in results:
    print(f"  ✅ {r.get('positive', '')[:50]}... seed={r.get('seed', '?')}")

# ============================================================================
# 6. 工作流模板
# ============================================================================
print("\n--- 6. 工作流模板 ---")
print("""
预设工作流（自动化复杂任务）：

工作流1: 角色设计
  1. txt2img: 生成角色全身图
  2. txt2img: 换角度（正面/侧面/背面）
  3. inpaint: 微调细节
  4. upscale: 放大到高分辨率

工作流2: 场景概念图
  1. txt2img: 生成多个构图方案
  2. img2img: 选中最好的做风格微调
  3. outpaint: 扩展画布
  4. upscale: 放大

工作流3: 产品展示图
  1. txt2img: 生成产品图
  2. inpaint: 调整产品细节
  3. 背景替换: 更换展示背景
  4. upscale: 高清输出

工作流4: 照片转插画
  1. img2img: 照片→插画（strength=0.6）
  2. ControlNet Canny: 保持轮廓
  3. inpaint: 修复不满意的区域
  4. upscale: 放大
""")

workflows = {
    "角色设计": ["txt2img(全身图)", "txt2img(多角度)", "inpaint(微调)", "upscale(4x)"],
    "场景概念": ["txt2img(多方案)", "img2img(风格)", "outpaint(扩展)", "upscale(2x)"],
    "产品展示": ["txt2img(产品)", "inpaint(细节)", "背景替换", "upscale(4x)"],
    "照片转插画": ["img2img(转风格)", "ControlNet(轮廓)", "inpaint(修复)", "upscale(2x)"],
}

print("预设工作流:")
for name, steps in workflows.items():
    print(f"  [{name}] {' → '.join(steps)}")

# ============================================================================
# 7. 项目架构总结
# ============================================================================
stats = station.get_stats()
print(f"\n\n--- 7. 项目架构总结 ---")
print(f"""
┌────────────────────────────────────────────────────────┐
│           AI 绘画工作站 - 项目架构                      │
├────────────────────────────────────────────────────────┤
│                                                        │
│  AIPaintingStation（主控）                              │
│  ├── generate()          统一生成接口                  │
│  ├── batch_generate()    批量多风格生成                │
│  ├── create_project()    项目管理                      │
│  └── get_stats()         统计信息                      │
│                                                        │
│  PromptEngine（提示词引擎）                            │
│  ├── build_prompt()      风格预设+质量标签             │
│  ├── optimize_with_llm() LLM 提示词优化               │
│  └── STYLE_PRESETS       6种风格预设                   │
│                                                        │
│  GenerationEngine（生成引擎）                          │
│  ├── txt2img()           文生图                        │
│  ├── img2img()           图生图                        │
│  ├── inpaint()           局部重绘                      │
│  └── upscale()           超分辨率                      │
│                                                        │
│  整合的知识点                                          │
│  ├── 第1课: 扩散模型原理+模型选型                     │
│  ├── 第2课: DALL-E API 生成                           │
│  ├── 第3课: Stable Diffusion 本地部署                 │
│  ├── 第4课: Prompt 工程（风格/权重/模板）             │
│  ├── 第5课: ControlNet 精确控制                       │
│  └── 第6课: 图像编辑（Inpaint/风格迁移/超分）        │
│                                                        │
│  统计: {stats['projects']}个项目, {stats['total_images']}张图片, {stats['history']}条记录     │
│                                                        │
│  扩展方向                                              │
│  → 接入真实 SD/SDXL diffusers 后端                    │
│  → 接入 ComfyUI API（工作流编排）                     │
│  → 添加 ControlNet 支持                               │
│  → 添加 IP-Adapter 风格迁移                           │
│  → 部署为 Web 服务（FastAPI + React 前端）            │
│  → 用户画廊和分享功能                                 │
└────────────────────────────────────────────────────────┘
""")

print("=" * 60)
print("[完成] 第7课完成！你已经学会了：")
print("  [v] 提示词引擎（风格预设+LLM优化）")
print("  [v] 多模式生成（txt2img/img2img/inpaint/upscale）")
print("  [v] 批量多风格生成")
print("  [v] 工作流模板设计")
print("  [v] 项目管理")
print("  [v] 整合前6课所有核心知识")
print("=" * 60)
print("\nlearn-image-gen 图像生成课程全部完成！🎉")
