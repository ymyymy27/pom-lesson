> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Agent 概念与架构

## 学习目标

- 理解 AI Agent 的核心概念
- 掌握 Agent 的架构模式（ReAct、Plan-and-Execute）
- 了解工具调用的机制

## 1. 什么是 AI Agent

AI Agent 是能自主推理、规划和执行任务的 AI 系统。

```
普通 LLM 调用：
  输入 → LLM → 输出（一次性）

AI Agent：
  任务 → 思考（推理）→ 决定行动 → 执行工具 → 观察结果 → 再思考 → ... → 最终答案

核心能力：
- 推理（Reasoning）：分析问题，制定计划
- 工具使用（Tool Use）：调用外部 API、搜索、计算等
- 记忆（Memory）：记住上下文和历史操作
- 反思（Reflection）：评估执行结果，调整策略
```

## 2. Agent 架构模式

### ReAct（Reasoning + Acting）

最经典的 Agent 模式：思考-行动-观察循环。

```
Thought: 用户想知道明天北京的天气，我需要查询天气 API
Action:  call weather_api(city="北京", date="明天")
Observation: 明天北京晴，最高温度 25°C，最低 15°C
Thought: 我已经获取了天气信息，可以回答了
Answer:  明天北京天气晴朗，气温 15-25°C，建议穿...
```

### Plan-and-Execute

先制定完整计划，再逐步执行。

```
Plan:
  1. 搜索最近的 AI 论文
  2. 筛选与 RAG 相关的论文
  3. 阅读摘要
  4. 总结关键发现

Execute:
  Step 1: 调用搜索工具...
  Step 2: 筛选结果...
  ...
```

### Multi-Agent

多个专业 Agent 协作完成复杂任务。

```
用户任务 → Coordinator Agent
  ├→ Research Agent（搜索信息）
  ├→ Code Agent（编写代码）
  ├→ Review Agent（审核质量）
  └→ 综合输出
```

## 3. 工具（Tools）

Agent 通过工具与外部世界交互。

```python
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """搜索互联网获取最新信息"""
    # 实际实现：调用搜索 API
    return f"搜索 '{query}' 的结果..."

@tool
def calculator(expression: str) -> str:
    """计算数学表达式"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"

@tool
def read_file(file_path: str) -> str:
    """读取本地文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

@tool
def write_file(file_path: str, content: str) -> str:
    """写入内容到文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return f"已写入 {file_path}"

@tool
def run_python(code: str) -> str:
    """执行 Python 代码并返回结果"""
    import subprocess
    result = subprocess.run(
        ["python", "-c", code],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout or result.stderr

tools = [search_web, calculator, read_file, write_file, run_python]
```

## 4. 用 LangChain 创建 Agent

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个能力全面的 AI 助手。你可以使用以下工具来帮助用户：
- search_web: 搜索网络
- calculator: 数学计算
- read_file: 读取文件
- write_file: 写入文件
- run_python: 执行 Python 代码

请根据用户需求，合理使用工具完成任务。"""),
    ("placeholder", "{chat_history}"),
    ("user", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,       # 打印推理过程
    max_iterations=10,  # 最大迭代次数
    handle_parsing_errors=True,
)

# 使用
result = agent_executor.invoke({
    "input": "帮我计算 (15 * 23 + 78) / 3 的结果，然后搜索一下这个数字有什么特别含义",
    "chat_history": [],
})
print(result["output"])
```

## 5. MCP（Model Context Protocol）

MCP 是 Anthropic 提出的标准化工具调用协议。

```
MCP 的核心概念：
- Server：提供工具和资源的服务
- Client：调用工具的 AI 应用
- Tools：可执行的操作
- Resources：可读取的数据源
- Prompts：预定义的提示模板

优势：
- 标准化接口，工具可复用
- 跨平台兼容
- 安全的权限控制
```

```python
# MCP Server 示例（概念）
# 一个 MCP Server 暴露文件系统操作
# AI 应用通过 MCP 协议调用这些工具
# 无需为每个 AI 框架重复实现
```

## 6. Agent 设计原则

```
1. 工具粒度适中
   - 太粗：灵活性差
   - 太细：决策步骤多，容易出错
   
2. 清晰的工具描述
   - 名称直观
   - description 详细说明用途和参数
   
3. 错误处理
   - 工具调用失败时返回有意义的错误信息
   - Agent 能根据错误调整策略

4. 安全边界
   - 限制文件操作范围
   - 代码执行使用沙箱
   - 设置最大迭代次数

5. 可观测性
   - 记录每步推理和工具调用
   - 便于调试和优化
```

## 练习

1. 实现 3 个自定义工具（如天气查询、汇率转换、翻译）
2. 用 LangChain 创建一个 Agent，验证工具调用流程
3. 设置 verbose=True，观察 Agent 的完整推理过程
4. 测试当工具调用失败时，Agent 如何处理

## 下一节

→ [02-LangGraph构建Agent](<02-LangGraph 构建 Agent.md>)
