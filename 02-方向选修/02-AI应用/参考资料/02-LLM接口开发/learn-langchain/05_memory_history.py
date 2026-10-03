import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：对话记忆与历史管理
==============================================================================

为什么需要记忆？
--------------
LLM 本身是无状态的——每次调用都是独立的，它不记得上一轮你说了什么。
要实现多轮对话，我们必须手动把"对话历史"传给模型。

但对话历史会越来越长，带来两个问题：
1. Token 消耗增加（上下文越长越贵）
2. 超过上下文窗口限制（模型无法处理太长的输入）

LangChain 提供了多种记忆策略：
- 完整历史:     保留所有消息（简单但最费 token）
- 窗口记忆:     只保留最近 N 轮（节省 token）
- 摘要记忆:     把旧对话压缩为摘要（平衡效果和成本）
- Token 限制:   按 token 数截断历史

本课核心组件：
- ChatMessageHistory:         消息存储
- RunnableWithMessageHistory: 自动管理历史的链包装器
==============================================================================
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_models import ChatOllama

llm = ChatOllama(model="qwen2.5:7b", temperature=0.7)

print("=" * 60)
print("第5课：对话记忆与历史管理")
print("=" * 60)

# ============================================================================
# 1. 手动管理对话历史（最基础的方式）
# ============================================================================
print("\n--- 1. 手动管理对话历史 ---")
print("""
最朴素的做法：自己维护一个消息列表，每轮对话手动追加。
优点：完全可控
缺点：代码重复，历史无限增长
""")

class SimpleChat:
    """最简单的多轮对话实现"""

    def __init__(self, system_prompt="你是一个有帮助的助手，回答简洁。"):
        self.llm = ChatOllama(model="qwen2.5:7b", temperature=0.7)
        self.history = [SystemMessage(content=system_prompt)]

    def chat(self, message: str) -> str:
        # 1. 追加用户消息
        self.history.append(HumanMessage(content=message))

        # 2. 调用模型（传入完整历史）
        response = self.llm.invoke(self.history)

        # 3. 追加 AI 回复
        self.history.append(response)

        return response.content

    def get_history_length(self) -> int:
        return len(self.history)

# 测试
chat = SimpleChat()
print(f"用户: 我叫小明，我是一个 Python 程序员")
r1 = chat.chat("我叫小明，我是一个 Python 程序员")
print(f"AI:   {r1[:80]}...")

print(f"\n用户: 我叫什么？我是做什么的？")
r2 = chat.chat("我叫什么？我是做什么的？")
print(f"AI:   {r2[:80]}...")

print(f"\n历史消息数: {chat.get_history_length()}")

# ============================================================================
# 2. ChatMessageHistory - 消息存储
# ============================================================================
print("\n--- 2. ChatMessageHistory - 消息存储 ---")
print("""
InMemoryChatMessageHistory 是一个内存中的消息存储。
它提供标准的 add/get 接口，方便与其他组件配合。
""")

# 创建历史存储
history_store = InMemoryChatMessageHistory()

# 添加消息
history_store.add_user_message("你好，我叫小明")
history_store.add_ai_message("你好小明！有什么可以帮你的？")
history_store.add_user_message("帮我解释一下什么是闭包")
history_store.add_ai_message("闭包是一个函数加上它引用的外部变量...")

# 获取所有消息
print(f"存储的消息数: {len(history_store.messages)}")
for msg in history_store.messages:
    print(f"  [{msg.type:>5}] {msg.content[:50]}")

# 清空历史
# history_store.clear()

# ============================================================================
# 3. RunnableWithMessageHistory - 自动历史管理（推荐！）
# ============================================================================
print("\n--- 3. RunnableWithMessageHistory - 自动历史管理 ---")
print("""
RunnableWithMessageHistory 是最推荐的方式：
- 自动从存储中加载历史
- 自动将新消息保存到存储
- 支持多个会话（通过 session_id 区分）

工作流程：
  用户输入 → 加载历史 → 拼入 Prompt → LLM → 保存新消息 → 输出
""")

# 3.1 创建带历史占位符的 Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个友好的助手，回答简洁。记住用户告诉你的信息。"),
    MessagesPlaceholder(variable_name="history"),  # ← 历史消息插入位置
    ("human", "{input}"),
])

chain = prompt | llm | StrOutputParser()

# 3.2 会话存储（支持多用户/多会话）
session_store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """根据 session_id 获取对应的历史存储"""
    if session_id not in session_store:
        session_store[session_id] = InMemoryChatMessageHistory()
    return session_store[session_id]

# 3.3 包装链
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",      # 用户输入对应的 key
    history_messages_key="history",  # 历史消息对应的 key
)

# 3.4 使用（用 config 指定 session_id）
config_user1 = {"configurable": {"session_id": "user_001"}}
config_user2 = {"configurable": {"session_id": "user_002"}}

# 用户1 的对话
print(f"\n[用户1 - 第1轮]")
r1 = chain_with_history.invoke(
    {"input": "我叫张三，我今年25岁"},
    config=config_user1,
)
print(f"  AI: {r1[:80]}...")

print(f"\n[用户1 - 第2轮]")
r2 = chain_with_history.invoke(
    {"input": "我叫什么？多大了？"},
    config=config_user1,
)
print(f"  AI: {r2[:80]}...")

# 用户2 的对话（独立的会话，不会混淆）
print(f"\n[用户2 - 第1轮]")
r3 = chain_with_history.invoke(
    {"input": "我叫李四"},
    config=config_user2,
)
print(f"  AI: {r3[:80]}...")

print(f"\n[用户2 问同样的问题]")
r4 = chain_with_history.invoke(
    {"input": "我叫什么？"},
    config=config_user2,
)
print(f"  AI: {r4[:80]}...")

