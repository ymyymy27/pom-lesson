import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第1课：Prompt 基础
==============================================================================

Prompt = 给 LLM 的指令/输入
Prompt Engineering = 设计最优指令的技术

好的 Prompt 可以让同一个模型的输出质量天差地别。

本课内容：
1. Prompt 基本结构
2. 三大核心原则
3. 参数控制（Temperature/Top-p/Max tokens）
4. Tokenizer 与 Token 计费
5. System / User / Assistant 消息
6. 第一个 Prompt 实验
==============================================================================
"""

import json
import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"

print("=" * 60)
print("第1课：Prompt 基础")
print("=" * 60)

# ============================================================================
# 1. Prompt 基本结构
# ============================================================================
print("\n--- 1. Prompt 结构 ---")
print("""
一个好的 Prompt 包含以下要素：

  ┌──────────────────────────────────────────────────────┐
  │  ① 角色定义     你是一个...专家/助手               │
  │  ② 任务描述     请你做...                           │
  │  ③ 上下文       给定以下信息/背景...                │
  │  ④ 输入数据     具体要处理的内容                    │
  │  ⑤ 输出格式     请以 JSON/列表/表格 格式输出       │
  │  ⑥ 约束条件     不要.../注意.../限制...            │
  │  ⑦ 示例（可选） 例如：输入→输出                    │
  └──────────────────────────────────────────────────────┘

不需要每次都包含全部要素，根据任务复杂度选择。

简单任务（只需②）：
  "把这段话翻译成英文"

中等任务（①②⑤）：
  "你是翻译专家。请翻译以下文本，以 JSON 格式输出"

复杂任务（全部要素）：
  "你是资深金融分析师(①)。分析以下财报数据(②)，
   背景：Q3整体市场下行(③)。数据：...(④)
   以表格列出关键指标(⑤)。不要给投资建议(⑥)。
   示例格式：...(⑦)"
""")

# ============================================================================
# 2. 三大核心原则
# ============================================================================
print("\n--- 2. 三大原则 ---")
print("""
原则1：清晰具体（Be Specific）

  ❌ "帮我写点关于 AI 的东西"
  ✅ "写一篇 300 字的科普文章，面向非技术读者介绍大语言模型的工作原理，
     使用 2 个生活化比喻，分 3 段。"

原则2：提供足够上下文（Give Context）

  ❌ "这段代码有什么问题？"
  ✅ "以下 Python 代码在处理 5GB 文件时报 MemoryError，
     服务器内存 8GB。请分析原因并给出优化方案。"

