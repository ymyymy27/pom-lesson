import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第1课：什么是 Function Calling（原理与流程）
==============================================================================

Function Calling（函数调用）是让 LLM "做事"的核心能力。

传统 LLM 只能"说话"（生成文本），但通过 Function Calling：
- LLM 可以调用外部函数/API
- LLM 可以查询数据库
- LLM 可以操作文件
- LLM 可以执行任何你定义的操作

⚠️ 重要认知：LLM 不会"执行"函数！
  LLM 只是"决定"调用什么函数、传什么参数。
  实际执行由你的程序负责。

完整流程（4 步）：
  ┌──────────────────────────────────────────────────────┐
  │  Step 1: 你告诉 LLM "你可以用这些函数"（函数定义）   │
  │  Step 2: 用户提问 → LLM 返回"我要调用 xxx(参数)"     │
  │  Step 3: 你的程序执行函数，得到结果                   │
  │  Step 4: 把结果告诉 LLM → LLM 生成最终回答           │
  └──────────────────────────────────────────────────────┘

本课内容：
- Function Calling 的本质和原理
- 函数定义的 JSON Schema 格式
- 完整的 4 步流程手动演示
- 与传统 Prompt Engineering 的对比
==============================================================================
"""

import json

print("=" * 60)
print("第1课：什么是 Function Calling（原理与流程）")
print("=" * 60)

# ============================================================================
# 1. 从一个问题开始理解
# ============================================================================
print("\n--- 1. 从一个问题开始理解 ---")
print("""
用户问："北京今天天气怎么样？"

没有 Function Calling 的 LLM：
  → "我无法获取实时天气信息..."（或者编造一个答案）

有 Function Calling 的 LLM：
  → "我需要调用 get_weather 函数，参数是 city='北京'"
  → 你的程序调用天气 API
  → 返回 "晴，25°C"
  → LLM："北京今天天气晴朗，气温25度。"

关键区别：LLM 从"只能说"变成了"能做事"。
""")

# ============================================================================
# 2. 函数定义的格式（JSON Schema）
# ============================================================================
print("\n--- 2. 函数定义的格式 ---")
print("""
你需要用 JSON Schema 告诉 LLM "你有哪些函数可用"。

