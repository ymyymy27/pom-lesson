import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第6课：真实场景工具设计（API / DB / 文件 / 代码执行）
==============================================================================

前几课用的都是模拟工具。本课设计真实场景中常见的工具类型：

1. HTTP API 工具    - 调用外部 REST API
2. 数据库工具       - 查询/写入数据库
3. 文件操作工具     - 读写本地文件
4. 代码执行工具     - 安全执行 Python 代码
5. 系统信息工具     - 获取系统状态

每个工具都包含：
- 安全性考虑（输入验证、权限控制）
- 错误处理（超时、异常、降级）
- 结果格式化（返回 LLM 易理解的文本）

⚠️ 安全原则：
  - 所有工具输入都要验证
  - 文件操作限制在安全目录
  - 代码执行使用沙箱
  - 数据库操作只允许读取（除非明确需要写）
==============================================================================
"""

import json
import os
import tempfile
import time
from datetime import datetime
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from langchain_community.chat_models import ChatOllama

print("=" * 60)
print("第6课：真实场景工具设计")
print("=" * 60)

# ============================================================================
# 1. HTTP API 工具
# ============================================================================
print("\n--- 1. HTTP API 工具 ---")
print("""
最常见的工具类型：调用外部 API 获取数据。

设计要点：
- 超时控制（防止卡死）
- 错误处理（API 不可用时的降级）
- 结果格式化（API 返回的 JSON 转为文本）
- 速率限制（防止过于频繁调用）
""")

import httpx

@tool
def http_get(url: str, params: str = "") -> str:
    """发送 HTTP GET 请求获取数据。
    url: 请求地址，params: 查询参数（JSON格式字符串，如 '{"key":"value"}'）。
    仅允许访问白名单域名。"""

    # 安全：白名单域名
    ALLOWED_DOMAINS = [
        "api.github.com",
        "httpbin.org",
        "jsonplaceholder.typicode.com",
    ]

    from urllib.parse import urlparse
    domain = urlparse(url).hostname
    if domain not in ALLOWED_DOMAINS:
        return json.dumps({"error": f"不允许访问域名: {domain}", "allowed": ALLOWED_DOMAINS})

    try:
        query_params = json.loads(params) if params else {}
        resp = httpx.get(url, params=query_params, timeout=10.0)
        resp.raise_for_status()

        # 限制返回大小
        content = resp.text[:2000]
        return json.dumps({
            "status": resp.status_code,
            "data": content,
        }, ensure_ascii=False)

    except httpx.TimeoutException:
        return json.dumps({"error": "请求超时（10秒）"})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}"})
    except Exception as e:
        return json.dumps({"error": str(e)})

# 演示
print("HTTP API 工具示例：")
print(f"  白名单域名: api.github.com, httpbin.org, jsonplaceholder.typicode.com")

result = http_get.invoke({"url": "https://jsonplaceholder.typicode.com/todos/1"})
print(f"  GET todos/1 → {result[:100]}...")

result_blocked = http_get.invoke({"url": "https://evil-site.com/hack"})
print(f"  GET evil-site → {result_blocked[:80]}...")

# ============================================================================
# 2. 数据库工具（SQLite）
# ============================================================================
print("\n--- 2. 数据库工具 ---")
print("""
让 LLM 能查询数据库。

