import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第4课：MCP Resources 与 Prompts
==============================================================================

上一课深入了 Tools。本课聚焦 MCP 的另外两种能力：

Resources（资源）：
  - LLM 可以读取的数据源
  - 由应用程序控制何时加载
  - 类比：给 LLM 提供"参考资料"

Prompts（提示模板）：
  - 预定义的交互模板
  - 由用户选择使用
  - 类比：给用户提供"快捷方式"

本课内容：
1. Resource 的 URI 体系
2. 静态资源 vs 动态资源
3. Resource Templates（资源模板）
4. Prompt 设计与参数
5. 多消息 Prompt
6. 三种能力的协作
==============================================================================
"""

import json
from datetime import datetime
import random

print("=" * 60)
print("第4课：MCP Resources 与 Prompts")
print("=" * 60)

# ============================================================================
# 1. Resource URI 体系
# ============================================================================
print("\n--- 1. Resource URI 体系 ---")
print("""
每个 Resource 通过 URI（统一资源标识符）唯一标识。

常用 URI 模式：
┌─────────────────────────────────┬────────────────────────┐
│  URI                            │  含义                   │
├─────────────────────────────────┼────────────────────────┤
│  file:///path/to/file.md        │  本地文件               │
│  db://mydb/users                │  数据库表               │
│  db://mydb/users/schema         │  表结构                 │
│  api://github/repos             │  API 数据               │
│  config://app/settings          │  配置信息               │
│  log://app/2024-01-15           │  日志                   │
│  metric://server/cpu            │  监控指标               │
│  doc://api/reference            │  文档                   │
└─────────────────────────────────┴────────────────────────┘

URI 设计原则：
- scheme://authority/path 格式
- scheme 表示数据类型（file/db/api/config）
- 路径层级清晰
""")

# ============================================================================
# 2. 静态资源 vs 动态资源
# ============================================================================
print("\n--- 2. 静态资源 vs 动态资源 ---")
print("""
静态资源：内容固定不变（配置、Schema、文档）
动态资源：内容实时生成（监控、日志、状态）
""")

# 模拟资源注册表
class ResourceRegistry:
    def __init__(self):
        self.resources = {}

    def register(self, uri, name, description, mime_type, content_fn):
        self.resources[uri] = {
            "uri": uri, "name": name,
            "description": description, "mimeType": mime_type,
            "_fn": content_fn,
        }

    def list_resources(self):
        return [{k: v for k, v in r.items() if k != "_fn"}
                for r in self.resources.values()]

    def read_resource(self, uri):
        r = self.resources.get(uri)
        if not r:
            raise ValueError(f"资源不存在: {uri}")
        return r["_fn"]()

registry = ResourceRegistry()

# 2.1 静态资源
registry.register(
    "config://app/settings", "应用配置",
    "应用的全局配置参数", "application/json",
    lambda: json.dumps({
        "app_name": "MyAIApp", "version": "2.1.0",
        "model": "qwen2.5:7b", "max_tokens": 4096,
        "temperature": 0.7, "debug": False,
    }, ensure_ascii=False, indent=2)
)

registry.register(
    "db://main/schema", "数据库结构",
    "主数据库的所有表结构", "text/plain",
    lambda: """Table: users
  id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, created_at TIMESTAMP

Table: products
  id INTEGER PRIMARY KEY, name TEXT, price DECIMAL, category TEXT, stock INTEGER

Table: orders
  id INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER, quantity INTEGER, total DECIMAL"""
)

registry.register(
    "doc://api/endpoints", "API 文档",
    "后端 API 端点列表", "text/markdown",
    lambda: """# API Endpoints
