import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：高级模式（强制调用 / 路由 / 嵌套 / 流式）
==============================================================================

掌握了基本的工具调用后，本课深入高级用法：

1. 强制工具调用（tool_choice）
   - 强制 LLM 必须调用工具
   - 强制调用指定的工具
   - 禁止调用工具

2. 工具路由（Tool Routing）
   - 根据用户意图动态选择工具集
   - 分层工具调用

3. 嵌套工具调用（Nested Tool Calls）
   - 一个工具的结果作为另一个工具的输入
   - 工具编排（Orchestration）

4. 流式工具调用（Streaming）
   - 实时获取工具调用过程
   - 提升用户体验
==============================================================================
"""

import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_community.chat_models import ChatOllama

print("=" * 60)
print("第5课：高级模式")
print("=" * 60)

# 准备基础工具
@tool
def get_weather(city: str) -> str:
    """查询城市天气。"""
    db = {"北京": "晴，25°C", "上海": "多云，22°C", "广州": "雨，30°C"}
    return db.get(city, f"暂无{city}数据")

@tool
def calculator(expression: str) -> str:
    """计算数学表达式。"""
    try:
        return str(eval(expression))
    except:
        return "计算错误"

@tool
def translate(text: str, target_lang: str = "english") -> str:
    """翻译文本。参数 target_lang 为目标语言如 'english'、'chinese'。"""
    # 模拟翻译
    translations = {
        ("你好世界", "english"): "Hello World",
        ("Hello World", "chinese"): "你好世界",
    }
    return translations.get((text, target_lang), f"[翻译] {text} → ({target_lang})")

@tool
def summarize(text: str, max_words: int = 50) -> str:
    """摘要文本，将长文本压缩为简短摘要。"""
    if len(text) <= max_words:
        return text
    return text[:max_words * 2] + "..."

@tool
def format_report(title: str, sections: str) -> str:
    """格式化生成报告。sections 为逗号分隔的段落内容。"""
    parts = sections.split(",")
    report = f"# {title}\n\n"
    for i, part in enumerate(parts, 1):
        report += f"## 第{i}部分\n{part.strip()}\n\n"
    return report

all_tools = [get_weather, calculator, translate, summarize, format_report]
tool_map = {t.name: t for t in all_tools}

llm = ChatOllama(model="qwen2.5:7b", temperature=0)

# ============================================================================
# 1. 强制工具调用（tool_choice）
# ============================================================================
print("\n--- 1. 强制工具调用 ---")
print("""
LangChain 的 bind_tools 支持 tool_choice 参数：

  llm.bind_tools(tools, tool_choice="auto")     # LLM 自己决定（默认）
  llm.bind_tools(tools, tool_choice="none")      # 禁止调用
  llm.bind_tools(tools, tool_choice="any")       # 必须调用某个工具
  llm.bind_tools(tools, tool_choice="get_weather")  # 必须调用指定工具
""")

# 1.1 auto（默认）
print("[tool_choice='auto'] LLM 自行决定:")
llm_auto = llm.bind_tools(all_tools, tool_choice="auto")
resp = llm_auto.invoke([HumanMessage(content="你好")])
print(f"  '你好' → tool_calls={resp.tool_calls}, content='{resp.content[:50]}...'")

# 1.2 强制调用指定工具
print("\n[tool_choice='calculator'] 强制使用计算器:")
llm_forced = llm.bind_tools(all_tools, tool_choice="calculator")
resp = llm_forced.invoke([HumanMessage(content="你好")])
if resp.tool_calls:
    print(f"  '你好' → 被强制调用: {resp.tool_calls[0]['name']}({resp.tool_calls[0]['args']})")
else:
    print(f"  结果: {resp.content[:60]}...")

# 1.3 必须调用任意工具
print("\n[tool_choice='any'] 必须调用某个工具:")
llm_any = llm.bind_tools(all_tools, tool_choice="any")
resp = llm_any.invoke([HumanMessage(content="你好，今天心情不错")])
if resp.tool_calls:
    print(f"  被迫调用: {resp.tool_calls[0]['name']}({resp.tool_calls[0]['args']})")
else:
    print(f"  结果: {resp.content[:60]}...")

print("""
使用场景：
- auto: 大多数情况（推荐）
- none: 纯聊天模式，不希望调用工具
- 指定工具: 表单填写、信息提取等确定性场景
- any: 确保至少执行一个动作
""")

# ============================================================================
# 2. 工具路由（动态选择工具集）
# ============================================================================
print("\n--- 2. 工具路由 ---")
print("""
不同类型的问题使用不同的工具集。
先识别意图，再绑定对应的工具。

  用户问题 → 意图分类 → ┬→ 查询类 → [天气, 搜索, 汇率]
                          ├→ 计算类 → [计算器]
                          ├→ 翻译类 → [翻译, 摘要]
                          └→ 通用   → [所有工具]

