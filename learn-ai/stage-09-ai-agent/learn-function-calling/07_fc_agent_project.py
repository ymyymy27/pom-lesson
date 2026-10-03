import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第7课：完整项目 - Function Calling 智能助手
==============================================================================

本课整合前6课所有知识，构建一个功能完备的 Function Calling 助手：

┌──────────────────────────────────────────────────────────┐
│               Function Calling 智能助手                   │
│                                                          │
│  功能模块：                                               │
│  1. 天气查询    - 多城市天气对比                          │
│  2. 数学计算    - 表达式计算                              │
│  3. 知识搜索    - 技术知识库检索                          │
│  4. 数据分析    - 数据库查询 + Python 分析                │
│  5. 文件管理    - 沙箱文件读写                            │
│  6. 时间日期    - 当前时间与日历计算                      │
│                                                          │
│  架构特性：                                               │
│  - 自动工具路由（意图识别 → 工具集选择）                  │
│  - 并行工具调用（多工具同时执行）                         │
│  - 多轮对话记忆（上下文追问）                             │
│  - 安全控制（输入验证 + 沙箱）                           │
│  - 流式输出（实时展示执行过程）                           │
│                                                          │
│  整合知识：                                               │
│  - 第1课: Function Calling 原理                          │
│  - 第2课: OpenAI API 格式                                │
│  - 第3课: Ollama 本地调用                                │
│  - 第4课: 并行 + 多轮                                    │
│  - 第5课: 强制调用 + 路由 + 流式                         │
│  - 第6课: 真实工具设计（安全+错误处理）                   │
└──────────────────────────────────────────────────────────┘
==============================================================================
"""

import json
import os
import tempfile
import sqlite3
from datetime import datetime, timedelta
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_community.chat_models import ChatOllama

print("=" * 60)
print("第7课：完整项目 - Function Calling 智能助手")
print("=" * 60)

# ============================================================================
# 1. 工具定义
# ============================================================================
print("\n--- 1. 定义工具集 ---")

# ----- 1.1 天气工具 -----
@tool
def get_weather(city: str) -> str:
    """查询城市的当前天气。参数 city 为中文城市名如'北京'、'上海'。
    返回温度、湿度、风力、天气描述。"""
    db = {
        "北京": {"temp": 25, "humidity": 40, "wind": "北风3级", "desc": "晴天", "aqi": 85},
        "上海": {"temp": 22, "humidity": 65, "wind": "东风2级", "desc": "多云", "aqi": 72},
        "广州": {"temp": 30, "humidity": 80, "wind": "南风1级", "desc": "小雨", "aqi": 68},
        "深圳": {"temp": 28, "humidity": 75, "wind": "西南风2级", "desc": "阵雨", "aqi": 65},
        "成都": {"temp": 20, "humidity": 70, "wind": "微风", "desc": "阴天", "aqi": 95},
        "杭州": {"temp": 23, "humidity": 60, "wind": "东南风2级", "desc": "晴转多云", "aqi": 78},
        "哈尔滨": {"temp": 5, "humidity": 55, "wind": "北风4级", "desc": "雪", "aqi": 50},
    }
    data = db.get(city)
    if not data:
        return json.dumps({"error": f"暂无{city}数据", "available": list(db.keys())}, ensure_ascii=False)
    return json.dumps({"city": city, **data}, ensure_ascii=False)

# ----- 1.2 计算工具 -----
@tool
def calculator(expression: str) -> str:
    """计算数学表达式。支持加减乘除、幂运算、括号、取余。
    示例: '(15+27)*3', '2**10', '100/7', '17%5'"""
    try:
        allowed = set("0123456789+-*/().** %")
        if not all(c in allowed for c in expression):
            return json.dumps({"error": "表达式包含不允许的字符"})
        result = eval(expression)
        if isinstance(result, float):
            result = round(result, 6)
        return json.dumps({"expression": expression, "result": result})
    except Exception as e:
        return json.dumps({"error": f"计算错误: {e}"})

# ----- 1.3 知识搜索工具 -----
@tool
def search_knowledge(query: str) -> str:
    """搜索技术知识库。支持编程语言、框架、AI、DevOps等技术话题。
    参数 query 为搜索关键词。"""
    kb = {
        "python": "Python 是通用编程语言，由 Guido van Rossum 于1991年创建。特点：简洁易读、丰富的库生态、广泛用于AI/Web/数据科学。最新版本3.12+。",
        "javascript": "JavaScript 是Web前端核心语言，也可用于后端(Node.js)。特点：事件驱动、异步编程、庞大的npm生态。",
        "langchain": "LangChain 是 LLM 应用开发框架。核心：Chat Models、Prompt Templates、Output Parsers、LCEL、Memory、Retrievers。",
        "langgraph": "LangGraph 是 Agent 编排框架，基于图结构。核心：State/Node/Edge、条件分支、循环、人机协作、多Agent协作。",
        "function calling": "Function Calling 让 LLM 能调用外部函数。LLM 决定调用什么函数和参数，程序负责执行。支持并行调用和多轮对话。",
        "mcp": "MCP (Model Context Protocol) 是 Anthropic 提出的开放协议，标准化 LLM 与外部工具/数据源的连接方式。采用 Client-Server 架构。",
        "rag": "RAG（检索增强生成）：文档分块→Embedding→向量存储→检索→拼入Prompt→LLM生成。减少幻觉，支持私域知识。",
        "docker": "Docker 容器化平台：镜像(Image)、容器(Container)、Dockerfile、Compose。比虚拟机更轻量。",
        "fastapi": "FastAPI 是高性能Python Web框架，基于Starlette+Pydantic。自动文档生成、类型安全、原生异步。",
        "pytorch": "PyTorch 是深度学习框架(Meta)。动态计算图、Pythonic API、GPU加速。学术研究和工业应用首选。",
        "transformer": "Transformer 由Google(2017)提出，核心是自注意力机制。GPT/BERT/LLaMA等大模型的基础架构。",
    }
    results = []
    q_lower = query.lower()
    for key, val in kb.items():
        if key in q_lower or any(w in q_lower for w in key.split()):
            results.append({"topic": key, "content": val})
    if results:
        return json.dumps({"query": query, "results": results}, ensure_ascii=False)
    return json.dumps({"query": query, "results": [], "hint": f"可搜索: {', '.join(kb.keys())}"}, ensure_ascii=False)

# ----- 1.4 数据库工具 -----
demo_db = tempfile.mktemp(suffix=".db")
_conn = sqlite3.connect(demo_db)
_conn.executescript("""
    CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, dept TEXT, salary REAL, hire_date TEXT);
    INSERT INTO employees VALUES (1,'张三','技术部',25000,'2022-03-15');
    INSERT INTO employees VALUES (2,'李四','产品部',22000,'2021-08-20');
    INSERT INTO employees VALUES (3,'王五','技术部',28000,'2020-01-10');
    INSERT INTO employees VALUES (4,'赵六','市场部',20000,'2023-06-01');
    INSERT INTO employees VALUES (5,'孙七','技术部',30000,'2019-11-25');
    INSERT INTO employees VALUES (6,'周八','产品部',24000,'2022-09-12');
    INSERT INTO employees VALUES (7,'吴九','市场部',21000,'2023-01-08');
    CREATE TABLE sales (id INTEGER PRIMARY KEY, product TEXT, amount REAL, quantity INT, date TEXT);
    INSERT INTO sales VALUES (1,'蓝牙耳机',299,50,'2024-01-15');
    INSERT INTO sales VALUES (2,'机械键盘',599,30,'2024-01-20');
    INSERT INTO sales VALUES (3,'蓝牙耳机',299,45,'2024-02-10');
    INSERT INTO sales VALUES (4,'显示器',1999,10,'2024-02-15');
    INSERT INTO sales VALUES (5,'机械键盘',599,25,'2024-03-01');