## Users
- GET /api/users - 用户列表
- POST /api/users - 创建用户
## Products
- GET /api/products - 商品列表
## Orders
- GET /api/orders - 订单列表
- POST /api/orders - 创建订单"""
)

# 2.2 动态资源
registry.register(
    "metric://server/status", "服务器状态",
    "服务器实时运行状态", "application/json",
    lambda: json.dumps({
        "timestamp": datetime.now().isoformat(),
        "cpu_usage": f"{random.uniform(20, 80):.1f}%",
        "memory_usage": f"{random.uniform(40, 70):.1f}%",
        "active_connections": random.randint(10, 100),
        "uptime": "3d 14h 22m",
    }, ensure_ascii=False, indent=2)
)

registry.register(
    "log://app/recent", "最近日志",
    "应用最近的日志条目", "text/plain",
    lambda: "\n".join([
        f"[{datetime.now().strftime('%H:%M:%S')}] INFO  请求处理完成 /api/users (200)",
        f"[{datetime.now().strftime('%H:%M:%S')}] WARN  数据库连接池使用率 85%",
        f"[{datetime.now().strftime('%H:%M:%S')}] ERROR 第三方API超时 payment-service",
        f"[{datetime.now().strftime('%H:%M:%S')}] INFO  定时任务完成: data_cleanup",
    ])
)

print("已注册的资源:")
for r in registry.list_resources():
    rtype = "动态" if r["uri"].startswith(("metric://", "log://")) else "静态"
    print(f"  📄 [{rtype}] {r['name']} ({r['mimeType']})")
    print(f"     URI: {r['uri']}")

print(f"\n读取静态资源 config://app/settings:")
print(f"  {registry.read_resource('config://app/settings')[:100]}...")

print(f"\n读取动态资源 metric://server/status:")
print(f"  {registry.read_resource('metric://server/status')[:100]}...")

# ============================================================================
# 3. Resource Templates（资源模板）
# ============================================================================
print("\n--- 3. Resource Templates ---")
print("""
Resource Templates 支持参数化的 URI，访问同类但不同实例的资源。

固定 URI:    db://main/schema           → 只能访问一个
模板 URI:    db://main/{table}/schema   → 可以访问任意表

MCP 协议中的定义：
```python
@server.list_resource_templates()
async def list_templates():
    return [
        types.ResourceTemplate(
            uriTemplate="db://main/{table}/schema",
            name="表结构查看",
            description="查看指定表的字段定义",
            mimeType="text/plain"
        ),
        types.ResourceTemplate(
            uriTemplate="log://app/{date}",
            name="历史日志",
            description="查看指定日期的日志，date格式: YYYY-MM-DD",
            mimeType="text/plain"
        )
    ]
```

Client 请求时替换参数：
  resources/read → uri: "db://main/users/schema"
  resources/read → uri: "log://app/2024-03-15"
""")

# 模拟 Resource Template 解析
table_schemas = {
    "users": "id INTEGER PK, name TEXT, email TEXT, created_at TIMESTAMP",
    "products": "id INTEGER PK, name TEXT, price DECIMAL, category TEXT",
    "orders": "id INTEGER PK, user_id INT FK, product_id INT FK, quantity INT",
}

def resolve_template(uri: str) -> str:
    """解析模板 URI 并返回内容"""
    if uri.startswith("db://main/") and uri.endswith("/schema"):
        table = uri.replace("db://main/", "").replace("/schema", "")
        schema = table_schemas.get(table)
        if schema:
            return f"Table: {table}\n  {schema}"
        return f"表不存在: {table}。可用表: {list(table_schemas.keys())}"

    if uri.startswith("log://app/"):
        date = uri.replace("log://app/", "")
        return f"[{date}] INFO 系统正常运行\n[{date}] WARN 内存使用率 78%"

    return f"无法解析 URI: {uri}"

print("模板 URI 解析演示:")
for uri in ["db://main/users/schema", "db://main/products/schema",
            "db://main/unknown/schema", "log://app/2024-03-15"]:
    print(f"  {uri}")
    print(f"    → {resolve_template(uri)[:60]}...")
    print()

# ============================================================================
# 4. Prompt 设计与参数
# ============================================================================
print("\n--- 4. Prompt 设计 ---")
print("""
Prompts 是预定义的交互模板，用户在 Host 中选择使用。

用途场景：
- IDE 中选择"代码审查"模板，自动填入当前文件
- Claude Desktop 选择"翻译"模板，填入文本
- 选择"SQL生成"模板，填入自然语言需求

Prompt 定义：
```python
@server.list_prompts()
async def list_prompts():
    return [
        types.Prompt(
            name="code-review",
            description="对代码进行专业审查",
            arguments=[
                types.PromptArgument(
                    name="code",
                    description="要审查的代码",
                    required=True
                ),
                types.PromptArgument(
                    name="language",
                    description="编程语言",
                    required=False
                )
            ]
        )
    ]
```
""")

# 模拟 Prompt 系统
class PromptRegistry:
    def __init__(self):
        self.prompts = {}

    def register(self, name, description, arguments, message_fn):
        self.prompts[name] = {
            "name": name,
            "description": description,
            "arguments": arguments,
            "_fn": message_fn,
        }

    def list_prompts(self):
        return [{k: v for k, v in p.items() if k != "_fn"}
                for p in self.prompts.values()]

    def get_prompt(self, name, arguments):
        p = self.prompts.get(name)
        if not p:
            raise ValueError(f"未知 Prompt: {name}")
        return p["_fn"](arguments)

prompt_registry = PromptRegistry()

# 4.1 代码审查模板
prompt_registry.register(
    "code-review",
    "对代码进行专业审查，给出改进建议",
    [
        {"name": "code", "description": "要审查的代码", "required": True},
        {"name": "language", "description": "编程语言", "required": False},
    ],
    lambda args: {
        "description": "代码审查",
        "messages": [
            {"role": "user", "content": f"""请对以下{args.get('language', '')}代码进行专业审查：