好处：
- 减少工具数量，提高 LLM 选择准确性
- 不同场景可以有不同的 system prompt
""")

# 工具分组
TOOL_GROUPS = {
    "query": {
        "tools": [get_weather],
        "system": "你是一个信息查询助手。使用工具获取准确数据。"
    },
    "math": {
        "tools": [calculator],
        "system": "你是一个数学助手。使用计算器工具精确计算。"
    },
    "language": {
        "tools": [translate, summarize],
        "system": "你是一个语言处理助手。使用工具完成翻译和摘要。"
    },
    "general": {
        "tools": all_tools,
        "system": "你是一个全能助手。根据需要使用合适的工具。"
    }
}

def classify_intent(question: str) -> str:
    """简单的意图分类（实际可以用 LLM 分类）"""
    q = question.lower()
    if any(w in q for w in ["天气", "温度", "weather"]):
        return "query"
    elif any(w in q for w in ["计算", "算", "+", "-", "*", "/", "等于"]):
        return "math"
    elif any(w in q for w in ["翻译", "translate", "摘要", "总结"]):
        return "language"
    return "general"

def routed_chat(question: str) -> str:
    """带路由的工具调用"""
    intent = classify_intent(question)
    group = TOOL_GROUPS[intent]

    print(f"  意图: {intent} → 工具: {[t.name for t in group['tools']]}")

    llm_routed = llm.bind_tools(group["tools"])
    messages = [
        SystemMessage(content=group["system"]),
        HumanMessage(content=question),
    ]

    # 工具调用循环
    for _ in range(5):
        resp = llm_routed.invoke(messages)
        messages.append(resp)

        if resp.tool_calls:
            for tc in resp.tool_calls:
                print(f"    🔧 {tc['name']}({tc['args']})")
                func = tool_map.get(tc["name"])
                result = func.invoke(tc["args"]) if func else "未知"
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
        else:
            return resp.content

    return "超时"

# 测试路由
test_cases = [
    "北京天气怎么样？",
    "计算 (15 + 25) * 4",
    "把'你好世界'翻译成英文",
]

for q in test_cases:
    print(f"\n  Q: {q}")
    a = routed_chat(q)
    print(f"  A: {a[:100]}...")

# ============================================================================
# 3. 嵌套工具调用（工具编排）
# ============================================================================
print("\n\n--- 3. 嵌套工具调用 ---")
print("""
一个工具的输出作为另一个工具的输入。
LLM 自动编排调用顺序。

例："查北京天气，然后翻译成英文"
  Step 1: get_weather("北京") → "晴，25°C"
  Step 2: translate("晴，25°C", "english") → "Sunny, 25°C"

更复杂的例子：
  "生成一份北京和上海的天气对比报告"
  Step 1: get_weather("北京") + get_weather("上海")  （并行）
  Step 2: format_report("天气对比", "北京晴25°C, 上海多云22°C")
""")

llm_all = llm.bind_tools(all_tools)

def orchestrated_chat(question: str) -> str:
    """支持嵌套调用的工具编排"""
    messages = [
        SystemMessage(content="你是一个助手。可以连续使用多个工具完成复杂任务。"),
        HumanMessage(content=question),
    ]

    for i in range(8):  # 允许更多轮次
        resp = llm_all.invoke(messages)
        messages.append(resp)

        if resp.tool_calls:
            print(f"    [Step {i+1}] 调用 {len(resp.tool_calls)} 个工具:")
            for tc in resp.tool_calls:
                print(f"      🔧 {tc['name']}({str(tc['args'])[:60]})")
                func = tool_map.get(tc["name"])
                result = func.invoke(tc["args"]) if func else "未知"
                print(f"      📋 → {str(result)[:80]}")
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
        else:
            return resp.content

    return "超时"

print("\n[测试: 嵌套调用]")
print("  Q: 查北京天气然后翻译成英文")
answer = orchestrated_chat("查一下北京的天气，然后把天气信息翻译成英文")
print(f"  A: {answer[:150]}...")

# ============================================================================
# 4. 流式工具调用
# ============================================================================
print("\n\n--- 4. 流式工具调用 ---")
print("""
流式输出让用户实时看到 Agent 的执行过程：
- 正在思考...
- 调用工具 get_weather...
- 收到结果...
- 生成回答...

