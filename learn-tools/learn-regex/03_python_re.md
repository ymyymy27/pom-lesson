# 第3课：Python re 模块

## 1. 导入和基本概念

```python
import re

# Python 正则字符串建议用 r"..." 原始字符串
# 避免反斜杠转义问题
pattern = r"\d+"        # ✓ 推荐
pattern = "\\d+"        # ✗ 容易出错
```

### 为什么用 r"..."？

```python
# 不用 r：\d 会被 Python 解释为转义
print("\d")        # → \d（Python 不认识，原样输出，但不安全）
print("\n")        # → 换行（被 Python 转义了！）

# 用 r：所有字符原样传给 re 模块
print(r"\d")       # → \d
print(r"\n")       # → \n（不是换行，是两个字符）
```

---

## 2. 核心函数

### 2.1 re.match() - 从开头匹配

```python
import re

# match 只从字符串开头匹配
result = re.match(r"\d+", "123abc")
print(result.group())    # '123'

result = re.match(r"\d+", "abc123")
print(result)            # None（开头不是数字）
```

### 2.2 re.search() - 搜索第一个匹配

```python
# search 搜索整个字符串，返回第一个匹配
result = re.search(r"\d+", "abc123def456")
print(result.group())    # '123'（第一个匹配）
print(result.start())    # 3（匹配开始位置）
print(result.end())      # 6（匹配结束位置）
print(result.span())     # (3, 6)
```

### 2.3 re.findall() - 找所有匹配

```python
# findall 返回所有匹配的列表
results = re.findall(r"\d+", "abc123def456ghi789")
print(results)    # ['123', '456', '789']

# 有捕获组时，返回捕获的内容
results = re.findall(r"(\d+)-(\d+)", "12-34 56-78")
print(results)    # [('12', '34'), ('56', '78')]

# 单个捕获组，返回字符串列表
results = re.findall(r"@(\w+)", "email@gmail.com cc@qq.com")
print(results)    # ['gmail', 'qq']
```

### 2.4 re.finditer() - 迭代所有匹配

```python
# finditer 返回迭代器，每个元素是 Match 对象（比 findall 更灵活）
for match in re.finditer(r"\d+", "abc123def456"):
    print(f"匹配: {match.group()}, 位置: {match.span()}")
# 匹配: 123, 位置: (3, 6)
# 匹配: 456, 位置: (9, 12)
```

### 2.5 re.sub() - 替换

```python
# 基本替换
result = re.sub(r"\d+", "NUM", "abc123def456")
print(result)    # 'abcNUMdefNUM'

# 限制替换次数
result = re.sub(r"\d+", "NUM", "abc123def456", count=1)
print(result)    # 'abcNUMdef456'

# 用函数替换（更灵活）
def double_number(match):
    num = int(match.group())
    return str(num * 2)

result = re.sub(r"\d+", double_number, "价格: 100元, 数量: 5个")
print(result)    # '价格: 200元, 数量: 10个'

# 用捕获组替换
result = re.sub(r"(\w+)@(\w+)", r"\1 at \2", "alice@gmail.com")
print(result)    # 'alice at gmail.com'
```

### 2.6 re.split() - 分割

```python
# 按正则分割
result = re.split(r"[,;，；\s]+", "苹果, 香蕉; 橙子，葡萄  西瓜")
print(result)    # ['苹果', '香蕉', '橙子', '葡萄', '西瓜']

# 按多种分隔符分割
result = re.split(r"[-/.]", "2024-01-15")
print(result)    # ['2024', '01', '15']

# 保留分隔符（用捕获组）
result = re.split(r"([,;])", "a,b;c,d")
print(result)    # ['a', ',', 'b', ';', 'c', ',', 'd']

# 限制分割次数
result = re.split(r"\s+", "a b c d e", maxsplit=2)
print(result)    # ['a', 'b', 'c d e']
```

---

## 3. Match 对象

```python
import re

text = "生日: 2024-01-15, 电话: 13812345678"
pattern = r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"

match = re.search(pattern, text)

if match:
    # 基本方法
    print(match.group())       # '2024-01-15'（完整匹配）
    print(match.group(0))      # '2024-01-15'（同上）
    print(match.group(1))      # '2024'（第1个捕获组）
    print(match.group(2))      # '01'
    print(match.group(3))      # '15'

    # 命名捕获组
    print(match.group('year'))   # '2024'
    print(match.group('month'))  # '01'
    print(match.group('day'))    # '15'

    # 其他方法
    print(match.groups())      # ('2024', '01', '15')
    print(match.groupdict())   # {'year': '2024', 'month': '01', 'day': '15'}
    print(match.span())        # (4, 14)
    print(match.start())       # 4
    print(match.end())         # 14
```