```{args.get('language', '')}
{args['code']}
```

请从以下方面审查：
1. 代码正确性
2. 性能问题
3. 安全隐患
4. 代码风格
5. 改进建议"""}
        ]
    }
)

# 4.2 错误诊断模板
prompt_registry.register(
    "debug-error",
    "分析错误信息并给出解决方案",
    [
        {"name": "error", "description": "错误信息", "required": True},
        {"name": "context", "description": "相关代码上下文", "required": False},
    ],
    lambda args: {
        "description": "错误诊断",
        "messages": [
            {"role": "user", "content": f"""我遇到了以下错误：

```
{args['error']}
```
{f'''
相关代码：
```
{args["context"]}
```''' if args.get('context') else ''}

请帮我：
1. 解释这个错误的原因
2. 给出具体的解决方案
3. 说明如何避免类似错误"""}
        ]
    }
)

# 4.3 SQL 生成模板
prompt_registry.register(
    "generate-sql",
    "根据自然语言描述生成 SQL 查询",
    [
        {"name": "description", "description": "用自然语言描述你想查询的内容", "required": True},
        {"name": "schema", "description": "数据库表结构", "required": False},
    ],
    lambda args: {
        "description": "SQL 生成",
        "messages": [
            {"role": "user", "content": f"""根据以下描述生成 SQL 查询：

需求：{args['description']}
{f'''
数据库结构：
{args["schema"]}''' if args.get('schema') else ''}

要求：
1. 只生成 SELECT 查询
2. 添加中文注释说明
3. 考虑性能优化"""}
        ]
    }
)

# 4.4 测试用例生成模板
prompt_registry.register(
    "generate-tests",
    "为代码生成单元测试",
    [
        {"name": "code", "description": "要测试的代码", "required": True},
        {"name": "framework", "description": "测试框架（pytest/unittest）", "required": False},
    ],
    lambda args: {
        "description": "测试生成",
        "messages": [
            {"role": "user", "content": f"""为以下代码生成单元测试：

```python
{args['code']}
```

使用 {args.get('framework', 'pytest')} 框架。
要求：覆盖正常情况、边界情况和异常情况。"""}
        ]
    }
)

print("已注册的 Prompt 模板:")
for p in prompt_registry.list_prompts():
    args_str = ", ".join([
        f"{a['name']}{'*' if a['required'] else ''}"
        for a in p["arguments"]
    ])
    print(f"  📝 {p['name']}({args_str})")
    print(f"     {p['description']}")

# 测试 Prompt 生成
print(f"\n使用 code-review 模板:")
result = prompt_registry.get_prompt("code-review", {
    "code": "def add(a, b): return a + b",
    "language": "python"
})
print(f"  生成的消息: {result['messages'][0]['content'][:100]}...")

print(f"\n使用 generate-sql 模板:")
result = prompt_registry.get_prompt("generate-sql", {
    "description": "查找每个部门薪资最高的员工",
    "schema": "employees(id, name, dept, salary)"
})
print(f"  生成的消息: {result['messages'][0]['content'][:100]}...")

# ============================================================================
# 5. 多消息 Prompt
# ============================================================================
print("\n--- 5. 多消息 Prompt ---")
print("""
Prompt 可以返回多条消息，构成完整的对话模板。

```python
@server.get_prompt()
async def get_prompt(name, arguments):
    if name == "expert-consultation":
        return types.GetPromptResult(
            description="专家咨询",
            messages=[
                # 先设定角色
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text="你是一位资深Python架构师..."
                    )
                ),
                # AI 确认角色
                types.PromptMessage(
                    role="assistant",
                    content=types.TextContent(
                        type="text",
                        text="好的，我是Python架构师..."
                    )
                ),
                # 用户提出实际问题
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"请审查: {arguments['code']}"
                    )
                )
            ]
        )
```

