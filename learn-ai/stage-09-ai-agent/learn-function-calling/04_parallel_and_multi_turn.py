import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第4课：并行调用与多轮工具对话
==============================================================================

上一课学了单次工具调用的完整流程。
本课深入两个重要场景：

1. 并行工具调用（Parallel Tool Calls）
   - LLM 一次返回多个 tool_calls
   - 多个工具同时执行，提高效率
   - 例如："查北京和上海的天气" → 并行调用两次 get_weather

2. 多轮工具对话（Multi-Turn Tool Conversations）
   - 一个问题需要多次工具调用才能解答
   - 第一次工具结果 → LLM 分析 → 需要第二次工具调用
   - 例如："北京比上海热多少度？" → 查两地天气 → 计算差值

这两个场景是构建复杂 Agent 的基础。
==============================================================================
"""

import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_community.chat_models import ChatOllama

print("=" * 60)
print("第4课：并行调用与多轮工具对话")
print("=" * 60)

# ============================================================================
# 1. 准备工具
# ============================================================================
print("\n--- 1. 准备工具 ---")

@tool
def get_weather(city: str) -> str:
    """查询城市天气。参数 city 为中文城市名。"""
    db = {
        "北京": {"temp": 25, "desc": "晴天", "humidity": 40},
        "上海": {"temp": 22, "desc": "多云", "humidity": 65},
        "广州": {"temp": 30, "desc": "小雨", "humidity": 80},
        "成都": {"temp": 20, "desc": "阴天", "humidity": 70},
        "哈尔滨": {"temp": 5, "desc": "雪", "humidity": 55},
    }
    data = db.get(city, {"temp": 0, "desc": "暂无数据", "humidity": 0})
    return json.dumps({"city": city, **data}, ensure_ascii=False)

@tool
def calculator(expression: str) -> str:
    """计算数学表达式。如 '25 - 5' 或 '(10+20)/2'。"""
    try:
        allowed = set("0123456789+-*/().** ")
        if not all(c in allowed for c in expression):
            return "不安全的表达式"
        result = eval(expression)
        return str(round(result, 4) if isinstance(result, float) else result)
    except Exception as e:
        return f"错误: {e}"

@tool
def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    """查询汇率。如 from_currency='USD', to_currency='CNY'。"""
    rates = {
        ("USD", "CNY"): 7.24,
        ("CNY", "USD"): 0.138,
        ("EUR", "CNY"): 7.86,
        ("CNY", "EUR"): 0.127,
        ("JPY", "CNY"): 0.048,
        ("GBP", "CNY"): 9.15,
    }
    rate = rates.get((from_currency.upper(), to_currency.upper()))
    if rate:
        return json.dumps({"from": from_currency, "to": to_currency, "rate": rate})
    return json.dumps({"error": f"不支持的汇率对: {from_currency}/{to_currency}"})

@tool
def get_stock_price(symbol: str) -> str:
    """查询股票价格。参数 symbol 为股票代码如 'AAPL'、'GOOGL'。"""
    prices = {
        "AAPL": {"name": "Apple", "price": 178.50, "change": "+1.2%"},
        "GOOGL": {"name": "Google", "price": 141.80, "change": "-0.5%"},
        "MSFT": {"name": "Microsoft", "price": 378.90, "change": "+0.8%"},
        "TSLA": {"name": "Tesla", "price": 248.30, "change": "-2.1%"},
    }
    data = prices.get(symbol.upper(), {"error": f"未找到股票: {symbol}"})
    return json.dumps(data, ensure_ascii=False)

tools = [get_weather, calculator, get_exchange_rate, get_stock_price]

llm = ChatOllama(model="qwen2.5:7b", temperature=0)
llm_with_tools = llm.bind_tools(tools)

tool_map = {t.name: t for t in tools}
print(f"工具: {[t.name for t in tools]}")

# ============================================================================
# 2. 并行工具调用
# ============================================================================
print("\n--- 2. 并行工具调用 ---")
print("""
当用户的问题涉及多个独立查询时，LLM 会一次返回多个 tool_calls。