---

## 4. 编译正则（提高性能）

```python
# 如果同一个正则要用很多次，先编译
pattern = re.compile(r"\d{4}-\d{2}-\d{2}")

# 编译后的对象有同样的方法
pattern.match(text)
pattern.search(text)
pattern.findall(text)
pattern.sub(replacement, text)

# 带修饰符编译
pattern = re.compile(r"hello", re.IGNORECASE)
print(pattern.findall("Hello HELLO hello"))
# ['Hello', 'HELLO', 'hello']
```

### 修饰符

```python
re.IGNORECASE  (re.I)   # 忽略大小写
re.MULTILINE   (re.M)   # 多行模式（^$ 匹配每行首尾）
re.DOTALL      (re.S)   # . 匹配换行符
re.VERBOSE     (re.X)   # 详细模式（可以加注释和空白）

# 组合使用
pattern = re.compile(r"pattern", re.I | re.M)

# VERBOSE 模式（写复杂正则时很有用）
email_pattern = re.compile(r"""
    [\w.+-]+        # 用户名部分
    @               # @ 符号
    [\w-]+          # 域名
    \.              # 点号
    [\w.]+          # 顶级域名
""", re.VERBOSE)
```

---

## 5. 常用模式对照

| 任务 | 代码 |
|------|------|
| 提取所有数字 | `re.findall(r'\d+', text)` |
| 提取所有邮箱 | `re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', text)` |
| 提取所有URL | `re.findall(r'https?://\S+', text)` |
| 验证手机号 | `re.match(r'^1[3-9]\d{9}$', phone)` |
| 替换多个空格为一个 | `re.sub(r'\s+', ' ', text)` |
| 删除HTML标签 | `re.sub(r'<[^>]+>', '', html)` |
| 提取括号内容 | `re.findall(r'\(([^)]+)\)', text)` |
| 驼峰转下划线 | `re.sub(r'(?<=[a-z])(?=[A-Z])', '_', name).lower()` |
| 分割中英文混合 | `re.findall(r'[\u4e00-\u9fff]+\|[a-zA-Z]+', text)` |

---

## 6. 注意事项

### 6.1 match vs search

```python
# match：只看开头
re.match(r"\d+", "abc123")   → None
re.search(r"\d+", "abc123")  → '123'

# 建议：大多数场景用 search，需要"完整匹配"时用 match + $
re.match(r"^\d+$", "123")    → 匹配（整个字符串都是数字）
```

### 6.2 findall 有捕获组的坑

```python
# 无捕获组：返回完整匹配
re.findall(r"\d+-\d+", "12-34 56-78")
# ['12-34', '56-78']

# 有捕获组：只返回捕获的内容！
re.findall(r"(\d+)-(\d+)", "12-34 56-78")
# [('12', '34'), ('56', '78')]

# 想要完整匹配又想要分组？用非捕获组
re.findall(r"(?:\d+)-(?:\d+)", "12-34 56-78")
# ['12-34', '56-78']
```

### 6.3 贪婪匹配的坑

```python
# 常见错误：提取引号内容
text = '"hello" and "world"'

re.findall(r'"(.+)"', text)     # ['"hello" and "world"']  ← 贪婪！
re.findall(r'"(.+?)"', text)    # ['hello', 'world']       ← 懒惰 ✓
re.findall(r'"([^"]+)"', text)  # ['hello', 'world']       ← 排除法 ✓
```

---

## 7. 动手练习

在 Python 中练习：

```python
import re

text = """
联系人：张三，电话：13812345678，邮箱：zhangsan@gmail.com
联系人：李四，电话：15987654321，邮箱：lisi@qq.com
日期：2024-01-15，金额：$100.50
网址：https://github.com 和 http://example.com
"""

# 1. 提取所有手机号
# 2. 提取所有邮箱
# 3. 提取所有联系人姓名
# 4. 提取日期的年、月、日
# 5. 提取所有 URL
# 6. 把手机号中间4位替换为 ****
```

---

## 8. 小结

| 函数 | 用途 | 返回 |
|------|------|------|
| `re.match()` | 从开头匹配 | Match 或 None |
| `re.search()` | 搜索第一个 | Match 或 None |
| `re.findall()` | 找所有匹配 | 列表 |
| `re.finditer()` | 迭代所有 | 迭代器 |
| `re.sub()` | 替换 | 新字符串 |
| `re.split()` | 分割 | 列表 |
| `re.compile()` | 编译正则 | Pattern 对象 |

---

**下一课：** `04_common_patterns.md` - 常用正则模式集锦
