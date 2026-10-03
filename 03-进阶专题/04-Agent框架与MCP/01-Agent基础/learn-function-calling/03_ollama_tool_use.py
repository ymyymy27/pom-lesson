import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：Ollama 本地模型工具调用
==============================================================================

不需要 API Key！用 Ollama 在本地免费运行支持工具调用的模型。

Ollama 支持工具调用的模型（推荐）：
- qwen2.5:7b     → 中文能力强，工具调用稳定
- llama3.1:8b    → Meta 出品，英文能力好
- mistral:7b     → 轻量高效
- command-r      → Cohere 出品，工具调用专精

本课使用两种方式调用 Ollama 的工具能力：
1. Ollama 原生 API（HTTP 请求）
2. LangChain 封装（更简洁）

前置条件：
- 安装 Ollama: https://ollama.ai
- 拉取模型: ollama pull qwen2.5:7b
- 确保服务运行: ollama serve（默认 http://localhost:11434）
==============================================================================
"""

import json

print("=" * 60)
print("第3课：Ollama 本地模型工具调用")
print("=" * 60)

# ============================================================================
# 1. Ollama 原生 API 工具调用
# ============================================================================
print("\n--- 1. Ollama 原生 API ---")
print("""
Ollama 的 /api/chat 接口兼容 OpenAI 的工具调用格式。

请求体：
{
  "model": "qwen2.5:7b",
  "messages": [...],
  "tools": [...],       ← 工具定义（与 OpenAI 格式一致）
  "stream": false
}

响应体中如果有工具调用：
{
  "message": {
    "role": "assistant",
    "content": "",
    "tool_calls": [
      {"function": {"name": "...", "arguments": {...}}}
    ]
  }
}
""")

import httpx

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"

# 定义工具（与 OpenAI 格式一致）
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的当前天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'"
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
            "description": "计算数学表达式，支持加减乘除、幂运算",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '(15+27)*3'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_info",
            "description": "搜索技术知识库，查找编程和AI相关信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# 实现工具函数
def get_weather(city: str) -> str:
    weather_db = {
        "北京": "晴天，25°C，湿度40%，北风3级",
        "上海": "多云，22°C，湿度65%，东风2级",
        "广州": "小雨，28°C，湿度80%，南风1级",
    }
    return weather_db.get(city, f"暂无 {city} 的天气数据")

def calculator(expression: str) -> str:
    try:
        allowed = set("0123456789+-*/().** ")
        if not all(c in allowed for c in expression):
            return f"不安全的表达式"
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"

def search_info(query: str) -> str:
    kb = {
        "python": "Python 是通用编程语言，广泛用于 AI、Web、数据科学。",
        "langchain": "LangChain 是 LLM 应用开发框架。",
        "rag": "RAG 通过检索外部知识增强 LLM 回答。",
    }
    for key, val in kb.items():
        if key in query.lower():
            return val
    return f"未找到 '{query}' 相关信息"

tool_map = {
    "get_weather": get_weather,
    "calculator": calculator,
    "search_info": search_info,
}

# 1.1 原生 HTTP 调用
def ollama_chat_with_tools(messages: list, max_iterations: int = 5) -> str:
    """使用 Ollama 原生 API 进行工具调用"""
    for i in range(max_iterations):
        try:
            response = httpx.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "tools": tools,
                    "stream": False,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError:
            return "❌ 无法连接 Ollama，请确保已运行: ollama serve"
        except Exception as e:
            return f"❌ API 错误: {e}"

        msg = data.get("message", {})
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls", [])

        # 将 AI 回复加入消息列表
        messages.append(msg)

        if tool_calls:
            print(f"  [迭代{i+1}] 调用 {len(tool_calls)} 个工具")

            for tc in tool_calls:
                func_info = tc.get("function", {})
                func_name = func_info.get("name", "")
                func_args = func_info.get("arguments", {})

                # Ollama 的 arguments 可能已经是 dict（不需要 json.loads）
                if isinstance(func_args, str):
                    func_args = json.loads(func_args)

                print(f"    🔧 {func_name}({func_args})")

                func = tool_map.get(func_name)
                if func:
                    result = func(**func_args)
                else:
                    result = f"未知函数: {func_name}"

                print(f"    📋 → {result[:80]}")

                messages.append({
                    "role": "tool",
                    "content": str(result),
                })
        else:
            # 没有工具调用 → 返回最终答案
            print(f"  [迭代{i+1}] 最终回答")
            return content

    return "达到最大迭代次数"

# 测试
print("\n[测试: Ollama 原生 API]")
messages = [
    {"role": "system", "content": "你是一个助手，可以使用工具回答问题。"},
    {"role": "user", "content": "北京今天天气如何？"}
]
answer = ollama_chat_with_tools(messages)
print(f"  Q: 北京今天天气如何？")
print(f"  A: {answer[:120]}...")

# ============================================================================
# 2. LangChain 封装调用
# ============================================================================
print("\n\n--- 2. LangChain 封装调用 ---")
print("""
LangChain 提供了更简洁的方式：
- ChatOllama + bind_tools()
- 自动处理消息格式转换
- 兼容 @tool 装饰器
""")

from langchain_core.tools import tool as lc_tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_community.chat_models import ChatOllama

llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)

# 用 @tool 装饰器定义工具
@lc_tool
def lc_get_weather(city: str) -> str:
    """查询指定城市的天气信息。参数 city 为城市名如'北京'。"""
    return get_weather(city)

@lc_tool
def lc_calculator(expression: str) -> str:
    """计算数学表达式。如 '(15+27)*3'。"""
    return calculator(expression)

@lc_tool
def lc_search_info(query: str) -> str:
    """搜索技术知识库。参数 query 为搜索关键词。"""
    return search_info(query)

lc_tools = [lc_get_weather, lc_calculator, lc_search_info]
llm_with_tools = llm.bind_tools(lc_tools)

# 2.1 简单调用
print("\n[LangChain 单次调用]")
response = llm_with_tools.invoke([HumanMessage(content="上海天气怎么样？")])
print(f"  content: '{response.content[:50]}...' " if response.content else "  content: (空)")
print(f"  tool_calls: {response.tool_calls}")

# 2.2 完整循环
def langchain_chat_with_tools(question: str, max_iter: int = 5) -> str:
    """LangChain 版工具调用循环"""
    lc_tool_map = {t.name: t for t in lc_tools}
    messages = [HumanMessage(content=question)]

    for i in range(max_iter):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if response.tool_calls:
            print(f"  [迭代{i+1}] 调用 {len(response.tool_calls)} 个工具")
            for tc in response.tool_calls:
                print(f"    🔧 {tc['name']}({tc['args']})")
                func = lc_tool_map[tc["name"]]
                result = func.invoke(tc["args"])
                print(f"    📋 → {result[:80]}")
                messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tc["id"],
                ))
        else:
            print(f"  [迭代{i+1}] 最终回答")
            return response.content

    return "达到最大迭代次数"

print("\n[LangChain 完整循环]")
answer = langchain_chat_with_tools("计算 (100 + 200) * 3")
print(f"  Q: 计算 (100 + 200) * 3")
print(f"  A: {answer[:120]}...")

# ============================================================================
# 3. Ollama 兼容 OpenAI 格式
# ============================================================================
print("\n--- 3. Ollama 兼容 OpenAI 格式 ---")
print("""
Ollama 也提供了 OpenAI 兼容的 API 端点：
  http://localhost:11434/v1/chat/completions

