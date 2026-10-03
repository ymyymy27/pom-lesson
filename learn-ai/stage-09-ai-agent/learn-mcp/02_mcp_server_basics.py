import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：MCP Server 基础（工具 / 资源 / 提示）
==============================================================================

本课学习如何创建一个 MCP Server。

MCP Server 是什么？
  → 一个独立的程序，通过 MCP 协议向 Client 暴露能力（工具/资源/提示）。

MCP Python SDK（官方库：mcp）提供了简洁的 API：

  from mcp.server import Server
  from mcp.server.stdio import stdio_server

  server = Server("my-server")

  @server.list_tools()          # 声明可用工具
  @server.call_tool()           # 处理工具调用
  @server.list_resources()      # 声明可用资源
  @server.read_resource()       # 处理资源读取
  @server.list_prompts()        # 声明可用提示
  @server.get_prompt()          # 处理提示获取

本课重点：
1. Server 的基本结构
2. 工具（Tools）定义
3. 资源（Resources）定义
4. 提示（Prompts）定义
5. 运行 Server

⚠️ 注意：本课代码展示 MCP Server 的结构和写法。
实际运行需要 MCP Client 连接（第5课）。
==============================================================================
"""

import json

print("=" * 60)
print("第2课：MCP Server 基础")
print("=" * 60)

# ============================================================================
# 1. MCP Server 基本结构
# ============================================================================
print("\n--- 1. MCP Server 基本结构 ---")
print("""
一个最小的 MCP Server：

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# 1. 创建 Server 实例
server = Server("my-first-server")

# 2. 定义工具列表
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="hello",
            description="打招呼",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "名字"}
                },
                "required": ["name"]
            }
        )
    ]

# 3. 处理工具调用
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "hello":
        return [types.TextContent(
            type="text",
            text=f"你好，{arguments['name']}！"
        )]
    raise ValueError(f"未知工具: {name}")

# 4. 运行
async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

import asyncio
asyncio.run(main())
```

关键组件：
- Server("name"):       创建服务器实例
- @server.list_tools():  声明工具列表
- @server.call_tool():   处理工具调用请求
- stdio_server():        通过 stdin/stdout 通信
""")

# ============================================================================
# 2. Tool 定义详解
# ============================================================================
print("\n--- 2. Tool 定义详解 ---")
print("""
Tool 的定义结构（types.Tool）：

  Tool(
      name="工具名",           # 唯一标识，LLM 看到的名字
      description="工具描述",   # LLM 判断何时使用的依据
      inputSchema={            # JSON Schema 格式的参数定义
          "type": "object",
          "properties": {
              "param1": {"type": "string", "description": "..."},
              "param2": {"type": "number", "description": "..."},
          },
          "required": ["param1"]
      }
  )

这和 Function Calling 的工具定义是同一个格式！
MCP 复用了 JSON Schema 标准。
""")

# 模拟定义几个工具
tools_definition = [
    {
        "name": "get_weather",
        "description": "查询指定城市的当前天气信息，返回温度、湿度和天气描述",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称，如'北京'"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"],
                         "description": "温度单位，默认celsius"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "search_database",
        "description": "查询数据库。只支持 SELECT 语句",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "SQL SELECT 查询语句"},
                "database": {"type": "string", "description": "数据库名称"}
            },
            "required": ["sql"]
        }
    },
    {
        "name": "send_notification",
        "description": "发送通知消息。这是一个有副作用的操作",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "通知标题"},
                "message": {"type": "string", "description": "通知内容"},
                "priority": {"type": "string", "enum": ["low", "normal", "high"]}
            },
            "required": ["title", "message"]
        }
    }
]

print(f"定义了 {len(tools_definition)} 个工具:")
for t in tools_definition:
    required = t["inputSchema"].get("required", [])
    all_params = list(t["inputSchema"]["properties"].keys())
    print(f"  🔧 {t['name']}({', '.join(all_params)})")
    print(f"     必需: {required}")
    print(f"     描述: {t['description'][:40]}...")
    print()

# ============================================================================
# 3. Tool 调用处理
# ============================================================================
print("\n--- 3. Tool 调用处理 ---")
print("""
当 Client 发来 tools/call 请求时，Server 需要：
1. 根据 name 找到对应的处理函数
2. 解析 arguments 参数
3. 执行操作
4. 返回结果（TextContent 或 ImageContent 或 EmbeddedResource）

返回值类型：
- TextContent:      纯文本结果（最常用）
- ImageContent:     图片（Base64）
- EmbeddedResource: 嵌入的资源内容

代码模式：
```python
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    match name:
        case "get_weather":
            result = get_weather(arguments["city"])
            return [types.TextContent(type="text", text=result)]
        case "search_database":
            result = query_db(arguments["sql"])
            return [types.TextContent(type="text", text=json.dumps(result))]
        case _:
            raise ValueError(f"未知工具: {name}")
