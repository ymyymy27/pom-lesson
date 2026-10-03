import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第7课：完整项目 - AI 工作助手
==============================================================================

本课将前面所有知识整合，构建一个完整的 AI 工作助手：

┌──────────────────────────────────────────────────────────┐
│                    AI 工作助手                            │
│                                                          │
│  功能：                                                  │
│  1. 智能问答（直接对话）                                 │
│  2. 数学计算（计算器工具）                               │
│  3. 知识搜索（知识库工具）                               │
│  4. 文本分析（摘要/情感/关键词 并行分析）                │
│  5. 多轮对话（记忆上下文）                               │
│  6. 安全控制（敏感操作需确认）                           │
│                                                          │
│  用到的知识：                                             │
│  - 第1课: State / Node / Edge                            │
│  - 第2课: 工具定义与调用                                 │
│  - 第3课: ReAct Agent 循环                               │
│  - 第4课: 检查点与多线程                                 │
│  - 第5课: 条件分支与并行                                 │
│  - 第6课: 多 Agent 协作                                  │
└──────────────────────────────────────────────────────────┘
==============================================================================
"""

from typing import Annotated, TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

print("=" * 60)
print("第7课：完整项目 - AI 工作助手")
print("=" * 60)

# ============================================================================
# 1. 定义工具集
# ============================================================================
print("\n--- 1. 定义工具集 ---")

@tool
def calculator(expression: str) -> str:
    """计算数学表达式。支持加减乘除、幂运算、括号。
    示例: '(15 + 27) * 3', '2 ** 10', '100 / 7'"""
    try:
        allowed = set("0123456789+-*/().** ")
        if not all(c in allowed for c in expression):
            return f"不安全的表达式，只允许数字和+-*/().**"
        result = eval(expression)
        if isinstance(result, float):
            result = round(result, 6)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"

@tool
def search_knowledge(query: str) -> str:
    """搜索知识库获取技术信息。当需要查找编程、AI、技术相关的事实性信息时使用。
    参数 query 为搜索关键词。"""
    knowledge_base = {
        "python": "Python 是一种通用编程语言，由 Guido van Rossum 创建于 1991 年。以简洁易读著称，广泛用于 Web、数据科学、AI 等领域。最新稳定版本是 3.12。",
        "langchain": "LangChain 是一个 LLM 应用开发框架，核心组件包括：Chat Models、Prompt Templates、Output Parsers、LCEL 链、Memory、Document Loaders、Retrievers。",
        "langgraph": "LangGraph 是 LangChain 团队推出的 Agent 编排框架。核心概念：State（状态）、Node（节点）、Edge（边）。支持循环、条件分支、人机协作、多 Agent 协作。",
        "rag": "RAG（Retrieval-Augmented Generation）通过检索外部知识增强 LLM。流程：文档分块→Embedding→向量存储→检索→LLM生成。可减少幻觉，支持私域知识。",
        "transformer": "Transformer 由 Google 在 2017 年论文'Attention is All You Need'中提出。核心是自注意力机制。是 GPT、BERT、LLaMA 等现代大模型的基础。",
        "docker": "Docker 是容器化平台。核心概念：镜像(Image)、容器(Container)、Dockerfile、Docker Compose。比虚拟机更轻量。",
        "fastapi": "FastAPI 是高性能 Python Web 框架，基于 Starlette 和 Pydantic。特点：自动文档生成、类型安全、原生异步支持。",
        "pytorch": "PyTorch 是 Facebook 开发的深度学习框架。特点：动态计算图、Pythonic API、强大的 GPU 加速。是学术研究和工业应用的首选。",
    }

    query_lower = query.lower()
    results = []
    for key, value in knowledge_base.items():
        if key in query_lower or any(word in query_lower for word in key.split()):
            results.append(value)

    if results:
        return "\n\n".join(results)
    return f"未找到与 '{query}' 直接相关的信息。试试搜索：{', '.join(knowledge_base.keys())}"

@tool
def analyze_text(text: str) -> str:
    """对文本进行综合分析，包括摘要、情感、关键词提取。
    当用户要求分析一段文本时使用。"""
    llm_local = ChatOllama(model="qwen2.5:7b", temperature=0)

    # 并行风格但串行执行（在工具内部简化）
    summary_prompt = ChatPromptTemplate.from_template(
        "用一句话总结（不超过30字）：\n{text}"
    )
    sentiment_prompt = ChatPromptTemplate.from_template(
        "判断情感倾向，只输出一个词（正面/负面/中性）：\n{text}"
    )
    keyword_prompt = ChatPromptTemplate.from_template(
        "提取3个关键词，逗号分隔：\n{text}"
    )

    summary = (summary_prompt | llm_local | StrOutputParser()).invoke({"text": text})
    sentiment = (sentiment_prompt | llm_local | StrOutputParser()).invoke({"text": text})
    keywords = (keyword_prompt | llm_local | StrOutputParser()).invoke({"text": text})

    return f"分析结果：\n  摘要: {summary.strip()}\n  情感: {sentiment.strip()}\n  关键词: {keywords.strip()}"

@tool
def get_current_time() -> str:
    """获取当前日期和时间。当用户询问时间相关问题时使用。"""
    from datetime import datetime
    now = datetime.now()
    return f"当前时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')} (星期{'一二三四五六日'[now.weekday()]})"

tools = [calculator, search_knowledge, analyze_text, get_current_time]
print(f"已定义 {len(tools)} 个工具:")
for t in tools:
    print(f"  🔧 {t.name}: {t.description[:40]}...")

# ============================================================================
# 2. 定义 Agent State
# ============================================================================
print("\n--- 2. 定义 Agent State ---")

class AssistantState(TypedDict):
    messages: Annotated[list, add_messages]

# ============================================================================
# 3. 构建 Agent 图
# ============================================================================
print("\n--- 3. 构建 Agent 图 ---")

SYSTEM_PROMPT = """你是"小助"，一个全能的 AI 工作助手。

