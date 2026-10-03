import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：MCP Client 开发与集成
==============================================================================

前面学了如何创建 MCP Server。本课学习 Client 端：
如何连接 Server、发现工具、调用工具。

MCP Client 的职责：
1. 连接 MCP Server（stdio 或 SSE）
2. 初始化握手（能力协商）
3. 发现可用的 Tools / Resources / Prompts
4. 转发 LLM 的工具调用请求
5. 管理多个 Server 的连接

本课内容：
1. Client 基本用法（mcp SDK）
2. stdio 连接方式
3. SSE 连接方式
4. 多 Server 管理
5. 错误处理与重连
6. Client 封装模式

⚠️ 实际运行 Client 需要有对应的 Server 在运行。
本课会模拟关键流程，并提供可运行的完整示例。
==============================================================================
"""

import json
import asyncio

print("=" * 60)
print("第5课：MCP Client 开发与集成")
print("=" * 60)

# ============================================================================
# 1. MCP Client 基本流程
# ============================================================================
print("\n--- 1. MCP Client 基本流程 ---")
print("""
使用 MCP Python SDK 连接 Server 的完整代码：

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # 1. 定义 Server 启动参数
    server_params = StdioServerParameters(
        command="python",
        args=["my_server.py"],
        env=None,  # 可选：环境变量
    )
    
    # 2. 连接 Server
    async with stdio_client(server_params) as (read, write):
        # 3. 创建会话
        async with ClientSession(read, write) as session:
            # 4. 初始化（握手）
            await session.initialize()
            
            # 5. 发现工具
            tools = await session.list_tools()
            print(f"可用工具: {[t.name for t in tools.tools]}")
            
            # 6. 调用工具
            result = await session.call_tool(
                "get_weather",
                arguments={"city": "北京"}
            )
            print(f"结果: {result.content[0].text}")
            
            # 7. 读取资源
            resources = await session.list_resources()
            content = await session.read_resource("config://app/settings")
            
            # 8. 获取 Prompt
            prompts = await session.list_prompts()
            prompt_result = await session.get_prompt(
                "code-review",
                arguments={"code": "def add(a,b): return a+b"}
            )

