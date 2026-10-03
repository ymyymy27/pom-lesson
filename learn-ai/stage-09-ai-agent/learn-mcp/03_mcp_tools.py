import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：MCP Tools 深入（定义 / 参数 / 错误处理）
==============================================================================

Tools 是 MCP 中最核心、最常用的能力。
本课深入讲解如何设计高质量的 MCP 工具。

内容：
1. 参数设计（复杂类型、可选参数、枚举）
2. 返回值设计（文本、结构化、多段内容）
3. 错误处理（异常捕获、用户友好的错误信息）
4. 工具分类与组织
5. 异步工具与超时控制
6. 工具的安全边界
7. 实战：构建一个多功能 MCP Server
==============================================================================
"""

import json
import asyncio
from datetime import datetime

print("=" * 60)
print("第3课：MCP Tools 深入")
print("=" * 60)

# ============================================================================
# 1. 参数设计
# ============================================================================
print("\n--- 1. 参数设计（JSON Schema）---")
print("""
MCP 工具的参数使用 JSON Schema 定义。
掌握 JSON Schema 是设计好工具的关键。

常用类型：
┌─────────────┬──────────────────────────────────────────┐
│  JSON类型    │  Python对应 + 示例                        │
├─────────────┼──────────────────────────────────────────┤
│  string     │  str    "hello"                           │
│  number     │  float  3.14                              │
│  integer    │  int    42                                │
│  boolean    │  bool   true/false                        │
│  array      │  list   [1, 2, 3]                         │
│  object     │  dict   {"key": "value"}                  │
│  null       │  None                                     │
└─────────────┴──────────────────────────────────────────┘
""")

# 1.1 简单参数
simple_tool = {
    "name": "greet",
    "description": "问候用户",
    "inputSchema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "用户名字"},
        },
        "required": ["name"]
    }
}

# 1.2 复杂参数（枚举、默认值、数组）
complex_tool = {
    "name": "search_products",
    "description": "搜索商品",
    "inputSchema": {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "搜索关键词"
            },
            "category": {
                "type": "string",
                "enum": ["electronics", "books", "clothing", "food"],
                "description": "商品类别"
            },
            "price_range": {
                "type": "object",
                "properties": {
                    "min": {"type": "number", "description": "最低价"},
                    "max": {"type": "number", "description": "最高价"}
                },
                "description": "价格范围"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "标签列表"
            },
            "sort_by": {
                "type": "string",
                "enum": ["price_asc", "price_desc", "rating", "newest"],
                "description": "排序方式，默认 rating"
            },
            "limit": {
                "type": "integer",
                "description": "返回数量，默认10，最大50",
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["keyword"]
    }
}

print("简单工具参数:")
print(f"  {json.dumps(simple_tool['inputSchema']['properties'], ensure_ascii=False)}")

print("\n复杂工具参数:")
for name, schema in complex_tool["inputSchema"]["properties"].items():
    type_info = schema.get("type", "?")
    if "enum" in schema:
        type_info += f" [{'/'.join(schema['enum'][:3])}...]"
    required = "必需" if name in complex_tool["inputSchema"].get("required", []) else "可选"
    print(f"  {name}: {type_info} ({required}) - {schema.get('description', '')[:30]}")

# ============================================================================
# 2. 返回值设计
# ============================================================================
print("\n--- 2. 返回值设计 ---")
print("""
MCP 工具的返回值是 Content 列表：
  [TextContent(...), TextContent(...), ...]

支持的 Content 类型：
- TextContent:      纯文本（最常用）
- ImageContent:     图片（Base64编码）
- EmbeddedResource: 嵌入的资源

设计原则：
1. 返回 LLM 能理解的文本（不是原始二进制）
2. 结构化数据用 JSON 格式
3. 大量数据时做摘要
4. 错误信息要清晰有用
""")

# 模拟不同的返回格式

def tool_return_text(city: str) -> list[dict]:
    """返回纯文本"""
    return [{"type": "text", "text": f"{city}: 晴天，25°C"}]

def tool_return_json(sql: str) -> list[dict]:
    """返回结构化 JSON"""
    data = {"rows": [{"name": "张三", "age": 30}], "count": 1}
    return [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]

def tool_return_multi(query: str) -> list[dict]:
    """返回多段内容"""
    return [
        {"type": "text", "text": f"搜索关键词: {query}"},
        {"type": "text", "text": "结果1: Python 编程入门"},
        {"type": "text", "text": "结果2: Python 数据分析"},
        {"type": "text", "text": f"共找到 2 条结果"},
    ]

print("返回格式示例:")
print(f"  纯文本: {tool_return_text('北京')}")
print(f"  JSON:   {tool_return_json('SELECT...')}")
print(f"  多段:   {tool_return_multi('Python')}")

# ============================================================================
# 3. 错误处理
# ============================================================================
print("\n--- 3. 错误处理 ---")
print("""
MCP 工具的错误处理方式：

