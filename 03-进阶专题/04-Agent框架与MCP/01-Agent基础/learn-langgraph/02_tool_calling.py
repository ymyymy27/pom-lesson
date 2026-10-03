import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：工具定义与 LLM 工具调用
==============================================================================

什么是工具调用（Tool Calling）？
-----------------------------
工具调用让 LLM 不只是"说话"，还能"做事"：
- 搜索网络
- 查询数据库
- 执行代码
- 调用 API
- 读写文件

工作流程：
  用户问题 → LLM 判断需要调用哪个工具 → 返回工具名+参数
  → 程序执行工具 → 将结果返回给 LLM → LLM 生成最终回答

注意：LLM 不直接执行工具！它只是"决定"调用什么工具、传什么参数。
实际执行由我们的程序完成。

本课内容：
1. 用 @tool 装饰器定义工具
2. 将工具绑定到 LLM
3. 理解 tool_calls 和 ToolMessage
4. 完整的工具调用循环
==============================================================================
"""

print("=" * 60)
print("第2课：工具定义与 LLM 工具调用")
print("=" * 60)

# ============================================================================
# 1. 定义工具
# ============================================================================
print("\n--- 1. 定义工具 ---")
print("""
用 @tool 装饰器把普通函数变成 LangChain 工具。

工具的三要素：
1. 函数名 → 工具名（LLM 看到的名字）
2. docstring → 工具描述（LLM 判断何时使用）
3. 参数类型注解 → 参数 schema（LLM 知道传什么参数）

⚠️  docstring 非常重要！它是 LLM 理解工具用途的唯一依据。
""")

from langchain_core.tools import tool

@tool
def add(a: int, b: int) -> int:
    """将两个整数相加。当用户需要做加法运算时使用此工具。"""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """将两个整数相乘。当用户需要做乘法运算时使用此工具。"""
    return a * b

@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气。当用户询问天气相关问题时使用此工具。"""
    # 模拟天气数据
    weather_data = {
        "北京": "晴，25°C，北风3级",
        "上海": "多云，22°C，东风2级",
        "广州": "小雨，28°C，南风1级",
    }
    return weather_data.get(city, f"暂无 {city} 的天气数据")

@tool
def search_knowledge(query: str) -> str:
    """在知识库中搜索信息。当用户提问需要查找资料时使用此工具。"""
    # 模拟知识库
    knowledge = {
        "python": "Python 是一种通用编程语言，由 Guido van Rossum 创建于 1991 年。",
        "langchain": "LangChain 是一个用于构建 LLM 应用的开源框架。",
        "langgraph": "LangGraph 是 LangChain 团队推出的 Agent 编排框架，基于图结构。",
    }
    for key, value in knowledge.items():
        if key in query.lower():
            return value
    return f"未找到与 '{query}' 相关的信息"

tools = [add, multiply, get_weather, search_knowledge]

# 查看工具信息
print(f"定义了 {len(tools)} 个工具：")
for t in tools:
    print(f"  - {t.name}: {t.description[:50]}...")
    print(f"    参数: {t.args_schema.schema()['properties']}")

# 直接调用工具
print(f"\n直接调用测试:")
print(f"  add(3, 5) = {add.invoke({'a': 3, 'b': 5})}")
print(f"  get_weather('北京') = {get_weather.invoke({'city': '北京'})}")

# ============================================================================
# 2. 将工具绑定到 LLM
# ============================================================================
print("\n--- 2. 将工具绑定到 LLM ---")
print("""
bind_tools() 告诉 LLM"你可以使用这些工具"。
LLM 收到用户问题后，会判断是否需要调用工具。

  llm_with_tools = llm.bind_tools(tools)

如果需要工具 → 返回的 AIMessage 包含 tool_calls
如果不需要   → 返回普通的文本回复
""")

from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

llm = ChatOllama(model="qwen2.5:7b", temperature=0)
llm_with_tools = llm.bind_tools(tools)

# 2.1 不需要工具的问题
response = llm_with_tools.invoke([HumanMessage(content="你好，你是谁？")])
print(f"[不需要工具]")
print(f"  回复: {response.content[:80]}...")
print(f"  tool_calls: {response.tool_calls}")  # 空列表

# 2.2 需要工具的问题
response = llm_with_tools.invoke([HumanMessage(content="请帮我计算 15 加 27")])
print(f"\n[需要工具]")
print(f"  回复内容: '{response.content}'")  # 通常为空
print(f"  tool_calls: {response.tool_calls}")

if response.tool_calls:
    tc = response.tool_calls[0]
    print(f"  工具名: {tc['name']}")
    print(f"  参数: {tc['args']}")
    print(f"  调用ID: {tc['id']}")

# ============================================================================
# 3. 理解完整的工具调用流程
# ============================================================================
print("\n--- 3. 完整的工具调用流程 ---")
print("""
完整流程有 4 步：

  Step 1: 用户问题 → LLM（带工具）
  Step 2: LLM 返回 tool_calls（我要调用 xxx 工具）
  Step 3: 程序执行工具，返回 ToolMessage
  Step 4: 将 ToolMessage 传给 LLM → 生成最终回答

消息流：
  [HumanMessage]  "15 + 27 等于多少？"
  [AIMessage]     tool_calls=[{name:"add", args:{a:15, b:27}}]
  [ToolMessage]   "42"
  [AIMessage]     "15 + 27 = 42"
""")

