import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第7课：完整项目 - MCP 工具生态系统
==============================================================================

本课整合前6课知识，构建完整的 MCP 工具生态系统：

  MCP Server 集群（4个）：
  ├── WeatherServer    天气查询
  ├── DatabaseServer   数据库查询
  ├── KnowledgeServer  知识库搜索
  └── UtilityServer    工具（计算/时间）

  MCP Client + LangGraph Agent：
  ├── 自动发现所有 Server 工具
  ├── 统一转换为 LangChain 工具
  ├── LangGraph ReAct Agent 智能调用
  └── 多轮对话记忆

  整合知识：第1-6课全部核心概念
==============================================================================
"""

import json
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
from typing import Annotated, TypedDict
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

print("=" * 60)
print("第7课：完整项目 - MCP 工具生态系统")
print("=" * 60)

# ============================================================================
# 1. 模拟 MCP Server 集群
# ============================================================================
print("\n--- 1. MCP Server 集群 ---")

class MCPServer:
    """通用 MCP Server 基类"""
    def __init__(self, name: str):
        self.name = name
        self.tools = {}
        self.resources = {}

    def add_tool(self, name, description, schema, handler):
        self.tools[name] = {
            "name": name, "description": description,
            "inputSchema": schema, "handler": handler,
        }

    def add_resource(self, uri, name, mime_type, fn):
        self.resources[uri] = {"uri": uri, "name": name, "mimeType": mime_type, "fn": fn}

    def list_tools(self):
        return [{"name": t["name"], "description": t["description"],
                 "inputSchema": t["inputSchema"]} for t in self.tools.values()]

    def call_tool(self, name, arguments):
        t = self.tools.get(name)
        if not t:
            return {"error": f"未知工具: {name}"}
        try:
            result = t["handler"](arguments)
            return {"content": [{"type": "text", "text": result}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"错误: {e}"}]}

    def list_resources(self):
        return [{"uri": r["uri"], "name": r["name"], "mimeType": r["mimeType"]}
                for r in self.resources.values()]

    def read_resource(self, uri):
        r = self.resources.get(uri)
        if not r:
            return {"error": f"未知资源: {uri}"}
        return {"contents": [{"uri": uri, "text": r["fn"]()}]}

# ----- 1.1 WeatherServer -----
weather_server = MCPServer("weather-server")
weather_server.add_tool(
    "get_weather", "查询城市天气。参数city为中文城市名如'北京'。",
    {"type": "object", "properties": {"city": {"type": "string", "description": "城市名"}}, "required": ["city"]},
    lambda args: json.dumps({
        "北京": {"city": "北京", "temp": 25, "desc": "晴天", "humidity": 40, "wind": "北风3级"},
        "上海": {"city": "上海", "temp": 22, "desc": "多云", "humidity": 65, "wind": "东风2级"},
        "广州": {"city": "广州", "temp": 30, "desc": "小雨", "humidity": 80, "wind": "南风1级"},
        "成都": {"city": "成都", "temp": 20, "desc": "阴天", "humidity": 70, "wind": "微风"},
        "哈尔滨": {"city": "哈尔滨", "temp": 5, "desc": "雪", "humidity": 55, "wind": "北风4级"},
    }.get(args.get("city", ""), {"error": f"暂无{args.get('city')}数据"}), ensure_ascii=False)
)
weather_server.add_resource(
    "config://weather/cities", "支持的城市", "application/json",
    lambda: json.dumps(["北京", "上海", "广州", "成都", "哈尔滨"], ensure_ascii=False)
)

# ----- 1.2 DatabaseServer -----
demo_db = tempfile.mktemp(suffix=".db")
_conn = sqlite3.connect(demo_db)
_conn.executescript("""
    CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, dept TEXT, salary REAL);
    INSERT INTO employees VALUES (1,'张三','技术部',25000);
    INSERT INTO employees VALUES (2,'李四','产品部',22000);
    INSERT INTO employees VALUES (3,'王五','技术部',28000);
    INSERT INTO employees VALUES (4,'赵六','市场部',20000);
    INSERT INTO employees VALUES (5,'孙七','技术部',30000);
    CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INT);
    INSERT INTO products VALUES (1,'蓝牙耳机',299,150);
    INSERT INTO products VALUES (2,'机械键盘',599,80);
    INSERT INTO products VALUES (3,'显示器',1999,30);