""")
_conn.commit()
_conn.close()

@tool
def query_db(sql: str) -> str:
    """查询数据库（只允许SELECT）。
    可用表：employees(id,name,dept,salary,hire_date), sales(id,product,amount,quantity,date)。
    sql: SQL查询语句。"""
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT"):
        return json.dumps({"error": "只允许SELECT查询"})
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
    for w in forbidden:
        if w in sql_upper:
            return json.dumps({"error": f"禁止{w}操作"})
    try:
        conn = sqlite3.connect(demo_db)
        conn.row_factory = sqlite3.Row
        rows = conn.cursor().execute(sql).fetchmany(50)
        data = [dict(r) for r in rows]
        conn.close()
        return json.dumps({"count": len(data), "data": data}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

# ----- 1.5 代码执行工具 -----
@tool
def run_python(code: str) -> str:
    """执行Python代码（受限沙箱环境）。禁止文件/网络/系统操作。
    用 print() 输出结果。可用模块: math, json, statistics。"""
    FORBIDDEN = ["import os", "import sys", "import subprocess", "__import__",
                 "eval(", "exec(", "open(", "import socket", "import http"]
    for p in FORBIDDEN:
        if p in code:
            return json.dumps({"error": f"禁止: {p}"})
    if len(code) > 5000:
        return json.dumps({"error": "代码过长"})
    try:
        import math, statistics
        safe_globals = {
            "__builtins__": {
                "print": print, "len": len, "range": range, "int": int,
                "float": float, "str": str, "list": list, "dict": dict,
                "tuple": tuple, "set": set, "bool": bool, "max": max,
                "min": min, "sum": sum, "abs": abs, "round": round,
                "sorted": sorted, "enumerate": enumerate, "zip": zip,
                "map": map, "filter": filter, "isinstance": isinstance,
                "True": True, "False": False, "None": None,
            },
            "math": math, "json": json, "statistics": statistics,
        }
        from io import StringIO
        buf = StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            exec(code, safe_globals)
        finally:
            sys.stdout = old
        output = buf.getvalue()[:5000]
        return json.dumps({"output": output or "(无输出)"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})

# ----- 1.6 时间工具 -----
@tool
def get_datetime() -> str:
    """获取当前日期和时间。"""
    now = datetime.now()
    weekday = "一二三四五六日"[now.weekday()]
    return json.dumps({
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday": f"星期{weekday}",
        "timestamp": int(now.timestamp()),
    }, ensure_ascii=False)

@tool
def date_calculate(operation: str, days: int = 0, date_str: str = "") -> str:
    """日期计算。operation: 'add'(加天数)/'diff'(计算天数差)/'weekday'(查星期几)。
    days: 天数。date_str: 日期字符串(YYYY-MM-DD格式)。"""
    try:
        base = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.now()
        if operation == "add":
            result = base + timedelta(days=days)
            weekday = "一二三四五六日"[result.weekday()]
            return json.dumps({"result": result.strftime("%Y-%m-%d"), "weekday": f"星期{weekday}"})
        elif operation == "diff":
            today = datetime.now()
            diff = (base - today).days
            return json.dumps({"from": today.strftime("%Y-%m-%d"), "to": date_str, "diff_days": diff})
        elif operation == "weekday":
            weekday = "一二三四五六日"[base.weekday()]
            return json.dumps({"date": date_str, "weekday": f"星期{weekday}"})
        else:
            return json.dumps({"error": f"未知操作: {operation}"})
    except ValueError as e:
        return json.dumps({"error": f"日期格式错误: {e}"})

# 汇总所有工具
ALL_TOOLS = [
    get_weather, calculator, search_knowledge,
    query_db, run_python, get_datetime, date_calculate,
]
TOOL_MAP = {t.name: t for t in ALL_TOOLS}

print(f"已定义 {len(ALL_TOOLS)} 个工具:")
for t in ALL_TOOLS:
    print(f"  🔧 {t.name}: {t.description[:45]}...")

# ============================================================================
# 2. 助手引擎
# ============================================================================
print("\n--- 2. 构建助手引擎 ---")

class FCAssistant:
    """Function Calling 智能助手"""

    SYSTEM_PROMPT = """你是"小函"，一个基于 Function Calling 的智能工作助手。

