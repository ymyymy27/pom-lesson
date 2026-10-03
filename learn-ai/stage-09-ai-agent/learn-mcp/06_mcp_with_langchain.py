import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第6课：MCP + LangChain / LangGraph 集成
==============================================================================

本课将 MCP 与 LangChain/LangGraph 生态集成，构建真正的 AI 应用。

集成方式：
1. langchain-mcp-adapters: 官方适配器，自动转换 MCP 工具
2. 手动集成: 自己实现 MCP → LangChain 工具转换

集成后的效果：
  MCP Server 提供工具 → 适配器转换 → LangChain Agent 使用
  → LLM 通过 Function Calling 调用 → 通过 MCP 协议执行

本课内容：
1. langchain-mcp-adapters 用法
2. MCP 工具转 LangChain Tool
3. 与 ReAct Agent 集成
4. 与 LangGraph 集成
5. 多 Server + Agent 架构
==============================================================================
"""

import json
from langchain_core.tools import tool, StructuredTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from pydantic import BaseModel, Field

print("=" * 60)
print("第6课：MCP + LangChain / LangGraph 集成")
print("=" * 60)

# ============================================================================
# 1. langchain-mcp-adapters 介绍
# ============================================================================
print("\n--- 1. langchain-mcp-adapters ---")
print("""
langchain-mcp-adapters 是官方提供的适配库，
自动将 MCP Server 的工具转换为 LangChain 可用的工具。

安装：
  pip install langchain-mcp-adapters

核心 API：
```python
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.client import MultiServerMCPClient

# 方式1：连接单个 Server
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await load_mcp_tools(session)
        # tools 就是标准的 LangChain Tool 列表！

# 方式2：连接多个 Server
async with MultiServerMCPClient({
    "weather": {
        "command": "python",
        "args": ["weather_server.py"],
        "transport": "stdio",
    },
    "database": {
        "url": "http://localhost:8080/sse",
        "transport": "sse",
    }
}) as client:
    tools = client.get_tools()
    # 所有 Server 的工具合并为一个列表
```