这意味着你可以直接用 openai 库连接 Ollama！
只需要修改 base_url。
""")

try:
    from openai import OpenAI

    ollama_client = OpenAI(
        api_key="ollama",  # Ollama 不需要真正的 key
        base_url=f"{OLLAMA_BASE_URL}/v1",
    )

    response = ollama_client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "user", "content": "什么是 Python？请简短回答。"}
        ],
        tools=tools,
        tool_choice="auto",
    )

    msg = response.choices[0].message
    if msg.tool_calls:
        print(f"  工具调用: {msg.tool_calls[0].function.name}")
    else:
        print(f"  直接回答: {msg.content[:80]}...")

    print("""
  用法：把 OpenAI 代码的 base_url 改为 Ollama 地址即可！
  
  client = OpenAI(
      api_key="ollama",
      base_url="http://localhost:11434/v1"
  )
  # 之后的代码和 OpenAI 完全一样
""")

except ImportError:
    print("  需要安装 openai 库: pip install openai")
except Exception as e:
    print(f"  连接失败: {e}")

# ============================================================================
# 4. 不同模型的工具调用对比
# ============================================================================
print("\n--- 4. 模型工具调用能力对比 ---")
print("""
┌──────────────────┬──────┬──────┬──────┬──────────────────┐
│  模型             │ 中文 │ 速度 │ 准确 │ 备注              │
├──────────────────┼──────┼──────┼──────┼──────────────────┤
│  qwen2.5:7b      │  ★★★ │  ★★  │  ★★★ │ 推荐！中文最佳    │
│  qwen2.5:14b     │  ★★★ │  ★   │  ★★★ │ 更准但更慢        │
│  llama3.1:8b     │  ★★  │  ★★  │  ★★★ │ 英文场景推荐      │
│  mistral:7b      │  ★   │  ★★★ │  ★★  │ 最快，中文一般    │
│  command-r:35b   │  ★★  │  ★   │  ★★★ │ 工具调用专精      │
│  deepseek-v2:16b │  ★★★ │  ★   │  ★★  │ 代码能力强        │
└──────────────────┴──────┴──────┴──────┴──────────────────┘

选择建议：
- 中文场景 → qwen2.5:7b（首选）
- 英文场景 → llama3.1:8b
- 追求速度 → mistral:7b
- 追求质量 → qwen2.5:14b 或 command-r
""")

# ============================================================================
# 5. 常见问题与排错
# ============================================================================
print("\n--- 5. 常见问题与排错 ---")
print("""
❓ 模型不调用工具，直接用文本回答
   → 检查 description 是否足够清晰
   → 尝试在 system prompt 中明确提示"请使用工具"
   → 换一个工具调用能力更好的模型

❓ 参数格式错误
   → Ollama 的 arguments 可能是 dict 而非 JSON string
   → 加 isinstance 检查: if isinstance(args, str): args = json.loads(args)

❓ 连接失败
   → 确认 Ollama 正在运行: ollama serve
   → 确认模型已下载: ollama list
   → 确认端口未被占用: 默认 11434

❓ 中文乱码
   → 确保 sys.stdout 设置了 utf-8 编码
   → JSON 序列化时用 ensure_ascii=False

❓ 响应太慢
   → 使用更小的模型（7b 而非 14b）
   → 确认 GPU 是否正常工作: ollama ps
   → 降低 num_ctx 参数
""")

print("\n" + "=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] Ollama 原生 HTTP API 工具调用")
print("  [v] LangChain ChatOllama + bind_tools")
print("  [v] Ollama 的 OpenAI 兼容模式")
print("  [v] 不同模型的工具调用能力对比")
print("  [v] 常见问题排错")
print("=" * 60)
print("\n下一课：04_parallel_and_multi_turn.py - 并行调用与多轮工具对话")
