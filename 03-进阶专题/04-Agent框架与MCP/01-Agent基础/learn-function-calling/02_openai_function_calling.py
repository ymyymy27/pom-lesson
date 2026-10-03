import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：OpenAI Function Calling 实战
==============================================================================

本课使用 OpenAI 的原生 API 来实战 Function Calling。
这是最标准、最成熟的实现，其他模型提供商大多兼容此格式。

OpenAI Function Calling 的演进：
- 2023.06: 首次推出 function_calling（旧版）
- 2023.11: 升级为 tool_calls（新版，支持并行调用）
- 2024+:   所有新模型默认使用 tool_calls 格式

本课使用新版 tool_calls 格式（推荐）。

⚠️ 注意：本课需要 OpenAI API Key。
如果没有，可以先阅读代码理解流程，下一课用 Ollama 免费替代。
也可以使用兼容 OpenAI 格式的国产 API（如 DeepSeek、智谱）。
==============================================================================
"""

import json
import os

print("=" * 60)
print("第2课：OpenAI Function Calling 实战")
print("=" * 60)

# ============================================================================
# 1. 环境准备
# ============================================================================
print("\n--- 1. 环境准备 ---")

# 尝试导入 openai
try:
    from openai import OpenAI
    print("  openai 库已安装 ✓")
except ImportError:
    print("  ❌ 请先安装: pip install openai")
    print("  本课需要 openai>=1.30.0")
    sys.exit(1)

# 初始化客户端
# 支持多种方式：
#   1. 环境变量 OPENAI_API_KEY
#   2. 兼容 API（如 DeepSeek）设置 base_url
api_key = os.environ.get("OPENAI_API_KEY", "")
base_url = os.environ.get("OPENAI_BASE_URL", None)  # 兼容 API 可设置

if not api_key:
    print("""
  ⚠️  未检测到 OPENAI_API_KEY 环境变量。
  
  设置方式：
    set OPENAI_API_KEY=sk-xxx          # Windows
    export OPENAI_API_KEY=sk-xxx       # macOS/Linux
  
  或使用兼容 API：
    set OPENAI_API_KEY=your-key
    set OPENAI_BASE_URL=https://api.deepseek.com/v1
  
  本课将使用模拟数据演示流程。
