import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第1课：Chat Model 与消息类型
==============================================================================

什么是 Chat Model？
-----------------
Chat Model 是 LangChain 中与大语言模型交互的核心接口。
不同于简单的"输入文本→输出文本"，Chat Model 使用「消息」来组织对话：

- SystemMessage:    系统消息，定义 AI 的角色和行为规则
- HumanMessage:     用户消息，用户发送的内容
- AIMessage:        AI 回复，模型生成的内容
- ToolMessage:      工具消息，工具调用的返回结果

LangChain 的价值在于：不管你用 OpenAI、Ollama、DeepSeek 还是其他模型，
代码接口都是一样的，切换模型只需改一行配置。

==============================================================================
"""

# ============================================================================
# 准备工作：选择你的模型
# ============================================================================
# 方式A：使用 Ollama（免费，本地运行）
# 请先安装 Ollama 并运行: ollama pull qwen2.5:7b

# 方式B：使用 OpenAI（需要 API Key）
# 设置环境变量: set OPENAI_API_KEY=sk-xxx

def get_llm(provider="ollama"):
    """
    获取 LLM 实例。修改 provider 参数来切换模型来源：
    - "ollama": 本地 Ollama（免费）
    - "openai": OpenAI API（收费）
    """
    if provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(model="qwen2.5:7b", temperature=0.7)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    else:
        raise ValueError(f"不支持的 provider: {provider}")


print("=" * 60)
print("第1课：Chat Model 与消息类型")
print("=" * 60)

# ============================================================================
# 1. 消息类型详解
# ============================================================================
print("\n--- 1. 消息类型详解 ---")
print("""
LangChain 中有 4 种核心消息类型：

┌─────────────────────────────────────────────────────┐
│  SystemMessage   │ 设定 AI 角色，如"你是一个翻译专家" │
│  HumanMessage    │ 用户说的话                        │
│  AIMessage       │ AI 的回复                         │
│  ToolMessage     │ 工具执行结果（后续课程详解）       │
└─────────────────────────────────────────────────────┘

