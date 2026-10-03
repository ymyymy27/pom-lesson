import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：条件分支与子图
==============================================================================

本课深入探讨 LangGraph 的高级图结构：

1. 复杂条件分支：多路径选择、动态路由
2. 并行执行：多个节点同时运行
3. 子图（Subgraph）：将图嵌套为另一个图的节点
4. 状态传递与映射

这些能力让你可以构建复杂的 AI 工作流：
- 根据用户意图分发到不同处理链
- 多个分析任务并行执行后汇总
- 将复杂流程分解为可复用的子图
==============================================================================
"""

from typing import Annotated, TypedDict, Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

llm = ChatOllama(model="qwen2.5:7b", temperature=0)

print("=" * 60)
print("第5课：条件分支与子图")
print("=" * 60)

# ============================================================================
# 1. 意图识别 + 多路径路由
# ============================================================================
print("\n--- 1. 意图识别 + 多路径路由 ---")
print("""
实际应用中，用户的问题类型多样，需要路由到不同的处理器：

  用户输入 → 意图识别 → ┬→ 代码问题 → 代码专家
                         ├→ 数学问题 → 计算器
                         ├→ 翻译请求 → 翻译器
                         └→ 其他问题 → 通用助手
""")

class RouterState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: str      # 识别出的意图
    answer: str      # 最终回答

def classify_intent(state: RouterState) -> dict:
    """用 LLM 识别用户意图"""
    last_msg = state["messages"][-1].content

    classify_prompt = ChatPromptTemplate.from_messages([
        ("system", """判断用户消息的意图类别。只输出类别名，不要其他内容。

可选类别：
- code: 编程/代码相关问题
- math: 数学计算问题
- translate: 翻译请求
- general: 其他一般问题"""),
        ("human", "{input}"),
    ])

    chain = classify_prompt | llm | StrOutputParser()
    intent = chain.invoke({"input": last_msg}).strip().lower()

    # 规范化
    valid_intents = {"code", "math", "translate", "general"}
    if intent not in valid_intents:
        intent = "general"

    print(f"  [意图识别] '{last_msg[:30]}...' → {intent}")
    return {"intent": intent}

def handle_code(state: RouterState) -> dict:
    """处理代码问题"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个资深程序员。回答编程问题，给出代码示例。回答简洁。"),
        ("human", "{question}"),
    ])
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"question": state["messages"][-1].content})
    return {"answer": answer}

def handle_math(state: RouterState) -> dict:
    """处理数学问题"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个数学老师。解答数学问题，给出详细步骤。回答简洁。"),
        ("human", "{question}"),
    ])
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"question": state["messages"][-1].content})
    return {"answer": answer}

def handle_translate(state: RouterState) -> dict:
    """处理翻译请求"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个翻译专家。将用户提供的文本翻译为目标语言。如果未指定，中文翻英文、英文翻中文。"),
        ("human", "{question}"),
    ])
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"question": state["messages"][-1].content})
    return {"answer": answer}

def handle_general(state: RouterState) -> dict:
    """处理一般问题"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个有帮助的通用助手。回答简洁。"),
        ("human", "{question}"),
    ])
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"question": state["messages"][-1].content})
    return {"answer": answer}

def route_by_intent(state: RouterState) -> str:
    """根据意图路由"""
    return state["intent"]

# 构建图
router_graph = StateGraph(RouterState)

router_graph.add_node("classify", classify_intent)
router_graph.add_node("code", handle_code)
router_graph.add_node("math", handle_math)
router_graph.add_node("translate", handle_translate)
router_graph.add_node("general", handle_general)

router_graph.add_edge(START, "classify")
router_graph.add_conditional_edges(
    "classify",
    route_by_intent,
    {
        "code": "code",
        "math": "math",
        "translate": "translate",
        "general": "general",
    }
)
router_graph.add_edge("code", END)
router_graph.add_edge("math", END)
router_graph.add_edge("translate", END)
router_graph.add_edge("general", END)

router_app = router_graph.compile()

# 测试
test_questions = [
    "Python 的列表推导式怎么写？",
    "计算 (15 + 27) * 3",
    "把'你好世界'翻译成英文",
    "推荐几本好书",
]

for q in test_questions:
    result = router_app.invoke({
        "messages": [HumanMessage(content=q)],
        "intent": "",
        "answer": "",
    })
    print(f"  Q: {q}")
    print(f"  A: {result['answer'][:80]}...")
    print()

# ============================================================================
# 2. 并行执行与结果汇总
# ============================================================================
print("\n--- 2. 并行执行与结果汇总 ---")
print("""
多个分析任务并行执行，最后汇总结果。

  输入 → ┬→ 摘要分析 ──┐
         ├→ 情感分析 ──┼→ 汇总 → 输出
         └→ 关键词提取 ─┘

