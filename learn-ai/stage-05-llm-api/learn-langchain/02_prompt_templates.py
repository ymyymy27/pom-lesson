import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：Prompt 模板与动态提示
==============================================================================

为什么需要 Prompt 模板？
---------------------
直接拼接字符串来构造 Prompt 有很多问题：
- 容易出错（忘记换行、格式混乱）
- 难以复用（每次都要重写）
- 难以维护（Prompt 散落在代码各处）

LangChain 的 Prompt Template 解决了这些问题：
- 模板化：用占位符 {variable} 定义可变部分
- 类型安全：自动检查是否传入了所有必需变量
- 消息级别：直接生成 System/Human/AI 消息列表
- 可组合：多个模板可以拼接、嵌套

核心类：
- ChatPromptTemplate:  聊天模板（最常用）
- PromptTemplate:      纯文本模板
- MessagesPlaceholder: 动态消息占位符（用于对话历史）
==============================================================================
"""

from langchain_core.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

print("=" * 60)
print("第2课：Prompt 模板与动态提示")
print("=" * 60)

# ============================================================================
# 1. ChatPromptTemplate 基础
# ============================================================================
print("\n--- 1. ChatPromptTemplate 基础 ---")
print("""
ChatPromptTemplate 是最常用的模板类。
它将一组消息模板打包成一个可复用的对象。

用法：from_messages([("角色", "内容模板"), ...])
角色可以是: "system", "human", "ai"
模板中用 {变量名} 作为占位符
""")

# 1.1 基本用法
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}。请用{language}回复，回答简洁。"),
    ("human", "{question}"),
])

# 查看模板信息
print(f"模板的输入变量: {prompt.input_variables}")
# → ['language', 'question', 'role']

# 1.2 格式化模板 → 生成消息列表
messages = prompt.invoke({
    "role": "Python 导师",
    "language": "中文",
    "question": "什么是列表推导式？",
})

print(f"\n格式化后的消息列表:")
for msg in messages.messages:
    print(f"  [{msg.type:>6}] {msg.content}")

# ============================================================================
# 2. 模板 + 模型连接
# ============================================================================
print("\n--- 2. 模板 + 模型连接 ---")
print("""
LangChain 最核心的设计：用管道符 | 连接组件。

  prompt | llm | parser

数据流向：输入字典 → 模板格式化 → 模型调用 → 输出解析
""")

from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser

llm = ChatOllama(model="qwen2.5:7b", temperature=0.7)

# 方式1：手动分步
messages = prompt.invoke({"role": "Python 导师", "language": "中文", "question": "什么是装饰器？"})
response = llm.invoke(messages)
print(f"[手动分步] {response.content[:100]}...")

# 方式2：用管道符 | 连成链（推荐！）
chain = prompt | llm | StrOutputParser()
result = chain.invoke({
    "role": "Python 导师",
    "language": "中文",
    "question": "什么是装饰器？",
})
print(f"\n[管道连接] {result[:100]}...")

# ============================================================================
# 3. 多种模板创建方式
# ============================================================================
print("\n--- 3. 多种模板创建方式 ---")

# 3.1 最简方式：from_template（只有一条 Human 消息）
simple_prompt = ChatPromptTemplate.from_template("翻译以下文本为{target_lang}：{text}")
print(f"[from_template] 变量: {simple_prompt.input_variables}")

result = (simple_prompt | llm | StrOutputParser()).invoke({
    "target_lang": "英文",
    "text": "今天天气真好",
})
print(f"  翻译结果: {result[:60]}...")

# 3.2 使用消息类构建
prompt_v2 = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template("你是{role}。"),
    HumanMessagePromptTemplate.from_template("{question}"),
])
print(f"\n[消息类构建] 变量: {prompt_v2.input_variables}")

# 3.3 混合固定消息和模板消息
prompt_v3 = ChatPromptTemplate.from_messages([
    ("system", "你是一个代码审查专家。"),           # 固定内容
    ("human", "请审查以下代码：\n```\n{code}\n```"),  # 模板内容
])
print(f"[混合构建] 变量: {prompt_v3.input_variables}")

# ============================================================================
# 4. 部分填充（Partial）
# ============================================================================
print("\n--- 4. 部分填充 ---")
print("""
partial() 可以预先填充部分变量，生成一个"半成品"模板。
适用于：某些变量在初始化时就确定，另一些在运行时才知道。
""")

base_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}，用{language}回复。"),
    ("human", "{question}"),
])

# 预先填充 role 和 language，之后只需要传 question
chinese_tutor = base_prompt.partial(role="Python 导师", language="中文")
english_tutor = base_prompt.partial(role="English teacher", language="English")

print(f"中文导师需要的变量: {chinese_tutor.input_variables}")   # ['question']
print(f"英文导师需要的变量: {english_tutor.input_variables}")   # ['question']

r1 = (chinese_tutor | llm | StrOutputParser()).invoke({"question": "什么是闭包？"})
print(f"\n[中文导师] {r1[:80]}...")

r2 = (english_tutor | llm | StrOutputParser()).invoke({"question": "What is closure?"})
print(f"[英文导师] {r2[:80]}...")

# ============================================================================
# 5. MessagesPlaceholder - 动态消息占位符
# ============================================================================
print("\n--- 5. MessagesPlaceholder - 动态消息占位符 ---")
print("""
MessagesPlaceholder 用来在模板中插入"一组消息"。
最常见的用途：插入对话历史（chat_history）。

