import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第1课：图的核心概念（State / Node / Edge）
==============================================================================

什么是 LangGraph？
-----------------
LangGraph 是 LangChain 团队推出的 Agent 编排框架。
它用"图"（Graph）来定义 AI 应用的工作流程。

为什么用"图"而不是"链"？
- 链（Chain）是线性的：A → B → C
- 图（Graph）支持循环、分支、并行：
  A → B → C
       ↑    ↓
       └────┘  （循环：C 可以回到 B）

这对 Agent 非常重要，因为 Agent 需要：
  思考 → 调用工具 → 观察结果 → 再思考 → ...（循环直到完成）

三个核心概念：
- State（状态）：图中流动的数据，所有节点共享
- Node（节点）：执行具体操作的函数
- Edge（边）：节点之间的连接，决定数据流向

  ┌──────┐    edge    ┌──────┐    edge    ┌──────┐
  │ Node │ ────────→ │ Node │ ────────→ │ Node │
  │  A   │           │  B   │           │  C   │
  └──────┘           └──────┘           └──────┘
       共享 State: {"messages": [...], "count": 0, ...}

==============================================================================
"""

print("=" * 60)
print("第1课：图的核心概念（State / Node / Edge）")
print("=" * 60)

# ============================================================================
# 1. State - 状态定义
# ============================================================================
print("\n--- 1. State - 状态定义 ---")
print("""
State 是一个 TypedDict，定义图中流动的数据结构。
所有节点都能读取和修改 State。

关键概念：Reducer（归约器）
- 当多个节点修改同一个字段时，如何合并？
- 最常用的 Reducer：add_messages（追加消息而非覆盖）
""")

from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage

# 1.1 最简单的 State
class SimpleState(TypedDict):
    name: str
    count: int

print(f"SimpleState 字段: name(str), count(int)")

# 1.2 带 Reducer 的 State（最常用）
class ChatState(TypedDict):
    messages: Annotated[list, add_messages]  # ← add_messages 是 Reducer
    user_name: str

print(f"ChatState 字段: messages(list + add_messages归约), user_name(str)")

# 1.3 演示 add_messages 的作用
print(f"\nadd_messages Reducer 演示：")
print(f"  普通 list 赋值：新值覆盖旧值")
print(f"  add_messages：新消息追加到列表末尾")

# 模拟 add_messages 的行为
existing = [HumanMessage(content="你好")]
new_msg = [AIMessage(content="你好！有什么可以帮你的？")]
result = add_messages(existing, new_msg)
print(f"  原有: {[m.content for m in existing]}")
print(f"  新增: {[m.content for m in new_msg]}")
print(f"  合并: {[m.content for m in result]}")

# ============================================================================
# 2. 构建第一个图
# ============================================================================
print("\n--- 2. 构建第一个图 ---")
print("""
构建图的 4 个步骤：
1. 定义 State
2. 定义 Node（函数）
3. 构建 Graph（添加节点和边）
4. 编译并运行

最简单的图：
  START → greet → farewell → END
""")

from langgraph.graph import StateGraph, START, END

# Step 1: 定义 State
class GreetingState(TypedDict):
    name: str
    greeting: str
    farewell: str

# Step 2: 定义 Node（普通 Python 函数）
def greet_node(state: GreetingState) -> dict:
    """问候节点：生成问候语"""
    name = state["name"]
    return {"greeting": f"你好，{name}！欢迎来到 LangGraph 世界！"}

def farewell_node(state: GreetingState) -> dict:
    """告别节点：生成告别语"""
    name = state["name"]
    return {"farewell": f"再见，{name}！祝你学习愉快！"}

# Step 3: 构建 Graph
graph = StateGraph(GreetingState)

# 添加节点
graph.add_node("greet", greet_node)
graph.add_node("farewell", farewell_node)

# 添加边
graph.add_edge(START, "greet")       # 入口 → 问候
graph.add_edge("greet", "farewell")  # 问候 → 告别
graph.add_edge("farewell", END)      # 告别 → 结束

# Step 4: 编译
app = graph.compile()

# 运行！
result = app.invoke({"name": "小明"})
print(f"输入: name='小明'")
print(f"输出:")
print(f"  greeting: {result['greeting']}")
print(f"  farewell: {result['farewell']}")

# ============================================================================
# 3. 节点的返回值规则
# ============================================================================
print("\n--- 3. 节点的返回值规则 ---")
print("""
节点函数的规则：
- 输入：完整的 State 字典
- 输出：一个字典，只包含要更新的字段
- 未返回的字段保持不变

  State = {"a": 1, "b": 2, "c": 3}
  节点返回 {"b": 20}
  → State 变为 {"a": 1, "b": 20, "c": 3}  # 只有 b 被更新
""")

class CountState(TypedDict):
    value: int
    history: Annotated[list, lambda old, new: old + new]  # 自定义 Reducer

def add_one(state: CountState) -> dict:
    new_val = state["value"] + 1
    return {"value": new_val, "history": [f"add_one → {new_val}"]}

def multiply_two(state: CountState) -> dict:
    new_val = state["value"] * 2
    return {"value": new_val, "history": [f"multiply_two → {new_val}"]}

def subtract_three(state: CountState) -> dict:
    new_val = state["value"] - 3
    return {"value": new_val, "history": [f"subtract_three → {new_val}"]}

graph2 = StateGraph(CountState)
graph2.add_node("add", add_one)
graph2.add_node("multiply", multiply_two)
graph2.add_node("subtract", subtract_three)

graph2.add_edge(START, "add")
graph2.add_edge("add", "multiply")
graph2.add_edge("multiply", "subtract")
graph2.add_edge("subtract", END)

app2 = graph2.compile()

result = app2.invoke({"value": 5, "history": ["初始值: 5"]})
print(f"计算过程: 5 → +1=6 → *2=12 → -3=9")
print(f"最终值: {result['value']}")
print(f"历史:")
for step in result["history"]:
    print(f"  {step}")

# ============================================================================
# 4. 条件边（Conditional Edge）
# ============================================================================
print("\n--- 4. 条件边 ---")
print("""
条件边根据 State 的值决定走哪条路。
这是实现分支和循环的关键！

  add_conditional_edges(
      source_node,        # 从哪个节点出发
      condition_function, # 判断函数，返回目标节点名
      path_map            # 可选：返回值 → 节点名的映射
  )