LangGraph 通过 fan-out / fan-in 模式实现并行。
方式：让多个节点都从同一个节点出发，然后汇聚到同一个节点。
""")

class AnalysisState(TypedDict):
    text: str
    summary: str
    sentiment: str
    keywords: str
    report: str

def analyze_summary(state: AnalysisState) -> dict:
    prompt = ChatPromptTemplate.from_template("用一句话总结以下内容（不超过30字）：\n{text}")
    result = (prompt | llm | StrOutputParser()).invoke({"text": state["text"]})
    return {"summary": result}

def analyze_sentiment(state: AnalysisState) -> dict:
    prompt = ChatPromptTemplate.from_template("判断以下内容的情感（正面/负面/中性），只输出一个词：\n{text}")
    result = (prompt | llm | StrOutputParser()).invoke({"text": state["text"]})
    return {"sentiment": result}

def analyze_keywords(state: AnalysisState) -> dict:
    prompt = ChatPromptTemplate.from_template("从以下内容中提取3个关键词，用逗号分隔：\n{text}")
    result = (prompt | llm | StrOutputParser()).invoke({"text": state["text"]})
    return {"keywords": result}

def generate_report(state: AnalysisState) -> dict:
    report = f"""分析报告：
  摘要: {state['summary']}
  情感: {state['sentiment']}
  关键词: {state['keywords']}"""
    return {"report": report}

# 构建并行分析图
analysis_graph = StateGraph(AnalysisState)

analysis_graph.add_node("summary", analyze_summary)
analysis_graph.add_node("sentiment", analyze_sentiment)
analysis_graph.add_node("keywords", analyze_keywords)
analysis_graph.add_node("report", generate_report)

# Fan-out: START → 三个并行节点
analysis_graph.add_edge(START, "summary")
analysis_graph.add_edge(START, "sentiment")
analysis_graph.add_edge(START, "keywords")

# Fan-in: 三个节点 → report
analysis_graph.add_edge("summary", "report")
analysis_graph.add_edge("sentiment", "report")
analysis_graph.add_edge("keywords", "report")

analysis_graph.add_edge("report", END)

analysis_app = analysis_graph.compile()

text = "今天参加了公司的年度技术大会，主题是AI和大模型。讲师们分享了很多前沿技术，特别是RAG和Agent的实践经验让我受益匪浅。组织也很好，午餐也不错。"

print(f"分析文本: {text[:50]}...")
result = analysis_app.invoke({
    "text": text,
    "summary": "", "sentiment": "", "keywords": "", "report": "",
})
print(result["report"])

# ============================================================================
# 3. 子图（Subgraph）
# ============================================================================
print("\n--- 3. 子图（Subgraph）---")
print("""
子图 = 把一个完整的图作为另一个图的一个节点。

好处：
- 模块化：复杂流程拆分为独立的子图
- 复用：同一个子图可以在多个地方使用
- 清晰：每个子图有自己的职责

