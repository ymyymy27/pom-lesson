# LangGraph 构建 Agent

## 学习目标

- 掌握 LangGraph 的核心概念（状态、节点、边）
- 用 LangGraph 构建可控的 Agent 工作流
- 实现带条件分支和循环的复杂 Agent

## 1. LangGraph 简介

LangGraph 是 LangChain 团队推出的 Agent 编排框架，用图（Graph）来定义 Agent 的工作流。

```bash
pip install langgraph
```

```
相比 AgentExecutor 的优势：
- 更精确的流程控制
- 支持条件分支、并行、循环
- 状态管理更清晰
- 支持人机协作（Human-in-the-loop）
- 支持持久化检查点
```

## 2. 核心概念

```
State（状态）：Agent 在执行过程中的所有信息
Node（节点）：执行具体操作的函数
Edge（边）：节点之间的连接，决定流转方向

┌─────┐    ┌─────┐    ┌─────┐
│ 节点A │ →→ │ 节点B │ →→ │ 节点C │
└─────┘    └─────┘    └─────┘
              ↑              │
              └──── 条件循环 ──┘
```

## 3. 基本 ReAct Agent

```python
from typing import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# 1. 定义状态
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# 2. 定义工具
@tool
def search(query: str) -> str:
    """搜索互联网"""
    return f"搜索结果: {query} 的相关信息..."

@tool
def calculator(expression: str) -> str:
    """数学计算"""
    return str(eval(expression))

tools = [search, calculator]

# 3. 定义模型
llm = ChatOpenAI(model="gpt-4o", temperature=0)
llm_with_tools = llm.bind_tools(tools)

# 4. 定义节点
def agent_node(state: AgentState):
    """Agent 推理节点"""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

tool_node = ToolNode(tools)

# 5. 定义条件边
def should_continue(state: AgentState):
    """判断是否需要继续调用工具"""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# 6. 构建图
graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)

graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")  # 工具执行后回到 agent

app = graph.compile()

# 7. 运行
result = app.invoke({
    "messages": [HumanMessage(content="搜索一下 LangGraph 是什么，然后计算 2024 * 365")]
})
for msg in result["messages"]:
    print(f"[{msg.type}] {msg.content[:100] if msg.content else msg.tool_calls}")
```

## 4. 带人机协作的 Agent

```python
from langgraph.checkpoint.memory import MemorySaver

# 添加检查点（支持暂停/恢复）
memory = MemorySaver()

def human_review_node(state: AgentState):
    """人工审核节点 - 图会在这里暂停"""
    pass  # 不做任何操作，等待人工输入

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_node("human_review", human_review_node)

graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {
    "tools": "human_review",  # 先经过人工审核
    END: END,
})
graph.add_edge("human_review", "tools")
graph.add_edge("tools", "agent")

app = graph.compile(checkpointer=memory, interrupt_before=["human_review"])

# 运行（会在 human_review 前暂停）
config = {"configurable": {"thread_id": "1"}}
result = app.invoke(
    {"messages": [HumanMessage(content="搜索最新的AI新闻")]},
    config=config,
)

# 查看待执行的工具调用
print("待执行的操作:", result["messages"][-1].tool_calls)

# 人工确认后继续
result = app.invoke(None, config=config)  # 继续执行
```

## 5. 多 Agent 协作

```python
from langgraph.graph import StateGraph, END

class MultiAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_agent: str
    task: str
    research_result: str
    code_result: str

# 研究 Agent
def research_agent(state: MultiAgentState):
    response = llm.invoke([
        {"role": "system", "content": "你是研究专家，负责搜集信息。"},
        {"role": "user", "content": f"任务: {state['task']}"},
    ])
    return {"research_result": response.content, "current_agent": "coder"}

# 编码 Agent
def code_agent(state: MultiAgentState):
    response = llm.invoke([
        {"role": "system", "content": "你是编程专家，根据研究结果编写代码。"},
        {"role": "user", "content": f"研究结果: {state['research_result']}\n请编写实现代码。"},
    ])
    return {"code_result": response.content, "current_agent": "reviewer"}

# 审核 Agent
def review_agent(state: MultiAgentState):
    response = llm.invoke([
        {"role": "system", "content": "你是代码审核专家，审核代码质量。"},
        {"role": "user", "content": f"请审核:\n{state['code_result']}"},
    ])
    return {"messages": [AIMessage(content=response.content)]}

# 路由
def router(state: MultiAgentState):
    return state.get("current_agent", "researcher")

graph = StateGraph(MultiAgentState)
graph.add_node("researcher", research_agent)
graph.add_node("coder", code_agent)
graph.add_node("reviewer", review_agent)

graph.set_entry_point("researcher")
graph.add_edge("researcher", "coder")
graph.add_edge("coder", "reviewer")
graph.add_edge("reviewer", END)

multi_agent = graph.compile()
result = multi_agent.invoke({"task": "实现一个简单的 TODO API", "messages": []})
```

## 6. 流式输出

```python
# 流式获取 Agent 的执行过程
async for event in app.astream_events(
    {"messages": [HumanMessage(content="你的问题")]},
    version="v2",
):
    if event["event"] == "on_chat_model_stream":
        chunk = event["data"]["chunk"]
        if chunk.content:
            print(chunk.content, end="", flush=True)
    elif event["event"] == "on_tool_start":
        print(f"\n🔧 调用工具: {event['name']}")
    elif event["event"] == "on_tool_end":
        print(f"✅ 工具结果: {event['data'].content[:100]}")
```

## 练习

1. 用 LangGraph 构建一个 ReAct Agent，支持搜索和计算
2. 添加 Human-in-the-loop，在执行敏感操作前暂停等待确认
3. 实现一个双 Agent 协作系统（研究 + 编码）
4. 为 Agent 添加流式输出，实时显示推理过程

## 下一节

→ [03-Agent项目实战](03-Agent项目实战.md)