## 你的能力
1. **智能对话**: 回答各种问题
2. **数学计算**: 使用 calculator 工具精确计算
3. **知识搜索**: 使用 search_knowledge 工具查找技术信息
4. **文本分析**: 使用 analyze_text 工具分析文本（摘要/情感/关键词）
5. **时间查询**: 使用 get_current_time 工具获取当前时间

## 工作原则
1. 需要事实信息时，先搜索再回答，不要编造
2. 数学计算一定要用工具，不要心算
3. 分析文本时使用 analyze_text 工具
4. 回答要简洁、有条理
5. 不确定时诚实说明
6. 如果一个问题需要多步操作，逐步执行"""

llm = ChatOllama(model="qwen2.5:7b", temperature=0)
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: AssistantState) -> dict:
    """Agent 推理节点"""
    messages = state["messages"]

    # 确保有 system prompt
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)

def should_continue(state: AssistantState) -> str:
    """判断是否继续工具调用"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

# 构建图
graph = StateGraph(AssistantState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")

# 编译（带检查点，支持多线程对话）
memory = MemorySaver()
assistant = graph.compile(checkpointer=memory)

print("AI 工作助手构建完成 ✓")
print("""
  图结构:
  START → Agent → ┬→ Tools → Agent (循环)
                   └→ END
""")

# ============================================================================
# 4. 助手封装类
# ============================================================================
print("--- 4. 助手封装类 ---")

class AIWorkAssistant:
    """AI 工作助手 - 封装了 LangGraph Agent"""

    def __init__(self):
        self.agent = assistant
        self.active_sessions = set()

    def chat(self, message: str, session_id: str = "default",
             verbose: bool = False) -> str:
        """发送消息并获取回复"""
        config = {"configurable": {"thread_id": session_id}}
        self.active_sessions.add(session_id)

        result = self.agent.invoke(
            {"messages": [HumanMessage(content=message)]},
            config=config,
        )

        if verbose:
            self._print_process(result["messages"])

        # 获取最终回答
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                return msg.content
        return "（无回复）"

    def _print_process(self, messages):
        """打印执行过程"""
        for msg in messages:
            if isinstance(msg, AIMessage) and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"    🔧 调用: {tc['name']}({str(tc['args'])[:60]}...)")
            elif isinstance(msg, ToolMessage):
                print(f"    📋 结果: {msg.content[:80]}...")

    def stream_chat(self, message: str, session_id: str = "default"):
        """流式对话，实时输出执行过程"""
        config = {"configurable": {"thread_id": session_id}}
        self.active_sessions.add(session_id)

        print(f"  思考中", end="", flush=True)
        final_answer = ""

        for step in self.agent.stream(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            stream_mode="updates",
        ):
            for node_name, output in step.items():
                if node_name == "agent" and "messages" in output:
                    for msg in output["messages"]:
                        if isinstance(msg, AIMessage):
                            if msg.tool_calls:
                                for tc in msg.tool_calls:
                                    print(f"\n    🔧 {tc['name']}({str(tc['args'])[:50]})")
                            elif msg.content:
                                final_answer = msg.content
                                print(f"\n    ✅ 完成")
                elif node_name == "tools" and "messages" in output:
                    for msg in output["messages"]:
                        if isinstance(msg, ToolMessage):
                            print(f"    📋 → {msg.content[:60]}...")

        return final_answer

    def get_history(self, session_id: str = "default") -> list:
        """获取对话历史"""
        config = {"configurable": {"thread_id": session_id}}
        state = self.agent.get_state(config)
        return state.values.get("messages", [])

    def get_stats(self) -> dict:
        """获取助手统计信息"""
        return {
            "active_sessions": len(self.active_sessions),
            "tools": [t.name for t in tools],
        }