```
""")

# 模拟工具执行
def simulate_tool_call(name: str, arguments: dict) -> dict:
    """模拟 MCP Server 处理工具调用"""
    if name == "get_weather":
        city = arguments.get("city", "未知")
        db = {"北京": "晴，25°C", "上海": "多云，22°C"}
        weather = db.get(city, f"暂无{city}数据")
        return {"type": "text", "text": weather}

    elif name == "search_database":
        sql = arguments.get("sql", "")
        return {"type": "text", "text": f"查询结果: [{sql}] → 3 rows returned"}

    elif name == "send_notification":
        title = arguments.get("title", "")
        message = arguments.get("message", "")
        return {"type": "text", "text": f"✅ 通知已发送: [{title}] {message}"}

    else:
        return {"type": "text", "text": f"未知工具: {name}"}

# 测试
test_calls = [
    ("get_weather", {"city": "北京"}),
    ("search_database", {"sql": "SELECT * FROM users LIMIT 5"}),
    ("send_notification", {"title": "提醒", "message": "会议在10分钟后开始"}),
]

for name, args in test_calls:
    result = simulate_tool_call(name, args)
    print(f"  tools/call: {name}({args})")
    print(f"  → {result['text']}")
    print()

# ============================================================================
# 4. Resource 定义
# ============================================================================
print("\n--- 4. Resource（资源）定义 ---")
print("""
Resources 是 MCP Server 暴露的数据源，Client/应用可以读取。

与 Tools 的区别：
- Tools: LLM 主动调用（"帮我查天气"）
- Resources: 应用被动加载（"把这份文档加入上下文"）

Resource 定义：
  Resource(
      uri="file:///path/to/doc.md",    # 唯一标识符（URI）
      name="项目文档",                  # 显示名称
      description="项目的README文档",   # 描述
      mimeType="text/markdown"          # MIME 类型
  )

URI 格式示例：
  file:///path/to/file.txt        本地文件
  db://database/table              数据库表
  api://service/endpoint           API 端点
  config://app/settings            配置信息

代码模式：
```python
@server.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="config://app/settings",
            name="应用配置",
            description="当前应用的配置信息",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "config://app/settings":
        return json.dumps({"debug": True, "version": "1.0"})
    raise ValueError(f"未知资源: {uri}")