消息的先后顺序很重要：System → Human → AI → Human → AI → ...
""")

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
)

# 创建各种类型的消息
system_msg = SystemMessage(content="你是一个热情友好的 Python 编程导师。")
human_msg = HumanMessage(content="什么是列表推导式？")
ai_msg = AIMessage(content="列表推导式是 Python 中创建列表的简洁语法...")

print(f"SystemMessage: {system_msg.content}")
print(f"  类型: {system_msg.type}")
print(f"HumanMessage:  {human_msg.content}")
print(f"  类型: {human_msg.type}")
print(f"AIMessage:     {ai_msg.content}")
print(f"  类型: {ai_msg.type}")

# ============================================================================
# 2. 调用 Chat Model
# ============================================================================
print("\n--- 2. 调用 Chat Model ---")

llm = get_llm("ollama")  # ← 改成 "openai" 可切换为 OpenAI
print(f"使用模型: {llm.__class__.__name__}")

# 2.1 最简单的调用：传入消息列表
messages = [
    SystemMessage(content="你是一个简洁的助手，每次回复不超过50个字。"),
    HumanMessage(content="什么是 Python？"),
]

response = llm.invoke(messages)
print(f"\n[调用方式1] 传入消息列表：")
print(f"  回复类型: {type(response).__name__}")  # AIMessage
print(f"  回复内容: {response.content}")

# 2.2 直接传入字符串（自动包装为 HumanMessage）
response2 = llm.invoke("用一句话解释什么是变量")
print(f"\n[调用方式2] 直接传字符串：")
print(f"  回复: {response2.content}")

# ============================================================================
# 3. 多轮对话
# ============================================================================
print("\n--- 3. 多轮对话 ---")
print("""
多轮对话的关键：把之前的对话历史都传给模型。
模型本身是"无状态的"，每次调用都是独立的，
所以我们需要手动维护对话历史。
""")

# 模拟一个多轮对话
conversation = [
    SystemMessage(content="你是一个 Python 编程导师，回答简洁。"),
]

# 第1轮
conversation.append(HumanMessage(content="什么是装饰器？"))
response = llm.invoke(conversation)
conversation.append(response)  # 把 AI 的回复加入历史
print(f"[第1轮]")
print(f"  用户: 什么是装饰器？")
print(f"  AI:   {response.content[:100]}...")

# 第2轮（模型能记住上下文）
conversation.append(HumanMessage(content="给我一个最简单的例子"))
response = llm.invoke(conversation)
conversation.append(response)
print(f"\n[第2轮]")
print(f"  用户: 给我一个最简单的例子")
print(f"  AI:   {response.content[:150]}...")

print(f"\n当前对话历史共 {len(conversation)} 条消息")

# ============================================================================
# 4. 模型参数控制
# ============================================================================
print("\n--- 4. 模型参数控制 ---")
print("""
常用参数：
- temperature: 控制随机性（0=确定性, 1=创造性）
- max_tokens:  最大输出长度
- top_p:       核采样，控制候选词范围
""")

# 低温度 = 更确定的输出
from langchain_community.chat_models import ChatOllama

llm_precise = ChatOllama(model="qwen2.5:7b", temperature=0)
llm_creative = ChatOllama(model="qwen2.5:7b", temperature=1.0)

prompt = "用一个比喻解释什么是递归"

print(f"[temperature=0]（确定性强）:")
r1 = llm_precise.invoke(prompt)
print(f"  {r1.content[:100]}...")

print(f"\n[temperature=1.0]（创造性强）:")
r2 = llm_creative.invoke(prompt)
print(f"  {r2.content[:100]}...")

# ============================================================================
# 5. 批量调用
# ============================================================================
print("\n--- 5. 批量调用 ---")
print("""
batch() 方法可以一次处理多个请求（部分模型支持并发加速）。
""")

questions = [
    "Python 的 GIL 是什么？",
    "什么是生成器？",
    "解释一下 *args 和 **kwargs",
]

messages_batch = [[HumanMessage(content=q)] for q in questions]
responses = llm.batch(messages_batch)

for q, r in zip(questions, responses):
    print(f"  Q: {q}")
    print(f"  A: {r.content[:80]}...")
    print()

# ============================================================================
# 6. 流式输出
# ============================================================================
print("\n--- 6. 流式输出 ---")
print("""
stream() 方法让模型逐字输出，而不是等全部生成完。
用户体验更好，也能更快看到第一个字。
""")

print("流式输出演示: ", end="", flush=True)
for chunk in llm.stream("用30个字介绍 LangChain"):
    print(chunk.content, end="", flush=True)
print()  # 换行

# ============================================================================
# 7. 模型切换的便利性
# ============================================================================
print("\n--- 7. 模型切换的便利性 ---")
print("""
LangChain 最大的优势之一：同样的代码，切换模型只需改一行！

┌────────────────────────────────────────────────────┐
│  Ollama:   ChatOllama(model="qwen2.5:7b")         │
│  OpenAI:   ChatOpenAI(model="gpt-4o-mini")        │
│  DeepSeek: ChatOpenAI(base_url="...", model="...")  │
│  Anthropic: ChatAnthropic(model="claude-3.5-...")   │
└────────────────────────────────────────────────────┘

所有后续代码中使用的 llm 变量，换模型只需改 get_llm() 即可！
""")

print("\n" + "=" * 60)
print("[完成] 第1课完成！你已经学会了：")
print("  [v] 4种消息类型（System/Human/AI/Tool）")
print("  [v] 调用 Chat Model 的两种方式")
print("  [v] 多轮对话（手动维护历史）")
print("  [v] 模型参数控制（temperature等）")
print("  [v] 批量调用 batch()")
print("  [v] 流式输出 stream()")
print("  [v] 无缝切换不同模型")
print("=" * 60)
print("\n下一课：02_prompt_templates.py - Prompt 模板与动态提示")