多消息的好处：
- 预设 AI 的角色和行为
- 提供 Few-shot 示例
- 构建完整的对话上下文
""")

# 多消息 Prompt 示例
multi_msg_prompt = {
    "description": "Python 架构师咨询",
    "messages": [
        {"role": "user", "content": "你是一位有 15 年经验的 Python 架构师，擅长设计高性能、可维护的系统。"},
        {"role": "assistant", "content": "好的，我会从架构设计、性能优化、代码质量等角度为你提供专业建议。请告诉我你的需求。"},
        {"role": "user", "content": "请帮我审查以下代码的架构设计：\n```python\ndef process(data): ...\n```"},
    ]
}

print("多消息 Prompt 示例:")
for msg in multi_msg_prompt["messages"]:
    print(f"  [{msg['role']:9s}] {msg['content'][:60]}...")

# ============================================================================
# 6. 三种能力的协作
# ============================================================================
print("\n--- 6. 三种能力的协作 ---")
print("""
Tools + Resources + Prompts 协同工作的典型场景：

场景：代码审查工作流

  1. Resource 提供上下文
     → 读取 config://project/settings（项目配置）
     → 读取 doc://coding-standards（编码规范）

  2. Prompt 构建交互模板
     → 用户选择 "code-review" 模板
     → 自动填入代码和上下文

  3. Tool 执行操作
     → LLM 调用 analyze_code() 工具检查复杂度
     → LLM 调用 check_style() 工具检查代码风格
     → LLM 基于所有信息生成审查报告

流程图：
  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │Resources │ ──→ │ Prompts  │ ──→ │  Tools   │
  │加载上下文 │     │构建模板  │     │执行操作  │
  └──────────┘     └──────────┘     └──────────┘
  (应用控制)       (用户选择)       (LLM控制)

另一个场景：数据库查询助手

  1. Resource: db://main/schema → 让 LLM 了解表结构
  2. Prompt: "generate-sql" → 用户描述需求
  3. Tool: query_database() → 执行生成的 SQL
""")

# 模拟协作流程
print("协作流程演示 - 数据库查询助手:")

print("  Step 1 [Resource] 加载表结构")
schema = registry.read_resource("db://main/schema")
print(f"    {schema[:80]}...")

print("  Step 2 [Prompt] 用户选择 SQL 生成模板")
prompt_result = prompt_registry.get_prompt("generate-sql", {
    "description": "查找每个部门薪资最高的员工",
    "schema": schema,
})
print(f"    模板已填充，消息长度: {len(prompt_result['messages'][0]['content'])} 字符")

print("  Step 3 [Tool] LLM 生成 SQL 并调用查询工具")
print("    🔧 query_database(sql='SELECT dept, name, MAX(salary)...')")
print("    📋 → 返回查询结果")

# ============================================================================
# 7. Resources & Prompts 最佳实践
# ============================================================================
print("\n--- 7. 最佳实践 ---")
print("""
Resources 最佳实践：
┌──────────────────────────────────────────────────────────┐
│  ✅ URI 命名清晰，scheme 表达数据类型                     │
│  ✅ 提供 mimeType 帮助 Client 正确处理                   │
│  ✅ 动态资源加缓存（避免每次重新生成）                    │
│  ✅ 大资源做分页或摘要                                    │
│  ✅ 使用 Resource Templates 支持参数化访问               │
│  ❌ 不要暴露敏感数据（密码、密钥）                        │
│  ❌ 不要返回超大内容（限制大小）                          │
└──────────────────────────────────────────────────────────┘

Prompts 最佳实践：
┌──────────────────────────────────────────────────────────┐
│  ✅ 描述清晰，用户一看就知道用途                          │
│  ✅ 参数有 description，说明格式要求                      │
│  ✅ 必需参数和可选参数区分明确                            │
│  ✅ 多消息 Prompt 预设角色和示例                          │
│  ✅ 生成的消息结构清晰、有格式                            │
│  ❌ 不要设计过于复杂的参数（保持简单）                    │
│  ❌ 不要在 Prompt 中硬编码变化的内容（用 Resource）       │
└──────────────────────────────────────────────────────────┘
""")

print("\n" + "=" * 60)
print("[完成] 第4课完成！你已经学会了：")
print("  [v] Resource URI 体系设计")
print("  [v] 静态资源 vs 动态资源")
print("  [v] Resource Templates 参数化访问")
print("  [v] Prompt 设计与参数定义")
print("  [v] 多消息 Prompt 构建")
print("  [v] Tools + Resources + Prompts 协作模式")
print("  [v] 最佳实践")
print("=" * 60)
print("\n下一课：05_mcp_client.py - MCP Client 开发与集成")
