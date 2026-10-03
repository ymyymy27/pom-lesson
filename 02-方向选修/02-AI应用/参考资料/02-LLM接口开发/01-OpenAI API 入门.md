> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# OpenAI API 入门

## 学习目标

- 掌握 OpenAI API 的调用方式
- 学会对话管理、流式输出、Function Calling
- 了解 API 费用控制与最佳实践

## 1. 环境搭建

```bash
pip install openai
```

```python
from openai import OpenAI

# 方式1：使用 OpenAI
client = OpenAI(api_key="sk-xxx")

# 方式2：使用兼容 API（DeepSeek、通义千问等）
client = OpenAI(
    api_key="your-api-key",
    base_url="https://api.deepseek.com"  # 或其他兼容端点
)

# 推荐：从环境变量读取
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

## 2. Chat Completions 基础

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": "什么是向量数据库？"},
    ],
    temperature=0.7,
    max_tokens=500,
)

# 获取回复
reply = response.choices[0].message.content
print(reply)

# 查看使用量
print(f"输入 tokens: {response.usage.prompt_tokens}")
print(f"输出 tokens: {response.usage.completion_tokens}")
print(f"总 tokens: {response.usage.total_tokens}")
```

## 3. 多轮对话

```python
class ChatBot:
    def __init__(self, model="gpt-4o", system_prompt="你是一个有帮助的助手。"):
        self.client = OpenAI()
        self.model = model
        self.messages = [{"role": "system", "content": system_prompt}]

    def chat(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.7,
        )

        assistant_message = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": assistant_message})

        return assistant_message

    def clear_history(self):
        self.messages = [self.messages[0]]  # 保留 system prompt

# 使用
bot = ChatBot(system_prompt="你是一个 Python 编程导师。")
print(bot.chat("什么是装饰器？"))
print(bot.chat("能给我一个具体的例子吗？"))  # 模型会记住上下文
```

## 4. 流式输出（Streaming）

```python
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "写一首关于编程的诗"}],
    stream=True,
)

for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
print()  # 换行
```

### 封装为异步生成器

```python
async def stream_chat(messages: list):
    """异步流式输出"""
    from openai import AsyncOpenAI
    client = AsyncOpenAI()

    stream = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        stream=True,
    )

    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content
```

## 5. Function Calling（工具调用）

让 LLM 调用外部函数获取信息或执行操作。

```python
import json

# 定义可用工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

# 实际的函数实现
def get_weather(city: str, unit: str = "celsius") -> str:
    # 模拟天气数据
    return json.dumps({"city": city, "temp": 22, "unit": unit, "condition": "晴"})

# 调用流程
messages = [{"role": "user", "content": "北京今天天气怎么样？"}]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
)

# 检查是否需要调用工具
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    func_name = tool_call.function.name
    func_args = json.loads(tool_call.function.arguments)

    # 执行函数
    result = get_weather(**func_args)

    # 将结果返回给模型
    messages.append(response.choices[0].message)
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": result,
    })

    # 获取最终回复
    final_response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )
    print(final_response.choices[0].message.content)
```

## 6. 结构化输出

```python
# 使用 response_format 强制 JSON 输出
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一个数据提取助手，总是以 JSON 格式输出。"},
        {"role": "user", "content": "从这段文本中提取人名和职位：张三是腾讯的高级工程师，李四是阿里的产品经理。"}
    ],
    response_format={"type": "json_object"},
)

data = json.loads(response.choices[0].message.content)
print(data)
# {"people": [{"name": "张三", "company": "腾讯", "title": "高级工程师"}, ...]}
```

## 7. 费用控制

```python
# 估算费用的工具函数
def estimate_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
    pricing = {
        "gpt-4o": {"input": 2.50, "output": 10.00},        # per 1M tokens
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "deepseek-chat": {"input": 0.14, "output": 0.28},   # 按人民币
    }
    if model not in pricing:
        return 0
    p = pricing[model]
    cost = (prompt_tokens * p["input"] + completion_tokens * p["output"]) / 1_000_000
    return cost

# 最佳实践
# 1. 开发阶段用便宜模型（gpt-4o-mini / deepseek）
# 2. 设置 max_tokens 限制输出长度
# 3. 缓存常见问题的回复
# 4. 监控 token 使用量
```

## 练习

1. 用 OpenAI API（或兼容 API）实现一个命令行聊天机器人
2. 实现流式输出，逐字打印回复
3. 设计 2 个 Function Calling 工具（如查天气、计算器）
4. 用结构化输出从一段新闻中提取关键信息

## 下一节

→ [02-开源模型API与Ollama](<02-开源模型 API 与 Ollama.md>)