转换后的工具与手写的 @tool 装饰器效果完全一样！
""")

# ============================================================================
# 2. 手动实现 MCP → LangChain 转换
# ============================================================================
print("\n--- 2. 手动 MCP → LangChain 转换 ---")
print("""
理解底层原理：如何将 MCP Tool 定义转为 LangChain Tool。
""")

# 模拟从 MCP Server 获取的工具定义
mcp_tools_from_server = [
    {
        "name": "get_weather",
        "description": "查询城市天气。参数 city 为中文城市名。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "calculator",
        "description": "计算数学表达式。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "数学表达式"}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "search_knowledge",
        "description": "搜索技术知识库。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"}
            },
            "required": ["query"]
        }
    }
]

# 模拟 MCP Server 端的工具实现
def mcp_server_execute(tool_name: str, arguments: dict) -> str:
    """模拟 MCP Server 执行工具（实际中通过 JSON-RPC 通信）"""
    if tool_name == "get_weather":
        db = {"北京": "晴天 25°C", "上海": "多云 22°C", "广州": "小雨 30°C"}
        city = arguments.get("city", "")
        return db.get(city, f"暂无{city}天气数据")
    elif tool_name == "calculator":
        expr = arguments.get("expression", "")
        try:
            return str(eval(expr))
        except:
            return "计算错误"
    elif tool_name == "search_knowledge":
        query = arguments.get("query", "").lower()
        kb = {
            "python": "Python 是通用编程语言。",
            "mcp": "MCP 是标准化 LLM 工具连接的协议。",
            "langchain": "LangChain 是 LLM 应用开发框架。",
        }
        for k, v in kb.items():
            if k in query:
                return v
        return f"未找到 '{query}' 相关信息"
    return f"未知工具: {tool_name}"

def mcp_to_langchain_tools(mcp_tools: list[dict], executor) -> list:
    """将 MCP 工具定义转为 LangChain StructuredTool"""
    lc_tools = []

    for mcp_tool in mcp_tools:
        name = mcp_tool["name"]
        description = mcp_tool["description"]

        # 创建一个闭包来捕获 tool_name
        def make_func(tool_name):
            def func(**kwargs) -> str:
                return executor(tool_name, kwargs)
            return func

        lc_tool = StructuredTool.from_function(
            func=make_func(name),
            name=name,
            description=description,
        )
        lc_tools.append(lc_tool)

    return lc_tools

# 转换
lc_tools = mcp_to_langchain_tools(mcp_tools_from_server, mcp_server_execute)

print(f"转换了 {len(lc_tools)} 个 MCP 工具为 LangChain 工具:")
for t in lc_tools:
    print(f"  🔧 {t.name}: {t.description[:40]}...")

# 测试调用
print(f"\n直接调用测试:")
print(f"  get_weather(city='北京') → {lc_tools[0].invoke({'city': '北京'})}")
print(f"  calculator(expression='2+3') → {lc_tools[1].invoke({'expression': '2+3'})}")

# ============================================================================
# 3. 与 ReAct Agent 集成
# ============================================================================
print("\n\n--- 3. 与 ReAct Agent 集成 ---")
print("""
将 MCP 工具接入 LangChain Agent（ReAct 模式）。
Agent 自动决定何时调用哪个 MCP 工具。
""")

llm = ChatOllama(model="qwen2.5:7b", temperature=0)
llm_with_tools = llm.bind_tools(lc_tools)

def run_agent(question: str, max_iter: int = 5) -> str:
    """运行带 MCP 工具的 Agent"""
    tool_map = {t.name: t for t in lc_tools}
    messages = [
        SystemMessage(content="你是一个助手。使用工具获取准确信息。回答简洁。"),
        HumanMessage(content=question),
    ]

    for i in range(max_iter):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if response.tool_calls:
            for tc in response.tool_calls:
                print(f"    🔧 [MCP] {tc['name']}({tc['args']})")
                func = tool_map.get(tc["name"])
                result = func.invoke(tc["args"]) if func else f"未知工具"
                print(f"    📋 → {str(result)[:80]}")
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
        else:
            return response.content

    return "超时"

print("[测试: MCP 工具 + Agent]")
tests = [
    "北京今天天气怎么样？",
    "计算 (100 + 200) * 3",
    "什么是 MCP？",
]

for q in tests:
    print(f"\n  Q: {q}")
    a = run_agent(q)
    print(f"  A: {a[:120]}...")

# ============================================================================
# 4. 与 LangGraph 集成
# ============================================================================
print("\n\n--- 4. 与 LangGraph 集成 ---")
print("""
MCP 工具与 LangGraph 的集成更加强大：
- 图结构支持循环（ReAct）
- 支持人机协作（敏感工具需确认）
- 支持检查点（对话记忆）

```python
from langgraph.prebuilt import create_react_agent

# 1. 从 MCP Server 获取工具
tools = await load_mcp_tools(session)  # MCP → LangChain

# 2. 创建 LangGraph Agent
agent = create_react_agent(
    model=llm,
    tools=tools,              # 直接使用！
    state_modifier="你是助手",
)

# 3. 使用
result = agent.invoke({"messages": [HumanMessage(content="...")]})
```
""")

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

def agent_node(state: AgentState) -> dict:
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content="你是一个助手，使用 MCP 工具回答问题。")] + list(messages)
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(lc_tools)

def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")

mcp_agent = graph.compile()

print("[测试: MCP + LangGraph Agent]")
result = mcp_agent.invoke({"messages": [HumanMessage(content="搜索一下什么是 LangChain")]})
for msg in result["messages"]:
    if isinstance(msg, AIMessage) and msg.tool_calls:
        for tc in msg.tool_calls:
            print(f"    🔧 [MCP→LangGraph] {tc['name']}({tc['args']})")
    elif isinstance(msg, AIMessage) and msg.content:
        print(f"    💬 {msg.content[:120]}...")
    elif isinstance(msg, ToolMessage):
        print(f"    📋 {msg.content[:80]}...")

# ============================================================================
# 5. 多 Server + Agent 完整架构
# ============================================================================
print("\n\n--- 5. 多 Server + Agent 架构 ---")
print("""
生产环境的完整架构：

