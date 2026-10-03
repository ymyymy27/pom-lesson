import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：输出解析器（Output Parsers）
==============================================================================

为什么需要输出解析器？
------------------
LLM 的输出是自由文本，但我们的程序需要结构化数据：
- 需要 JSON？ → LLM 可能输出额外的解释文字
- 需要列表？ → LLM 的格式可能不统一
- 需要特定字段？ → LLM 可能遗漏或改名

Output Parser 解决这个问题：
1. 告诉模型"请按这个格式输出"（生成格式说明）
2. 把模型的文本输出解析成 Python 对象（JSON/列表/Pydantic 模型）

核心解析器：
- StrOutputParser:     最简单，提取纯文本
- JsonOutputParser:    解析为 JSON/字典
- PydanticOutputParser: 解析为 Pydantic 模型（类型安全）
- CommaSeparatedListOutputParser: 解析为逗号分隔列表
==============================================================================
"""

from langchain_core.output_parsers import (
    StrOutputParser,
    JsonOutputParser,
    CommaSeparatedListOutputParser,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
from pydantic import BaseModel, Field
from typing import Optional

llm = ChatOllama(model="qwen2.5:7b", temperature=0)

print("=" * 60)
print("第3课：输出解析器（Output Parsers）")
print("=" * 60)

# ============================================================================
# 1. StrOutputParser - 字符串解析器
# ============================================================================
print("\n--- 1. StrOutputParser - 最简单的解析器 ---")
print("""
StrOutputParser 做的事情：
  AIMessage(content="你好") → "你好"

它只是把 AIMessage 对象中的 content 字段提取出来。
看似简单，但在链式调用中非常常用，因为下游通常需要字符串而非消息对象。
""")

# 没有解析器：返回的是 AIMessage 对象
raw_response = llm.invoke("你好")
print(f"无解析器: {type(raw_response).__name__} → {raw_response}")

# 有解析器：返回纯字符串
chain = llm | StrOutputParser()
parsed_response = chain.invoke("你好")
print(f"有解析器: {type(parsed_response).__name__} → {parsed_response}")

# ============================================================================
# 2. CommaSeparatedListOutputParser - 列表解析器
# ============================================================================
print("\n--- 2. CommaSeparatedListOutputParser - 列表解析器 ---")
print("""
让模型输出逗号分隔的列表，然后自动解析为 Python list。
""")

list_parser = CommaSeparatedListOutputParser()

# 查看格式说明（会自动注入到 Prompt 中）
print(f"格式说明: {list_parser.get_format_instructions()}")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个知识百科助手。"),
    ("human", "列出5个{topic}。\n{format_instructions}"),
])

chain = prompt | llm | list_parser

result = chain.invoke({
    "topic": "常见的编程语言",
    "format_instructions": list_parser.get_format_instructions(),
})

print(f"\n结果类型: {type(result)}")   # list
print(f"结果: {result}")

# ============================================================================
# 3. JsonOutputParser - JSON 解析器
# ============================================================================
print("\n--- 3. JsonOutputParser - JSON 解析器 ---")
print("""
让模型输出 JSON 格式，自动解析为 Python 字典。

