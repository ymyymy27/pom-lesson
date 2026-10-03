# LangChain 入门

## 学习目标

- 理解 LangChain 的核心概念和架构
- 掌握 Chain、Prompt Template、Output Parser
- 学会用 LangChain 构建 LLM 应用

## 1. LangChain 简介

LangChain 是构建 LLM 应用的框架，提供：
- 统一的模型接口
- 提示模板管理
- 链式调用（Chain）
- 记忆管理
- 工具集成

```bash
pip install langchain langchain-openai langchain-community
```

## 2. 基础组件

### Chat Models

```python
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama

# OpenAI
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

# Ollama（本地）
llm = ChatOllama(model="qwen2.5:7b")

# 调用
from langchain_core.messages import HumanMessage, SystemMessage

messages = [
    SystemMessage(content="你是一个 Python 专家"),
    HumanMessage(content="什么是生成器？"),
]
response = llm.invoke(messages)
print(response.content)
```

### Prompt Templates

```python
from langchain_core.prompts import ChatPromptTemplate

# 基础模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}。请用{language}回复。"),
    ("user", "{question}"),
])

# 格式化
messages = prompt.invoke({
    "role": "数据科学家",
    "language": "中文",
    "question": "什么是过拟合？"
})

# 直接连接模型
chain = prompt | llm
response = chain.invoke({
    "role": "数据科学家",
    "language": "中文",
    "question": "什么是过拟合？"
})
print(response.content)
```

### Output Parsers

```python
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic import BaseModel, Field

# 字符串输出
chain = prompt | llm | StrOutputParser()
result = chain.invoke({"role": "助手", "language": "中文", "question": "你好"})
print(type(result))  # str

# JSON 输出
class MovieReview(BaseModel):
    title: str = Field(description="电影名称")
    rating: float = Field(description="评分 1-10")
    summary: str = Field(description="一句话总结")

parser = JsonOutputParser(pydantic_object=MovieReview)

review_prompt = ChatPromptTemplate.from_messages([
    ("system", "分析用户给出的电影评论。{format_instructions}"),
    ("user", "{review}"),
])

chain = review_prompt | llm | parser
result = chain.invoke({
    "review": "《星际穿越》真是太震撼了，诺兰不愧是大师！",
    "format_instructions": parser.get_format_instructions(),
})
print(result)  # {'title': '星际穿越', 'rating': 9.5, 'summary': '...'}
```

## 3. LCEL（LangChain Expression Language）

用管道符 `|` 组合组件。

```python
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# 简单链
chain = prompt | llm | StrOutputParser()

# 并行执行
from langchain_core.runnables import RunnableParallel

parallel_chain = RunnableParallel(
    summary=summary_prompt | llm | StrOutputParser(),
    keywords=keyword_prompt | llm | StrOutputParser(),
)

# 条件分支
def route(input):
    if "代码" in input["question"]:
        return code_chain
    return general_chain

chain = RunnableLambda(route)

# 批量处理
results = chain.batch([
    {"question": "什么是 Python？"},
    {"question": "什么是 Java？"},
])

# 流式输出
for chunk in chain.stream({"question": "写一首诗"}):
    print(chunk, end="", flush=True)
```

## 4. 记忆（Memory）

```python
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 存储对话历史
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有帮助的助手。"),
    ("placeholder", "{history}"),
    ("user", "{input}"),
])

chain = prompt | llm | StrOutputParser()

with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# 使用（同一 session_id 共享历史）
config = {"configurable": {"session_id": "user_001"}}
print(with_history.invoke({"input": "我叫小明"}, config=config))
print(with_history.invoke({"input": "我叫什么？"}, config=config))  # 记得你叫小明
```

## 5. 工具集成

```python
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """计算数学表达式的结果"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"

@tool
def search_web(query: str) -> str:
    """搜索网络获取最新信息"""
    # 模拟搜索
    return f"搜索 '{query}' 的结果：..."

# 绑定工具到模型
llm_with_tools = llm.bind_tools([calculator, search_web])

response = llm_with_tools.invoke("计算 (23 + 45) * 2 的结果")
print(response.tool_calls)  # 模型决定调用 calculator
```

## 练习

1. 用 LangChain 构建一个带 Prompt Template 的翻译链
2. 实现一个带记忆的多轮对话机器人
3. 创建一个 JSON 输出解析链，从文本提取结构化数据
4. 用 LCEL 组合多个链实现：先翻译、再摘要

## 阶段总结

本阶段你已掌握：
- ✅ OpenAI API 调用与流式输出
- ✅ Ollama 本地模型部署
- ✅ LangChain 核心组件与 LCEL

→ 下一阶段：[stage-06 微调与模型适配](../stage-06-fine-tuning/)
