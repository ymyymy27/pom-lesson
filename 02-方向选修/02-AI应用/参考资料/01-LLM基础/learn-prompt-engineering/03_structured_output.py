import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：结构化输出（JSON / XML / 表格 / 代码）
==============================================================================

让 LLM 输出结构化数据是实际应用的关键。
非结构化文本难以被程序解析和使用。

本课内容：
1. JSON 输出
2. JSON Schema 约束
3. XML / Markdown 表格输出
4. 代码输出
5. 输出解析与错误处理
6. OpenAI Structured Outputs
==============================================================================
"""

import json
import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"

def chat(prompt: str, system: str = "", temperature: float = 0.0) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL, "messages": messages, "stream": False,
            "options": {"temperature": temperature, "num_predict": 800}
        }, timeout=30.0)
        return resp.json().get("message", {}).get("content", "")
    except:
        return '[{"mock": true}]'

print("=" * 60)
print("第3课：结构化输出")
print("=" * 60)

# ============================================================================
# 1. JSON 输出
# ============================================================================
print("\n--- 1. JSON 输出 ---")
print("""
让 LLM 输出 JSON 是最常见的结构化需求。

关键技巧：
1. 明确说"输出 JSON"
2. 给出完整的字段说明
3. 给出一个示例
4. 说"只输出 JSON，不要其他内容"

模板：
```
分析以下文本，以 JSON 格式输出：
{
  "sentiment": "positive/negative/neutral",
  "confidence": 0.0到1.0的浮点数,
  "keywords": ["关键词数组"],
  "summary": "一句话摘要"
}

只输出 JSON，不要其他任何文字。

文本：{text}
```
""")

# JSON 输出实验
json_prompt = """分析以下产品评论，以 JSON 格式输出。

输出格式：
{
  "sentiment": "positive/negative/neutral",
  "confidence": 0.0-1.0,
  "aspects": [{"aspect": "方面", "opinion": "评价", "sentiment": "情感"}],
  "summary": "一句话总结"
}

只输出 JSON，不要其他任何文字。

评论：这款耳机音质非常棒，低音浑厚。但佩戴时间长了耳朵会疼，而且价格偏贵。"""

result = chat(json_prompt)
print(f"JSON 输出:\n{result[:300]}")

# 尝试解析
try:
    # 提取 JSON（处理可能的 markdown 包裹）
    json_str = result.strip()
    if json_str.startswith("```"):
        json_str = json_str.split("```")[1]
        if json_str.startswith("json"):
            json_str = json_str[4:]
    parsed = json.loads(json_str.strip())
    print(f"\n解析成功 ✓")
    print(f"  情感: {parsed.get('sentiment')}")
    print(f"  置信度: {parsed.get('confidence')}")
    print(f"  方面数: {len(parsed.get('aspects', []))}")
except json.JSONDecodeError as e:
    print(f"\n解析失败: {e}")
    print("  这说明需要更强的格式约束或后处理")

# ============================================================================
# 2. JSON Schema 约束
# ============================================================================
print("\n--- 2. JSON Schema ---")
print("""
给出完整 JSON Schema 可以大幅提高输出准确率：

```python
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "姓名"},
        "age": {"type": "integer", "minimum": 0, "maximum": 150},
        "email": {"type": "string", "format": "email"},
        "skills": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 5
        }
    },
    "required": ["name", "age"]
}
```

在 Prompt 中使用 Schema：
  "请按照以下 JSON Schema 输出：{schema}"

Ollama 也支持 JSON 模式：
```python
resp = httpx.post(url, json={
    "model": "qwen2.5:7b",
    "messages": [...],
    "format": "json",  # 强制 JSON 输出
})
```
""")

# Ollama JSON 模式
def chat_json(prompt: str, system: str = "") -> dict:
    """强制 JSON 输出"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL, "messages": messages, "stream": False,
            "format": "json",
            "options": {"temperature": 0.0, "num_predict": 500}
        }, timeout=30.0)
        content = resp.json().get("message", {}).get("content", "{}")
        return json.loads(content)
    except:
        return {"error": "解析失败"}

result = chat_json(
    "提取以下文本中的人物信息：张三，25岁，在北京工作，电话13800138000。"
    "输出JSON：{name, age, city, phone}",
    system="你是数据提取专家，只输出JSON。"
)
print(f"JSON 模式输出: {json.dumps(result, ensure_ascii=False, indent=2)}")

# ============================================================================
# 3. XML / Markdown 表格
# ============================================================================
print("\n--- 3. XML / 表格 ---")
print("""
有时 XML 或 Markdown 表格比 JSON 更合适。

XML 输出（适合嵌套数据）：
```
请以 XML 格式输出：
<analysis>
  <sentiment>positive</sentiment>
  <aspects>
    <aspect name="音质" sentiment="positive">非常棒</aspect>
  </aspects>
</analysis>
```

Markdown 表格（适合展示给人看）：
```
请以 Markdown 表格输出对比结果：
| 特性 | 方案A | 方案B |
|------|-------|-------|
| 价格 | ...   | ...   |
```
""")