""")
    USE_REAL_API = False
else:
    client = OpenAI(api_key=api_key, base_url=base_url)
    USE_REAL_API = True
    print(f"  API Key 已配置 ✓")
    if base_url:
        print(f"  Base URL: {base_url}")

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
print(f"  使用模型: {MODEL}")

# ============================================================================
# 2. 定义工具（Tools）
# ============================================================================
print("\n--- 2. 定义工具 ---")

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的当前天气信息，返回温度、湿度、风力和天气描述",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'、'New York'"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位，默认celsius（摄氏度）"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式。支持加减乘除、幂运算、括号、取余等",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '(15 + 27) * 3' 或 '2 ** 10'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "在知识库中搜索技术相关信息。支持搜索编程语言、框架、工具等",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["programming", "ai", "devops", "general"],
                        "description": "搜索类别，可选"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

print(f"定义了 {len(tools)} 个工具:")
for t in tools:
    func = t["function"]
    params = list(func["parameters"]["properties"].keys())
    required = func["parameters"].get("required", [])
    print(f"  🔧 {func['name']}({', '.join(params)})")
    print(f"     必需: {required} | {func['description'][:40]}...")

# ============================================================================
# 3. 实现工具函数
# ============================================================================
print("\n--- 3. 实现工具函数 ---")

def get_weather(city: str, unit: str = "celsius") -> str:
    """查询天气（模拟数据）"""
    weather_db = {
        "北京": {"temp": 25, "humidity": 40, "wind": "北风3级", "desc": "晴天"},
        "上海": {"temp": 22, "humidity": 65, "wind": "东风2级", "desc": "多云"},
        "广州": {"temp": 28, "humidity": 80, "wind": "南风1级", "desc": "小雨"},
        "深圳": {"temp": 27, "humidity": 75, "wind": "西南风2级", "desc": "阵雨"},
        "成都": {"temp": 20, "humidity": 70, "wind": "微风", "desc": "阴天"},
    }
    data = weather_db.get(city, {"temp": 20, "humidity": 50, "wind": "未知", "desc": "暂无数据"})
    temp = data["temp"] if unit == "celsius" else round(data["temp"] * 9/5 + 32, 1)
    unit_str = "°C" if unit == "celsius" else "°F"
    return json.dumps({
        "city": city, "temperature": f"{temp}{unit_str}",
        "humidity": f"{data['humidity']}%", "wind": data["wind"],
        "description": data["desc"]
    }, ensure_ascii=False)

def calculator(expression: str) -> str:
    """数学计算"""
    try:
        allowed = set("0123456789+-*/().** %")
        if not all(c in allowed for c in expression):
            return json.dumps({"error": f"不安全的表达式: {expression}"})
        result = eval(expression)
        return json.dumps({"expression": expression, "result": result})
    except Exception as e:
        return json.dumps({"error": str(e)})

def search_knowledge(query: str, category: str = "general") -> str:
    """知识库搜索（模拟数据）"""
    kb = {
        "python": "Python 是通用编程语言，由 Guido van Rossum 于 1991 年创建。",
        "fastapi": "FastAPI 是高性能 Python Web 框架，基于 Starlette 和 Pydantic。",
        "docker": "Docker 是容器化平台，将应用和依赖打包到容器中运行。",
        "langchain": "LangChain 是 LLM 应用开发框架，支持链、记忆、检索等。",
        "rag": "RAG 通过检索外部知识增强 LLM 回答，减少幻觉问题。",
    }
    for key, value in kb.items():
        if key in query.lower():
            return json.dumps({"query": query, "result": value, "category": category}, ensure_ascii=False)
    return json.dumps({"query": query, "result": "未找到相关信息", "category": category}, ensure_ascii=False)

# 工具名 → 函数的映射
tool_functions = {
    "get_weather": get_weather,
    "calculator": calculator,
    "search_knowledge": search_knowledge,
}

print("工具函数已实现 ✓")

# ============================================================================
# 4. 封装完整的调用流程
# ============================================================================
print("\n--- 4. 封装完整的调用流程 ---")

def chat_with_tools(messages: list, max_iterations: int = 5) -> str:
    """
    带 Function Calling 的完整对话流程。
    
    流程：
    1. 发送消息 + 工具定义 → LLM
    2. 如果 LLM 返回 tool_calls → 执行工具 → 继续
    3. 如果 LLM 返回纯文本 → 返回最终答案
    4. 最多迭代 max_iterations 次
    """
    if not USE_REAL_API:
        return _simulate_chat(messages)

    for i in range(max_iterations):
        # 调用 API
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",  # 让 LLM 自己决定是否调用工具
        )

        assistant_message = response.choices[0].message

        # 将 AI 的回复加入消息列表
        messages.append(assistant_message.model_dump())

        # 检查是否有工具调用
        if assistant_message.tool_calls:
            print(f"  [迭代{i+1}] LLM 请求调用 {len(assistant_message.tool_calls)} 个工具")

            for tool_call in assistant_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                print(f"    🔧 {func_name}({func_args})")

                # 执行工具
                func = tool_functions.get(func_name)
                if func:
                    result = func(**func_args)
                else:
                    result = json.dumps({"error": f"未知函数: {func_name}"})

                print(f"    📋 → {result[:80]}...")

                # 添加工具结果消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
        else:
            # 没有工具调用 → 返回最终答案
            print(f"  [迭代{i+1}] LLM 生成最终回答")
            return assistant_message.content

    return "达到最大迭代次数"

def _simulate_chat(messages: list) -> str:
    """无 API Key 时的模拟演示"""
    user_msg = messages[-1]["content"] if messages else ""
    print(f"  [模拟模式] 用户: {user_msg[:50]}")
    print(f"  [模拟] LLM 会分析问题并决定是否调用工具")

    if "天气" in user_msg:
        print(f"    🔧 get_weather(city='北京')")
        result = get_weather("北京")
        print(f"    📋 → {result[:80]}")
        return f"根据查询结果，北京今天天气晴朗，气温25°C，湿度40%，北风3级。"
    elif "计算" in user_msg or "+" in user_msg or "*" in user_msg:
        print(f"    🔧 calculator(expression='...')")
        return f"计算结果已返回。"
    else:
        print(f"  [模拟] 不需要工具，直接回答")
        return f"这是一个模拟回答。实际使用需要配置 API Key。"

print("chat_with_tools 函数已定义 ✓")

# ============================================================================
# 5. 测试单工具调用
# ============================================================================
print("\n--- 5. 测试单工具调用 ---")

# 5.1 天气查询
print("\n[测试1: 天气查询]")
messages = [
    {"role": "system", "content": "你是一个有帮助的助手。使用工具获取准确信息。"},
    {"role": "user", "content": "北京今天天气怎么样？"}
]
answer = chat_with_tools(messages.copy())
print(f"  Q: 北京今天天气怎么样？")
print(f"  A: {answer[:120]}...")

# 5.2 数学计算
print("\n[测试2: 数学计算]")
messages = [
    {"role": "system", "content": "你是一个有帮助的助手。数学计算请使用 calculator 工具。"},
    {"role": "user", "content": "计算 (125 + 375) * 2.5 等于多少"}
]
answer = chat_with_tools(messages.copy())
print(f"  Q: 计算 (125 + 375) * 2.5")
print(f"  A: {answer[:120]}...")

# 5.3 知识搜索
print("\n[测试3: 知识搜索]")
messages = [
    {"role": "system", "content": "你是一个技术助手。查找信息时使用 search_knowledge 工具。"},
    {"role": "user", "content": "什么是 RAG？"}
]
answer = chat_with_tools(messages.copy())
print(f"  Q: 什么是 RAG？")
print(f"  A: {answer[:120]}...")

# 5.4 不需要工具的问题
print("\n[测试4: 不需要工具]")
messages = [
    {"role": "system", "content": "你是一个有帮助的助手。"},
    {"role": "user", "content": "你好，你是谁？"}
]
answer = chat_with_tools(messages.copy())
print(f"  Q: 你好，你是谁？")
print(f"  A: {answer[:120]}...")

# ============================================================================
# 6. tool_choice 参数详解
# ============================================================================
print("\n--- 6. tool_choice 参数详解 ---")
print("""
tool_choice 控制 LLM 是否调用工具：