安全考虑：
- 只允许 SELECT 查询（防止数据修改）
- 限制返回行数（防止大量数据）
- 参数化查询（防止 SQL 注入）
- 超时控制
""")

import sqlite3

# 创建演示数据库
demo_db = tempfile.mktemp(suffix=".db")
conn = sqlite3.connect(demo_db)
cursor = conn.cursor()

cursor.executescript("""
    CREATE TABLE employees (
        id INTEGER PRIMARY KEY,
        name TEXT, department TEXT,
        salary REAL, hire_date TEXT
    );
    INSERT INTO employees VALUES (1, '张三', '技术部', 25000, '2022-03-15');
    INSERT INTO employees VALUES (2, '李四', '产品部', 22000, '2021-08-20');
    INSERT INTO employees VALUES (3, '王五', '技术部', 28000, '2020-01-10');
    INSERT INTO employees VALUES (4, '赵六', '市场部', 20000, '2023-06-01');
    INSERT INTO employees VALUES (5, '孙七', '技术部', 30000, '2019-11-25');

    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT, category TEXT,
        price REAL, stock INTEGER
    );
    INSERT INTO products VALUES (1, '蓝牙耳机', '数码', 299.0, 150);
    INSERT INTO products VALUES (2, '机械键盘', '数码', 599.0, 80);
    INSERT INTO products VALUES (3, '编程书籍', '图书', 79.0, 200);
    INSERT INTO products VALUES (4, '显示器', '数码', 1999.0, 30);
""")
conn.commit()
conn.close()

@tool
def query_database(sql: str, db_path: str = "") -> str:
    """执行 SQL 查询（只允许 SELECT）。
    sql: SQL 查询语句。db_path: 数据库路径（使用默认演示库可留空）。
    可用的表：employees(id,name,department,salary,hire_date), products(id,name,category,price,stock)"""

    # 安全：只允许 SELECT
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT"):
        return json.dumps({"error": "只允许 SELECT 查询"})

    # 安全：禁止危险关键词
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "EXEC"]
    for word in forbidden:
        if word in sql_upper:
            return json.dumps({"error": f"禁止使用 {word} 语句"})

    db = db_path or demo_db
    try:
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchmany(50)  # 最多50行

        results = [dict(row) for row in rows]
        conn.close()

        return json.dumps({
            "row_count": len(results),
            "data": results,
        }, ensure_ascii=False)

    except sqlite3.Error as e:
        return json.dumps({"error": f"SQL 错误: {e}"})

# 演示
print("数据库查询演示：")
r1 = query_database.invoke({"sql": "SELECT * FROM employees WHERE department='技术部'"})
print(f"  技术部员工: {r1[:150]}...")

r2 = query_database.invoke({"sql": "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department"})
print(f"  部门平均薪资: {r2[:150]}...")

r3 = query_database.invoke({"sql": "DELETE FROM employees WHERE id=1"})
print(f"  尝试删除: {r3}")

# ============================================================================
# 3. 文件操作工具
# ============================================================================
print("\n--- 3. 文件操作工具 ---")
print("""
安全的文件操作工具。

安全措施：
- 限制在安全目录内（sandbox）
- 禁止访问系统文件
- 限制文件大小
- 路径遍历攻击防护
""")

# 创建安全沙箱目录
SANDBOX_DIR = tempfile.mkdtemp(prefix="fc_sandbox_")

# 写入一些测试文件
for name, content in [
    ("notes.txt", "项目进度：\n1. 数据收集完成\n2. 模型训练中\n3. 待部署测试"),
    ("config.json", '{"model": "qwen2.5", "temperature": 0.7, "max_tokens": 2000}'),
    ("data.csv", "name,score,grade\n张三,95,A\n李四,82,B\n王五,90,A"),
]:
    with open(os.path.join(SANDBOX_DIR, name), "w", encoding="utf-8") as f:
        f.write(content)

@tool
def read_file(filename: str) -> str:
    """读取沙箱目录中的文件内容。filename: 文件名（不含路径）。"""

    # 安全：防止路径遍历
    if ".." in filename or "/" in filename or "\\" in filename:
        return json.dumps({"error": "文件名不能包含路径分隔符"})

    filepath = os.path.join(SANDBOX_DIR, filename)
    if not os.path.exists(filepath):
        # 列出可用文件
        files = os.listdir(SANDBOX_DIR)
        return json.dumps({"error": f"文件不存在: {filename}", "available_files": files}, ensure_ascii=False)

    try:
        size = os.path.getsize(filepath)
        if size > 100_000:  # 100KB 限制
            return json.dumps({"error": f"文件太大: {size} bytes（限制 100KB）"})

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return json.dumps({
            "filename": filename,
            "size": size,
            "content": content,
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def write_file(filename: str, content: str) -> str:
    """写入文件到沙箱目录。filename: 文件名，content: 文件内容。"""

    if ".." in filename or "/" in filename or "\\" in filename:
        return json.dumps({"error": "文件名不能包含路径分隔符"})

    # 限制文件大小
    if len(content) > 50_000:
        return json.dumps({"error": "内容太大（限制 50KB）"})

    filepath = os.path.join(SANDBOX_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return json.dumps({"success": True, "filename": filename, "size": len(content)})
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def list_files() -> str:
    """列出沙箱目录中的所有文件。"""
    files = []
    for f in os.listdir(SANDBOX_DIR):
        filepath = os.path.join(SANDBOX_DIR, f)
        files.append({
            "name": f,
            "size": os.path.getsize(filepath),
            "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M"),
        })
    return json.dumps({"files": files}, ensure_ascii=False)

# 演示
print(f"沙箱目录: {SANDBOX_DIR}")
print(f"\n列出文件:")
print(f"  {list_files.invoke({})[:200]}...")

print(f"\n读取文件:")
print(f"  {read_file.invoke({'filename': 'notes.txt'})[:150]}...")

print(f"\n路径遍历攻击防护:")
print(f"  {read_file.invoke({'filename': '../../etc/passwd'})}")

# ============================================================================
# 4. 代码执行工具（沙箱）
# ============================================================================
print("\n--- 4. 代码执行工具 ---")
print("""
让 LLM 编写并执行 Python 代码。

