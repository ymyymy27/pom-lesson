import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：ReAct Agent（推理-行动循环）
==============================================================================

什么是 ReAct？
--------------
ReAct = Reasoning + Acting（推理 + 行动）

这是最经典的 Agent 模式，核心是一个循环：
  思考（Thought）→ 行动（Action）→ 观察（Observation）→ 再思考 → ...

用 LangGraph 实现 ReAct：
  ┌─────────┐         ┌─────────┐
  │  Agent  │ ──────→ │  Tools  │
  │  (LLM)  │ ←────── │  (执行)  │
  └─────────┘         └─────────┘
       │
       ↓ (无工具调用时)
      END

Agent 节点：LLM 思考，决定是否调用工具
  ├→ 有 tool_calls → 走到 Tools 节点
  └→ 无 tool_calls → 走到 END

Tools 节点：执行工具，返回结果 → 回到 Agent 节点

本课使用 LangGraph 的内置组件快速构建 ReAct Agent。
==============================================================================
"""

from typing import Annotated, TypedDict
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

print("=" * 60)
print("第3课：ReAct Agent（推理-行动循环）")
print("=" * 60)

# ============================================================================
# 1. 准备工具
# ============================================================================
print("\n--- 1. 准备工具 ---")

@tool
def calculator(expression: str) -> str:
    """计算数学表达式。支持加减乘除、幂运算、括号等。
    示例：'2 + 3 * 4'、'(10 + 5) ** 2'、'100 / 3'"""
    try:
        # 安全地计算数学表达式
        allowed = set("0123456789+-*/().** ")
        if not all(c in allowed for c in expression):
            return f"不安全的表达式: {expression}"
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"

@tool
def get_weather(city: str) -> str:
    """查询城市的当前天气。参数 city 为中文城市名，如'北京'、'上海'。"""
    weather_db = {
        "北京": "晴天，气温 25°C，湿度 40%，北风 3 级",
        "上海": "多云，气温 22°C，湿度 65%，东风 2 级",
        "广州": "小雨，气温 28°C，湿度 80%，南风 1 级",
        "深圳": "阵雨，气温 27°C，湿度 75%，西南风 2 级",
        "成都": "阴天，气温 20°C，湿度 70%，微风",
    }
    return weather_db.get(city, f"暂无 {city} 的天气数据，支持的城市：{list(weather_db.keys())}")

@tool
def search_info(query: str) -> str:
    """搜索知识库获取信息。当需要查找事实性信息时使用。"""
    knowledge = {
        "python": "Python 由 Guido van Rossum 于 1991 年发布，是最流行的编程语言之一。",
        "langchain": "LangChain 是一个 LLM 应用开发框架，支持 Prompt 管理、链、记忆、检索等。",
        "langgraph": "LangGraph 是基于图结构的 Agent 编排框架，支持循环、分支、人机协作。",
        "rag": "RAG（检索增强生成）通过检索外部知识增强 LLM 回答，减少幻觉。",
        "transformer": "Transformer 由 Google 在 2017 年提出，是现代大语言模型的基础架构。",
    }
    for key, value in knowledge.items():
        if key in query.lower():
            return value
    return f"未找到与 '{query}' 相关的信息"

tools = [calculator, get_weather, search_info]
print(f"已定义 {len(tools)} 个工具: {[t.name for t in tools]}")

# ============================================================================
# 2. 手动构建 ReAct Agent
# ============================================================================
print("\n--- 2. 手动构建 ReAct Agent ---")
print("""
构建步骤：
  1. 定义 State（消息列表）
  2. Agent 节点：LLM + 工具绑定
  3. Tools 节点：自动执行工具
  4. 条件边：有 tool_calls → Tools，否则 → END
  5. Tools → Agent 的回边（形成循环）
""")

# Step 1: 定义 State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Step 2: Agent 节点
llm = ChatOllama(model="qwen2.5:7b", temperature=0)
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """你是一个能力全面的 AI 助手。你可以使用工具来帮助回答问题。

可用工具：
- calculator: 数学计算
- get_weather: 查询天气
- search_info: 搜索知识库