┌─────────────────────────────────────────────────────────┐
│                    AI 应用                               │
│                                                         │
│  ┌───────────┐    ┌──────────────────────────────────┐ │
│  │   LLM     │    │       MCP Client Manager         │ │
│  │ (Ollama/  │    │  ┌─────────┐ ┌─────────┐        │ │
│  │  OpenAI)  │    │  │weather  │ │database │ ...     │ │
│  └─────┬─────┘    │  │server   │ │server   │        │ │
│        │          │  └────┬────┘ └────┬────┘        │ │
│        │          └───────┼───────────┼─────────────┘ │
│        │                  │           │               │
│  ┌─────┴──────────────────┴───────────┴──────────┐   │
│  │              LangGraph Agent                    │   │
│  │  ┌──────┐  FC格式  ┌───────┐  MCP  ┌───────┐ │   │
│  │  │Agent │ ←──────→ │Router │ ────→ │Server │ │   │
│  │  │(LLM) │         │       │ ←──── │       │ │   │
│  │  └──────┘         └───────┘       └───────┘ │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘

```python
# 完整集成代码模板
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

async def create_mcp_agent():
    async with MultiServerMCPClient({
        "weather": {
            "command": "python",
            "args": ["servers/weather_server.py"],
            "transport": "stdio",
        },
        "database": {
            "command": "python",
            "args": ["servers/db_server.py"],
            "transport": "stdio",
        },
        "github": {
            "url": "http://localhost:3001/sse",
            "transport": "sse",
        },
    }) as client:
        tools = client.get_tools()
        
        agent = create_react_agent(
            model=ChatOllama(model="qwen2.5:7b"),
            tools=tools,
        )
        
        result = agent.invoke({
            "messages": [HumanMessage(content="...")]
        })
```

这就是 MCP 的终极形态：
  任意 MCP Server → 统一适配 → LangGraph Agent → 智能调用
""")

# ============================================================================
# 6. 集成最佳实践
# ============================================================================
print("\n--- 6. 集成最佳实践 ---")
print("""
┌──────────────────────────────────────────────────────────┐
│  最佳实践                                                 │
├──────────────────────────────────────────────────────────┤
│  ✅ 用 langchain-mcp-adapters 自动转换（省去手动工作）    │
│  ✅ MultiServerMCPClient 管理多个 Server                 │
│  ✅ 用 LangGraph Agent（比纯 LangChain 更灵活）          │
│  ✅ 添加 checkpointer 支持多轮对话                       │
│  ✅ 对敏感 MCP 工具设置 interrupt_before                 │
│  ✅ 设置 recursion_limit 防止无限循环                    │
│  ✅ 工具描述要详细（LLM 靠描述选择工具）                 │
│                                                          │
│  ❌ 不要同时连接太多 Server（工具太多 LLM 选择困难）     │
│  ❌ 不要忽略错误处理（Server 可能崩溃）                  │
│  ❌ 不要在工具描述中暴露实现细节                         │
└──────────────────────────────────────────────────────────┘
""")

print("\n" + "=" * 60)
print("[完成] 第6课完成！你已经学会了：")
print("  [v] langchain-mcp-adapters 适配器用法")
print("  [v] 手动 MCP → LangChain Tool 转换原理")
print("  [v] MCP 工具 + ReAct Agent 集成")
print("  [v] MCP 工具 + LangGraph Agent 集成")
print("  [v] 多 Server + Agent 完整架构")
print("  [v] 集成最佳实践")
print("=" * 60)
print("\n下一课：07_mcp_project.py - 完整项目：MCP 工具生态系统")