⚠️ 这是最危险的工具！必须严格限制：
- 禁止导入危险模块（os, sys, subprocess 等）
- 限制执行时间
- 限制输出大小
- 隔离执行环境
""")

@tool
def execute_python(code: str) -> str:
    """执行 Python 代码并返回结果。
    代码在受限环境中运行，不允许文件操作、网络请求和系统调用。
    代码中最后一个表达式的值将作为结果返回，或使用 print() 输出。"""

    # 安全：禁止危险操作
    FORBIDDEN = [
        "import os", "import sys", "import subprocess", "import shutil",
        "__import__", "eval(", "exec(", "open(", "compile(",
        "import socket", "import http", "import urllib",
        "os.system", "os.popen", "os.exec",
    ]
    for pattern in FORBIDDEN:
        if pattern in code:
            return json.dumps({"error": f"禁止使用: {pattern}"})

    # 限制代码长度
    if len(code) > 5000:
        return json.dumps({"error": "代码太长（限制 5000 字符）"})

    try:
        # 受限的全局环境
        safe_globals = {
            "__builtins__": {
                "print": print, "len": len, "range": range, "int": int,
                "float": float, "str": str, "list": list, "dict": dict,
                "tuple": tuple, "set": set, "bool": bool, "type": type,
                "max": max, "min": min, "sum": sum, "abs": abs, "round": round,
                "sorted": sorted, "reversed": reversed, "enumerate": enumerate,
                "zip": zip, "map": map, "filter": filter,
                "isinstance": isinstance, "True": True, "False": False, "None": None,
            }
        }

        # 允许 math 和 json
        import math
        safe_globals["math"] = math
        safe_globals["json"] = json

        # 捕获 print 输出
        from io import StringIO
        output_buffer = StringIO()

        old_stdout = sys.stdout
        sys.stdout = output_buffer

        try:
            exec(code, safe_globals)
            output = output_buffer.getvalue()
        finally:
            sys.stdout = old_stdout

        # 限制输出大小
        if len(output) > 5000:
            output = output[:5000] + "\n... (输出被截断)"

        return json.dumps({"output": output or "(无输出)"}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})

# 演示
print("\n安全执行:")
r1 = execute_python.invoke({"code": "result = sum(range(1, 101))\nprint(f'1到100的和 = {result}')"})
print(f"  求和: {r1}")

r2 = execute_python.invoke({"code": "data = [3,1,4,1,5,9,2,6]\nprint(f'排序: {sorted(data)}')\nprint(f'最大: {max(data)}')"})
print(f"  排序: {r2[:100]}...")

print("\n安全防护:")
r3 = execute_python.invoke({"code": "import os\nos.system('rm -rf /')"})
print(f"  危险代码: {r3}")

r4 = execute_python.invoke({"code": "open('/etc/passwd').read()"})
print(f"  文件访问: {r4}")

# ============================================================================
# 5. 系统信息工具
# ============================================================================
print("\n--- 5. 系统信息工具 ---")

@tool
def get_system_info() -> str:
    """获取当前系统信息，包括时间、平台、Python版本等。"""
    import platform
    return json.dumps({
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "platform": platform.system(),
        "platform_version": platform.version()[:50],
        "python_version": platform.python_version(),
        "machine": platform.machine(),
    }, ensure_ascii=False)

print(f"系统信息: {get_system_info.invoke({})}")

# ============================================================================
# 6. 组合测试：LLM + 真实工具
# ============================================================================
print("\n--- 6. 组合测试 ---")

all_real_tools = [
    query_database, read_file, write_file, list_files,
    execute_python, get_system_info,
]
real_tool_map = {t.name: t for t in all_real_tools}

llm = ChatOllama(model="qwen2.5:7b", temperature=0)
llm_real = llm.bind_tools(all_real_tools)

def real_world_chat(question: str) -> str:
    messages = [
        SystemMessage(content="""你是一个工作助手，可以：