""")
_conn.commit()
_conn.close()

db_server = MCPServer("database-server")
db_server.add_tool(
    "query_db", "执行SQL查询（只允许SELECT）。可用表: employees(id,name,dept,salary), products(id,name,price,stock)。",
    {"type": "object", "properties": {"sql": {"type": "string", "description": "SQL SELECT语句"}}, "required": ["sql"]},
    lambda args: _db_query(args.get("sql", ""))
)

def _db_query(sql):
    sql_up = sql.strip().upper()
    if not sql_up.startswith("SELECT"):
        return json.dumps({"error": "只允许SELECT"})
    for w in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]:
        if w in sql_up:
            return json.dumps({"error": f"禁止{w}"})
    try:
        conn = sqlite3.connect(demo_db)
        conn.row_factory = sqlite3.Row
        rows = conn.cursor().execute(sql).fetchmany(30)
        data = [dict(r) for r in rows]
        conn.close()
        return json.dumps({"count": len(data), "data": data}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

db_server.add_resource(
    "db://main/schema", "数据库结构", "text/plain",
    lambda: "employees(id,name,dept,salary)\nproducts(id,name,price,stock)"
)

# ----- 1.3 KnowledgeServer -----
knowledge_server = MCPServer("knowledge-server")
knowledge_server.add_tool(
    "search_knowledge", "搜索技术知识库。支持搜索编程、AI、框架等。",
    {"type": "object", "properties": {"query": {"type": "string", "description": "搜索关键词"}}, "required": ["query"]},
    lambda args: _search_kb(args.get("query", ""))
)

def _search_kb(query):
    kb = {
        "python": "Python 是通用编程语言，广泛用于AI/Web/数据科学。最新版本3.12+。",
        "langchain": "LangChain 是 LLM 应用开发框架。核心: Models/Prompts/Chains/Memory/Retrievers。",
        "langgraph": "LangGraph 是 Agent 编排框架。核心: State/Node/Edge/条件分支/循环。",
        "mcp": "MCP(Model Context Protocol) 标准化LLM与工具的连接。三种能力: Tools/Resources/Prompts。",
        "rag": "RAG 通过检索外部知识增强LLM回答。流程: 分块→Embedding→向量存储→检索→生成。",
        "function calling": "Function Calling 让LLM能调用外部函数。LLM决定调用什么，程序负责执行。",
        "docker": "Docker 容器化平台: 镜像/容器/Dockerfile/Compose。比虚拟机更轻量。",
        "fastapi": "FastAPI 高性能Python Web框架。自动文档、类型安全、原生异步。",
    }
    q = query.lower()
    results = [{"topic": k, "content": v} for k, v in kb.items() if k in q]
    if results:
        return json.dumps({"query": query, "results": results}, ensure_ascii=False)
    return json.dumps({"query": query, "results": [], "available": list(kb.keys())}, ensure_ascii=False)

# ----- 1.4 UtilityServer -----
utility_server = MCPServer("utility-server")
utility_server.add_tool(
    "calculator", "计算数学表达式。如 '(15+27)*3'。",
    {"type": "object", "properties": {"expression": {"type": "string", "description": "数学表达式"}}, "required": ["expression"]},
    lambda args: _calc(args.get("expression", ""))
)

def _calc(expr):
    try:
        allowed = set("0123456789+-*/().** %")
        if not all(c in allowed for c in expr):
            return "不安全的表达式"
        r = eval(expr)
        return str(round(r, 6) if isinstance(r, float) else r)
    except Exception as e:
        return f"计算错误: {e}"

utility_server.add_tool(
    "get_datetime", "获取当前日期时间。",
    {"type": "object", "properties": {}},
    lambda args: json.dumps({
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "weekday": f"星期{'一二三四五六日'[datetime.now().weekday()]}",
    }, ensure_ascii=False)
)

utility_server.add_tool(
    "date_calc", "日期加减。days为正数表示未来，负数表示过去。",
    {"type": "object", "properties": {
        "days": {"type": "integer", "description": "加减天数"},
    }, "required": ["days"]},
    lambda args: json.dumps({
        "result": (datetime.now() + timedelta(days=args.get("days", 0))).strftime("%Y-%m-%d"),
    })
)

ALL_SERVERS = {
    "weather": weather_server,
    "database": db_server,
    "knowledge": knowledge_server,
    "utility": utility_server,
}

print(f"创建了 {len(ALL_SERVERS)} 个 MCP Server:")
for name, srv in ALL_SERVERS.items():
    print(f"  📦 {srv.name} ({len(srv.tools)} tools, {len(srv.resources)} resources)")

# ============================================================================
# 2. MCP Client Manager
# ============================================================================
print("\n--- 2. MCP Client Manager ---")

class MCPClientManager:
    """多 Server 管理器 + 工具转换"""

    def __init__(self):
        self.servers = {}
        self.tool_to_server = {}

    def connect_all(self, servers: dict):
        for name, server in servers.items():
            self.servers[name] = server
            tools = server.list_tools()
            for t in tools:
                self.tool_to_server[t["name"]] = name
            print(f"  ✅ {name}: {[t['name'] for t in tools]}")

    def get_all_mcp_tools(self) -> list[dict]:
        all_tools = []
        for server in self.servers.values():
            all_tools.extend(server.list_tools())
        return all_tools

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        server_name = self.tool_to_server.get(tool_name)
        if not server_name:
            return f"未知工具: {tool_name}"
        result = self.servers[server_name].call_tool(tool_name, arguments)
        if "error" in result:
            return result["error"]
        return result["content"][0]["text"]

    def to_langchain_tools(self) -> list:
        lc_tools = []
        for mcp_tool in self.get_all_mcp_tools():
            name = mcp_tool["name"]
            def make_fn(n):
                def fn(**kwargs):
                    return self.call_tool(n, kwargs)
                return fn
            lc_tools.append(StructuredTool.from_function(
                func=make_fn(name), name=name,
                description=mcp_tool["description"],
            ))
        return lc_tools

manager = MCPClientManager()
print("连接所有 Server:")
manager.connect_all(ALL_SERVERS)

lc_tools = manager.to_langchain_tools()
print(f"\n转换为 {len(lc_tools)} 个 LangChain 工具:")
for t in lc_tools:
    print(f"  🔧 {t.name}: {t.description[:45]}...")

# ============================================================================
# 3. LangGraph Agent
# ============================================================================
print("\n--- 3. 构建 LangGraph Agent ---")

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

SYSTEM_PROMPT = """你是"MCP助手"，一个基于 MCP 协议连接多个服务的智能助手。