asyncio.run(main())
```

关键 API：
┌──────────────────────────┬─────────────────────────────┐
│  方法                     │  说明                        │
├──────────────────────────┼─────────────────────────────┤
│  session.initialize()    │  握手，协商能力               │
│  session.list_tools()    │  获取工具列表                 │
│  session.call_tool()     │  调用工具                     │
│  session.list_resources()│  获取资源列表                 │
│  session.read_resource() │  读取资源                     │
│  session.list_prompts()  │  获取提示模板列表             │
│  session.get_prompt()    │  获取提示模板内容             │
│  session.ping()          │  心跳检测                     │
└──────────────────────────┴─────────────────────────────┘
""")

# ============================================================================
# 2. 模拟 Client-Server 交互
# ============================================================================
print("\n--- 2. 模拟 Client-Server 交互 ---")

class MockMCPServer:
    """模拟 MCP Server（用于学习演示）"""

    def __init__(self, name: str):
        self.name = name
        self.tools = {}
        self.resources = {}

    def register_tool(self, name, description, schema, handler):
        self.tools[name] = {
            "name": name, "description": description,
            "inputSchema": schema, "handler": handler,
        }

    def register_resource(self, uri, name, mime_type, content_fn):
        self.resources[uri] = {
            "uri": uri, "name": name,
            "mimeType": mime_type, "fn": content_fn,
        }

    def handle_request(self, method: str, params: dict = None) -> dict:
        """处理 JSON-RPC 请求"""
        params = params or {}

        if method == "initialize":
            return {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": self.name, "version": "1.0"},
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": False},
                    "prompts": {"listChanged": False},
                }
            }
        elif method == "tools/list":
            return {"tools": [
                {"name": t["name"], "description": t["description"],
                 "inputSchema": t["inputSchema"]}
                for t in self.tools.values()
            ]}
        elif method == "tools/call":
            tool = self.tools.get(params.get("name"))
            if not tool:
                return {"error": f"未知工具: {params.get('name')}"}
            result = tool["handler"](params.get("arguments", {}))
            return {"content": [{"type": "text", "text": result}]}
        elif method == "resources/list":
            return {"resources": [
                {"uri": r["uri"], "name": r["name"], "mimeType": r["mimeType"]}
                for r in self.resources.values()
            ]}
        elif method == "resources/read":
            res = self.resources.get(params.get("uri"))
            if not res:
                return {"error": f"未知资源: {params.get('uri')}"}
            return {"contents": [{"uri": res["uri"], "text": res["fn"]()}]}
        elif method == "ping":
            return {}
        else:
            return {"error": f"未知方法: {method}"}


class MockMCPClient:
    """模拟 MCP Client"""

    def __init__(self):
        self.servers = {}
        self.all_tools = {}  # tool_name → server_name 映射

    def connect(self, name: str, server: MockMCPServer):
        """连接到 Server"""
        # 握手
        init_result = server.handle_request("initialize")
        print(f"  ✅ 连接 '{name}': {init_result['serverInfo']}")

        self.servers[name] = server

        # 发现工具
        tools_result = server.handle_request("tools/list")
        for tool in tools_result["tools"]:
            self.all_tools[tool["name"]] = name
            print(f"     🔧 {tool['name']}: {tool['description'][:40]}...")

    def list_all_tools(self) -> list[dict]:
        """列出所有 Server 的工具"""
        all_tools = []
        for name, server in self.servers.items():
            result = server.handle_request("tools/list")
            for tool in result["tools"]:
                tool["_server"] = name
                all_tools.append(tool)
        return all_tools

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        """调用工具（自动路由到正确的 Server）"""
        server_name = self.all_tools.get(tool_name)
        if not server_name:
            return f"未知工具: {tool_name}"

        server = self.servers[server_name]
        result = server.handle_request("tools/call", {
            "name": tool_name, "arguments": arguments
        })

        if "error" in result:
            return result["error"]
        return result["content"][0]["text"]

    def read_resource(self, server_name: str, uri: str) -> str:
        """从指定 Server 读取资源"""
        server = self.servers.get(server_name)
        if not server:
            return f"未知 Server: {server_name}"

        result = server.handle_request("resources/read", {"uri": uri})
        if "error" in result:
            return result["error"]
        return result["contents"][0]["text"]

# 创建两个模拟 Server
weather_server = MockMCPServer("weather-server")
weather_server.register_tool(
    "get_weather", "查询城市天气",
    {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    lambda args: json.dumps({"city": args["city"], "temp": "25°C", "desc": "晴天"}, ensure_ascii=False)
)
weather_server.register_resource(
    "config://weather/cities", "支持的城市", "application/json",
    lambda: json.dumps(["北京", "上海", "广州", "深圳"], ensure_ascii=False)
)

db_server = MockMCPServer("database-server")
db_server.register_tool(
    "query_db", "查询数据库（只读）",
    {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]},
    lambda args: json.dumps({"rows": [{"name": "张三", "dept": "技术部"}], "count": 1}, ensure_ascii=False)
)
db_server.register_tool(
    "get_schema", "获取表结构",
    {"type": "object", "properties": {"table": {"type": "string"}}, "required": ["table"]},
    lambda args: f"Table {args['table']}: id INT PK, name TEXT, dept TEXT"
)

# 创建 Client 并连接
print("创建 MCP Client 并连接 Server:")
client = MockMCPClient()
client.connect("weather", weather_server)
client.connect("database", db_server)

# 使用
print(f"\n所有可用工具:")
for tool in client.list_all_tools():
    print(f"  [{tool['_server']}] 🔧 {tool['name']}")

print(f"\n调用工具:")
r1 = client.call_tool("get_weather", {"city": "北京"})
print(f"  get_weather(北京) → {r1}")

r2 = client.call_tool("query_db", {"sql": "SELECT * FROM employees"})
print(f"  query_db(...) → {r2}")

print(f"\n读取资源:")
r3 = client.read_resource("weather", "config://weather/cities")
print(f"  weather/cities → {r3}")

# ============================================================================
# 3. SSE 连接方式
# ============================================================================
print("\n--- 3. SSE 连接方式 ---")
print("""
SSE（Server-Sent Events）适合远程 Server：

```python
from mcp.client.sse import sse_client

async def connect_sse():
    async with sse_client("http://localhost:8080/mcp") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            # ... 使用方式与 stdio 完全一样
```

SSE Server 端（使用 Starlette）：
```python
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route

sse = SseServerTransport("/messages")

async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(
            streams[0], streams[1],
            server.create_initialization_options()
        )

app = Starlette(routes=[
    Route("/sse", endpoint=handle_sse),
    Route("/messages", endpoint=sse.handle_post_message, methods=["POST"]),
])