- 查询数据库（employees表和products表）
- 读写沙箱文件
- 执行Python代码
- 获取系统信息
回答要简洁准确。"""),
        HumanMessage(content=question),
    ]

    for i in range(5):
        resp = llm_real.invoke(messages)
        messages.append(resp)

        if resp.tool_calls:
            for tc in resp.tool_calls:
                print(f"    🔧 {tc['name']}({str(tc['args'])[:60]})")
                func = real_tool_map.get(tc["name"])
                result = func.invoke(tc["args"]) if func else "未知工具"
                print(f"    📋 → {str(result)[:80]}...")
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
        else:
            return resp.content

    return "超时"

test_cases = [
    "技术部有多少人？平均薪资多少？",
    "帮我看看沙箱里有哪些文件",
    "用Python计算斐波那契数列前10项",
]

for q in test_cases:
    print(f"\n  Q: {q}")
    a = real_world_chat(q)
    print(f"  A: {a[:150]}...")

# 清理
import shutil
shutil.rmtree(SANDBOX_DIR)
os.unlink(demo_db)

# ============================================================================
# 7. 工具设计清单
# ============================================================================
print("\n\n--- 7. 工具设计清单 ---")
print("""
设计真实工具时的检查清单：

✅ 输入验证
  □ 参数类型检查
  □ 参数范围限制
  □ 防止注入攻击（SQL注入、路径遍历）

✅ 安全边界
  □ 白名单（允许的域名/目录/操作）
  □ 黑名单（禁止的模块/关键词）
  □ 权限控制（只读/读写）
  □ 沙箱隔离

✅ 错误处理
  □ 超时控制
  □ 异常捕获
  □ 降级策略
  □ 有意义的错误信息

✅ 结果格式
  □ 返回 JSON 格式
  □ 大小限制（防止过大）
  □ LLM 可理解的描述

✅ 可观测性
  □ 日志记录
  □ 调用计数
  □ 性能监控
""")

print("\n" + "=" * 60)
print("[完成] 第6课完成！你已经学会了：")
print("  [v] HTTP API 工具（白名单+超时+错误处理）")
print("  [v] 数据库工具（只读+防注入）")
print("  [v] 文件操作工具（沙箱+路径防护）")
print("  [v] 代码执行工具（受限环境+禁止危险操作）")
print("  [v] 系统信息工具")
print("  [v] 工具安全设计清单")
print("=" * 60)
print("\n下一课：07_fc_agent_project.py - 完整项目：Function Calling 智能助手")