LangChain 支持 stream() 方法获取流式输出。
""")

print("[流式输出演示]")
print("  Q: 北京天气如何？")

llm_stream = llm.bind_tools([get_weather, calculator])
messages = [
    SystemMessage(content="你是一个助手。使用工具获取信息。"),
    HumanMessage(content="北京天气如何？"),
]

# 第一次调用（可能返回 tool_calls）
full_response = llm_stream.invoke(messages)
messages.append(full_response)

if full_response.tool_calls:
    print(f"  → 决定调用工具...")
    for tc in full_response.tool_calls:
        print(f"  → 🔧 {tc['name']}({tc['args']})")
        func = tool_map.get(tc["name"])
        result = func.invoke(tc["args"]) if func else "未知"
        print(f"  → 📋 结果: {result}")
        messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    # 第二次调用，流式输出最终回答
    print("  → 生成回答: ", end="", flush=True)
    collected = []
    for chunk in llm_stream.stream(messages):
        if chunk.content:
            print(chunk.content, end="", flush=True)
            collected.append(chunk.content)
    print()  # 换行
else:
    print(f"  → {full_response.content[:100]}...")

# ============================================================================
# 5. 结构化提取（Extraction）
# ============================================================================
print("\n--- 5. 结构化提取 ---")
print("""
Function Calling 的另一个强大用途：结构化信息提取。
把非结构化文本转为结构化数据。

原理：定义一个"提取函数"，让 LLM 必须调用它（tool_choice=指定工具）。
LLM 的输出就是结构化的参数！

例：从 "我叫张三，今年25岁，在北京工作"
  → extract_person_info(name="张三", age=25, city="北京")
""")

@tool
def extract_person_info(name: str, age: int, city: str, occupation: str = "") -> str:
    """提取人物信息。从文本中提取姓名、年龄、城市、职业。"""
    return json.dumps({
        "name": name, "age": age, "city": city, "occupation": occupation
    }, ensure_ascii=False)

@tool
def extract_product_info(name: str, price: float, category: str, rating: float = 0) -> str:
    """提取商品信息。从文本中提取商品名、价格、类别、评分。"""
    return json.dumps({
        "name": name, "price": price, "category": category, "rating": rating
    }, ensure_ascii=False)

# 强制调用提取工具
llm_extract_person = llm.bind_tools([extract_person_info], tool_choice="extract_person_info")
llm_extract_product = llm.bind_tools([extract_product_info], tool_choice="extract_product_info")

# 提取人物信息
text1 = "我叫李明，今年30岁，在上海做软件工程师"
resp1 = llm_extract_person.invoke([HumanMessage(content=f"从以下文本中提取信息：{text1}")])
if resp1.tool_calls:
    print(f"  文本: {text1}")
    print(f"  提取: {resp1.tool_calls[0]['args']}")

# 提取商品信息
text2 = "这款蓝牙耳机售价299元，属于数码配件，用户评分4.8"
resp2 = llm_extract_product.invoke([HumanMessage(content=f"从以下文本中提取信息：{text2}")])
if resp2.tool_calls:
    print(f"\n  文本: {text2}")
    print(f"  提取: {resp2.tool_calls[0]['args']}")

print("""
结构化提取的应用：
- 简历解析 → 提取姓名、学历、经验
- 订单处理 → 提取商品、数量、地址
- 日志分析 → 提取时间、级别、错误信息
- 评论分析 → 提取情感、主题、评分
""")

# ============================================================================
# 6. 高级模式总结
# ============================================================================
print("\n--- 6. 高级模式总结 ---")
print("""
┌──────────────────┬──────────────────────────────────────┐
│  模式             │  场景                                 │
├──────────────────┼──────────────────────────────────────┤
│  tool_choice     │  控制是否/调用哪个工具                 │
│  工具路由         │  根据意图动态选择工具集                │
│  嵌套调用         │  工具结果作为下个工具的输入            │
│  流式输出         │  实时展示执行过程                      │
│  结构化提取       │  把文本转为结构化数据                  │
│  并行+多轮        │  复杂任务的工具编排                    │
└──────────────────┴──────────────────────────────────────┘
""")

print("\n" + "=" * 60)
print("[完成] 第5课完成！你已经学会了：")
print("  [v] tool_choice 控制调用行为")
print("  [v] 工具路由（意图→工具集映射）")
print("  [v] 嵌套工具调用（工具编排）")
print("  [v] 流式工具调用")
print("  [v] 结构化信息提取")
print("=" * 60)
print("\n下一课：06_real_world_tools.py - 真实场景工具设计")