两种用法：
A. 不指定结构 → 模型自由发挥，返回 dict
B. 指定 Pydantic 模型 → 模型按结构输出，返回 dict（字段有保障）
""")

# 3.1 不指定结构的 JSON 输出
json_parser = JsonOutputParser()
print(f"格式说明: {json_parser.get_format_instructions()[:100]}...")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个数据提取助手。"),
    ("human", "从以下文本中提取人名、公司、职位信息：\n{text}\n\n{format_instructions}"),
])

chain = prompt | llm | json_parser
result = chain.invoke({
    "text": "张三是腾讯的高级工程师，他的同事李四在阿里担任产品经理。",
    "format_instructions": json_parser.get_format_instructions(),
})

print(f"\n[自由 JSON]")
print(f"  类型: {type(result)}")   # dict
print(f"  结果: {result}")

# 3.2 指定 Pydantic 模型的 JSON 输出
class BookInfo(BaseModel):
    """书籍信息"""
    title: str = Field(description="书名")
    author: str = Field(description="作者")
    year: Optional[int] = Field(description="出版年份", default=None)
    genre: str = Field(description="类型/分类")
    summary: str = Field(description="一句话简介")

book_parser = JsonOutputParser(pydantic_object=BookInfo)
print(f"\n[Pydantic JSON] 格式说明:")
print(f"  {book_parser.get_format_instructions()[:200]}...")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个图书信息提取助手。"),
    ("human", "请提取以下书籍的信息：\n{book_description}\n\n{format_instructions}"),
])

chain = prompt | llm | book_parser

result = chain.invoke({
    "book_description": "《Python编程：从入门到实践》是 Eric Matthes 在2019年出版的一本编程入门书，覆盖了Python基础语法和项目实战。",
    "format_instructions": book_parser.get_format_instructions(),
})

print(f"\n  类型: {type(result)}")
print(f"  结果: {result}")
for key, value in result.items():
    print(f"    {key}: {value}")

# ============================================================================
# 4. PydanticOutputParser - 类型安全的结构化输出
# ============================================================================
print("\n--- 4. PydanticOutputParser - 类型安全的结构化输出 ---")
print("""
与 JsonOutputParser 类似，但返回的直接是 Pydantic 模型实例，
可以利用 Pydantic 的字段验证、类型检查等功能。
""")

from langchain_core.output_parsers import PydanticOutputParser

class MovieReview(BaseModel):
    """电影评论分析结果"""
    movie_name: str = Field(description="电影名称")
    sentiment: str = Field(description="情感倾向: 正面/负面/中性")
    score: float = Field(description="评分，1到10之间")
    keywords: list[str] = Field(description="关键词列表，3-5个")
    summary: str = Field(description="一句话总结")

pydantic_parser = PydanticOutputParser(pydantic_object=MovieReview)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个电影评论分析助手。"),
    ("human", "分析以下电影评论：\n{review}\n\n{format_instructions}"),
])

chain = prompt | llm | pydantic_parser

review_text = "昨天看了《星际穿越》，诺兰太厉害了！视觉效果震撼，剧情深刻感人，虫洞和黑洞的呈现非常科学。唯一不足是节奏有些慢。强烈推荐！"

try:
    result = chain.invoke({
        "review": review_text,
        "format_instructions": pydantic_parser.get_format_instructions(),
    })
    print(f"\n  类型: {type(result)}")       # MovieReview
    print(f"  电影: {result.movie_name}")
    print(f"  情感: {result.sentiment}")
    print(f"  评分: {result.score}")
    print(f"  关键词: {result.keywords}")
    print(f"  总结: {result.summary}")
except Exception as e:
    print(f"  解析失败（模型输出格式不符）: {e}")
    print(f"  提示：可以尝试换用更强的模型，或在 Prompt 中增加更多格式示例")

# ============================================================================
# 5. 自定义解析器
# ============================================================================
print("\n--- 5. 自定义解析器 ---")
print("""
如果内置解析器不够用，可以用 RunnableLambda 自定义解析逻辑。
""")

from langchain_core.runnables import RunnableLambda

def extract_code_blocks(text: str) -> list[str]:
    """从文本中提取所有代码块"""
    import re
    pattern = r'```(?:\w+)?\n(.*?)```'
    blocks = re.findall(pattern, text, re.DOTALL)
    return [b.strip() for b in blocks] if blocks else [text.strip()]

custom_parser = StrOutputParser() | RunnableLambda(extract_code_blocks)

prompt = ChatPromptTemplate.from_template(
    "写一个 Python 函数：{task}。只输出代码，用代码块包裹。"
)

chain = prompt | llm | custom_parser
result = chain.invoke({"task": "计算列表中所有偶数的和"})
print(f"提取的代码块:")
for i, code in enumerate(result):
    print(f"  --- 代码块 {i+1} ---")
    print(f"  {code[:120]}...")

# ============================================================================
# 6. 解析器选择指南
# ============================================================================
print("\n--- 6. 解析器选择指南 ---")
print("""
┌──────────────────────────┬─────────────────────────────────┐
│  需求                     │  推荐解析器                      │
├──────────────────────────┼─────────────────────────────────┤
│  纯文本输出               │  StrOutputParser                │
│  逗号分隔列表             │  CommaSeparatedListOutputParser  │
│  JSON 字典               │  JsonOutputParser                │
│  类型安全的结构化数据     │  PydanticOutputParser            │
│  自定义逻辑              │  RunnableLambda                   │
└──────────────────────────┴─────────────────────────────────┘

小技巧：
1. 格式说明一定要注入到 Prompt 中（{format_instructions}）
2. 如果解析失败，先检查模型的原始输出是否符合格式
3. 强模型（GPT-4o）比弱模型更容易遵循格式要求
4. 可以在 Prompt 中增加 JSON 示例来提高成功率
""")

print("\n" + "=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] StrOutputParser 纯文本解析")
print("  [v] CommaSeparatedListOutputParser 列表解析")
print("  [v] JsonOutputParser JSON 解析")
print("  [v] PydanticOutputParser 类型安全解析")
print("  [v] RunnableLambda 自定义解析")
print("  [v] format_instructions 的作用")
print("=" * 60)
print("\n下一课：04_lcel_chains.py - LCEL 链式表达式语言")
