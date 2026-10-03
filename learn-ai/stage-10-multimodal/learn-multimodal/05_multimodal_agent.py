import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：多模态 Agent（视觉+语音+工具调用）
==============================================================================

多模态 Agent = 能看、能听、能说、能用工具的 AI 智能体

传统 Agent：只能处理文本（接收文字 → 调用工具 → 返回文字）
多模态 Agent：处理任意模态（接收图片+语音 → 调用工具 → 返回图片+语音）

本课内容：
1. 多模态 Agent 架构
2. 视觉 Agent（看图→分析→行动）
3. 语音 Agent（听→理解→回答→说）
4. 工具调用与多模态
5. LangGraph 多模态 Agent
6. 多模态 Agent 设计模式
==============================================================================
"""

import json
import numpy as np
from datetime import datetime

print("=" * 60)
print("第5课：多模态 Agent")
print("=" * 60)

# ============================================================================
# 1. 多模态 Agent 架构
# ============================================================================
print("\n--- 1. 架构 ---")
print("""
多模态 Agent 的核心循环：

  感知（多模态输入）→ 思考（多模态LLM）→ 行动（工具调用）→ 反馈

  ┌─────────────────────────────────────────────────────┐
  │                多模态 Agent                          │
  │                                                     │
  │  输入层                                             │
  │  ├── 文本：用户消息                                 │
  │  ├── 图像：截图/照片/文档                           │
  │  ├── 音频：语音输入                                 │
  │  └── 视频：实时摄像头                               │
  │                                                     │
  │  处理层                                             │
  │  ├── 多模态 LLM（GPT-4o / Qwen2-VL）              │
  │  ├── 意图识别 + 任务规划                            │
  │  └── 工具选择 + 参数生成                            │
  │                                                     │
  │  工具层                                             │
  │  ├── 视觉工具：OCR / 检测 / 搜索                   │
  │  ├── 音频工具：ASR / TTS / 情感分析                │
  │  ├── 生成工具：DALL-E / SD / 图像编辑              │
  │  ├── 搜索工具：Web搜索 / 知识库检索                │
  │  └── 外部工具：API调用 / 数据库 / 文件操作         │
  │                                                     │
  │  输出层                                             │
  │  ├── 文本回复                                       │
  │  ├── 生成的图像                                     │
  │  └── 语音回复（TTS）                                │
  └─────────────────────────────────────────────────────┘
""")

# ============================================================================
# 2. 视觉 Agent
# ============================================================================
print("\n--- 2. 视觉 Agent ---")
print("""
视觉 Agent = 能"看"的 Agent

场景示例：
  用户上传一张电路板照片
  → Agent 识别元器件 → 检测焊接缺陷 → 查询规格书 → 生成报告

```python
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

@tool
def analyze_image(image_b64: str, task: str) -> str:
    '''分析图像内容'''
    response = vision_llm.invoke([HumanMessage(content=[
        {"type": "text", "text": task},
        {"type": "image_url", "image_url": {
            "url": f"data:image/png;base64,{image_b64}"
        }}
    ])])
    return response.content

@tool
def detect_objects(image_b64: str) -> str:
    '''检测图像中的物体'''
    # 调用 YOLO 或 VLM 检测
    return "检测到: person(0.95), car(0.87), dog(0.82)"

@tool
def ocr_extract(image_b64: str) -> str:
    '''OCR 提取文字'''
    # 调用 PaddleOCR 或 VLM
    return "提取的文字内容..."

@tool
def generate_image(prompt: str) -> str:
    '''根据描述生成图像'''
    # 调用 DALL-E 3
    return "generated_image_url"

@tool
def search_similar_images(image_b64: str) -> str:
    '''搜索相似图片'''
    # CLIP 嵌入 + 向量搜索
    return "找到3张相似图片"

# 创建视觉 Agent
llm = ChatOpenAI(model="gpt-4o").bind_tools([
    analyze_image, detect_objects, ocr_extract,
    generate_image, search_similar_images
])
```
""")

# 模拟视觉 Agent
import httpx

class VisionAgent:
    """视觉 Agent"""

    def __init__(self):
        self.tools = {
            "analyze": lambda img, task: f"[分析结果] {task}: 图像分析完成",
            "detect": lambda img: "[检测] person(0.95), car(0.87)",
            "ocr": lambda img: "[OCR] 提取到3行文字",
            "generate": lambda prompt: f"[生成] 已根据'{prompt[:20]}'生成图像",
            "search": lambda img: "[搜索] 找到5张相似图片",
        }

    def plan_and_execute(self, user_msg: str, has_image: bool = False) -> list:
        """规划并执行任务"""
        steps = []
        msg_lower = user_msg.lower()

        if "识别" in user_msg or "检测" in user_msg:
            steps.append(("detect", "检测图像中的物体"))
        if "文字" in user_msg or "ocr" in msg_lower:
            steps.append(("ocr", "提取图像中的文字"))
        if "分析" in user_msg or "描述" in user_msg:
            steps.append(("analyze", "分析图像内容"))
        if "生成" in user_msg or "画" in user_msg:
            steps.append(("generate", f"生成图像: {user_msg}"))
        if "搜索" in user_msg or "找" in user_msg:
            steps.append(("search", "搜索相似图片"))

        if not steps:
            steps.append(("analyze", "通用分析"))

        results = []
        for tool_name, desc in steps:
            result = f"✅ {desc} → 完成"
            results.append({"tool": tool_name, "description": desc, "result": result})
        return results

agent = VisionAgent()
print("视觉 Agent 测试:")
tasks = [
    "分析这张产品照片的设计特点",
    "识别图中的所有物体并提取文字",
    "帮我生成一张类似风格的图片",
]
for task in tasks:
    results = agent.plan_and_execute(task, has_image=True)
    print(f"\n  任务: {task}")
    for r in results:
        print(f"    {r['result']}")

# ============================================================================
# 3. 语音 Agent
# ============================================================================
print("\n\n--- 3. 语音 Agent ---")
print("""
语音 Agent = 能"听"和"说"的 Agent

  用户语音 → ASR → 多模态LLM(+工具调用) → TTS → 语音回复

