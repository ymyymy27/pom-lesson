import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第4课：人机协作与检查点
==============================================================================

为什么需要人机协作？
-----------------
Agent 自主执行任务很方便，但有些操作需要人工确认：
- 敏感操作（删除文件、发送邮件、修改数据库）
- 高风险决策（大额支付、合同签署）
- 需要人工判断的场景（审核内容、确认信息）

LangGraph 的解决方案：
1. Checkpoint（检查点）：保存图的执行状态
2. Interrupt（中断）：在指定节点前暂停，等待人工输入
3. Resume（恢复）：人工确认后继续执行

关键组件：
- MemorySaver:       内存检查点存储
- interrupt_before:  在指定节点前中断
- interrupt_after:   在指定节点后中断
- thread_id:         对话线程标识（支持多个独立对话）
==============================================================================
"""

from typing import Annotated, TypedDict
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

print("=" * 60)
print("第4课：人机协作与检查点")
print("=" * 60)

# ============================================================================
# 1. Checkpoint 检查点
# ============================================================================
print("\n--- 1. Checkpoint 检查点 ---")
print("""
检查点 = 图执行过程中某个时刻的完整状态快照。

作用：
- 暂停/恢复：图可以暂停，稍后从断点继续
- 时间旅行：可以回到任意检查点重新执行
- 多线程：同一个图支持多个独立的对话

存储方式：
- MemorySaver:       内存存储（开发测试用）
- SqliteSaver:       SQLite 文件存储
- PostgresSaver:     PostgreSQL 存储（生产环境）
""")

# 创建检查点存储
memory = MemorySaver()

# ============================================================================
# 2. 带检查点的 Agent
# ============================================================================
print("\n--- 2. 带检查点的 Agent ---")

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """发送邮件。这是一个敏感操作，需要人工确认。"""
    return f"✅ 邮件已发送给 {to}，主题: {subject}"

@tool
def delete_file(path: str) -> str:
    """删除文件。这是一个危险操作，需要人工确认。"""
    return f"✅ 文件 {path} 已删除"

@tool
def search_info(query: str) -> str:
    """搜索信息。这是安全操作，无需确认。"""
    return f"搜索结果: {query} 的相关信息..."

tools = [send_email, delete_file, search_info]
llm = ChatOllama(model="qwen2.5:7b", temperature=0)
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: AgentState) -> dict:
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content="你是一个助手，可以搜索信息、发送邮件和删除文件。")] + messages
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)

def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")

# 编译时添加检查点 + 中断配置
# interrupt_before=["tools"] 表示：在执行工具前暂停
agent_with_hitl = graph.compile(
    checkpointer=memory,
    interrupt_before=["tools"],  # ← 关键！在工具执行前暂停
)

print("带人机协作的 Agent 构建完成 ✓")
print("  → 每次工具调用前会暂停，等待人工确认")

# ============================================================================
# 3. 人机协作流程演示
# ============================================================================
print("\n--- 3. 人机协作流程演示 ---")
print("""
完整流程：
  1. 用户提问
  2. Agent 决定调用工具 → 图暂停 ⏸️
  3. 程序展示待执行的操作
  4. 人工决定：批准 / 拒绝 / 修改
  5. 继续执行（或终止）
