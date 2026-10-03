# Agent 项目实战

## 学习目标

- 构建一个完整的多功能 AI Agent
- 整合 RAG、工具调用、记忆等能力
- 实现可部署的 Agent 服务

## 1. 项目：AI 工作助手

功能：
- 知识库问答（RAG）
- 网络搜索
- 代码执行
- 文件操作
- 数据分析
- 任务规划

## 2. 工具集

```python
from langchain_core.tools import tool
import subprocess
import json
import requests

@tool
def rag_search(query: str) -> str:
    """从知识库中检索相关信息"""
    from rag_engine import RAGEngine
    rag = RAGEngine()
    results = rag.query(query)
    return results

@tool
def web_search(query: str) -> str:
    """搜索互联网获取最新信息"""
    # 使用 SerpAPI / Tavily / DuckDuckGo
    from langchain_community.tools import DuckDuckGoSearchResults
    search = DuckDuckGoSearchResults()
    return search.invoke(query)

@tool
def execute_python(code: str) -> str:
    """在安全沙箱中执行 Python 代码"""
    try:
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout
        if result.returncode != 0:
            output += f"\n错误: {result.stderr}"
        return output or "执行完成，无输出"
    except subprocess.TimeoutExpired:
        return "执行超时（30秒限制）"

@tool
def analyze_csv(file_path: str, question: str) -> str:
    """分析 CSV 文件，回答数据相关问题"""
    import pandas as pd
    df = pd.read_csv(file_path)
    info = f"数据集: {df.shape[0]} 行, {df.shape[1]} 列\n"
    info += f"列名: {list(df.columns)}\n"
    info += f"前5行:\n{df.head().to_string()}\n"
    info += f"统计:\n{df.describe().to_string()}"
    return info

@tool
def create_chart(data_json: str, chart_type: str, title: str) -> str:
    """根据数据创建图表并保存"""
    import matplotlib.pyplot as plt
    import json
    data = json.loads(data_json)
    
    plt.figure(figsize=(10, 6))
    if chart_type == "bar":
        plt.bar(data["labels"], data["values"])
    elif chart_type == "line":
        plt.plot(data["labels"], data["values"], marker='o')
    elif chart_type == "pie":
        plt.pie(data["values"], labels=data["labels"], autopct='%1.1f%%')
    
    plt.title(title)
    path = f"./charts/{title.replace(' ', '_')}.png"
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return f"图表已保存: {path}"

tools = [rag_search, web_search, execute_python, analyze_csv, create_chart]
```

## 3. Agent 工作流

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

class WorkAssistantState(TypedDict):
    messages: Annotated[list, add_messages]

SYSTEM_PROMPT = """你是一个全能的 AI 工作助手，具备以下能力：

1. **知识库问答**：使用 rag_search 从内部知识库检索信息
2. **网络搜索**：使用 web_search 获取最新互联网信息
3. **代码执行**：使用 execute_python 运行 Python 代码
4. **数据分析**：使用 analyze_csv 分析数据文件
5. **图表生成**：使用 create_chart 创建可视化图表

工作原则：
- 先思考需要哪些信息和步骤
- 优先使用知识库，知识库无结果再搜索网络
- 代码执行注意安全性
- 给出清晰、有条理的回答
- 不确定时主动说明"""

llm = ChatOpenAI(model="gpt-4o", temperature=0)
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: WorkAssistantState):
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)

def should_continue(state: WorkAssistantState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# 构建图
graph = StateGraph(WorkAssistantState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")

memory = MemorySaver()
work_assistant = graph.compile(checkpointer=memory)
```

## 4. Web 服务

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="AI Work Assistant")

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

@app.post("/chat")
async def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.session_id}}
    result = work_assistant.invoke(
        {"messages": [HumanMessage(content=req.message)]},
        config=config,
    )
    return {"reply": result["messages"][-1].content}

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    config = {"configurable": {"thread_id": req.session_id}}
    
    async def generate():
        async for event in work_assistant.astream_events(
            {"messages": [HumanMessage(content=req.message)]},
            config=config,
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield chunk.content
    
    return StreamingResponse(generate(), media_type="text/plain")
```

## 5. 使用示例

```python
config = {"configurable": {"thread_id": "user_001"}}

# 知识库问答
result = work_assistant.invoke(
    {"messages": [HumanMessage(content="我们公司的退款政策是什么？")]},
    config=config,
)

# 数据分析
result = work_assistant.invoke(
    {"messages": [HumanMessage(content="分析 sales.csv 文件，找出销售额最高的月份")]},
    config=config,
)

# 复合任务
result = work_assistant.invoke(
    {"messages": [HumanMessage(content="""
    请完成以下任务：
    1. 搜索 2024 年最新的 AI 发展趋势
    2. 用 Python 生成一个趋势对比图表
    3. 写一段 200 字的总结
    """)]},
    config=config,
)
```

## 练习

1. 完成 AI 工作助手项目，至少实现 4 个工具
2. 添加多轮对话支持（同一 session 保持上下文）
3. 实现流式输出，前端实时显示推理和执行过程
4. 添加错误恢复机制：工具调用失败时自动重试或换方案

## 阶段总结

本阶段你已掌握：
- ✅ AI Agent 核心概念与架构模式
- ✅ LangGraph 图编排框架
- ✅ 多工具集成与多 Agent 协作
- ✅ 完整 Agent 项目实战

→ 下一阶段：[stage-10 多模态 AI](../stage-10-multimodal/)