```python
class VoiceAgent:
    def __init__(self):
        self.asr = WhisperASR()
        self.tts = EdgeTTS()
        self.llm = ChatOpenAI(model="gpt-4o").bind_tools([
            search_web, get_weather, set_alarm, play_music,
            send_message, translate_text
        ])
    
    async def process_voice(self, audio_bytes):
        # 1. 语音→文字
        text = self.asr.transcribe(audio_bytes)
        
        # 2. LLM + 工具调用
        response = await self.llm.ainvoke([
            SystemMessage("你是语音助手，回答要简洁（适合语音播报）"),
            HumanMessage(text)
        ])
        
        # 处理工具调用
        while response.tool_calls:
            tool_results = execute_tools(response.tool_calls)
            response = await self.llm.ainvoke([...tool_results...])
        
        # 3. 文字→语音
        audio = await self.tts.synthesize(response.content)
        return audio
```

语音 Agent 的特殊设计：
- 回复要简短（适合听觉）
- 需要确认机制（"你是说...对吗？"）
- 支持打断（用户随时可以插话）
- 错误恢复（"我没听清，请再说一次"）
""")

# ============================================================================
# 4. 工具调用与多模态
# ============================================================================
print("\n--- 4. 多模态工具调用 ---")
print("""
多模态 Agent 的工具可以接收和返回多种模态：

输入多模态的工具：
```python
@tool
def analyze_receipt(image_b64: str) -> dict:
    '''分析收据/发票图片，提取金额和项目'''
    ...

@tool
def transcribe_meeting(audio_url: str) -> str:
    '''转录会议录音为文字'''
    ...

@tool
def describe_video(video_url: str, question: str) -> str:
    '''分析视频内容并回答问题'''
    ...
```

输出多模态的工具：
```python
@tool
def generate_diagram(description: str) -> str:
    '''根据描述生成流程图/架构图，返回图片URL'''
    ...

@tool  
def text_to_speech(text: str, voice: str = "小晓") -> str:
    '''将文字转为语音，返回音频文件路径'''
    ...

@tool
def create_presentation(outline: str) -> str:
    '''根据大纲生成PPT，返回文件路径'''
    ...
```

GPT-4o Function Calling + 图像输入：
```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "帮我分析这张发票"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
        ]
    }],
    tools=[{
        "type": "function",
        "function": {
            "name": "save_invoice_data",
            "parameters": {
                "type": "object",
                "properties": {
                    "vendor": {"type": "string"},
                    "amount": {"type": "number"},
                    "date": {"type": "string"},
                    "items": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    }]
)
# GPT-4o 看图 → 提取信息 → 调用 save_invoice_data 工具
```
""")

# ============================================================================
# 5. LangGraph 多模态 Agent
# ============================================================================
print("\n--- 5. LangGraph 多模态 ---")
print("""
用 LangGraph 构建多模态 Agent 工作流：