工作原则：
1. 仔细分析用户问题，判断是否需要使用工具
2. 如果需要多步操作，逐步执行
3. 得到工具结果后，用自然语言总结回答
4. 如果不需要工具，直接回答"""

def agent_node(state: AgentState) -> dict:
    """Agent 节点：LLM 推理并决定是否调用工具"""
    messages = state["messages"]

    # 确保有 system prompt
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# Step 3: Tools 节点（LangGraph 内置）
tool_node = ToolNode(tools)

# Step 4: 条件函数
def should_continue(state: AgentState) -> str:
    """判断是否需要继续调用工具"""
    last_message = state["messages"][-1]

    # 如果最后一条消息有 tool_calls → 继续
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # 否则 → 结束
    return END

# Step 5: 构建图
graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")  # 工具执行后回到 agent（循环！）

# 编译
react_agent = graph.compile()
print("ReAct Agent 构建完成 ✓")

# ============================================================================
# 3. 测试 Agent
# ============================================================================
print("\n--- 3. 测试 Agent ---")

def run_agent(question: str, verbose: bool = True):
    """运行 Agent 并展示过程"""
    print(f"\nQ: {question}")
    print("-" * 40)

    result = react_agent.invoke({
        "messages": [HumanMessage(content=question)]
    })

    if verbose:
        for msg in result["messages"]:
            if isinstance(msg, HumanMessage):
                pass  # 跳过，已经打印了
            elif isinstance(msg, AIMessage):
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"  🔧 调用工具: {tc['name']}({tc['args']})")
                elif msg.content:
                    print(f"  💬 回答: {msg.content[:150]}{'...' if len(msg.content) > 150 else ''}")
            elif isinstance(msg, ToolMessage):
                print(f"  📋 工具结果: {msg.content[:100]}")

    final_answer = result["messages"][-1].content
    return final_answer

# 3.1 简单问题（不需要工具）
run_agent("你好，你是谁？")

# 3.2 需要一个工具
run_agent("北京今天天气怎么样？")

# 3.3 需要计算
run_agent("计算 (25 + 17) * 3 的结果")

# 3.4 需要搜索
run_agent("什么是 RAG？")

# 3.5 可能需要多步
run_agent("帮我查一下上海的天气，然后计算 25 加 17")

# ============================================================================
# 4. 使用 LangGraph 预构建 Agent（更简洁）
# ============================================================================
print("\n\n--- 4. 使用预构建 Agent ---")
print("""
LangGraph 提供了 create_react_agent() 快捷函数，
一行代码就能创建标准的 ReAct Agent。
""")

from langgraph.prebuilt import create_react_agent

# 一行创建！
quick_agent = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier=SYSTEM_PROMPT,  # 系统提示
)

result = quick_agent.invoke({
    "messages": [HumanMessage(content="什么是 LangChain？")]
})

print(f"预构建 Agent 回答:")
final = result["messages"][-1].content
print(f"  {final[:150]}...")

# ============================================================================
# 5. 流式输出
# ============================================================================
print("\n--- 5. 流式输出 ---")
print("""
Agent 执行过程中实时查看每个步骤：
- stream() 返回每个节点的输出
- 可以看到 Agent 的推理过程和工具调用
""")

print("流式执行过程:")
for step in react_agent.stream(
    {"messages": [HumanMessage(content="成都天气如何？")]},
    stream_mode="updates",
):
    for node_name, output in step.items():
        print(f"  [{node_name}]")
        if "messages" in output:
            for msg in output["messages"]:
                if isinstance(msg, AIMessage) and msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"    🔧 {tc['name']}({tc['args']})")
                elif isinstance(msg, AIMessage) and msg.content:
                    print(f"    💬 {msg.content[:80]}...")
                elif isinstance(msg, ToolMessage):
                    print(f"    📋 {msg.content[:80]}")

# ============================================================================
# 6. 限制最大迭代次数
# ============================================================================
print("\n--- 6. 限制最大迭代次数 ---")
print("""
防止 Agent 陷入无限循环，设置 recursion_limit。
""")

try:
    result = react_agent.invoke(
        {"messages": [HumanMessage(content="帮我计算 1+1")]},
        config={"recursion_limit": 10},  # 最多执行 10 步
    )
    print(f"  结果: {result['messages'][-1].content[:80]}...")
except Exception as e:
    print(f"  达到递归限制: {e}")

# ============================================================================
# 7. ReAct 模式总结
# ============================================================================
print("\n--- 7. ReAct 模式总结 ---")
print("""
ReAct Agent 的完整图结构：

          ┌─────────────┐
          │    START     │
          └──────┬──────┘
                 ↓
          ┌─────────────┐     有 tool_calls    ┌──────────┐
          │    Agent     │ ──────────────────→ │  Tools   │
          │   (LLM)     │ ←────────────────── │  (执行)   │
          └──────┬──────┘      执行完回来       └──────────┘
                 │
                 ↓ 无 tool_calls
          ┌─────────────┐
          │     END      │
          └─────────────┘

代码结构：
  graph.add_node("agent", agent_node)          # LLM 推理
  graph.add_node("tools", ToolNode(tools))     # 工具执行
  graph.add_edge(START, "agent")               # 入口
  graph.add_conditional_edges("agent", ...)    # 条件分支
  graph.add_edge("tools", "agent")             # 循环回去

快捷方式：
  agent = create_react_agent(model, tools)     # 一行搞定
""")

print("\n" + "=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] ReAct 模式的原理（思考→行动→观察循环）")
print("  [v] 手动构建 ReAct Agent（理解每个组件）")
print("  [v] ToolNode 自动执行工具")
print("  [v] 条件边实现循环")
print("  [v] create_react_agent 快捷构建")
print("  [v] 流式输出观察执行过程")
print("  [v] recursion_limit 防止无限循环")
print("=" * 60)
print("\n下一课：04_human_in_the_loop.py - 人机协作与检查点")