JSON Schema 定义了：
- name:        函数名
- description: 函数用途（LLM 靠这个判断何时调用）
- parameters:  参数列表（类型、描述、是否必需）
""")

# 示例：定义一个天气查询函数
weather_function = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查询指定城市的当前天气信息，包括温度、湿度、风力等",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，如'北京'、'上海'、'广州'"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "温度单位，默认摄氏度"
                }
            },
            "required": ["city"]
        }
    }
}

print(f"函数定义示例：")
print(json.dumps(weather_function, ensure_ascii=False, indent=2))

# 再定义一个计算器函数
calculator_function = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "计算数学表达式，支持加减乘除、幂运算、括号",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，如 '(15 + 27) * 3' 或 '2 ** 10'"
                }
            },
            "required": ["expression"]
        }
    }
}

print(f"\n定义了 2 个函数: get_weather, calculator")

# ============================================================================
# 3. 手动模拟完整流程
# ============================================================================
print("\n--- 3. 手动模拟完整流程 ---")
print("""
为了深入理解，我们先手动模拟整个过程（不调用真正的 LLM）。
""")

# Step 1: 定义函数
print("[Step 1] 定义可用函数")
tools = [weather_function, calculator_function]
print(f"  可用函数: {[t['function']['name'] for t in tools]}")

# Step 2: 模拟 LLM 的响应（实际中这是 LLM 返回的）
print("\n[Step 2] 用户提问 → LLM 决定调用函数")
user_question = "北京今天天气怎么样？"
print(f"  用户: {user_question}")

# 模拟 LLM 返回的 tool_call
llm_response = {
    "role": "assistant",
    "content": None,  # 注意：调用函数时 content 通常为空
    "tool_calls": [
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "get_weather",
                "arguments": '{"city": "北京", "unit": "celsius"}'
            }
        }
    ]
}
print(f"  LLM 决定: 调用 {llm_response['tool_calls'][0]['function']['name']}")
print(f"  参数: {llm_response['tool_calls'][0]['function']['arguments']}")

# Step 3: 执行函数
print("\n[Step 3] 程序执行函数")
def get_weather(city: str, unit: str = "celsius") -> str:
    """实际的天气查询函数（这里用模拟数据）"""
    weather_db = {
        "北京": {"temp": 25, "humidity": 40, "wind": "北风3级", "desc": "晴"},
        "上海": {"temp": 22, "humidity": 65, "wind": "东风2级", "desc": "多云"},
    }
    data = weather_db.get(city, {"temp": 20, "humidity": 50, "wind": "微风", "desc": "未知"})
    temp = data["temp"] if unit == "celsius" else data["temp"] * 9/5 + 32
    unit_str = "°C" if unit == "celsius" else "°F"
    return json.dumps({
        "city": city,
        "temperature": f"{temp}{unit_str}",
        "humidity": f"{data['humidity']}%",
        "wind": data["wind"],
        "description": data["desc"]
    }, ensure_ascii=False)

# 解析 LLM 的调用请求并执行
tool_call = llm_response["tool_calls"][0]
args = json.loads(tool_call["function"]["arguments"])
result = get_weather(**args)
print(f"  执行 get_weather(city='北京', unit='celsius')")
print(f"  结果: {result}")

# Step 4: 将结果返回给 LLM
print("\n[Step 4] 结果返回给 LLM → 生成最终回答")
tool_message = {
    "role": "tool",
    "tool_call_id": tool_call["id"],
    "content": result
}
print(f"  Tool Message: {tool_message}")
print(f"  LLM 最终回答: 北京今天天气晴朗，气温25°C，湿度40%，北风3级。")

# ============================================================================
# 4. 消息流（Message Flow）
# ============================================================================
print("\n--- 4. 消息流详解 ---")
print("""
完整的消息流：

  messages = [
    {"role": "system", "content": "你是一个助手..."},
    {"role": "user", "content": "北京天气怎么样？"},    ← 用户提问
    
    # API 调用 → LLM 返回 tool_call
    {"role": "assistant", "content": null,               ← LLM 决定调用函数
     "tool_calls": [{
       "id": "call_abc123",
       "function": {"name": "get_weather", "arguments": "..."}
     }]},
    
    # 你执行函数后，把结果放进消息
    {"role": "tool",                                     ← 函数执行结果
     "tool_call_id": "call_abc123",
     "content": "{温度: 25°C, ...}"},
    
    # 再次调用 API → LLM 生成最终回答
    {"role": "assistant",                                ← 最终回答
     "content": "北京今天天气晴朗，气温25度。"}
  ]