""")

# 每个对话需要一个唯一的 thread_id
config = {"configurable": {"thread_id": "demo_thread_1"}}

# Step 1: 用户提问
print("\n[Step 1] 用户提问")
result = agent_with_hitl.invoke(
    {"messages": [HumanMessage(content="搜索一下什么是 LangGraph")]},
    config=config,
)

# 检查是否被中断
snapshot = agent_with_hitl.get_state(config)
print(f"  图状态: {'已暂停' if snapshot.next else '已完成'}")

if snapshot.next:
    # Step 2: 查看待执行的操作
    print(f"\n[Step 2] 待执行的操作:")
    last_msg = snapshot.values["messages"][-1]
    if hasattr(last_msg, "tool_calls"):
        for tc in last_msg.tool_calls:
            print(f"  🔧 工具: {tc['name']}")
            print(f"     参数: {tc['args']}")

    # Step 3: 人工批准（继续执行）
    print(f"\n[Step 3] 人工批准 → 继续执行")
    result = agent_with_hitl.invoke(None, config=config)
    # 传入 None 表示"从断点继续"

    # 可能再次暂停（如果还有工具调用）
    snapshot = agent_with_hitl.get_state(config)
    while snapshot.next:
        print(f"  再次暂停，自动批准继续...")
        result = agent_with_hitl.invoke(None, config=config)
        snapshot = agent_with_hitl.get_state(config)

print(f"\n[最终结果]")
final = result["messages"][-1].content if result["messages"] else "无回复"
print(f"  {final[:150]}...")

# ============================================================================
# 4. 拒绝操作
# ============================================================================
print("\n\n--- 4. 拒绝操作 ---")
print("""
如果人工不同意执行工具，可以：
- 直接终止
- 用 ToolMessage 返回拒绝信息，让 Agent 重新思考
""")

config2 = {"configurable": {"thread_id": "demo_thread_2"}}

# 用户请求发邮件
result = agent_with_hitl.invoke(
    {"messages": [HumanMessage(content="帮我发一封邮件给 boss@company.com，主题是请假，内容是明天请假一天")]},
    config=config2,
)

snapshot = agent_with_hitl.get_state(config2)
if snapshot.next:
    last_msg = snapshot.values["messages"][-1]
    print(f"待执行操作:")
    if hasattr(last_msg, "tool_calls"):
        for tc in last_msg.tool_calls:
            print(f"  🔧 {tc['name']}({tc['args']})")

    # 模拟人工拒绝：注入一条 ToolMessage 告知拒绝
    print(f"\n❌ 人工拒绝此操作")

    # 方式：更新状态，添加拒绝消息
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        reject_messages = []
        for tc in last_msg.tool_calls:
            reject_messages.append(ToolMessage(
                content="操作被用户拒绝。请告知用户操作已取消。",
                tool_call_id=tc["id"],
            ))

        agent_with_hitl.update_state(
            config2,
            {"messages": reject_messages},
        )

        # 继续执行（Agent 会看到拒绝消息并做出相应回复）
        result = agent_with_hitl.invoke(None, config=config2)
        snapshot = agent_with_hitl.get_state(config2)
        while snapshot.next:
            result = agent_with_hitl.invoke(None, config=config2)
            snapshot = agent_with_hitl.get_state(config2)

        print(f"Agent 回复: {result['messages'][-1].content[:120]}...")

# ============================================================================
# 5. 多线程（多个独立对话）
# ============================================================================
print("\n\n--- 5. 多线程 ---")
print("""
thread_id 让同一个 Agent 支持多个独立的对话。
不同 thread_id 的对话互不干扰。
""")

# 不用 interrupt 的普通 Agent 来演示多线程
simple_agent = graph.compile(checkpointer=MemorySaver())

# 线程 A
config_a = {"configurable": {"thread_id": "user_alice"}}
result_a = simple_agent.invoke(
    {"messages": [HumanMessage(content="你好，我叫 Alice")]},
    config=config_a,
)
print(f"[Alice] AI: {result_a['messages'][-1].content[:60]}...")

# 线程 B
config_b = {"configurable": {"thread_id": "user_bob"}}
result_b = simple_agent.invoke(
    {"messages": [HumanMessage(content="你好，我叫 Bob")]},
    config=config_b,
)
print(f"[Bob]   AI: {result_b['messages'][-1].content[:60]}...")

# Alice 追问（记得上下文）
result_a2 = simple_agent.invoke(
    {"messages": [HumanMessage(content="我叫什么名字？")]},
    config=config_a,
)
print(f"[Alice] 追问→ AI: {result_a2['messages'][-1].content[:60]}...")

# Bob 追问（独立上下文）
result_b2 = simple_agent.invoke(
    {"messages": [HumanMessage(content="我叫什么名字？")]},
    config=config_b,
)
print(f"[Bob]   追问→ AI: {result_b2['messages'][-1].content[:60]}...")

# ============================================================================
# 6. 查看和操作状态
# ============================================================================
print("\n--- 6. 查看和操作状态 ---")
print("""
检查点提供了丰富的状态查看能力：
  get_state():    获取当前状态
  get_state_history(): 获取历史状态
  update_state():  手动修改状态
""")

# 查看当前状态
state = simple_agent.get_state(config_a)
print(f"Alice 的对话状态:")
print(f"  消息数: {len(state.values['messages'])}")
print(f"  下一步: {state.next}")
print(f"  最后消息: {state.values['messages'][-1].content[:50]}...")

# 查看历史状态
print(f"\n状态历史:")
for i, snapshot in enumerate(simple_agent.get_state_history(config_a)):
    msg_count = len(snapshot.values.get("messages", []))
    print(f"  检查点 {i}: {msg_count} 条消息, 下一步={snapshot.next}")
    if i >= 4:
        print(f"  ... (更多)")
        break

# ============================================================================
# 7. 实用模式：选择性中断
# ============================================================================
print("\n--- 7. 实用模式：选择性中断 ---")
print("""
不是所有工具调用都需要人工确认。
可以根据工具类型决定是否中断。

思路：
- 安全工具（搜索、查询）→ 自动执行
- 危险工具（删除、发送、修改）→ 人工确认
""")

SAFE_TOOLS = {"search_info"}
DANGEROUS_TOOLS = {"send_email", "delete_file"}

def selective_should_continue(state: AgentState) -> str:
    """选择性中断：安全工具直接执行，危险工具需要确认"""
    last_message = state["messages"][-1]

    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return END

    # 检查是否有危险工具调用
    tool_names = {tc["name"] for tc in last_message.tool_calls}
    has_dangerous = bool(tool_names & DANGEROUS_TOOLS)

    if has_dangerous:
        return "human_review"  # 走人工审核
    else:
        return "tools"  # 直接执行

print(f"安全工具（自动执行）: {SAFE_TOOLS}")
print(f"危险工具（需确认）: {DANGEROUS_TOOLS}")

print("""
图结构：
                ┌────────────────┐
                │     Agent      │
                └───────┬────────┘
                   ┌────┴────┐
              安全  │         │ 危险
                   ↓         ↓
              ┌────────┐ ┌──────────┐
              │ Tools  │ │ 人工审核  │ ⏸️
              └────┬───┘ └────┬─────┘
                   │          │
                   └────┬─────┘
                        ↓
                   ┌────────┐
                   │ Agent  │
                   └────────┘
""")

print("\n" + "=" * 60)
print("[完成] 第4课完成！你已经学会了：")
print("  [v] Checkpoint 检查点原理")
print("  [v] MemorySaver 内存检查点")
print("  [v] interrupt_before 中断机制")
print("  [v] 批准/拒绝操作流程")
print("  [v] 多线程独立对话")
print("  [v] get_state/update_state 状态管理")
print("  [v] 选择性中断模式")
print("=" * 60)
print("\n下一课：05_conditional_branching.py - 条件分支与子图")