## 可用工具（来自4个MCP Server）
- **get_weather**: 查询城市天气（weather-server）
- **query_db**: SQL数据库查询（database-server）
- **search_knowledge**: 技术知识搜索（knowledge-server）
- **calculator**: 数学计算（utility-server）
- **get_datetime**: 当前时间（utility-server）
- **date_calc**: 日期加减（utility-server）

## 工作原则
1. 需要事实数据时必须用工具，不要编造
2. 数学计算用 calculator
3. 多个独立查询可以并行
4. 回答简洁准确"""

llm = ChatOllama(model="qwen2.5:7b", temperature=0)
llm_with_tools = llm.bind_tools(lc_tools)
tool_map = {t.name: t for t in lc_tools}

def agent_node(state: AgentState) -> dict:
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
    return {"messages": [llm_with_tools.invoke(messages)]}

def tool_node(state: AgentState) -> dict:
    last = state["messages"][-1]
    results = []
    for tc in last.tool_calls:
        func = tool_map.get(tc["name"])
        result = func.invoke(tc["args"]) if func else f"未知: {tc['name']}"
        results.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
    return {"messages": results}

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

memory = MemorySaver()
mcp_agent = graph.compile(checkpointer=memory)
print("LangGraph Agent 构建完成 ✓")

# ============================================================================
# 4. 助手封装
# ============================================================================
print("\n--- 4. 助手封装 ---")

class MCPAssistant:
    def __init__(self, agent, tool_map):
        self.agent = agent
        self.tool_map = tool_map

    def chat(self, message: str, session: str = "default", verbose: bool = True) -> str:
        config = {"configurable": {"thread_id": session}}
        result = self.agent.invoke(
            {"messages": [HumanMessage(content=message)]}, config=config
        )
        if verbose:
            for msg in result["messages"]:
                if isinstance(msg, AIMessage) and msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"    🔧 [{self._server_for(tc['name'])}] {tc['name']}({str(tc['args'])[:50]})")
                elif isinstance(msg, ToolMessage):
                    print(f"    📋 → {msg.content[:80]}...")
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content and not getattr(msg, 'tool_calls', None):
                return msg.content
        return "(无回复)"

    def _server_for(self, tool_name):
        return manager.tool_to_server.get(tool_name, "?")

bot = MCPAssistant(mcp_agent, tool_map)
print("MCP 助手封装完成 ✓")

# ============================================================================
# 5. 功能测试
# ============================================================================
print("\n--- 5. 功能测试 ---")

print("\n[测试1: 天气查询 - weather-server]")
print("  Q: 北京天气怎么样？")
a = bot.chat("北京天气怎么样？", session="t1")
print(f"  A: {a[:120]}...")

print("\n[测试2: 数据库查询 - database-server]")
print("  Q: 技术部有哪些员工？")
a = bot.chat("技术部有哪些员工？", session="t2")
print(f"  A: {a[:120]}...")

print("\n[测试3: 知识搜索 - knowledge-server]")
print("  Q: 什么是 MCP？")
a = bot.chat("什么是 MCP？", session="t3")
print(f"  A: {a[:150]}...")

print("\n[测试4: 数学计算 - utility-server]")
print("  Q: 计算 (256 + 512) * 1.5")
a = bot.chat("计算 (256 + 512) * 1.5", session="t4")
print(f"  A: {a[:100]}...")

print("\n[测试5: 时间查询 - utility-server]")
print("  Q: 今天几号？30天后呢？")
a = bot.chat("今天几号？30天后是哪天？", session="t5")
print(f"  A: {a[:120]}...")

# ============================================================================
# 6. 多轮对话测试
# ============================================================================
print("\n\n--- 6. 多轮对话 ---")

session = "multi"
for q in [
    "技术部平均薪资多少？",
    "最高薪的是谁？",
    "帮我搜一下 LangGraph 是什么",
]:
    print(f"\n  Q: {q}")
    a = bot.chat(q, session=session)
    print(f"  A: {a[:120]}...")

# ============================================================================
# 7. 跨 Server 复合任务
# ============================================================================
print("\n\n--- 7. 跨 Server 复合任务 ---")

print("\n[复合: 天气+计算]")
print("  Q: 北京和哈尔滨温差多少度？")
a = bot.chat("北京和哈尔滨温差多少度？", session="comp1")
print(f"  A: {a[:150]}...")

print("\n[复合: 数据库+知识]")
print("  Q: 查一下所有员工信息，另外搜索 Python 的知识")
a = bot.chat("查一下所有员工信息，另外搜索 Python 的知识", session="comp2")
print(f"  A: {a[:200]}...")

# ============================================================================
# 8. 项目架构总结
# ============================================================================
print("\n\n--- 8. 项目架构总结 ---")
print(f"""
┌────────────────────────────────────────────────────────┐
│           MCP 工具生态系统 - 项目架构                   │
├────────────────────────────────────────────────────────┤
│                                                        │
│  MCPAssistant（用户接口）                               │
│  └── chat() 多轮对话 + 自动路由 + 流式日志             │
│                                                        │
│  LangGraph Agent（智能核心）                            │
│  ├── State: messages (add_messages)                    │
│  ├── Node: agent (LLM + bind_tools)                   │
│  ├── Node: tools (工具执行)                            │
│  ├── Edge: agent →条件→ tools / END                    │
│  └── Checkpointer: MemorySaver                         │
│                                                        │
│  MCPClientManager（连接层）                             │
│  ├── connect_all()       连接所有 Server               │
│  ├── get_all_mcp_tools() 汇总工具列表                  │
│  ├── call_tool()         自动路由到 Server             │
│  └── to_langchain_tools() MCP→LangChain 转换          │
│                                                        │
│  MCP Server 集群（服务层）                              │
│  ├── weather-server   (1 tool, 1 resource)             │
│  ├── database-server  (1 tool, 1 resource)             │
│  ├── knowledge-server (1 tool)                         │
│  └── utility-server   (3 tools)                        │
│                                                        │
│  整合的知识点                                          │
│  ├── 第1课: MCP协议（N+M方案/JSON-RPC/传输方式）       │
│  ├── 第2课: Server三种能力（Tools/Resources/Prompts）  │
│  ├── 第3课: Tool设计（参数/返回值/错误处理/安全）      │
│  ├── 第4课: Resources+Prompts（URI/模板/协作）         │
│  ├── 第5课: Client（连接/发现/多Server管理）           │
│  └── 第6课: LangChain/LangGraph集成                    │
│                                                        │
│  生产环境扩展方向                                      │
│  → stdio/SSE 真实传输（替换模拟）                      │
│  → 接入社区 MCP Server（GitHub/Slack/文件系统）        │
│  → 人机协作（敏感操作需确认）                          │
│  → 部署为 Web 服务（FastAPI + WebSocket）              │
│  → 监控与日志（工具调用审计）                          │
└────────────────────────────────────────────────────────┘
""")

# 清理
os.unlink(demo_db)

print("=" * 60)
print("[完成] 第7课完成！你已经学会了：")
print("  [v] 设计多 MCP Server 集群")
print("  [v] MCPClientManager 统一管理")
print("  [v] MCP → LangChain 工具自动转换")
print("  [v] LangGraph Agent + 检查点记忆")
print("  [v] 跨 Server 复合任务处理")
print("  [v] 整合前6课所有核心知识")
print("=" * 60)
print("\nMCP 深入课程全部完成！🎉")
print("你已经掌握了 MCP 协议的核心概念和实战开发能力。")
print("建议回顾: learn-function-calling → learn-mcp → learn-langgraph")
print("三门课形成完整的 AI Agent 开发技能体系。")