例："查一下北京和上海的天气"
  tool_calls: [
    {name: "get_weather", args: {city: "北京"}},
    {name: "get_weather", args: {city: "上海"}}
  ]

好处：所有工具可以并行执行，而不是串行等待。
""")

def run_with_tools(question: str, max_iter: int = 5, verbose: bool = True) -> str:
    """完整的工具调用循环（支持并行和多轮）"""
    messages = [
        SystemMessage(content="你是一个助手。使用工具获取准确信息，不要编造数据。"),
        HumanMessage(content=question),
    ]

    for i in range(max_iter):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if response.tool_calls:
            if verbose:
                print(f"  [轮次{i+1}] 调用 {len(response.tool_calls)} 个工具"
                      f"{'（并行）' if len(response.tool_calls) > 1 else ''}")

            for tc in response.tool_calls:
                if verbose:
                    print(f"    🔧 {tc['name']}({tc['args']})")

                func = tool_map.get(tc["name"])
                result = func.invoke(tc["args"]) if func else f"未知工具: {tc['name']}"

                if verbose:
                    print(f"    📋 → {str(result)[:80]}")

                messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tc["id"],
                ))
        else:
            if verbose:
                print(f"  [轮次{i+1}] 生成最终回答")
            return response.content

    return "达到最大迭代次数"

# 2.1 测试并行调用
print("\n[测试: 并行查询多个城市天气]")
answer = run_with_tools("查一下北京和上海的天气")
print(f"  Q: 查一下北京和上海的天气")
print(f"  A: {answer[:150]}...")

print("\n[测试: 并行查询多只股票]")
answer = run_with_tools("AAPL 和 TSLA 今天股价多少？")
print(f"  Q: AAPL 和 TSLA 今天股价多少？")
print(f"  A: {answer[:150]}...")

# ============================================================================
# 3. 多轮工具调用
# ============================================================================
print("\n\n--- 3. 多轮工具调用 ---")
print("""
有些问题需要多轮工具调用：

例："1000 美元换成人民币是多少？"
  轮次1: get_exchange_rate(USD, CNY) → 7.24
  轮次2: calculator("1000 * 7.24") → 7240
  最终: "1000美元可以换7240元人民币"

LLM 会根据第一轮结果决定是否需要继续调用。
""")

print("\n[测试: 多轮 - 汇率+计算]")
answer = run_with_tools("500 美元换成人民币是多少钱？")
print(f"  Q: 500 美元换成人民币是多少钱？")
print(f"  A: {answer[:150]}...")

print("\n[测试: 多轮 - 天气对比+计算]")
answer = run_with_tools("北京比哈尔滨热多少度？")
print(f"  Q: 北京比哈尔滨热多少度？")
print(f"  A: {answer[:150]}...")

# ============================================================================
# 4. 复杂场景：混合并行与多轮
# ============================================================================
print("\n--- 4. 混合并行与多轮 ---")
print("""
复杂问题可能同时涉及并行和多轮：

例："比较 Apple 和 Google 的股价，算一下差了多少"
  轮次1 (并行): get_stock_price(AAPL) + get_stock_price(GOOGL)
  轮次2: calculator("178.50 - 141.80")
  最终: "Apple 比 Google 贵 36.70 美元"
""")

print("\n[测试: 混合场景]")
answer = run_with_tools("Apple 和 Microsoft 的股价差多少？换算成人民币大约多少？")
print(f"  Q: Apple 和 Microsoft 的股价差多少？换算成人民币大约多少？")
print(f"  A: {answer[:200]}...")

# ============================================================================
# 5. 对话上下文中的工具调用
# ============================================================================
print("\n\n--- 5. 对话上下文中的工具调用 ---")
print("""
在多轮对话中，LLM 能利用之前的上下文决定工具调用。

例：
  用户: "北京天气怎么样？"
  AI:   "北京晴天，25°C"
  用户: "上海呢？"         ← LLM 理解"上海的天气"
  AI:   调用 get_weather("上海")