# 查看各会话的历史
for sid, store in session_store.items():
    print(f"\n会话 {sid} 的历史 ({len(store.messages)} 条消息):")
    for msg in store.messages:
        print(f"  [{msg.type:>5}] {msg.content[:50]}")

# ============================================================================
# 4. 窗口记忆（只保留最近 N 轮）
# ============================================================================
print("\n--- 4. 窗口记忆 ---")
print("""
问题：对话越来越长，token 消耗增加，甚至超出上下文窗口。
方案：只保留最近 N 轮对话。

实现方式：在获取历史时截断。
""")

def get_windowed_history(session_id: str, max_messages: int = 6) -> InMemoryChatMessageHistory:
    """带窗口限制的历史获取"""
    if session_id not in session_store:
        session_store[session_id] = InMemoryChatMessageHistory()

    store = session_store[session_id]
    if len(store.messages) > max_messages:
        # 只保留最近 max_messages 条
        recent = store.messages[-max_messages:]
        store.clear()
        for msg in recent:
            store.add_message(msg)

    return store

# 也可以用更简单的 RunnableLambda 在链中截断
from langchain_core.runnables import RunnableLambda

def trim_history(messages, max_pairs=3):
    """保留最近 max_pairs 轮对话（每轮 = 1 human + 1 ai）"""
    if len(messages) <= max_pairs * 2:
        return messages
    return messages[-(max_pairs * 2):]

print("窗口记忆策略：")
print("  - 保留最近 N 轮对话")
print("  - 老的对话被丢弃")
print("  - 节省 token，但可能丢失重要信息")

# ============================================================================
# 5. 摘要记忆（压缩历史）
# ============================================================================
print("\n--- 5. 摘要记忆 ---")
print("""
更聪明的策略：用 LLM 把旧对话压缩成摘要，保留关键信息。

  完整历史: [msg1, msg2, msg3, msg4, msg5, msg6, msg7, msg8]
  压缩后:   [摘要: "用户叫小明，25岁，讨论了Python装饰器", msg7, msg8]
""")

def summarize_history(messages: list, llm_instance=None) -> str:
    """用 LLM 将对话历史压缩为摘要"""
    _llm = llm_instance or llm

    if not messages:
        return ""

    history_text = "\n".join(
        f"{'用户' if msg.type == 'human' else 'AI'}: {msg.content}"
        for msg in messages
    )

    summary_prompt = ChatPromptTemplate.from_template(
        "请将以下对话历史压缩为一段简短的摘要，保留关键信息（人名、事实、偏好等）：\n\n{history}\n\n摘要："
    )

    chain = summary_prompt | _llm | StrOutputParser()
    return chain.invoke({"history": history_text})

# 演示
demo_messages = [
    HumanMessage(content="我叫小明，是一个前端开发者"),
    AIMessage(content="你好小明！前端开发者很棒！"),
    HumanMessage(content="我主要用 React 和 TypeScript"),
    AIMessage(content="React + TS 是很好的技术栈！"),
    HumanMessage(content="我想学习后端开发"),
    AIMessage(content="推荐从 Python + FastAPI 开始"),
]

summary = summarize_history(demo_messages)
print(f"\n6条消息的摘要:")
print(f"  {summary[:120]}...")

# ============================================================================
# 6. 完整的聊天机器人（整合所有技术）
# ============================================================================
print("\n--- 6. 完整的聊天机器人 ---")

class ChatBot:
    """带记忆管理的聊天机器人"""

    def __init__(self, system_prompt: str = "你是一个友好的助手，回答简洁。",
                 max_history: int = 10):
        self.llm = ChatOllama(model="qwen2.5:7b", temperature=0.7)
        self.system_prompt = system_prompt
        self.max_history = max_history
        self.sessions = {}

    def _get_history(self, session_id: str) -> list:
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]

    def _trim_history(self, history: list) -> list:
        """如果历史过长，保留最近的消息"""
        if len(history) > self.max_history:
            return history[-self.max_history:]
        return history

    def chat(self, message: str, session_id: str = "default") -> str:
        history = self._get_history(session_id)

        # 构建消息列表
        messages = [
            SystemMessage(content=self.system_prompt),
            *self._trim_history(history),
            HumanMessage(content=message),
        ]

        # 调用模型
        response = self.llm.invoke(messages)

        # 保存历史
        history.append(HumanMessage(content=message))
        history.append(response)

        return response.content

    def get_stats(self, session_id: str = "default") -> dict:
        history = self._get_history(session_id)
        return {
            "session_id": session_id,
            "message_count": len(history),
            "sessions_total": len(self.sessions),
        }

# 使用
bot = ChatBot(system_prompt="你是一个 Python 编程导师，回答简洁有趣。")

print(f"Bot: {bot.chat('我是一个Python初学者，请多关照', 'session_A')[:60]}...")
print(f"Bot: {bot.chat('什么是列表？', 'session_A')[:60]}...")
print(f"Bot: {bot.chat('我刚才说我是什么水平？', 'session_A')[:60]}...")

stats = bot.get_stats("session_A")
print(f"\n会话统计: {stats}")

print("\n" + "=" * 60)
print("[完成] 第5课完成！你已经学会了：")
print("  [v] 手动管理对话历史")
print("  [v] ChatMessageHistory 消息存储")
print("  [v] RunnableWithMessageHistory 自动历史管理")
print("  [v] 多会话隔离（session_id）")
print("  [v] 窗口记忆（最近 N 轮）")
print("  [v] 摘要记忆（压缩历史）")
print("  [v] 完整聊天机器人实现")
print("=" * 60)
print("\n下一课：06_document_loaders.py - 文档加载与文本分割")