┌──────────────────────┬──────────────────────────────────┐
│  值                   │  行为                             │
├──────────────────────┼──────────────────────────────────┤
│  "auto"              │  LLM 自己决定是否调用（默认）      │
│  "none"              │  禁止调用任何工具                  │
│  "required"          │  必须调用至少一个工具              │
│  {"type":"function", │  强制调用指定的工具                │
│   "function":        │                                   │
│   {"name":"xxx"}}    │                                   │
└──────────────────────┴──────────────────────────────────┘
""")

if USE_REAL_API:
    # 强制不调用工具
    print("[tool_choice='none'] 禁止工具调用:")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "北京天气怎么样？"}
        ],
        tools=tools,
        tool_choice="none",
    )
    print(f"  结果: {response.choices[0].message.content[:80]}...")
    print(f"  tool_calls: {response.choices[0].message.tool_calls}")

    # 强制调用指定工具
    print("\n[tool_choice=指定工具] 强制调用 calculator:")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "你好"}  # 正常不需要工具
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "calculator"}},
    )
    if response.choices[0].message.tool_calls:
        tc = response.choices[0].message.tool_calls[0]
        print(f"  强制调用: {tc.function.name}({tc.function.arguments})")
else:
    print("  [模拟模式] 跳过 tool_choice 实际测试")
    print("  auto: LLM 自行决定 | none: 禁止 | required: 必须调用")

# ============================================================================
# 7. 错误处理
# ============================================================================
print("\n--- 7. 错误处理 ---")
print("""
工具调用可能出错，需要优雅处理：

1. 函数执行异常 → 返回错误信息给 LLM
2. 参数解析失败 → 返回参数错误说明
3. 未知函数名   → 返回"不支持的函数"
4. 超时         → 返回超时信息

LLM 收到错误信息后，通常会：
- 尝试用不同参数重试
- 换一个工具
- 直接告诉用户失败原因
""")

def safe_execute_tool(func_name: str, func_args: dict) -> str:
    """安全的工具执行封装"""
    try:
        func = tool_functions.get(func_name)
        if not func:
            return json.dumps({"error": f"不支持的函数: {func_name}"})

        result = func(**func_args)
        return result

    except TypeError as e:
        return json.dumps({"error": f"参数错误: {e}"})
    except Exception as e:
        return json.dumps({"error": f"执行失败: {type(e).__name__}: {e}"})

# 测试错误处理
print(f"  正常调用: {safe_execute_tool('get_weather', {'city': '北京'})[:60]}...")
print(f"  未知函数: {safe_execute_tool('unknown_func', {})}")
print(f"  参数错误: {safe_execute_tool('get_weather', {'wrong_param': 123})}")

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] OpenAI API 的 Function Calling 调用方式")
print("  [v] tools 参数的定义和传递")
print("  [v] 完整的 tool_calls → 执行 → tool message 流程")
print("  [v] tool_choice 控制调用行为")
print("  [v] 错误处理最佳实践")
print("=" * 60)
print("\n下一课：03_ollama_tool_use.py - Ollama 本地模型工具调用")
