import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：正则表达式实战练习
==============================================================================

本课是可运行的 Python 脚本，涵盖前4课所学的正则表达式知识。
直接运行即可看到结果：python 05_practice.py
==============================================================================
"""

import re

print("=" * 60)
print("正则表达式 - 实战练习")
print("=" * 60)

# ============================================================================
# 1. 基础匹配
# ============================================================================
print("\n--- 1. 基础匹配 ---")

text = "Python 3.12 发布于 2024-10-01，下载量超过 1000000 次"

# 提取所有数字
numbers = re.findall(r"\d+", text)
print(f"所有数字: {numbers}")
# ['3', '12', '2024', '10', '01', '1000000']

# 提取小数/版本号
versions = re.findall(r"\d+\.\d+", text)
print(f"版本号: {versions}")

# 提取日期
dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
print(f"日期: {dates}")

# 提取中文
chinese = re.findall(r"[\u4e00-\u9fff]+", text)
print(f"中文: {chinese}")

# ============================================================================
# 2. 数据验证
# ============================================================================
print("\n--- 2. 数据验证 ---")

def validate(pattern, text, name=""):
    """验证函数"""
    result = bool(re.match(pattern, text))
    icon = "✓" if result else "✗"
    print(f"  {icon} {name}: '{text}' → {'通过' if result else '未通过'}")
    return result

# 手机号验证
print("手机号验证:")
phone_pattern = r"^1[3-9]\d{9}$"
validate(phone_pattern, "13812345678", "有效手机号")
validate(phone_pattern, "12345678901", "12开头")
validate(phone_pattern, "1381234567", "只有10位")
validate(phone_pattern, "23812345678", "2开头")

# 邮箱验证
print("\n邮箱验证:")
email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
validate(email_pattern, "user@gmail.com", "标准邮箱")
validate(email_pattern, "test.name+tag@example.co.uk", "复杂邮箱")
validate(email_pattern, "@gmail.com", "无用户名")
validate(email_pattern, "user@", "无域名")

# 密码强度
print("\n密码强度验证 (至少8位，含大小写和数字):")
pwd_pattern = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,}$"
validate(pwd_pattern, "Abc12345", "合格密码")
validate(pwd_pattern, "abc12345", "无大写")
validate(pwd_pattern, "ABCD1234", "无小写")
validate(pwd_pattern, "Abcdefgh", "无数字")
validate(pwd_pattern, "Ab1", "太短")

# ============================================================================
# 3. 信息提取
# ============================================================================
print("\n--- 3. 信息提取 ---")

contacts = """
张三，手机：13812345678，邮箱：zhangsan@gmail.com
李四，手机：15987654321，邮箱：lisi@qq.com
王五，手机：18611112222，邮箱：wangwu@outlook.com
"""

# 提取所有手机号
phones = re.findall(r"1[3-9]\d{9}", contacts)
print(f"手机号: {phones}")

# 提取所有邮箱
emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", contacts)
print(f"邮箱: {emails}")

# 提取姓名+手机号（用捕获组）
name_phones = re.findall(r"([\u4e00-\u9fff]+)，手机：(\d{11})", contacts)
print(f"联系人: {name_phones}")

# 用命名捕获组
for m in re.finditer(
    r"(?P<name>[\u4e00-\u9fff]+)，手机：(?P<phone>\d{11})，邮箱：(?P<email>\S+)",
    contacts
):
    print(f"  {m.group('name')}: {m.group('phone')} / {m.group('email')}")

# ============================================================================
# 4. 文本替换
# ============================================================================
print("\n--- 4. 文本替换 ---")

# 手机号脱敏
def mask_phone(text):
    return re.sub(r"(1\d{2})\d{4}(\d{4})", r"\1****\2", text)

print(f"脱敏: {mask_phone('电话：13812345678')}")
print(f"脱敏: {mask_phone('联系 15987654321 或 18611112222')}")

# 邮箱脱敏
def mask_email(text):
    def _mask(m):
        user = m.group(1)
        domain = m.group(2)
        if len(user) <= 2:
            masked = user[0] + "***"
        else:
            masked = user[0] + "***" + user[-1]
        return f"{masked}@{domain}"
    return re.sub(r"([\w.+-]+)@([\w.-]+)", _mask, text)

print(f"脱敏: {mask_email('zhangsan@gmail.com')}")
print(f"脱敏: {mask_email('li@qq.com')}")

# 数字翻倍
def double_numbers(text):
    return re.sub(r"\d+", lambda m: str(int(m.group()) * 2), text)

print(f"翻倍: {double_numbers('价格 100 元，数量 5 个')}")

# 驼峰转下划线
def camel_to_snake(name):
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

for name in ["getUserName", "HTMLParser", "myAPIKey", "simpleTest"]:
    print(f"  {name} → {camel_to_snake(name)}")

# 下划线转驼峰
def snake_to_camel(name):
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])

for name in ["get_user_name", "my_api_key", "simple_test"]:
    print(f"  {name} → {snake_to_camel(name)}")

# ============================================================================
# 5. 日志分析
# ============================================================================
print("\n--- 5. 日志分析 ---")

logs = """
2024-01-15 14:30:00 INFO [app] 服务启动成功
2024-01-15 14:30:05 WARNING [db] 数据库连接池接近上限
2024-01-15 14:30:10 ERROR [api] 请求超时: /api/users
2024-01-15 14:30:15 INFO [app] 处理请求 200 OK
2024-01-15 14:30:20 ERROR [api] 参数错误: /api/chat
2024-01-15 14:30:25 INFO [app] 处理请求 200 OK
2024-01-15 14:31:00 WARNING [mem] 内存使用率 85%
"""

# 日志解析
log_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) \[(\w+)\] (.+)"
for m in re.finditer(log_pattern, logs):
    time, level, module, message = m.groups()
    if level in ("ERROR", "WARNING"):
        print(f"  [{level:>7}] {time} [{module}] {message}")

# 统计各级别日志数
from collections import Counter
levels = re.findall(r"\d{2}:\d{2}:\d{2} (\w+) ", logs)
counts = Counter(levels)
print(f"\n日志统计: {dict(counts)}")

# 提取所有 ERROR 的模块
error_modules = re.findall(r"ERROR \[(\w+)\]", logs)
print(f"出错模块: {error_modules}")

# ============================================================================
# 6. 文本清洗
# ============================================================================
print("\n--- 6. 文本清洗 ---")

# HTML 标签清除
html = "<p>Hello <b>World</b>! <a href='#'>Link</a></p>"
clean = re.sub(r"<[^>]+>", "", html)
print(f"去HTML: '{html}' → '{clean}'")

# 多余空白清理
messy = "  hello    world   foo   bar  "
clean = re.sub(r"\s+", " ", messy).strip()
print(f"清理空白: '{messy}' → '{clean}'")

# 提取 Markdown 链接
md_text = "查看 [Google](https://google.com) 和 [GitHub](https://github.com)"
links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", md_text)
print(f"Markdown链接:")
for text, url in links:
    print(f"  {text} → {url}")

# 提取 Python import
code = """
import os
import sys
from pathlib import Path
from collections import Counter, defaultdict
import re
"""
imports = re.findall(r"^(?:from\s+([\w.]+)\s+)?import\s+(.+)$", code, re.MULTILINE)
print(f"\nPython导入:")
for module, names in imports:
    if module:
        print(f"  from {module} import {names}")
    else:
        print(f"  import {names}")

# ============================================================================
# 7. 数据格式转换
# ============================================================================
print("\n--- 7. 格式转换 ---")

# 日期格式转换: 2024/01/15 → 2024年01月15日
dates_text = "开始: 2024/01/15, 结束: 2024/02/28"
converted = re.sub(
    r"(\d{4})/(\d{2})/(\d{2})",
    r"\1年\2月\3日",
    dates_text
)
print(f"日期转换: {converted}")

# 千分位格式化
def format_number(n):
    s = str(n)
    return re.sub(r"(?<=\d)(?=(\d{3})+$)", ",", s)

for n in [1000, 1234567, 9876543210]:
    print(f"  {n} → {format_number(n)}")

# CSV 解析（处理带引号的字段）
csv_line = 'Alice,"New York, USA",30,"Engineer, Senior"'
fields = re.findall(r'"([^"]*)"|\s*([^,]+)', csv_line)
parsed = [a or b for a, b in fields]
print(f"\nCSV解析: {parsed}")

# ============================================================================
# 8. 综合练习：URL 解析器
# ============================================================================
print("\n--- 8. URL 解析器 ---")

url_pattern = re.compile(r"""
    ^(?P<scheme>https?)://       # 协议
    (?P<host>[\w.-]+)            # 主机名
    (?::(?P<port>\d+))?          # 端口（可选）
    (?P<path>/[\w./%-]*)?        # 路径（可选）
    (?:\?(?P<query>[\w=&%+-]*))?  # 查询参数（可选）
    (?:\#(?P<fragment>\w*))?     # 片段（可选）
""", re.VERBOSE)

test_urls = [
    "https://www.google.com/search?q=python",
    "http://localhost:8000/api/v1/users",
    "https://example.com/path/to/page#section",
    "https://api.github.com:443/repos",
]

for url in test_urls:
    m = url_pattern.match(url)
    if m:
        parts = {k: v for k, v in m.groupdict().items() if v}
        print(f"  {url}")
        print(f"    → {parts}")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 60)
print("[完成] 正则表达式实战练习完成！")
print("  [v] 基础匹配（数字/日期/中文）")
print("  [v] 数据验证（手机/邮箱/密码）")
print("  [v] 信息提取（捕获组/命名组）")
print("  [v] 文本替换（脱敏/转换/清洗）")
print("  [v] 日志分析")
print("  [v] 格式转换（日期/千分位/CSV）")
print("  [v] URL 解析器")
print("=" * 60)
print("\nlearn-regex 课程完成！")