## 可用工具
1. **get_weather** - 查询城市天气
2. **calculator** - 数学计算
3. **search_knowledge** - 技术知识库搜索
4. **query_db** - 数据库查询（员工表employees、销售表sales）
5. **run_python** - 执行Python代码（受限沙箱）
6. **get_datetime** - 获取当前时间
7. **date_calculate** - 日期计算（加天数/算天数差/查星期）

## 工作原则
1. 需要数据时，必须使用工具获取，不要编造
2. 数学计算必须用 calculator 工具
3. 复杂分析可以用 run_python 编写代码
4. 回答简洁、准确、有条理
5. 多个独立查询可以并行执行
6. 不确定时诚实说明"""

    def __init__(self, model: str = "qwen2.5:7b"):
        self.llm = ChatOllama(model=model, temperature=0)
        self.llm_with_tools = self.llm.bind_tools(ALL_TOOLS)
        self.sessions: dict[str, list] = {}

    def _get_messages(self, session_id: str) -> list:
        if session_id not in self.sessions:
            self.sessions[session_id] = [SystemMessage(content=self.SYSTEM_PROMPT)]
        return self.sessions[session_id]

    def chat(self, message: str, session_id: str = "default",
             verbose: bool = True, max_iter: int = 6) -> str:
        """发送消息并获取回复"""
        messages = self._get_messages(session_id)
        messages.append(HumanMessage(content=message))

        for i in range(max_iter):
            response = self.llm_with_tools.invoke(messages)
            messages.append(response)

            if response.tool_calls:
                n = len(response.tool_calls)
                if verbose:
                    print(f"    [{i+1}] 调用 {n} 个工具{'（并行）' if n > 1 else ''}")

                for tc in response.tool_calls:
                    if verbose:
                        args_str = str(tc['args'])
                        print(f"      🔧 {tc['name']}({args_str[:60]}{'...' if len(args_str)>60 else ''})")

                    func = TOOL_MAP.get(tc["name"])
                    if func:
                        result = func.invoke(tc["args"])
                    else:
                        result = json.dumps({"error": f"未知工具: {tc['name']}"})

                    if verbose:
                        print(f"      📋 → {str(result)[:80]}...")

                    messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            else:
                if verbose:
                    print(f"    [{i+1}] 生成回答")
                return response.content

        return "达到最大迭代次数"

    def clear_session(self, session_id: str = "default"):
        self.sessions.pop(session_id, None)

    def get_history_length(self, session_id: str = "default") -> int:
        return len(self.sessions.get(session_id, []))

bot = FCAssistant()
print("FC 助手构建完成 ✓")

# ============================================================================
# 3. 功能测试
# ============================================================================
print("\n--- 3. 功能测试 ---")

# 3.1 天气查询
print("\n[测试1: 天气查询]")
print("  Q: 北京和上海天气怎么样？")
a = bot.chat("北京和上海天气怎么样？", session_id="t1")
print(f"  A: {a[:150]}...")

# 3.2 数学计算
print("\n[测试2: 数学计算]")
print("  Q: (256 + 512) * 1.5 / 3 等于多少？")
a = bot.chat("(256 + 512) * 1.5 / 3 等于多少？", session_id="t2")
print(f"  A: {a[:100]}...")

# 3.3 知识搜索
print("\n[测试3: 知识搜索]")
print("  Q: 什么是 Function Calling？和 MCP 有什么关系？")
a = bot.chat("什么是 Function Calling？和 MCP 有什么关系？", session_id="t3")
print(f"  A: {a[:200]}...")

# 3.4 数据库查询
print("\n[测试4: 数据库查询]")
print("  Q: 查一下各部门的平均薪资")
a = bot.chat("查一下各部门的平均薪资是多少？", session_id="t4")
print(f"  A: {a[:150]}...")

# 3.5 代码执行
print("\n[测试5: 代码执行]")
print("  Q: 用Python计算1到100中所有质数的和")
a = bot.chat("用Python计算1到100中所有质数的和", session_id="t5")
print(f"  A: {a[:150]}...")

# 3.6 日期计算
print("\n[测试6: 日期计算]")
print("  Q: 今天是几号？100天后是哪天？")
a = bot.chat("今天是几号？100天后是哪天？", session_id="t6")
print(f"  A: {a[:150]}...")

# ============================================================================
# 4. 多轮对话测试
# ============================================================================
print("\n\n--- 4. 多轮对话测试 ---")

session = "multi_turn"
conversations = [
    "各部门有多少人？",
    "哪个部门薪资最高？最高的那个人是谁？",
    "帮我算一下所有员工的总薪资",
]

for i, q in enumerate(conversations, 1):
    print(f"\n  [第{i}轮]")
    print(f"  Q: {q}")
    a = bot.chat(q, session_id=session)
    print(f"  A: {a[:150]}...")

# ============================================================================
# 5. 复合任务测试
# ============================================================================
print("\n\n--- 5. 复合任务测试 ---")

print("\n[复合: 天气+计算]")
print("  Q: 北京和哈尔滨温差多少度？")
a = bot.chat("北京和哈尔滨温差多少度？", session_id="comp1")
print(f"  A: {a[:150]}...")

print("\n[复合: 数据库+代码]")
print("  Q: 查询所有销售记录，算一下总销售额")
a = bot.chat("查询所有销售记录，算一下总销售额", session_id="comp2")
print(f"  A: {a[:150]}...")

# ============================================================================
# 6. 统计与回顾
# ============================================================================
print("\n\n--- 6. 项目架构回顾 ---")
print(f"""
┌────────────────────────────────────────────────────────┐
│              FC 智能助手 - 项目架构                     │
├────────────────────────────────────────────────────────┤
│                                                        │
│  FCAssistant（封装类）                                  │
│  ├── chat()           多轮工具调用对话                  │
│  ├── clear_session()  清除会话                         │
│  └── get_history_length()  消息数统计                  │
│                                                        │
│  工具集（7个）                                         │
│  ├── get_weather       天气查询                        │
│  ├── calculator        数学计算                        │
│  ├── search_knowledge  知识搜索                        │
│  ├── query_db          数据库查询                      │
│  ├── run_python        代码执行（沙箱）                │
│  ├── get_datetime      时间查询                        │
│  └── date_calculate    日期计算                        │
│                                                        │
│  核心流程                                              │
│  用户消息 → LLM(bind_tools) → tool_calls?              │
│  ├─ 有 → 执行工具 → ToolMessage → 回到 LLM            │
│  └─ 无 → 返回最终回答                                  │
│                                                        │
│  整合的知识点                                          │
│  ├── 第1课: FC原理（4步流程）                          │
│  ├── 第2课: OpenAI格式（tools + tool_choice）          │
│  ├── 第3课: Ollama本地调用（ChatOllama）               │
│  ├── 第4课: 并行调用 + 多轮对话                        │
│  ├── 第5课: 路由/嵌套/流式/结构化提取                  │
│  └── 第6课: 安全工具设计（验证/沙箱/错误处理）         │
│                                                        │
│  扩展方向                                              │
│  → 接入 MCP 协议（标准化工具连接）                     │
│  → 接入 LangGraph（图编排 + 人机协作）                 │
│  → 部署为 Web 服务（FastAPI + WebSocket）              │
│  → 添加 RAG 知识库（向量检索）                         │
└────────────────────────────────────────────────────────┘
""")

# 清理
os.unlink(demo_db)

print("=" * 60)
print("[完成] 第7课完成！你已经学会了：")
print("  [v] 设计多功能工具集（7个真实工具）")
print("  [v] 构建完整的 FC 助手引擎")
print("  [v] 并行工具调用 + 多轮对话记忆")
print("  [v] 复合任务处理（多工具协作）")
print("  [v] 安全控制（沙箱 + 输入验证）")
print("  [v] 整合前6课所有核心知识")
print("=" * 60)
print("\nFunction Calling 深入课程全部完成！🎉")
print("建议下一步学习：learn-mcp（Model Context Protocol）")
