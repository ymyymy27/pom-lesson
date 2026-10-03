import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第4课：LCEL 链式表达式语言
==============================================================================

什么是 LCEL？
-----------
LCEL = LangChain Expression Language（LangChain 表达式语言）

它是 LangChain 的核心编程范式，用管道符 | 把组件串联起来：
    chain = component_a | component_b | component_c

数据从左到右流动：
    输入 → A处理 → B处理 → C处理 → 输出

LCEL 的威力：
- 自动支持 stream / batch / async（不用额外写代码）
- 可以并行执行独立的分支
- 支持条件路由（根据输入走不同路径）
- 支持容错和重试

核心 Runnable 组件：
- RunnablePassthrough:   透传，原样传递数据
- RunnableLambda:        包装任意 Python 函数
- RunnableParallel:      并行执行多个分支
- RunnableBranch:        条件路由

一条 LCEL 链中的每个组件都是 Runnable，都有这些方法：
  .invoke()  - 同步调用
  .stream()  - 流式调用
  .batch()   - 批量调用
  .ainvoke() - 异步调用
==============================================================================
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableLambda,
    RunnableParallel,
)
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage

llm = ChatOllama(model="qwen2.5:7b", temperature=0.7)

print("=" * 60)
print("第4课：LCEL 链式表达式语言")
print("=" * 60)

# ============================================================================
# 1. 最基础的链：Prompt | LLM | Parser
# ============================================================================
print("\n--- 1. 最基础的链 ---")
print("""
最常用的三步链：

  输入字典 → [Prompt模板] → [LLM] → [输出解析] → 结果
              格式化消息      生成回复    提取文本

用管道符连起来就是：prompt | llm | parser
""")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{domain}专家，回答简洁。"),
    ("human", "{question}"),
])
parser = StrOutputParser()

# 组装链
chain = prompt | llm | parser

# 调用
result = chain.invoke({"domain": "Python", "question": "什么是 GIL？"})
print(f"结果: {result[:100]}...")

# 链的信息
print(f"\n链的类型: {type(chain).__name__}")
print(f"链的输入 schema: {chain.input_schema.schema()['properties'].keys()}")

# ============================================================================
# 2. RunnablePassthrough - 透传数据
# ============================================================================
print("\n--- 2. RunnablePassthrough - 透传数据 ---")
print("""
RunnablePassthrough 的作用：把输入原封不动地传给下一步。
常用场景：在 RunnableParallel 中保留原始输入。

  RunnablePassthrough()           → 原样传递
  RunnablePassthrough.assign(x=fn) → 在原数据上追加新字段
""")

# 2.1 基本透传
passthrough = RunnablePassthrough()
result = passthrough.invoke("hello")
print(f"透传: 'hello' → '{result}'")

# 2.2 assign - 追加字段
chain = RunnablePassthrough.assign(
    upper=lambda x: x["text"].upper(),
    length=lambda x: len(x["text"]),
)
result = chain.invoke({"text": "hello world"})
print(f"\nassign 追加字段:")
print(f"  输入: {{'text': 'hello world'}}")
print(f"  输出: {result}")
# → {'text': 'hello world', 'upper': 'HELLO WORLD', 'length': 11}

# ============================================================================
# 3. RunnableLambda - 包装任意函数
# ============================================================================
print("\n--- 3. RunnableLambda - 包装任意函数 ---")
print("""
RunnableLambda 把普通 Python 函数变成 Runnable，
就可以用 | 接入链中。
""")

def word_count(text: str) -> dict:
    """统计文本信息"""
    words = text.split()
    return {
        "original": text,
        "word_count": len(words),
        "char_count": len(text),
    }

def format_stats(data: dict) -> str:
    """格式化统计结果"""
    return f"文本: '{data['original'][:30]}...' | 词数: {data['word_count']} | 字符数: {data['char_count']}"

# 方式1：显式包装
count_step = RunnableLambda(word_count)
format_step = RunnableLambda(format_stats)

chain = count_step | format_step
result = chain.invoke("LangChain is a framework for building LLM applications")
print(f"  {result}")

# 方式2：lambda 直接用（简单逻辑推荐）
chain2 = RunnableLambda(lambda x: x.upper()) | RunnableLambda(lambda x: f"结果: {x}")
result2 = chain2.invoke("hello")
print(f"  {result2}")

# ============================================================================
# 4. RunnableParallel - 并行执行
# ============================================================================
print("\n--- 4. RunnableParallel - 并行执行 ---")
print("""
RunnableParallel 可以同时执行多个独立的链，
将结果合并为一个字典。

    RunnableParallel(
        summary=summary_chain,
        keywords=keyword_chain,
    )

输入数据会分别传给每个分支，所有分支的输出合并为一个 dict。
""")

# 定义两个不同的处理链
summary_prompt = ChatPromptTemplate.from_template(
    "用一句话总结以下内容（不超过30字）：\n{text}"
)
keyword_prompt = ChatPromptTemplate.from_template(
    "从以下内容中提取3个关键词，用逗号分隔：\n{text}"
)
sentiment_prompt = ChatPromptTemplate.from_template(
    "判断以下内容的情感倾向（正面/负面/中性），只输出一个词：\n{text}"
)