# 手动执行完整流程
print("手动执行完整工具调用流程：")

# Step 1: 用户提问
messages = [HumanMessage(content="北京今天天气怎么样？")]
print(f"  Step 1 - 用户: {messages[0].content}")

# Step 2: LLM 决定调用工具
ai_response = llm_with_tools.invoke(messages)
messages.append(ai_response)
print(f"  Step 2 - LLM 决定: tool_calls={ai_response.tool_calls}")

# Step 3: 执行工具
if ai_response.tool_calls:
    for tc in ai_response.tool_calls:
        # 找到对应的工具函数
        tool_map = {t.name: t for t in tools}
        tool_fn = tool_map[tc["name"]]

        # 执行工具
        result = tool_fn.invoke(tc["args"])
        print(f"  Step 3 - 执行 {tc['name']}({tc['args']}) → {result}")

        # 构建 ToolMessage
        tool_msg = ToolMessage(
            content=str(result),
            tool_call_id=tc["id"],  # 必须与 tool_call 的 id 对应
        )
        messages.append(tool_msg)

    # Step 4: 将工具结果返回给 LLM
    final_response = llm_with_tools.invoke(messages)
    print(f"  Step 4 - 最终回答: {final_response.content}")

# ============================================================================
# 4. 多工具调用
# ============================================================================
print("\n--- 4. 多工具调用 ---")
print("""
LLM 可能一次返回多个 tool_calls（并行调用多个工具）。
""")

response = llm_with_tools.invoke([
    HumanMessage(content="计算 10+20 和 5*6 的结果")
])

print(f"tool_calls 数量: {len(response.tool_calls)}")
for i, tc in enumerate(response.tool_calls):
    print(f"  调用 {i+1}: {tc['name']}({tc['args']})")

# ============================================================================
# 5. 自动工具执行器
# ============================================================================
print("\n--- 5. 自动工具执行器 ---")
print("""
手动执行工具很繁琐。我们封装一个自动执行器：
根据 tool_calls 自动找到工具并执行。

LangGraph 提供了 ToolNode 来自动完成这个工作（下一课会用到）。
""")

def execute_tools(ai_message: AIMessage, tools_list: list) -> list[ToolMessage]:
    """自动执行 AI 消息中的所有 tool_calls"""
    tool_map = {t.name: t for t in tools_list}
    results = []

    for tc in ai_message.tool_calls:
        tool_fn = tool_map.get(tc["name"])
        if tool_fn:
            result = tool_fn.invoke(tc["args"])
            results.append(ToolMessage(
                content=str(result),
                tool_call_id=tc["id"],
            ))
        else:
            results.append(ToolMessage(
                content=f"未知工具: {tc['name']}",
                tool_call_id=tc["id"],
            ))

    return results

# 完整的自动化流程
def chat_with_tools(question: str) -> str:
    """带工具调用的完整对话"""
    messages = [HumanMessage(content=question)]

    # 最多循环 5 次（防止无限循环）
    for i in range(5):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if response.tool_calls:
            # 有工具调用 → 执行工具 → 继续
            tool_messages = execute_tools(response, tools)
            messages.extend(tool_messages)
            print(f"  [轮次{i+1}] 调用了 {len(response.tool_calls)} 个工具")
        else:
            # 无工具调用 → 得到最终回答
            print(f"  [轮次{i+1}] 生成最终回答")
            return response.content

    return "达到最大迭代次数"

print(f"\n自动化测试:")
print(f"Q: 搜索一下什么是 LangGraph？")
answer = chat_with_tools("搜索一下什么是 LangGraph？")
print(f"A: {answer[:120]}...")

print(f"\nQ: 3 乘以 7 加上 10 等于多少？")
answer = chat_with_tools("3 乘以 7 加上 10 等于多少？")
print(f"A: {answer[:120]}...")

# ============================================================================
# 6. 工具设计最佳实践
# ============================================================================
print("\n--- 6. 工具设计最佳实践 ---")
print("""
┌──────────────────────────────────────────────────────────┐
│  原则                │  说明                              │
├──────────────────────────────────────────────────────────┤
│  描述要清晰          │  docstring 是 LLM 选择工具的依据   │
│  参数要有类型注解    │  LLM 需要知道传什么类型的参数       │
│  功能要单一          │  一个工具做一件事，不要大而全        │
│  返回值要有意义      │  返回结构化的、LLM 能理解的文本     │
│  错误要处理          │  工具执行失败时返回有用的错误信息    │
│  名字要直观          │  函数名就是工具名，LLM 会看到        │
│  避免副作用          │  或至少在描述中说明会有什么影响      │
└──────────────────────────────────────────────────────────┘

好的工具描述示例：
  "查询指定城市的实时天气信息，返回温度、湿度和天气状况。
   参数 city 为城市名称，如'北京'、'上海'。"

差的工具描述：
  "获取天气"  ← LLM 不知道要传什么参数，也不知道返回什么
""")

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] @tool 装饰器定义工具")
print("  [v] bind_tools() 绑定工具到 LLM")
print("  [v] tool_calls 和 ToolMessage 的关系")
print("  [v] 完整的 4 步工具调用流程")
print("  [v] 多工具并行调用")
print("  [v] 自动工具执行器")
print("  [v] 工具设计最佳实践")
print("=" * 60)
print("\n下一课：03_react_agent.py - ReAct Agent（推理-行动循环）")