```
""")

# 模拟资源
resources = [
    {
        "uri": "file:///project/README.md",
        "name": "项目说明",
        "description": "项目的 README 文档",
        "mimeType": "text/markdown",
        "content": "# My Project\n\n这是一个示例项目。\n\n## 功能\n- 功能A\n- 功能B"
    },
    {
        "uri": "config://app/settings",
        "name": "应用配置",
        "description": "当前运行环境的配置",
        "mimeType": "application/json",
        "content": json.dumps({"debug": True, "version": "2.1.0", "model": "qwen2.5:7b"})
    },
    {
        "uri": "db://main/schema",
        "name": "数据库Schema",
        "description": "主数据库的表结构",
        "mimeType": "text/plain",
        "content": "employees(id, name, dept, salary)\nproducts(id, name, price, stock)"
    },
]

print(f"定义了 {len(resources)} 个资源:")
for r in resources:
    print(f"  📄 {r['name']} [{r['mimeType']}]")
    print(f"     URI: {r['uri']}")
    print(f"     内容: {r['content'][:50]}...")
    print()

# ============================================================================
# 5. Prompt 定义
# ============================================================================
print("\n--- 5. Prompt（提示模板）定义 ---")
print("""
Prompts 是预定义的交互模板，用户可以选择使用。

用途：
- 代码审查模板
- 翻译模板
- 数据分析模板
- 总结模板

Prompt 定义：
  Prompt(
      name="code-review",
      description="代码审查模板",
      arguments=[
          PromptArgument(name="code", description="要审查的代码", required=True),
          PromptArgument(name="language", description="编程语言", required=False),
      ]
  )

返回的消息：
  GetPromptResult(
      description="代码审查",
      messages=[
          PromptMessage(role="user", content=TextContent(text="请审查..."))
      ]
  )
""")

prompts = [
    {
        "name": "code-review",
        "description": "对代码进行专业审查，给出改进建议",
        "arguments": [
            {"name": "code", "description": "要审查的代码", "required": True},
            {"name": "language", "description": "编程语言", "required": False},
        ]
    },
    {
        "name": "explain-error",
        "description": "解释错误信息并给出解决方案",
        "arguments": [
            {"name": "error", "description": "错误信息", "required": True},
            {"name": "context", "description": "相关上下文", "required": False},
        ]
    },
    {
        "name": "summarize-text",
        "description": "将长文本总结为要点",
        "arguments": [
            {"name": "text", "description": "要总结的文本", "required": True},
            {"name": "max_points", "description": "最多几个要点", "required": False},
        ]
    }
]

print(f"定义了 {len(prompts)} 个提示模板:")
for p in prompts:
    args = [a["name"] + ("*" if a["required"] else "") for a in p["arguments"]]
    print(f"  📝 {p['name']}({', '.join(args)})")
    print(f"     {p['description']}")
    print()

# ============================================================================
# 6. 完整 Server 代码示例
# ============================================================================
print("\n--- 6. 完整 Server 代码示例 ---")
print("""
下面是一个包含 Tools + Resources + Prompts 的完整 MCP Server：

```python
# weather_server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types
import json

server = Server("weather-server")

# ===== Tools =====
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_weather",
            description="查询城市天气",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名"}
                },
                "required": ["city"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_weather":
        city = arguments["city"]
        # 实际中调用天气API
        weather = f"{city}: 晴天，25°C"
        return [types.TextContent(type="text", text=weather)]
    raise ValueError(f"未知工具: {name}")

# ===== Resources =====
@server.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="config://weather/cities",
            name="支持的城市列表",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "config://weather/cities":
        return json.dumps(["北京","上海","广州","深圳"])
    raise ValueError(f"未知资源: {uri}")

# ===== Prompts =====
@server.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="weather-report",
            description="生成天气报告",
            arguments=[
                types.PromptArgument(
                    name="city", description="城市", required=True
                )
            ]
        )
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: dict):
    if name == "weather-report":
        city = arguments.get("city", "未知")
        return types.GetPromptResult(
            description=f"{city}天气报告",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"请查询{city}的天气并生成详细报告"
                    )
                )
            ]
        )

# ===== 运行 =====
async def main():
    async with stdio_server() as (read, write):
        await server.run(
            read, write,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

运行方式：
  python weather_server.py          # 作为 stdio server 运行
  
  # 或在 Claude Desktop 配置文件中引用：
  # claude_desktop_config.json
  {
    "mcpServers": {
      "weather": {
        "command": "python",
        "args": ["weather_server.py"]
      }
    }
  }
""")

# ============================================================================
# 7. Server 配置（Claude Desktop / Cursor）
# ============================================================================
print("\n--- 7. 在 Host 中配置 Server ---")
print("""
不同的 MCP Host 有不同的配置方式：

1. Claude Desktop（claude_desktop_config.json）：
   {
     "mcpServers": {
       "weather": {
         "command": "python",
         "args": ["/path/to/weather_server.py"]
       },
       "database": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-sqlite",
                  "/path/to/db.sqlite"]
       }
     }
   }

2. Cursor（.cursor/mcp.json）：
   {
     "mcpServers": {
       "my-server": {
         "command": "python",
         "args": ["server.py"],
         "env": {"API_KEY": "xxx"}
       }
     }
   }

3. 使用 uvx/npx 运行已发布的 Server：
   {
     "weather": {
       "command": "uvx",
       "args": ["mcp-server-weather"]
     }
   }
""")

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] MCP Server 的基本结构")
print("  [v] Tool 定义（name + description + inputSchema）")
print("  [v] Tool 调用处理（call_tool）")
print("  [v] Resource 定义与读取")
print("  [v] Prompt 模板定义")
print("  [v] 完整 Server 代码结构")
print("  [v] 在 Host 中配置 Server")
print("=" * 60)
print("\n下一课：03_mcp_tools.py - MCP Tools 深入")