# 并行执行三个分析任务
parallel_chain = RunnableParallel(
    summary=summary_prompt | llm | StrOutputParser(),
    keywords=keyword_prompt | llm | StrOutputParser(),
    sentiment=sentiment_prompt | llm | StrOutputParser(),
)

text = "今天参加了 LangChain 的技术分享会，学到了很多关于 RAG 和 Agent 的知识，讲师非常专业，组织也很好。"

print(f"输入: {text[:50]}...")
result = parallel_chain.invoke({"text": text})
print(f"\n并行结果:")
print(f"  摘要: {result['summary'][:50]}")
print(f"  关键词: {result['keywords'][:50]}")
print(f"  情感: {result['sentiment'][:20]}")

# ============================================================================
# 5. 链的嵌套与组合
# ============================================================================
print("\n--- 5. 链的嵌套与组合 ---")
print("""
链可以像乐高积木一样组合：
- 链可以作为另一个链的一部分
- RunnableParallel 的输出可以传给下一个链
""")

# 第一步：并行提取信息
extract_chain = RunnableParallel(
    summary=summary_prompt | llm | StrOutputParser(),
    keywords=keyword_prompt | llm | StrOutputParser(),
)

# 第二步：基于提取结果生成报告
report_prompt = ChatPromptTemplate.from_template(
    "基于以下分析结果，写一段50字以内的分析报告：\n摘要：{summary}\n关键词：{keywords}"
)
report_chain = report_prompt | llm | StrOutputParser()

# 组合：提取 → 报告
full_chain = extract_chain | report_chain

result = full_chain.invoke({"text": text})
print(f"最终报告: {result[:100]}...")

# ============================================================================
# 6. 条件路由
# ============================================================================
print("\n--- 6. 条件路由 ---")
print("""
根据输入的不同，走不同的处理链。
实现方式：RunnableLambda + 条件判断
""")

# 不同类型的处理链
code_prompt = ChatPromptTemplate.from_template(
    "你是一个编程专家。请回答：{question}"
)
general_prompt = ChatPromptTemplate.from_template(
    "你是一个通用助手。请回答：{question}"
)

code_chain = code_prompt | llm | StrOutputParser()
general_chain = general_prompt | llm | StrOutputParser()

def route(input_data: dict) -> str:
    """根据问题内容选择不同的链"""
    question = input_data["question"]
    code_keywords = ["代码", "编程", "函数", "Python", "bug", "报错", "code", "def"]
    if any(kw in question for kw in code_keywords):
        return code_chain.invoke(input_data)
    else:
        return general_chain.invoke(input_data)

router_chain = RunnableLambda(route)

q1 = "Python 的装饰器怎么写？"
q2 = "推荐几本好书"

r1 = router_chain.invoke({"question": q1})
print(f"[代码问题] Q: {q1}")
print(f"  → 路由到代码专家: {r1[:80]}...")

r2 = router_chain.invoke({"question": q2})
print(f"\n[一般问题] Q: {q2}")
print(f"  → 路由到通用助手: {r2[:80]}...")

# ============================================================================
# 7. 流式输出和批量处理
# ============================================================================
print("\n--- 7. 流式与批量（LCEL 自动支持）---")
print("""
LCEL 链自动获得 stream/batch/async 能力，无需额外代码！
""")

simple_chain = ChatPromptTemplate.from_template("用20字介绍{topic}") | llm | StrOutputParser()

# 7.1 流式
print("流式输出: ", end="", flush=True)
for chunk in simple_chain.stream({"topic": "LangChain"}):
    print(chunk, end="", flush=True)
print()

# 7.2 批量
results = simple_chain.batch([
    {"topic": "Python"},
    {"topic": "机器学习"},
    {"topic": "Docker"},
])
print(f"\n批量结果:")
for topic, r in zip(["Python", "机器学习", "Docker"], results):
    print(f"  {topic}: {r[:40]}...")

# ============================================================================
# 8. 链的调试：查看中间步骤
# ============================================================================
print("\n--- 8. 链的调试 ---")
print("""
调试技巧：在链中插入一个"打印"步骤，查看中间数据。
""")

def debug_print(data):
    """调试用：打印中间数据"""
    print(f"  [DEBUG] 类型={type(data).__name__}, 内容={str(data)[:80]}...")
    return data  # 原样返回，不影响数据流

debug_chain = (
    ChatPromptTemplate.from_template("用10个字介绍{topic}")
    | RunnableLambda(debug_print)   # ← 打印 Prompt 格式化结果
    | llm
    | RunnableLambda(debug_print)   # ← 打印 LLM 原始输出
    | StrOutputParser()
)

result = debug_chain.invoke({"topic": "LCEL"})
print(f"  最终结果: {result}")

print("\n" + "=" * 60)
print("[完成] 第4课完成！你已经学会了：")
print("  [v] LCEL 管道符 | 连接组件")
print("  [v] RunnablePassthrough 透传与 assign")
print("  [v] RunnableLambda 包装自定义函数")
print("  [v] RunnableParallel 并行执行")
print("  [v] 链的嵌套与组合")
print("  [v] 条件路由")
print("  [v] 自动 stream/batch 能力")
print("  [v] 调试技巧")
print("=" * 60)
print("\n下一课：05_memory_history.py - 对话记忆与历史管理")