bot = AIWorkAssistant()
print("助手封装完成 ✓")

# ============================================================================
# 5. 功能测试
# ============================================================================
print("\n--- 5. 功能测试 ---")

# 5.1 直接对话
print("\n[测试1: 直接对话]")
answer = bot.chat("你好，你能做什么？", session_id="test")
print(f"  Q: 你好，你能做什么？")
print(f"  A: {answer[:150]}...")

# 5.2 数学计算
print("\n[测试2: 数学计算]")
answer = bot.chat("计算 (125 + 375) * 2.5", session_id="test", verbose=True)
print(f"  Q: 计算 (125 + 375) * 2.5")
print(f"  A: {answer[:100]}...")

# 5.3 知识搜索
print("\n[测试3: 知识搜索]")
answer = bot.chat("什么是 RAG？", session_id="test", verbose=True)
print(f"  Q: 什么是 RAG？")
print(f"  A: {answer[:150]}...")

# 5.4 时间查询
print("\n[测试4: 时间查询]")
answer = bot.chat("现在几点了？", session_id="test", verbose=True)
print(f"  Q: 现在几点了？")
print(f"  A: {answer[:100]}...")

# 5.5 文本分析
print("\n[测试5: 文本分析]")
answer = bot.chat(
    "帮我分析这段话：今天的AI技术发展大会非常精彩，各位专家分享了关于大模型和Agent的最新进展，收获很多。",
    session_id="test", verbose=True,
)
print(f"  A: {answer[:200]}...")

# ============================================================================
# 6. 多轮对话测试
# ============================================================================
print("\n\n--- 6. 多轮对话测试 ---")

session = "multi_turn"

q1 = "我想学习 AI 开发，应该先学什么？"
a1 = bot.chat(q1, session_id=session)
print(f"  Q1: {q1}")
print(f"  A1: {a1[:120]}...")

q2 = "帮我搜索一下 PyTorch 的相关信息"
a2 = bot.chat(q2, session_id=session, verbose=True)
print(f"\n  Q2: {q2}")
print(f"  A2: {a2[:120]}...")