# 运行: uvicorn server:app --port 8080
```

stdio vs SSE 对比：
┌────────────┬────────────────────┬────────────────────┐
│            │  stdio             │  SSE               │
├────────────┼────────────────────┼────────────────────┤
│  启动方式  │  Client 启动进程   │  Server 独立运行   │
│  通信      │  stdin/stdout      │  HTTP + SSE        │
│  适用场景  │  本地工具          │  远程/共享服务     │
│  多用户    │  单用户            │  多用户            │
│  部署      │  简单              │  需要 HTTP 服务    │
│  调试      │  看日志            │  HTTP 工具可调试   │
└────────────┴────────────────────┴────────────────────┘
""")

# ============================================================================
# 4. 多 Server 管理
# ============================================================================
print("\n--- 4. 多 Server 管理 ---")
print("""
实际使用中，一个 Client 通常连接多个 Server：
- weather-server: 提供天气查询
- database-server: 提供数据库操作
- github-server: 提供 GitHub 操作
- filesystem-server: 提供文件系统操作

管理策略：
1. 工具名去重（不同 Server 的工具名不能冲突）
2. 自动路由（根据工具名找到对应的 Server）
3. 并行初始化（同时连接所有 Server）
4. 健康检查（定期 ping）
5. 故障隔离（一个 Server 挂了不影响其他）
""")

class MultiServerManager:
    """多 Server 管理器"""

    def __init__(self):
        self.client = MockMCPClient()
        self.server_status = {}

    def add_server(self, name: str, server: MockMCPServer):
        try:
            self.client.connect(name, server)
            self.server_status[name] = "connected"
        except Exception as e:
            self.server_status[name] = f"error: {e}"
            print(f"  ❌ {name} 连接失败: {e}")

    def health_check(self):
        """检查所有 Server 状态"""
        for name, server in self.client.servers.items():
            try:
                server.handle_request("ping")
                self.server_status[name] = "healthy"
            except Exception:
                self.server_status[name] = "unhealthy"

    def get_status(self):
        return self.server_status

    def call_tool_safe(self, tool_name: str, arguments: dict) -> str:
        """安全的工具调用（带错误处理）"""
        try:
            return self.client.call_tool(tool_name, arguments)
        except Exception as e:
            return f"工具调用失败: {e}"

print("多 Server 管理演示:")
manager = MultiServerManager()
manager.add_server("weather", weather_server)
manager.add_server("database", db_server)

manager.health_check()
print(f"\n  Server 状态: {manager.get_status()}")

result = manager.call_tool_safe("get_weather", {"city": "上海"})
print(f"  安全调用: {result}")

# ============================================================================
# 5. 错误处理与重连
# ============================================================================
print("\n--- 5. 错误处理 ---")
print("""
Client 端需要处理的错误类型：

┌──────────────────┬──────────────────────────────────────┐
│  错误类型         │  处理方式                             │
├──────────────────┼──────────────────────────────────────┤
│  连接失败         │  重试 N 次，间隔递增                  │
│  握手失败         │  检查协议版本兼容性                   │
│  工具不存在       │  返回友好错误信息给 LLM               │
│  工具执行超时     │  设置超时，返回超时错误               │
│  Server 崩溃      │  检测断连，自动重启/重连              │
│  参数无效         │  返回参数错误信息给 LLM               │
│  权限不足         │  提示用户配置权限                     │
└──────────────────┴──────────────────────────────────────┘

重连策略（指数退避）：
```python
async def connect_with_retry(server_params, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await connect(server_params)
        except ConnectionError:
            wait = 2 ** attempt  # 1s, 2s, 4s
            print(f"连接失败，{wait}秒后重试...")
            await asyncio.sleep(wait)
    raise ConnectionError(f"重试{max_retries}次后仍无法连接")
```
""")

# ============================================================================
# 6. MCP 工具转 Function Calling 格式
# ============================================================================
print("\n--- 6. MCP → Function Calling 转换 ---")
print("""
MCP Client 获取工具后，需要转为 LLM 能理解的 Function Calling 格式。

MCP Tool 格式：
  {"name": "get_weather", "description": "...", "inputSchema": {...}}

OpenAI Function Calling 格式：
  {"type": "function", "function": {"name": "...", "description": "...", "parameters": {...}}}

LangChain @tool 格式：
  Tool(name="...", description="...", args_schema=...)
""")

def mcp_tools_to_openai_format(mcp_tools: list[dict]) -> list[dict]:
    """将 MCP 工具列表转为 OpenAI Function Calling 格式"""
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["inputSchema"],
            }
        }
        for tool in mcp_tools
    ]

def mcp_tools_to_langchain_format(mcp_tools: list[dict]) -> list[dict]:
    """将 MCP 工具列表转为 LangChain 兼容格式"""
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "args_schema": tool["inputSchema"],
        }
        for tool in mcp_tools
    ]

# 演示转换
all_tools = client.list_all_tools()
openai_tools = mcp_tools_to_openai_format(all_tools)
print("MCP → OpenAI 格式:")
for t in openai_tools:
    print(f"  {json.dumps(t, ensure_ascii=False)[:100]}...")

print("""
完整的集成流程：
  1. MCP Client 连接 Server → 获取工具列表
  2. 转换为 Function Calling 格式 → 传给 LLM
  3. LLM 返回 tool_calls → 提取工具名和参数
  4. MCP Client 调用对应 Server → 获取结果
  5. 结果返回给 LLM → 生成最终回答

这就是 MCP 与 LLM 集成的核心机制！
下一课会用 LangChain 实际实现这个流程。
""")

print("\n" + "=" * 60)
print("[完成] 第5课完成！你已经学会了：")
print("  [v] MCP Client 基本 API（连接/发现/调用）")
print("  [v] stdio 和 SSE 两种连接方式")
print("  [v] 多 Server 管理（路由/健康检查/故障隔离）")
print("  [v] 错误处理与重连策略")
print("  [v] MCP 工具 → Function Calling 格式转换")
print("=" * 60)
print("\n下一课：06_mcp_with_langchain.py - MCP + LangChain/LangGraph 集成")
