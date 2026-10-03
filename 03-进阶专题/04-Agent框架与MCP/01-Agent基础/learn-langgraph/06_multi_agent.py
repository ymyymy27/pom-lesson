import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第6课：多 Agent 协作系统
==============================================================================

什么是多 Agent？
--------------
单 Agent 适合简单任务，但复杂任务往往需要多个"专家"协作：

单 Agent：一个人包打天下（容易出错、Prompt 过长）
多 Agent：每个 Agent 有专长，协作完成复杂任务

协作模式：
1. Supervisor（主管模式）：一个主管 Agent 分配任务给工人 Agent
2. Sequential（顺序模式）：Agent A 完成后交给 Agent B
3. Hierarchical（层级模式）：多层主管，分级管理

本课重点：
- Supervisor 模式（最常用）
- 顺序协作模式
- Agent 之间的通信
==============================================================================
"""

from typing import Annotated, TypedDict, Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

llm = ChatOllama(model="qwen2.5:7b", temperature=0)

print("=" * 60)
print("第6课：多 Agent 协作系统")
print("=" * 60)

# ============================================================================
# 1. 顺序协作：研究 → 写作 → 审核
# ============================================================================
print("\n--- 1. 顺序协作模式 ---")
print("""
三个 Agent 顺序协作完成一篇文章：

  用户需求 → [研究员] → [作者] → [审核员] → 最终输出
              搜集素材    写文章    审核质量

每个 Agent 有独立的 System Prompt，扮演不同角色。
""")

class WritingState(TypedDict):
    topic: str
    research: str
    draft: str
    review: str
    final: str

def researcher_agent(state: WritingState) -> dict:
    """研究员：搜集素材和要点"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个资深研究员。你的任务是为写作提供素材。
根据给定的主题，列出 3-5 个关键要点和事实。
每个要点用一句话概括。不要写文章，只提供素材。"""),
        ("human", "主题：{topic}"),
    ])
    chain = prompt | llm | StrOutputParser()
    research = chain.invoke({"topic": state["topic"]})
    print(f"  [研究员] 完成素材搜集")
    return {"research": research}

def writer_agent(state: WritingState) -> dict:
    """作者：根据素材写文章"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的技术作者。根据研究员提供的素材写一段简短的文章。
要求：
- 100-150字
- 结构清晰
- 语言流畅专业"""),
        ("human", "主题：{topic}\n\n素材：\n{research}"),
    ])
    chain = prompt | llm | StrOutputParser()
    draft = chain.invoke({"topic": state["topic"], "research": state["research"]})
    print(f"  [作者] 完成初稿")
    return {"draft": draft}

def reviewer_agent(state: WritingState) -> dict:
    """审核员：审核文章质量"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个严格的内容审核员。审核文章质量并给出评价。
输出格式：
评分：X/10
优点：...
建议：...
如果评分>=7，在最后加上"✅ 审核通过"
如果评分<7，在最后加上"❌ 需要修改" """),
        ("human", "主题：{topic}\n\n文章：\n{draft}"),
    ])
    chain = prompt | llm | StrOutputParser()
    review = chain.invoke({"topic": state["topic"], "draft": state["draft"]})
    print(f"  [审核员] 完成审核")
    return {"review": review, "final": state["draft"]}

# 构建图
writing_graph = StateGraph(WritingState)
writing_graph.add_node("researcher", researcher_agent)
writing_graph.add_node("writer", writer_agent)
writing_graph.add_node("reviewer", reviewer_agent)

writing_graph.add_edge(START, "researcher")
writing_graph.add_edge("researcher", "writer")
writing_graph.add_edge("writer", "reviewer")
writing_graph.add_edge("reviewer", END)

writing_app = writing_graph.compile()

# 测试
result = writing_app.invoke({
    "topic": "Python 在 AI 开发中的优势",
    "research": "", "draft": "", "review": "", "final": "",
})

print(f"\n[素材]:\n{result['research'][:200]}...")
print(f"\n[文章]:\n{result['draft'][:200]}...")
print(f"\n[审核]:\n{result['review'][:200]}...")

# ============================================================================
# 2. Supervisor 主管模式
# ============================================================================
print("\n\n--- 2. Supervisor 主管模式 ---")
print("""
主管 Agent 接收任务，分析后决定分配给哪个工人 Agent。

          ┌──────────┐
          │Supervisor│
          └────┬─────┘
          ┌────┼────────┐
          ↓    ↓        ↓
      ┌──────┐┌──────┐┌──────┐
      │Coder ││Writer││Analyst│
      └──┬───┘└──┬───┘└──┬───┘
         └───────┼───────┘
                 ↓
          ┌──────────┐
          │Supervisor│ → 决定下一步或结束
          └──────────┘

主管的职责：
1. 分析当前任务状态
2. 决定下一个该哪个 Agent 工作
3. 判断任务是否完成
""")

class SupervisorState(TypedDict):
    messages: Annotated[list, add_messages]
    next_agent: str
    task_complete: bool

WORKERS = ["coder", "writer", "analyst"]

def supervisor_node(state: SupervisorState) -> dict:
    """主管：决定下一步该谁工作"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""你是一个项目主管。你管理着以下团队成员：
- coder: 编程专家，负责写代码和解决技术问题
- writer: 写作专家，负责撰写文档和文章
- analyst: 数据分析师，负责分析数据和给出洞察

根据对话内容，决定下一步应该由谁来工作。
如果任务已经完成，输出 FINISH。