""")

def multi_turn_conversation(conversation: list[str]):
    """模拟多轮对话"""
    messages = [
        SystemMessage(content="你是一个助手。使用工具获取准确信息。回答简洁。"),
    ]

    for i, user_msg in enumerate(conversation):
        print(f"\n  [第{i+1}轮]")
        print(f"  用户: {user_msg}")

        messages.append(HumanMessage(content=user_msg))

        # 可能需要多次工具调用
        for _ in range(5):
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            if response.tool_calls:
                for tc in response.tool_calls:
                    print(f"    🔧 {tc['name']}({tc['args']})")
                    func = tool_map.get(tc["name"])
                    result = func.invoke(tc["args"]) if func else "未知"
                    messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            else:
                print(f"  AI: {response.content[:100]}...")
                break

print("[测试: 多轮对话中的工具调用]")
multi_turn_conversation([
    "北京今天天气怎么样？",
    "上海呢？",
    "哪个城市更热？热多少度？",
])

# ============================================================================
# 6. 处理并行调用的注意事项
# ============================================================================
print("\n\n--- 6. 并行调用注意事项 ---")
print("""
┌──────────────────────────────────────────────────────────┐
│  注意事项                                                 │
├──────────────────────────────────────────────────────────┤
│  1. tool_call_id 必须一一对应                             │
│     每个 tool_call 都需要一个对应的 ToolMessage            │
│     tool_call_id 必须匹配，否则 API 报错                  │
│                                                          │
│  2. 并行执行可以提速                                      │
│     多个 tool_call 之间没有依赖 → 可以用 asyncio 并行     │
│     但注意不是所有调用都能并行（有依赖关系的不行）         │
│                                                          │
│  3. 部分工具可能失败                                      │
│     某个工具失败不应影响其他工具                           │
│     返回错误信息，让 LLM 自行处理                         │
│                                                          │
│  4. 消息顺序                                              │
│     AI message (含 tool_calls) 后面紧跟所有 ToolMessage   │
│     ToolMessage 的顺序最好与 tool_calls 顺序一致          │
│                                                          │
│  5. 并行调用不是所有模型都支持                             │
│     OpenAI GPT-4o/GPT-4 ✅                               │
│     Ollama qwen2.5 ✅（部分场景）                        │
│     有些模型只支持单次调用                                │
└──────────────────────────────────────────────────────────┘
""")

# ============================================================================
# 7. 异步并行执行（性能优化）
# ============================================================================
print("\n--- 7. 异步并行执行（性能优化）---")
print("""
当多个工具可以并行执行时，用 asyncio 提速：

  同步（串行）：Tool_A(1s) → Tool_B(1s) → Tool_C(1s) = 3s
  异步（并行）：Tool_A(1s) + Tool_B(1s) + Tool_C(1s) = 1s
""")

import asyncio
import time

async def execute_tools_parallel(tool_calls: list, tool_map: dict) -> list[ToolMessage]:
    """异步并行执行多个工具调用"""

    async def execute_one(tc):
        func = tool_map.get(tc["name"])
        if func:
            # 模拟异步执行（实际中可能是 HTTP 请求等）
            result = func.invoke(tc["args"])
        else:
            result = f"未知工具: {tc['name']}"
        return ToolMessage(content=str(result), tool_call_id=tc["id"])

    # 并行执行所有工具
    tasks = [execute_one(tc) for tc in tool_calls]
    results = await asyncio.gather(*tasks)
    return list(results)

# 性能对比演示
print("\n串行 vs 并行对比（概念演示）：")
print("  串行: 依次执行每个工具")
print("  并行: asyncio.gather() 同时执行所有工具")
print("  在 I/O 密集场景（HTTP 请求）下，并行可节省大量时间")

print("\n" + "=" * 60)
print("[完成] 第4课完成！你已经学会了：")
print("  [v] 并行工具调用（多个 tool_calls 同时执行）")
print("  [v] 多轮工具对话（结果驱动的连续调用）")
print("  [v] 混合场景处理（并行 + 多轮）")
print("  [v] 对话上下文中的工具调用")
print("  [v] 并行调用的注意事项")
print("  [v] asyncio 异步并行优化")
print("=" * 60)
print("\n下一课：05_advanced_patterns.py - 高级模式（强制调用/路由/嵌套/流式）")