```python
from langgraph.graph import StateGraph, MessagesState

class MultimodalState(MessagesState):
    images: list[str]       # Base64 图片列表
    audio_files: list[str]  # 音频文件路径
    generated_images: list[str]  # 生成的图片

def perception_node(state: MultimodalState):
    '''感知节点：分析输入的多模态内容'''
    analysis = []
    for img in state.get("images", []):
        desc = vision_llm.describe(img)
        analysis.append(f"[图片] {desc}")
    return {"messages": [AIMessage(content="\\n".join(analysis))]}

def reasoning_node(state: MultimodalState):
    '''推理节点：基于感知结果做决策'''
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

def action_node(state: MultimodalState):
    '''行动节点：执行工具调用'''
    # 根据 LLM 决策执行对应工具
    ...

def output_node(state: MultimodalState):
    '''输出节点：生成多模态回复'''
    # 文本回复 + 可能的图像/语音生成
    ...

# 构建图
graph = StateGraph(MultimodalState)
graph.add_node("perceive", perception_node)
graph.add_node("reason", reasoning_node)
graph.add_node("act", action_node)
graph.add_node("output", output_node)

graph.set_entry_point("perceive")
graph.add_edge("perceive", "reason")
graph.add_conditional_edges("reason", should_act_or_output)
graph.add_edge("act", "reason")  # 工具结果反馈
graph.add_edge("output", END)

agent = graph.compile()
```
""")

# ============================================================================
# 6. 设计模式
# ============================================================================
print("\n--- 6. 多模态 Agent 设计模式 ---")
print("""
模式1: 感知-推理-行动（PRA）
  适合：单次任务（分析一张图、回答一个问题）
  感知 → 推理 → 行动 → 输出

模式2: 多模态路由
  适合：多种任务类型（根据输入模态路由到不同处理器）
  输入 → 模态检测 → 路由 → 专用处理器 → 输出

模式3: 协作多 Agent
  适合：复杂任务（视觉Agent + 语音Agent + 工具Agent 协作）
  ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ 视觉Agent│ ←→ │ 编排Agent│ ←→ │ 语音Agent│
  └──────────┘    └────┬─────┘    └──────────┘
                       │
                  ┌────▼─────┐
                  │ 工具Agent│
                  └──────────┘

模式4: 反思增强
  适合：需要高准确度的场景
  生成 → 自检（"这个分析准确吗？"）→ 修正 → 输出

最佳实践：
  ✅ 简单任务用模式1（PRA）
  ✅ 多模态入口用模式2（路由）
  ✅ 复杂业务用模式3（多Agent）
  ✅ 高准确要求用模式4（反思）
""")

# 模拟完整的多模态 Agent 交互
print("\n多模态 Agent 完整交互演示:")
interactions = [
    {
        "input": "🎤 语音: '帮我看看这张发票，总金额是多少？' + 📷 发票图片",
        "steps": ["ASR: 语音→文字", "VLM: 分析发票图片", "OCR: 提取金额", "TTS: 语音回复"],
        "output": "🔊 '这张发票的总金额是1,250元，开票日期是3月15日。'"
    },
    {
        "input": "💬 文字: '把这张照片改成油画风格' + 📷 照片",
        "steps": ["VLM: 分析照片内容", "Prompt: 生成风格描述", "SD: img2img风格转换"],
        "output": "🖼️ [油画风格的图片] + '已将照片转换为油画风格'"
    },
    {
        "input": "🎤 语音: '分析一下这个月的销售数据' + 📊 数据图表",
        "steps": ["ASR: 语音→文字", "VLM: 读取图表数据", "LLM: 分析趋势", "TTS: 语音播报"],
        "output": "🔊 '本月销售额环比增长15%，主要增长来自线上渠道。'"
    },
]

for i, interaction in enumerate(interactions, 1):
    print(f"\n  场景{i}:")
    print(f"  输入: {interaction['input']}")
    print(f"  步骤: {' → '.join(interaction['steps'])}")
    print(f"  输出: {interaction['output']}")

print("\n" + "=" * 60)
print("[完成] 第5课完成！你已经学会了：")
print("  [v] 多模态 Agent 架构（感知→思考→行动→反馈）")
print("  [v] 视觉 Agent（看图分析+工具调用）")
print("  [v] 语音 Agent（听说+工具调用）")
print("  [v] 多模态工具调用（输入/输出多模态）")
print("  [v] LangGraph 多模态 Agent")
print("  [v] 四种 Agent 设计模式")
print("=" * 60)
print("\n下一课：06_video_and_realtime.py - 视频理解与实时交互")