只输出一个词：{'/'.join(WORKERS)}/FINISH"""),
        ("placeholder", "{messages}"),
    ])

    chain = prompt | llm | StrOutputParser()
    decision = chain.invoke({"messages": state["messages"]}).strip().lower()

    # 规范化
    if "finish" in decision or "完成" in decision:
        return {"next_agent": "FINISH", "task_complete": True}

    for worker in WORKERS:
        if worker in decision:
            return {"next_agent": worker, "task_complete": False}

    return {"next_agent": "FINISH", "task_complete": True}

def coder_node(state: SupervisorState) -> dict:
    """编码专家"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个编程专家。根据对话需求完成编程任务。回答简洁，给出关键代码。"),
        ("placeholder", "{messages}"),
    ])
    response = (prompt | llm).invoke({"messages": state["messages"]})
    return {"messages": [AIMessage(content=f"[Coder] {response.content}", name="coder")]}

def writer_node(state: SupervisorState) -> dict:
    """写作专家"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个写作专家。根据对话需求完成写作任务。回答简洁专业。"),
        ("placeholder", "{messages}"),
    ])
    response = (prompt | llm).invoke({"messages": state["messages"]})
    return {"messages": [AIMessage(content=f"[Writer] {response.content}", name="writer")]}

def analyst_node(state: SupervisorState) -> dict:
    """分析专家"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个数据分析专家。根据对话需求完成分析任务。给出关键洞察。"),
        ("placeholder", "{messages}"),
    ])
    response = (prompt | llm).invoke({"messages": state["messages"]})
    return {"messages": [AIMessage(content=f"[Analyst] {response.content}", name="analyst")]}

def route_to_worker(state: SupervisorState) -> str:
    """路由到下一个工人或结束"""
    if state.get("task_complete") or state["next_agent"] == "FINISH":
        return END
    return state["next_agent"]

# 构建 Supervisor 图
supervisor_graph = StateGraph(SupervisorState)

supervisor_graph.add_node("supervisor", supervisor_node)
supervisor_graph.add_node("coder", coder_node)
supervisor_graph.add_node("writer", writer_node)
supervisor_graph.add_node("analyst", analyst_node)

supervisor_graph.add_edge(START, "supervisor")
supervisor_graph.add_conditional_edges(
    "supervisor",
    route_to_worker,
    {"coder": "coder", "writer": "writer", "analyst": "analyst", END: END}
)
# 工人完成后回到主管
supervisor_graph.add_edge("coder", "supervisor")
supervisor_graph.add_edge("writer", "supervisor")
supervisor_graph.add_edge("analyst", "supervisor")

supervisor_app = supervisor_graph.compile()

# 测试
print("\n测试 Supervisor 模式:")
result = supervisor_app.invoke({
    "messages": [HumanMessage(content="写一个 Python 的快速排序函数，然后写一段说明文档")],
    "next_agent": "",
    "task_complete": False,
}, config={"recursion_limit": 15})

print(f"\n执行过程:")
for msg in result["messages"]:
    if isinstance(msg, HumanMessage):
        print(f"  [用户] {msg.content[:60]}...")
    elif isinstance(msg, AIMessage):
        name = getattr(msg, 'name', 'AI')
        print(f"  [{name}] {msg.content[:80]}...")

# ============================================================================
# 3. Agent 间通信最佳实践
# ============================================================================
print("\n\n--- 3. Agent 间通信最佳实践 ---")
print("""
多 Agent 系统的通信方式：

1. 共享 State（本课方式）
   - 所有 Agent 读写同一个 State
   - 适合紧密协作
   - 通过 messages 字段传递信息

2. 消息传递
   - Agent 通过 messages 互发消息
   - 用 name 字段标识消息来源
   - 类似"群聊"模式

3. 结构化交接
   - 每个 Agent 输出到专门的字段
   - 下一个 Agent 从该字段读取
   - 接口清晰，耦合度低

最佳实践：
┌──────────────────────────────────────────────────────────┐
│  ✅ 每个 Agent 有明确的职责边界                           │
│  ✅ Agent 输出带名字标识（name="coder"）                  │
│  ✅ Supervisor 有清晰的路由逻辑                           │
│  ✅ 设置 recursion_limit 防止无限循环                     │
│  ✅ 每个 Agent 的 System Prompt 简洁聚焦                  │
│  ❌ 避免 Agent 职责重叠                                   │
│  ❌ 避免过多 Agent（3-5个为宜）                           │
│  ❌ 避免 Agent 之间直接相互调用（通过 Supervisor 协调）    │
└──────────────────────────────────────────────────────────┘
""")

# ============================================================================
# 4. 协作模式对比
# ============================================================================
print("\n--- 4. 协作模式对比 ---")
print("""
┌─────────────┬──────────────────────────────────────────┐
│  模式        │  适用场景                                 │
├─────────────┼──────────────────────────────────────────┤
│  顺序模式    │  流程固定：研究→写作→审核                 │
│  主管模式    │  动态分配：根据任务类型选择专家            │
│  并行模式    │  独立分析：多个维度同时分析后汇总          │
│  层级模式    │  大型系统：主管管理子主管，子主管管理工人   │
└─────────────┴──────────────────────────────────────────┘

选择建议：
- 流程明确 → 顺序模式（简单可靠）
- 任务多变 → 主管模式（灵活）
- 可以并行 → 并行模式（效率高）
- 超复杂   → 层级模式（可扩展，但复杂度高）
""")

print("\n" + "=" * 60)
print("[完成] 第6课完成！你已经学会了：")
print("  [v] 顺序协作模式（研究→写作→审核）")
print("  [v] Supervisor 主管模式（动态分配）")
print("  [v] Agent 间通信方式")
print("  [v] 多 Agent 最佳实践")
print("  [v] 协作模式选型")
print("=" * 60)
print("\n下一课：07_agent_project.py - 完整项目：AI 工作助手")