实现方式：编译后的图可以直接作为节点函数使用。
""")

# 3.1 定义一个"质量检查"子图
class QAState(TypedDict):
    text: str
    quality_score: str
    improved_text: str

def check_quality(state: QAState) -> dict:
    prompt = ChatPromptTemplate.from_template(
        "评估以下文本的质量（1-10分），只输出数字：\n{text}"
    )
    score = (prompt | llm | StrOutputParser()).invoke({"text": state["text"]})
    return {"quality_score": score.strip()}

def improve_text(state: QAState) -> dict:
    prompt = ChatPromptTemplate.from_template(
        "改进以下文本的表达，使其更加清晰和专业，保持原意（50字内）：\n{text}"
    )
    improved = (prompt | llm | StrOutputParser()).invoke({"text": state["text"]})
    return {"improved_text": improved}

def should_improve(state: QAState) -> str:
    try:
        score = int(state["quality_score"])
        if score < 7:
            return "improve"
        return "pass"
    except ValueError:
        return "pass"

qa_graph = StateGraph(QAState)
qa_graph.add_node("check", check_quality)
qa_graph.add_node("improve", improve_text)

qa_graph.add_edge(START, "check")
qa_graph.add_conditional_edges(
    "check",
    should_improve,
    {"improve": "improve", "pass": END}
)
qa_graph.add_edge("improve", END)

qa_app = qa_graph.compile()

# 测试子图
test_texts = [
    "这个东西挺好的吧",
    "本系统采用微服务架构，通过容器化部署实现高可用性和弹性扩展。",
]

for text in test_texts:
    result = qa_app.invoke({"text": text, "quality_score": "", "improved_text": ""})
    print(f"  原文: {text}")
    print(f"  质量: {result['quality_score']}")
    if result["improved_text"]:
        print(f"  改进: {result['improved_text'][:60]}...")
    else:
        print(f"  无需改进")
    print()

# ============================================================================
# 4. 动态工具路由（实用模式）
# ============================================================================
print("\n--- 4. 动态工具路由 ---")
print("""
根据工具的"危险等级"走不同的路径：

  Agent → ┬→ 安全工具 → 直接执行 → Agent
          ├→ 危险工具 → 人工审核 → 执行 → Agent
          └→ 无工具 → END
""")

class SmartAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    pending_approval: bool

SAFE_TOOLS = {"search_info", "calculator"}
DANGEROUS_TOOLS = {"send_email", "delete_file", "modify_database"}

def classify_tool_risk(state: SmartAgentState) -> str:
    """根据工具类型决定走哪条路"""
    last_msg = state["messages"][-1]

    if not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
        return "end"

    tool_names = {tc["name"] for tc in last_msg.tool_calls}

    if tool_names & DANGEROUS_TOOLS:
        return "dangerous"
    elif tool_names & SAFE_TOOLS:
        return "safe"
    else:
        return "safe"  # 默认安全

print("""
图结构：
  START → Agent → ┬→ safe → tools → Agent
                   ├→ dangerous → review → tools → Agent
                   └→ end → END
""")

# ============================================================================
# 5. 状态设计模式
# ============================================================================
print("\n--- 5. 状态设计模式 ---")
print("""
好的 State 设计是成功的一半。

模式1：最小化 State
  只存必要的数据，不存中间结果（除非下游需要）

模式2：用 Reducer 管理列表
  Annotated[list, add_messages]  → 消息追加
  Annotated[list, operator.add]  → 列表拼接

模式3：标志位控制流程
  approved: bool  → 人工是否批准
  retry_count: int → 重试次数
  
模式4：元数据传递
  metadata: dict  → 携带额外信息

示例：
""")

import operator

class WellDesignedState(TypedDict):
    # 核心数据
    messages: Annotated[list, add_messages]

    # 流程控制
    current_step: str
    retry_count: int
    approved: bool

    # 中间结果（下游需要用到）
    search_results: Annotated[list, operator.add]

    # 元数据
    user_id: str
    session_start: str

print("  WellDesignedState 包含:")
print("  - messages: 对话历史（add_messages 归约）")
print("  - current_step: 当前步骤标识")
print("  - retry_count: 重试计数")
print("  - approved: 审批标志")
print("  - search_results: 搜索结果累积")
print("  - user_id/session_start: 元数据")

print("\n" + "=" * 60)
print("[完成] 第5课完成！你已经学会了：")
print("  [v] 意图识别 + 多路径路由")
print("  [v] 并行执行与结果汇总（Fan-out/Fan-in）")
print("  [v] 子图（Subgraph）封装与复用")
print("  [v] 动态工具风险路由")
print("  [v] State 设计模式")
print("=" * 60)
print("\n下一课：06_multi_agent.py - 多 Agent 协作系统")