table_prompt = """对比 Python、Java、Go 三种语言，以 Markdown 表格格式输出。

对比维度：学习难度、运行速度、生态丰富度、适用场景。
每个维度用 ★ 表示评分（1-5星）。"""

result = chat(table_prompt)
print(f"表格输出:\n{result[:400]}")

# ============================================================================
# 4. 代码输出
# ============================================================================
print("\n\n--- 4. 代码输出 ---")
print("""
让 LLM 生成可执行代码的技巧：

1. 指定语言和版本
2. 指定风格（类型注解/文档字符串/注释）
3. 要求处理边界情况
4. 要求附带测试用例

模板：
```
用 Python 3.10+ 实现以下函数：

函数名：extract_emails
功能：从文本中提取所有邮箱地址
参数：text (str)
返回：list[str]

要求：
1. 使用正则表达式
2. 包含类型注解
3. 包含 docstring
4. 处理边界情况（空字符串、无邮箱）
5. 附带 3 个测试用例

只输出代码，使用 ```python 包裹。
```
""")

code_prompt = """用 Python 实现一个函数：

函数名：parse_duration
功能：将时间字符串（如 "2h30m", "1h", "45m", "1h15m30s"）转为总秒数
参数：duration_str (str)
返回：int

要求：
1. 使用正则表达式
2. 包含类型注解和 docstring
3. 处理无效输入（返回 0）
4. 附带 3 个 assert 测试

只输出代码。"""

result = chat(code_prompt)
print(f"代码输出:\n{result[:400]}...")

# ============================================================================
# 5. 输出解析与错误处理
# ============================================================================
print("\n\n--- 5. 解析与错误处理 ---")
print("""
LLM 输出不总是完美的，需要鲁棒的解析。

常见问题及处理：
┌────────────────────────┬──────────────────────────────┐
│  问题                   │  解决方案                     │
├────────────────────────┼──────────────────────────────┤
│  JSON 被 ``` 包裹      │  strip掉 markdown 代码块     │
│  多余的解释文字        │  提取第一个 { 到最后一个 }   │
│  字段名不一致          │  大小写/下划线容错           │
│  缺少必填字段          │  设置默认值                   │
│  数据类型错误          │  类型转换                     │
│  完全无法解析          │  重试（换temperature）        │
└────────────────────────┴──────────────────────────────┘
""")

def robust_parse_json(text: str) -> dict:
    """鲁棒的 JSON 解析"""
    # 1. 直接尝试
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. 去除 markdown 代码块
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            try:
                return json.loads(part)
            except json.JSONDecodeError:
                continue

    # 3. 提取 { 到 }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass

    # 4. 提取 [ 到 ]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass

    return {"_raw": text, "_error": "无法解析"}

# 测试鲁棒解析
test_cases = [
    '{"name": "张三", "age": 25}',
    '```json\n{"name": "李四", "age": 30}\n```',
    '分析结果如下：\n{"sentiment": "positive", "score": 0.9}\n以上是分析。',
    '这不是JSON',
]

print("鲁棒解析测试:")
for tc in test_cases:
    parsed = robust_parse_json(tc)
    status = "✅" if "_error" not in parsed else "❌"
    print(f"  {status} \"{tc[:40]}{'...' if len(tc)>40 else ''}\"")
    print(f"     → {parsed}")

# ============================================================================
# 6. OpenAI Structured Outputs
# ============================================================================
print("\n--- 6. OpenAI Structured Outputs ---")
print("""
OpenAI 提供了原生的结构化输出支持（最可靠）：

```python
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

# 用 Pydantic 定义输出结构
class SentimentResult(BaseModel):
    sentiment: str       # positive/negative/neutral
    confidence: float    # 0.0-1.0
    keywords: list[str]  # 关键词
    summary: str         # 摘要

# Structured Outputs
response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "分析评论情感"},
        {"role": "user", "content": "这款耳机音质很好但偏贵"}
    ],
    response_format=SentimentResult,  # 指定输出类型
)

result = response.choices[0].message.parsed
# result 是 SentimentResult 对象，字段和类型都保证正确！
print(result.sentiment)    # "positive"
print(result.confidence)   # 0.7
print(result.keywords)     # ["音质", "偏贵"]
```

response_format 也可以用 JSON Schema：
```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[...],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "sentiment",
            "schema": {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                    "score": {"type": "number"}
                },
                "required": ["sentiment", "score"]
            }
        }
    }
)
```

这是最推荐的方式——100% 保证输出符合 Schema。
""")

print("\n" + "=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] JSON 输出 Prompt 设计")
print("  [v] JSON Schema 约束")
print("  [v] XML / Markdown 表格输出")
print("  [v] 代码生成 Prompt 模板")
print("  [v] 鲁棒的输出解析（容错处理）")
print("  [v] OpenAI Structured Outputs（原生保证）")
print("=" * 60)
print("\n下一课：04_role_and_system.py - 角色设计与 System Prompt")