""")

class RouterState(TypedDict):
    number: int
    result: str

def check_number(state: RouterState) -> dict:
    """不做修改，只是让条件边读取状态"""
    return {}

def handle_positive(state: RouterState) -> dict:
    return {"result": f"{state['number']} 是正数"}

def handle_negative(state: RouterState) -> dict:
    return {"result": f"{state['number']} 是负数"}

def handle_zero(state: RouterState) -> dict:
    return {"result": f"{state['number']} 是零"}

def route_by_number(state: RouterState) -> str:
    """条件函数：根据数字决定走哪条路"""
    n = state["number"]
    if n > 0:
        return "positive"
    elif n < 0:
        return "negative"
    else:
        return "zero"

graph3 = StateGraph(RouterState)

graph3.add_node("check", check_number)
graph3.add_node("positive", handle_positive)
graph3.add_node("negative", handle_negative)
graph3.add_node("zero", handle_zero)

graph3.add_edge(START, "check")

# 条件边：从 check 节点出发，根据 route_by_number 的返回值选择路径
graph3.add_conditional_edges(
    "check",
    route_by_number,
    {
        "positive": "positive",
        "negative": "negative",
        "zero": "zero",
    }
)

graph3.add_edge("positive", END)
graph3.add_edge("negative", END)
graph3.add_edge("zero", END)

app3 = graph3.compile()

for num in [42, -7, 0]:
    result = app3.invoke({"number": num})
    print(f"  输入 {num:3d} → {result['result']}")

# ============================================================================
# 5. 循环（Loop）
# ============================================================================
print("\n--- 5. 循环 ---")
print("""
Agent 的核心就是循环：思考 → 行动 → 观察 → 再思考 → ...

用条件边可以实现循环：
  条件函数返回当前节点名 → 重新执行该节点
  条件函数返回 END → 退出循环
""")

class LoopState(TypedDict):
    counter: int
    log: Annotated[list, lambda old, new: old + new]

def increment(state: LoopState) -> dict:
    new_val = state["counter"] + 1
    return {"counter": new_val, "log": [f"计数: {new_val}"]}

def should_continue(state: LoopState) -> str:
    """当计数器 < 5 时继续循环"""
    if state["counter"] < 5:
        return "continue"
    return "done"

graph4 = StateGraph(LoopState)
graph4.add_node("increment", increment)

graph4.add_edge(START, "increment")
graph4.add_conditional_edges(
    "increment",
    should_continue,
    {
        "continue": "increment",  # 循环回自己
        "done": END,              # 结束
    }
)

app4 = graph4.compile()

result = app4.invoke({"counter": 0, "log": ["开始"]})
print(f"最终计数: {result['counter']}")
print(f"执行日志: {result['log']}")

# ============================================================================
# 6. 图的可视化（了解即可）
# ============================================================================
print("\n--- 6. 图的结构信息 ---")
print("""
编译后的图可以查看结构信息：
- app.get_graph()      获取图对象
- graph.draw_mermaid() 生成 Mermaid 图表代码

如果安装了 graphviz，还可以生成图片：
  graph.draw_png("my_graph.png")
""")

try:
    mermaid = app4.get_graph().draw_mermaid()
    print(f"Mermaid 图表代码（可粘贴到 mermaid.live 查看）:\n")
    print(mermaid)
except Exception:
    print("（需要安装额外依赖才能生成图表）")

# ============================================================================
# 7. 核心概念总结
# ============================================================================
print("\n--- 7. 核心概念总结 ---")
print("""
┌──────────────────────────────────────────────────────────┐
│  概念          │  说明                                    │
├──────────────────────────────────────────────────────────┤
│  State         │  图中流动的数据结构（TypedDict）          │
│  Node          │  执行操作的函数，输入State，返回更新      │
│  Edge          │  节点之间的连接                           │
│  Conditional   │  条件边，根据State值选择路径              │
│  Edge          │                                          │
│  START         │  图的入口点                               │
│  END           │  图的终止点                               │
│  Reducer       │  字段合并策略（如 add_messages）          │
│  compile()     │  编译图，生成可运行的 app                 │
│  invoke()      │  执行图                                  │
└──────────────────────────────────────────────────────────┘

构建步骤：
  1. 定义 State（TypedDict）
  2. 定义节点函数
  3. StateGraph(State) 创建图
  4. add_node() 添加节点
  5. add_edge() / add_conditional_edges() 添加边
  6. compile() 编译
  7. invoke() 运行
""")

print("\n" + "=" * 60)
print("[完成] 第1课完成！你已经学会了：")
print("  [v] State 状态定义与 Reducer")
print("  [v] Node 节点函数")
print("  [v] Edge 普通边连接")
print("  [v] Conditional Edge 条件分支")
print("  [v] 循环（Loop）实现")
print("  [v] 图的编译与运行")
print("=" * 60)
print("\n下一课：02_tool_calling.py - 工具定义与 LLM 工具调用")