方式1：在结果中返回错误信息（推荐，LLM 能看到并处理）
  return [TextContent(type="text", text="错误: 城市不存在")]

方式2：设置 isError 标志
  return [TextContent(type="text", text="...")]
  # 并在响应中标记 isError=True

方式3：抛出异常（会被框架捕获，返回 JSON-RPC error）
  raise McpError(INVALID_PARAMS, "参数错误")

最佳实践：
- 预期内的错误（参数无效、数据不存在）→ 方式1（文本错误）
- 严重错误（权限不足、系统故障）→ 方式2或3
""")

def safe_tool_handler(name: str, arguments: dict) -> list[dict]:
    """带完善错误处理的工具处理器"""
    try:
        # 参数验证
        if name == "get_weather":
            city = arguments.get("city")
            if not city:
                return [{"type": "text", "text": "错误: 缺少必需参数 'city'",
                         "isError": True}]
            if not isinstance(city, str):
                return [{"type": "text", "text": f"错误: 'city' 必须是字符串，收到 {type(city).__name__}",
                         "isError": True}]

            # 业务逻辑
            db = {"北京": "晴，25°C", "上海": "多云，22°C"}
            weather = db.get(city)
            if weather is None:
                # 不存在但不是错误，返回有用信息
                available = list(db.keys())
                return [{"type": "text",
                         "text": f"暂无'{city}'的天气数据。支持的城市: {available}"}]
            return [{"type": "text", "text": f"{city}天气: {weather}"}]

        elif name == "divide":
            a = arguments.get("a", 0)
            b = arguments.get("b", 0)
            if b == 0:
                return [{"type": "text", "text": "错误: 除数不能为零",
                         "isError": True}]
            return [{"type": "text", "text": f"{a} / {b} = {a/b:.4f}"}]

        else:
            return [{"type": "text", "text": f"未知工具: {name}",
                     "isError": True}]

    except Exception as e:
        # 兜底异常处理
        return [{"type": "text",
                 "text": f"工具执行异常: {type(e).__name__}: {e}",
                 "isError": True}]

# 测试各种错误场景
test_cases = [
    ("get_weather", {"city": "北京"}),
    ("get_weather", {}),
    ("get_weather", {"city": "巴黎"}),
    ("divide", {"a": 10, "b": 3}),
    ("divide", {"a": 10, "b": 0}),
    ("unknown_tool", {}),
]

for name, args in test_cases:
    result = safe_tool_handler(name, args)
    is_error = result[0].get("isError", False)
    status = "❌" if is_error else "✅"
    print(f"  {status} {name}({args}) → {result[0]['text']}")

# ============================================================================
# 4. 工具分类与组织
# ============================================================================
print("\n--- 4. 工具分类与组织 ---")
print("""
当工具数量多时，按功能分类组织：

┌─────────────────────────────────────────────────────────┐
│  类别        │  工具                  │  说明             │
├─────────────────────────────────────────────────────────┤
│  查询类      │  get_weather           │  只读，无副作用   │
│              │  search_products       │                   │
│              │  query_database        │                   │
├─────────────────────────────────────────────────────────┤
│  操作类      │  send_email            │  有副作用         │
│              │  create_file           │  需要确认         │
│              │  update_record         │                   │
├─────────────────────────────────────────────────────────┤
│  计算类      │  calculator            │  纯计算           │
│              │  convert_unit          │  无外部依赖       │
│              │  format_date           │                   │
├─────────────────────────────────────────────────────────┤
│  系统类      │  get_system_info       │  获取环境信息     │
│              │  check_health          │                   │
│              │  get_logs              │                   │
└─────────────────────────────────────────────────────────┘

命名规范：
- 动词开头: get_, search_, create_, update_, delete_, send_
- 清晰具体: get_weather > get_data
- 用下划线: search_products > searchProducts
""")

# ============================================================================
# 5. 异步工具与超时控制
# ============================================================================
print("\n--- 5. 异步工具与超时控制 ---")
print("""
MCP Server 是异步的（async/await）。
对于耗时操作（HTTP请求、数据库查询），需要超时控制。

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "fetch_url":
        url = arguments["url"]
        try:
            async with asyncio.timeout(10):  # 10秒超时
                async with httpx.AsyncClient() as client:
                    response = await client.get(url)
                    return [types.TextContent(
                        type="text",
                        text=response.text[:5000]
                    )]
        except asyncio.TimeoutError:
            return [types.TextContent(
                type="text",
                text="请求超时（10秒），请稍后重试"
            )]