q3 = "根据你搜索到的信息，用一句话总结 PyTorch 的特点"
a3 = bot.chat(q3, session_id=session)
print(f"\n  Q3: {q3}")
print(f"  A3: {a3[:120]}...")

# ============================================================================
# 7. 流式输出演示
# ============================================================================
print("\n\n--- 7. 流式输出演示 ---")

print("  Q: 搜索 LangGraph 的信息，然后计算 2024 * 365")
answer = bot.stream_chat(
    "搜索 LangGraph 的信息，然后计算 2024 * 365",
    session_id="stream_test",
)
print(f"  A: {answer[:150]}...")

# ============================================================================
# 8. 对话历史查看
# ============================================================================
print("\n\n--- 8. 对话历史 ---")

history = bot.get_history(session_id="multi_turn")
print(f"多轮对话会话共 {len(history)} 条消息:")
for msg in history:
    if isinstance(msg, HumanMessage):
        print(f"  [用户] {msg.content[:50]}...")
    elif isinstance(msg, AIMessage) and msg.content:
        print(f"  [AI]   {msg.content[:50]}...")
    elif isinstance(msg, ToolMessage):
        print(f"  [工具] {msg.content[:50]}...")

stats = bot.get_stats()
print(f"\n助手统计: {stats}")

# ============================================================================
# 9. 项目架构总结
# ============================================================================
print("\n\n--- 9. 项目架构总结 ---")
print("""
┌────────────────────────────────────────────────────────┐
│                   AI 工作助手架构                       │
├────────────────────────────────────────────────────────┤
│                                                        │
│  AIWorkAssistant（封装类）                              │
│  ├── chat()        同步对话                            │
│  ├── stream_chat() 流式对话                            │
│  ├── get_history() 获取历史                            │
│  └── get_stats()   统计信息                            │
│                                                        │
│  LangGraph Agent（核心图）                              │
│  ├── State: messages (add_messages)                    │
│  ├── Node: agent (LLM + tools)                        │
│  ├── Node: tools (ToolNode)                            │
│  ├── Edge: agent →条件→ tools / END                    │
│  ├── Edge: tools → agent                               │
│  └── Checkpointer: MemorySaver                         │
│                                                        │
│  工具集                                                │
│  ├── calculator      数学计算                          │
│  ├── search_knowledge 知识搜索                         │
│  ├── analyze_text    文本分析                          │
│  └── get_current_time 时间查询                         │
│                                                        │
│  整合的知识点                                          │
│  ├── 第1课: State/Node/Edge 图结构                     │
│  ├── 第2课: @tool 工具定义 + bind_tools               │
│  ├── 第3课: ReAct 循环（agent↔tools）                  │
│  ├── 第4课: MemorySaver 检查点 + 多线程               │
│  ├── 第5课: 条件分支 should_continue                   │
│  └── 第6课: 多 Agent 思想（工具即专家）                │
│                                                        │
└────────────────────────────────────────────────────────┘

下一步扩展方向：
1. 添加 RAG 知识库（接入向量数据库）
2. 添加网络搜索工具（接入搜索 API）
3. 添加代码执行工具（沙箱执行 Python）
4. 实现人机协作（敏感操作需确认）
5. 部署为 Web 服务（FastAPI + WebSocket）
6. 添加多模态能力（图片理解、语音输入）
""")

print("\n" + "=" * 60)
print("[完成] 第7课完成！你已经学会了：")
print("  [v] 设计完整的 Agent 系统架构")
print("  [v] 多工具集成（计算/搜索/分析/时间）")
print("  [v] ReAct 循环 + 检查点 + 多线程")
print("  [v] 助手封装（同步/流式/历史/统计）")
print("  [v] 多轮对话与上下文记忆")
print("  [v] 整合前6课所有核心知识")
print("=" * 60)
print("\nLangGraph 深入课程全部完成！🎉")
print("你已经具备了构建复杂 AI Agent 系统的能力。")