注意：
- 一次 API 调用可能返回多个 tool_calls（并行调用）
- 每个 tool_call 都需要一个对应的 tool message
- tool_call_id 必须对应
""")

# ============================================================================
# 5. 与传统 Prompt Engineering 的对比
# ============================================================================
print("\n--- 5. 与 Prompt Engineering 的对比 ---")
print("""
传统方式（纯 Prompt）：
  "如果用户问天气，请按以下JSON格式回复：
   {\"action\": \"get_weather\", \"city\": \"xxx\"}"
  
  问题：
  ❌ 输出格式不稳定（可能不是合法JSON）
  ❌ 需要自己解析文本
  ❌ 不同模型表现差异大
  ❌ 复杂参数难以可靠传递

Function Calling 方式：
  提供 JSON Schema 函数定义 → LLM 返回结构化的 tool_call

  优点：
  ✅ 输出格式稳定可靠（模型原生支持）
  ✅ 参数自动验证
  ✅ 支持复杂参数类型
  ✅ 支持并行调用多个函数
  ✅ 与 tool message 协议标准化

支持 Function Calling 的模型：
┌──────────────────────┬─────────────────────────────┐
│  提供商               │  模型                        │
├──────────────────────┼─────────────────────────────┤
│  OpenAI              │  GPT-4o, GPT-4, GPT-3.5     │
│  Anthropic           │  Claude 3.5, Claude 3        │
│  Google              │  Gemini 1.5 Pro/Flash        │
│  Ollama (本地)       │  Qwen2.5, Llama3.1, Mistral │
│  DeepSeek            │  DeepSeek-V3, DeepSeek-R1    │
│  Moonshot (月之暗面) │  Moonshot-v1                  │
│  智谱 AI             │  GLM-4                       │
└──────────────────────┴─────────────────────────────┘
""")

# ============================================================================
# 6. 函数定义设计原则
# ============================================================================
print("\n--- 6. 函数定义设计原则 ---")
print("""
函数定义的质量直接决定 LLM 调用的准确性！

┌──────────────────────────────────────────────────────────┐
│  原则              │  说明                                │
├──────────────────────────────────────────────────────────┤
│  名字要直观        │  get_weather 比 func1 好              │
│  描述要详细        │  说清楚"什么时候用"和"返回什么"        │
│  参数要有描述      │  每个参数说明含义和示例                │
│  用 enum 约束      │  可选值明确时用 enum 限制              │
│  required 要准确   │  区分必需和可选参数                    │
│  功能要单一        │  一个函数做一件事                      │
│  返回值要有意义    │  返回 LLM 能理解的文本                 │
└──────────────────────────────────────────────────────────┘

反面示例：
  name: "do_stuff"              ← 名字不清楚
  description: "做一些事情"      ← 描述太模糊
  parameters: {data: any}       ← 参数没有类型和描述

正面示例：
  name: "search_products"
  description: "在商品数据库中搜索商品。根据关键词返回匹配的商品列表，
                包含名称、价格、评分。最多返回10条结果。"
  parameters: {
    keyword: {type: string, description: "搜索关键词，如'蓝牙耳机'"},
    max_price: {type: number, description: "最高价格（元），可选"},
    sort_by: {type: string, enum: ["price", "rating", "sales"]}
  }
""")

# 演示好的函数定义
good_examples = [
    {
        "name": "search_products",
        "description": "在商品数据库中搜索商品，返回匹配的商品列表",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "搜索关键词"},
                "max_price": {"type": "number", "description": "最高价格（元）"},
                "sort_by": {"type": "string", "enum": ["price", "rating", "sales"]}
            },
            "required": ["keyword"]
        }
    },
    {
        "name": "send_email",
        "description": "发送邮件给指定收件人。这是一个敏感操作。",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "收件人邮箱地址"},
                "subject": {"type": "string", "description": "邮件主题"},
                "body": {"type": "string", "description": "邮件正文内容"},
                "cc": {"type": "array", "items": {"type": "string"}, "description": "抄送列表"}
            },
            "required": ["to", "subject", "body"]
        }
    }
]

for func in good_examples:
    print(f"\n  ✅ {func['name']}: {func['description']}")
    print(f"     必需参数: {func['parameters'].get('required', [])}")

# ============================================================================
# 7. 核心概念总结
# ============================================================================
print("\n\n--- 7. 核心概念总结 ---")
print("""
┌──────────────────────────────────────────────────────────┐
│  概念              │  说明                                │
├──────────────────────────────────────────────────────────┤
│  Function Calling  │  让 LLM 能"调用"外部函数的能力      │
│  Tool              │  函数的定义（name + description +     │
│                    │  parameters）                        │
│  tool_calls        │  LLM 返回的调用请求（函数名+参数）   │
│  Tool Message      │  函数执行结果，返回给 LLM            │
│  tool_call_id      │  关联请求和结果的唯一标识             │
│  JSON Schema       │  描述参数类型和格式的标准             │
└──────────────────────────────────────────────────────────┘

核心流程：
  1. 定义 tools（JSON Schema）
  2. 发送 messages + tools → LLM
  3. LLM 返回 tool_calls
  4. 执行函数，构建 tool message
  5. 发送更新后的 messages → LLM
  6. LLM 返回最终回答

下一课将用 OpenAI API 实际操作这个流程！
""")

print("\n" + "=" * 60)
print("[完成] 第1课完成！你已经学会了：")
print("  [v] Function Calling 的本质（LLM 决定，程序执行）")
print("  [v] JSON Schema 函数定义格式")
print("  [v] 完整的 4 步调用流程")
print("  [v] 消息流（message flow）结构")
print("  [v] 与传统 Prompt Engineering 的对比")
print("  [v] 函数定义设计原则")
print("=" * 60)
print("\n下一课：02_openai_function_calling.py - OpenAI Function Calling 实战")