```
""")

# 模拟异步工具执行
async def simulate_async_tool(name: str, arguments: dict, timeout: float = 5.0):
    """模拟带超时的异步工具"""
    try:
        async with asyncio.timeout(timeout):
            # 模拟耗时操作
            await asyncio.sleep(0.1)
            return {"status": "success", "data": f"{name} 执行完成"}
    except asyncio.TimeoutError:
        return {"status": "timeout", "error": f"操作超时（{timeout}秒）"}

# 运行异步示例
result = asyncio.run(simulate_async_tool("fetch_data", {"url": "..."}, timeout=5.0))
print(f"  异步工具执行: {result}")

# ============================================================================
# 6. 安全边界
# ============================================================================
print("\n--- 6. 安全边界 ---")
print("""
MCP Server 运行在用户机器上，安全至关重要！

┌──────────────────────────────────────────────────────────┐
│  安全原则                                                 │
├──────────────────────────────────────────────────────────┤
│  1. 最小权限                                              │
│     - 只暴露必要的工具                                    │
│     - 文件操作限制在特定目录                              │
│     - 数据库只允许 SELECT                                 │
│                                                          │
│  2. 输入验证                                              │
│     - 检查参数类型和范围                                  │
│     - 防止路径遍历（../../etc/passwd）                    │
│     - 防止 SQL 注入                                      │
│     - 防止命令注入                                        │
│                                                          │
│  3. 资源限制                                              │
│     - 超时控制（防止卡死）                                │
│     - 返回大小限制（防止内存溢出）                        │
│     - 频率限制（防止滥用）                                │
│                                                          │
│  4. 副作用控制                                            │
│     - 只读操作优先                                        │
│     - 有副作用的操作标记清楚                              │
│     - 敏感操作需要二次确认                                │
│                                                          │
│  5. 日志审计                                              │
│     - 记录所有工具调用                                    │
│     - 记录参数和结果                                      │
│     - 便于排查问题和安全审计                              │
└──────────────────────────────────────────────────────────┘
""")

# 安全工具包装器示例
class SecureToolWrapper:
    """安全的工具执行包装器"""

    def __init__(self):
        self.call_count = {}
        self.max_calls_per_minute = 60

    def validate_and_execute(self, name: str, arguments: dict) -> list[dict]:
        """验证参数并安全执行"""
        # 频率限制
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        key = f"{name}:{now}"
        self.call_count[key] = self.call_count.get(key, 0) + 1
        if self.call_count[key] > self.max_calls_per_minute:
            return [{"type": "text", "text": f"频率限制: {name} 每分钟最多{self.max_calls_per_minute}次",
                     "isError": True}]

        # 日志
        print(f"    [LOG] tools/call: {name}({json.dumps(arguments, ensure_ascii=False)[:80]})")

        # 执行
        result = safe_tool_handler(name, arguments)

        # 结果大小限制
        for item in result:
            if len(item.get("text", "")) > 10000:
                item["text"] = item["text"][:10000] + "\n... (结果被截断，超过10KB限制)"

        return result

wrapper = SecureToolWrapper()
print("\n安全包装器测试:")
r = wrapper.validate_and_execute("get_weather", {"city": "北京"})
print(f"  结果: {r[0]['text']}")

# ============================================================================
# 7. 实战：多功能 Server 设计
# ============================================================================
print("\n--- 7. 实战：多功能 Server 设计 ---")
print("""
设计一个"开发者助手"MCP Server 的完整工具集：

```python
# dev_assistant_server.py

tools = [
    # 查询类
    Tool("search_docs",     "搜索技术文档"),
    Tool("query_database",  "查询数据库（只读）"),
    Tool("get_api_status",  "检查API健康状态"),
    
    # 文件类
    Tool("read_file",       "读取项目文件"),
    Tool("list_directory",  "列出目录内容"),
    
    # 分析类
    Tool("analyze_code",    "分析代码复杂度"),
    Tool("check_deps",      "检查依赖版本"),
    
    # 执行类
    Tool("run_test",        "运行单元测试"),
    Tool("format_code",     "格式化代码"),
]

resources = [
    Resource("config://project/settings",  "项目配置"),
    Resource("file://README.md",           "项目说明"),
    Resource("db://main/schema",           "数据库结构"),
]

prompts = [
    Prompt("code-review",   "代码审查"),
    Prompt("debug-error",   "调试错误"),
    Prompt("write-test",    "编写测试"),
]
```

这就是一个实用的 MCP Server 蓝图！
第5-7课会实际构建并运行。
""")

print("\n" + "=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] 复杂参数设计（枚举/数组/嵌套对象）")
print("  [v] 返回值设计（文本/JSON/多段内容）")
print("  [v] 完善的错误处理策略")
print("  [v] 工具分类与命名规范")
print("  [v] 异步工具与超时控制")
print("  [v] 安全边界（验证/限制/审计）")
print("  [v] 多功能 Server 设计蓝图")
print("=" * 60)
print("\n下一课：04_mcp_resources.py - MCP Resources 与 Prompts")