原则3：指定输出格式（Define Output）

  ❌ "分析这条评论"
  ✅ "分析评论的情感，输出 JSON：
     {\"sentiment\": \"positive/negative/neutral\",
      \"confidence\": 0.0-1.0,
      \"keywords\": [\"关键词\"]}"
""")

# ============================================================================
# 3. 参数控制
# ============================================================================
print("\n--- 3. 参数控制 ---")
print("""
LLM 生成的核心参数：

┌──────────────────┬──────────────────────────────────────┐
│  参数             │  说明                                 │
├──────────────────┼──────────────────────────────────────┤
│  temperature     │  随机性，0=确定性，1=创意性           │
│                  │  0.0: 事实问答/数据提取               │
│                  │  0.3: 翻译/摘要                       │
│                  │  0.7: 通用对话（默认）                │
│                  │  1.0: 创意写作/头脑风暴               │
├──────────────────┼──────────────────────────────────────┤
│  top_p           │  核采样，0.1=保守，1.0=完整分布      │
│                  │  通常和 temperature 二选一调节        │
├──────────────────┼──────────────────────────────────────┤
│  max_tokens      │  最大输出 token 数                    │
│                  │  不是越大越好，避免浪费               │
├──────────────────┼──────────────────────────────────────┤
│  frequency_penalty│ 重复惩罚，减少重复词语               │
│  presence_penalty │ 话题惩罚，鼓励谈论新话题             │
└──────────────────┴──────────────────────────────────────┘
""")

# 封装调用函数
def chat(prompt: str, system: str = "", temperature: float = 0.7,
         max_tokens: int = 500) -> str:
    """调用 Ollama 进行对话"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }, timeout=30.0)
        return resp.json().get("message", {}).get("content", "")
    except Exception as e:
        return f"[连接失败: {e}]"

# temperature 对比实验
print("Temperature 对比实验:")
prompt = "用一句话形容人工智能"
for temp in [0.0, 0.5, 1.0]:
    result = chat(prompt, temperature=temp, max_tokens=100)
    print(f"  temp={temp}: {result[:80]}...")

# ============================================================================
# 4. Tokenizer
# ============================================================================
print("\n\n--- 4. Tokenizer ---")
print("""
LLM 处理的不是"字"而是"token"。

Token ≈ 词的片段
  英文: 1 word ≈ 1.3 tokens（"hello"=1, "unhappiness"=3）
  中文: 1 字 ≈ 1-2 tokens（"你好"=2, "人工智能"=2-4）

计费：按输入+输出 token 总数计费
""")

try:
    import tiktoken
    enc = tiktoken.encoding_for_model("gpt-4")

    texts = [
        "Hello, world!",
        "你好，世界！",
        "Prompt Engineering is the art of communicating with AI models effectively.",
        "大语言模型通过预测下一个词元来生成文本，这是自回归的核心原理。",
    ]

    print("Token 计数演示（GPT-4 tokenizer）:")
    for text in texts:
        tokens = enc.encode(text)
        print(f"  \"{text[:40]}{'...' if len(text)>40 else ''}\"")
        print(f"    字符数: {len(text)}, Token数: {len(tokens)}, 比率: {len(tokens)/len(text):.2f}")
except ImportError:
    print("  tiktoken 未安装，跳过 Token 计数演示")
    print("  安装: pip install tiktoken")

# ============================================================================
# 5. 消息角色
# ============================================================================
print("\n--- 5. 消息角色 ---")
print("""
Chat 模型使用三种消息角色：

  system:    系统消息 → 定义 AI 的行为/角色/规则（用户不可见）
  user:      用户消息 → 用户的输入/问题
  assistant: 助手消息 → AI 的回复（或预设回复）

```python
messages = [
    {"role": "system",    "content": "你是一个Python专家，回答要简洁。"},
    {"role": "user",      "content": "什么是列表推导式？"},
    {"role": "assistant", "content": "列表推导式是..."},  # 可选：预设回复
    {"role": "user",      "content": "给我一个复杂的例子"}
]
```

多轮对话 = 把之前的 user/assistant 消息都传入
LLM 本身无记忆，靠消息列表模拟"记忆"
""")

# 演示 system prompt 的影响
print("System Prompt 影响演示:")
question = "如何学好编程？"
systems = [
    ("无 system", ""),
    ("简洁专家", "你是编程教育专家。回答不超过2句话。"),
    ("鼓励导师", "你是一个充满热情的编程导师，善于鼓励学生。用口语化的方式回答。"),
]

for name, sys_prompt in systems:
    result = chat(question, system=sys_prompt, max_tokens=150)
    print(f"\n  [{name}]")
    print(f"  Q: {question}")
    print(f"  A: {result[:120]}...")

# ============================================================================
# 6. 第一个实验
# ============================================================================
print("\n\n--- 6. Prompt 实验 ---")

experiments = [
    {
        "name": "模糊 vs 具体",
        "bad": "写个故事",
        "good": "写一个100字的微型科幻故事，主角是一个AI，结尾要有反转",
    },
    {
        "name": "无格式 vs 有格式",
        "bad": "分析苹果这家公司",
        "good": "分析苹果公司，以以下格式输出：\n公司名称：\n主营业务：\n核心优势：（3点）\n主要挑战：（2点）",
    },
    {
        "name": "无约束 vs 有约束",
        "bad": "介绍机器学习",
        "good": "用一段话（不超过80字）向10岁小朋友解释什么是机器学习，不使用任何专业术语",
    },
]

for exp in experiments:
    print(f"\n  实验: {exp['name']}")
    print(f"  ❌ 差: \"{exp['bad']}\"")
    result_bad = chat(exp["bad"], max_tokens=100)
    print(f"     → {result_bad[:80]}...")
    print(f"  ✅ 好: \"{exp['good'][:60]}...\"")
    result_good = chat(exp["good"], max_tokens=150)
    print(f"     → {result_good[:100]}...")

print("\n" + "=" * 60)
print("[完成] 第1课完成！你已经学会了：")
print("  [v] Prompt 7大结构要素")
print("  [v] 三大核心原则（清晰/上下文/格式）")
print("  [v] Temperature / Top-p 参数控制")
print("  [v] Tokenizer 与 Token 计费")
print("  [v] System / User / Assistant 消息角色")
print("  [v] Prompt 质量对比实验")
print("=" * 60)
print("\n下一课：02_few_shot_and_cot.py - Few-shot 与 CoT 推理")