不同于普通变量（插入字符串），它插入的是完整的消息对象列表。
""")

prompt_with_history = ChatPromptTemplate.from_messages([
    ("system", "你是一个有帮助的助手，回答简洁。"),
    MessagesPlaceholder(variable_name="chat_history"),  # ← 动态消息
    ("human", "{question}"),
])

print(f"变量: {prompt_with_history.input_variables}")
# → ['chat_history', 'question']

# 模拟对话历史
history = [
    HumanMessage(content="我叫小明"),
    AIMessage(content="你好小明！有什么可以帮你的？"),
]

# 带历史的调用
chain_with_history = prompt_with_history | llm | StrOutputParser()
result = chain_with_history.invoke({
    "chat_history": history,
    "question": "我叫什么名字？",
})
print(f"\n带历史调用（能记住名字）:")
print(f"  回复: {result[:80]}...")

# 不带历史的调用
result_no_history = chain_with_history.invoke({
    "chat_history": [],
    "question": "我叫什么名字？",
})
print(f"\n不带历史调用（不知道名字）:")
print(f"  回复: {result_no_history[:80]}...")

# ============================================================================
# 6. Few-shot 模板
# ============================================================================
print("\n--- 6. Few-shot 模板（给模型举例子）---")
print("""
Few-shot = 在 Prompt 中给出几个输入→输出的示例，
让模型"照葫芦画瓢"，输出更符合预期的格式。
""")

few_shot_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个情感分析助手。根据用户的文本判断情感。"),
    # 示例1
    ("human", "这家餐厅太好吃了，下次还来！"),
    ("ai", "情感: 正面\n关键词: 好吃, 还来"),
    # 示例2
    ("human", "等了一个小时才上菜，体验很差。"),
    ("ai", "情感: 负面\n关键词: 等, 差"),
    # 示例3
    ("human", "菜品一般般，价格还行。"),
    ("ai", "情感: 中性\n关键词: 一般般, 还行"),
    # 实际输入
    ("human", "{text}"),
])

chain = few_shot_prompt | llm | StrOutputParser()
result = chain.invoke({"text": "服务态度非常好，但是菜有点咸。"})
print(f"输入: 服务态度非常好，但是菜有点咸。")
print(f"输出:\n{result}")

# ============================================================================
# 7. 纯文本 PromptTemplate
# ============================================================================
print("\n--- 7. 纯文本 PromptTemplate ---")
print("""
PromptTemplate 生成的是普通字符串，不是消息列表。
适用于不需要角色区分的场景（如文本补全、简单格式化）。
""")

text_prompt = PromptTemplate.from_template(
    "请将以下内容翻译为{language}，只输出翻译结果：\n\n{text}"
)

formatted = text_prompt.invoke({"language": "日文", "text": "你好世界"})
print(f"格式化结果:\n{formatted.text}")

# ============================================================================
# 8. 实用模式：Prompt 工厂
# ============================================================================
print("\n--- 8. 实用模式：Prompt 工厂 ---")

def create_expert_chain(expertise: str, llm_instance=None):
    """创建一个特定领域的专家链"""
    _llm = llm_instance or llm
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"你是一个{expertise}领域的资深专家。"
                   f"回答专业、简洁、有条理。如果不确定，请说明。"),
        ("human", "{question}"),
    ])
    return prompt | _llm | StrOutputParser()

# 创建不同领域的专家
python_expert = create_expert_chain("Python 编程")
ml_expert = create_expert_chain("机器学习")

r1 = python_expert.invoke({"question": "Python 3.12 有什么新特性？"})
print(f"[Python专家] {r1[:100]}...")

r2 = ml_expert.invoke({"question": "过拟合有哪些解决方法？"})
print(f"\n[ML专家] {r2[:100]}...")

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] ChatPromptTemplate 基础用法")
print("  [v] 模板 + 模型用管道符 | 连接")
print("  [v] 多种模板创建方式")
print("  [v] partial() 部分填充")
print("  [v] MessagesPlaceholder 对话历史占位符")
print("  [v] Few-shot 示例模板")
print("  [v] PromptTemplate 纯文本模板")
print("  [v] Prompt 工厂模式")
print("=" * 60)
print("\n下一课：03_output_parsers.py - 输出解析器")
