import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：Few-shot / Chain-of-Thought / 高级推理技巧
==============================================================================

三种核心 Prompt 策略：
- Zero-shot: 直接提问，不给示例
- Few-shot:  给几个示例，让模型学习模式
- CoT:       让模型逐步推理，而非直接给答案

本课内容：
1. Zero-shot vs Few-shot
2. Few-shot 示例设计
3. Chain-of-Thought 思维链
4. Self-Consistency 自一致性
5. Tree-of-Thought 思维树
6. ReAct 推理+行动
==============================================================================
"""

import json
import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"

def chat(prompt: str, system: str = "", temperature: float = 0.3) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL, "messages": messages, "stream": False,
            "options": {"temperature": temperature, "num_predict": 500}
        }, timeout=30.0)
        return resp.json().get("message", {}).get("content", "")
    except:
        return "[模拟回答]"

print("=" * 60)
print("第2课：Few-shot / CoT / 高级推理")
print("=" * 60)

# ============================================================================
# 1. Zero-shot vs Few-shot
# ============================================================================
print("\n--- 1. Zero-shot vs Few-shot ---")
print("""
Zero-shot（零样本）：不给示例，直接提问
  "判断以下评论的情感：这家餐厅太好吃了！"

One-shot（单样本）：给1个示例
  "示例：'真棒' → 正面
   判断：'这家餐厅太好吃了！' → ?"

Few-shot（少样本）：给2-5个示例
  "示例1：'真棒' → 正面
   示例2：'太差了' → 负面
   示例3：'还行吧' → 中性
   判断：'这家餐厅太好吃了！' → ?"

Few-shot 的优势：
- 模型能从示例中学习"你想要的格式和风格"
- 减少歧义，输出更稳定
- 不需要微调模型
""")

# 对比实验
print("情感分析对比:")

# Zero-shot
zero_shot = "判断以下评论的情感（正面/负面/中性）：\n评论：服务态度很差，但菜品还不错"
result_zero = chat(zero_shot)
print(f"\n  [Zero-shot]")
print(f"  Prompt: {zero_shot[:50]}...")
print(f"  回答: {result_zero[:100]}...")

# Few-shot
few_shot = """判断以下评论的情感。

示例：
评论：味道太好了，下次还来！→ 正面
评论：等了一个小时，服务太差！→ 负面
评论：味道一般，价格合理。→ 中性

请判断：
评论：服务态度很差，但菜品还不错 → """

result_few = chat(few_shot)
print(f"\n  [Few-shot]")
print(f"  回答: {result_few[:100]}...")

# ============================================================================
# 2. Few-shot 示例设计
# ============================================================================
print("\n\n--- 2. Few-shot 设计技巧 ---")
print("""
技巧1：示例要覆盖各种情况
  ✅ 正面/负面/中性 各一个
  ❌ 全是正面示例

技巧2：示例格式要统一
  ✅ "输入：xxx → 输出：yyy"（每条格式一致）
  ❌ 第一条用冒号，第二条用箭头，第三条用换行

技巧3：示例难度接近实际任务
  ✅ 示例中包含边界情况（如"有好有坏"的混合评论）
  ❌ 示例太简单，实际任务太复杂

技巧4：3-5 个示例通常最佳
  太少：模式不明确
  太多：占用 token，性价比下降

技巧5：示例顺序可能影响结果
  最后一个示例权重最高（近因效应）
""")

# 结构化 Few-shot 模板
def few_shot_classify(text: str) -> str:
    prompt = f"""你是文本分类专家。将用户输入分类到以下类别。

示例：
输入：我的订单三天还没到 → 类别：物流问题
输入：怎么修改收货地址 → 类别：账号操作
输入：这个产品质量太差了 → 类别：投诉
输入：你们有没有红色的 → 类别：商品咨询

输入：{text} → 类别："""
    return chat(prompt, temperature=0.0)

test_texts = [
    "退款什么时候到账？",
    "快递显示已签收但我没收到",
    "这款有没有大号的？",
    "用了三天就坏了，太失望了",
]

print("Few-shot 分类测试:")
for t in test_texts:
    result = few_shot_classify(t)
    print(f"  \"{t}\" → {result[:30]}")

# ============================================================================
# 3. Chain-of-Thought
# ============================================================================
print("\n--- 3. Chain-of-Thought ---")
print("""
CoT = 让模型展示推理过程，而非直接给答案。

直接回答（容易出错）：
  "一个班30人，60%喜欢数学，40%喜欢英语，20%两门都喜欢。
   至少喜欢一门的有多少？"
  → "24"（可能对也可能错）

CoT（更准确）：
  "...请逐步推理：
   1. 先算喜欢数学的人数
   2. 再算喜欢英语的人数
   3. 算两门都喜欢的
   4. 用容斥原理计算"
  → "步骤1：30×60%=18人...步骤4：18+12-6=24人"

触发 CoT 的方式：
  方式1："请逐步思考"（Let's think step by step）
  方式2：给出推理步骤的框架
  方式3：用 Few-shot + 推理过程示例
""")

# CoT 对比
math_problem = "一个水池有两个水管，A管单独注满需要6小时，B管单独注满需要4小时。两管同时开，多久注满？"

# 直接回答
direct = chat(f"直接给出答案（只需要一个数字）：{math_problem}", temperature=0.0)
print(f"直接回答: {direct[:60]}...")

# CoT
cot = chat(f"请逐步推理解答以下问题，展示完整计算过程：\n{math_problem}", temperature=0.0)
print(f"\nCoT 推理: {cot[:200]}...")

# Zero-shot CoT（最简单的 CoT）
zero_cot = chat(f"{math_problem}\n\nLet's think step by step.", temperature=0.0)
print(f"\nZero-shot CoT: {zero_cot[:200]}...")

# ============================================================================
# 4. Self-Consistency
# ============================================================================
print("\n\n--- 4. Self-Consistency ---")
print("""
自一致性 = 多次采样（高 temperature）→ 取多数答案

原理：
  采样1 (temp=0.8) → 答案 A
  采样2 (temp=0.8) → 答案 B
  采样3 (temp=0.8) → 答案 A
  采样4 (temp=0.8) → 答案 A
  采样5 (temp=0.8) → 答案 B
  多数投票 → 答案 A（3票 vs 2票）

适用场景：
- 数学题/逻辑题
- 有明确正确答案的任务
- 模型不够确定的问题

```python
def self_consistency(prompt, n=5, temperature=0.8):
    answers = []
    for _ in range(n):
        result = chat(prompt + "\\n请逐步推理，最后给出答案。",
                      temperature=temperature)
        answers.append(extract_answer(result))
    # 投票
    from collections import Counter
    return Counter(answers).most_common(1)[0][0]
```
""")

# 模拟 Self-Consistency
print("Self-Consistency 模拟:")
question = "小明有5个苹果，给了小红2个，又买了3个，现在有几个？"
answers = []
for i in range(5):
    result = chat(f"{question}\n请逐步计算，最后一行只写数字答案。", temperature=0.8)
    # 提取最后的数字
    nums = [c for c in result.split() if c.isdigit()]
    ans = nums[-1] if nums else "?"
    answers.append(ans)
    print(f"  采样{i+1}: {result[:60]}... → 答案: {ans}")

from collections import Counter
if answers:
    most_common = Counter(answers).most_common(1)[0]
    print(f"  投票结果: {most_common[0]}（{most_common[1]}/{len(answers)}票）")

# ============================================================================
# 5. Tree-of-Thought
# ============================================================================
print("\n--- 5. Tree-of-Thought ---")
print("""
思维树 = 生成多条推理路径 → 评估 → 选最优

比 CoT 更进一步：
  CoT:  一条推理链
  ToT:  多条推理链 + 自评估 + 选择最优

Prompt 模板：
```
对于以下问题，请：
1. 提出 3 种不同的解题思路
2. 分别沿每条思路推理
3. 评估每条路径的可靠性（1-10分）
4. 选择最优路径，给出最终答案
```

适用：
- 开放性问题
- 设计/规划任务
- 需要创造性思维的问题
""")

tot_prompt = """问题：如何设计一个高效的待办事项 App？

请用思维树方法分析：
1. 提出 3 种不同的设计思路
2. 简要分析每种思路的优缺点
3. 给每种打分（1-10）
4. 推荐最优方案"""

result = chat(tot_prompt, temperature=0.5)
print(f"ToT 输出:\n{result[:300]}...")

# ============================================================================
# 6. ReAct
# ============================================================================
print("\n\n--- 6. ReAct 推理+行动 ---")
print("""
ReAct = Reasoning + Acting（推理 + 行动交替）

核心模式：
  Thought: 我需要...（推理）
  Action:  search("xxx")（行动）
  Observation: 搜索结果是...（观察）
  Thought: 根据结果，我知道...（推理）
  Action:  calculate(...)（行动）
  ...
  Final Answer: ...（最终答案）

ReAct 是 AI Agent 的核心 Prompt 模式！
（后续 learn-langgraph 课程会深入实践）

```python
react_prompt = '''
回答以下问题，使用 Thought/Action/Observation 格式：

可用工具：
- search(query): 搜索信息
- calculate(expression): 计算数学表达式

问题：{question}

Thought: 让我分析这个问题...
'''
```
""")

react_demo = """回答以下问题，使用 Thought/Action/Observation 格式推理：

问题：一个正方形的对角线长度是10厘米，这个正方形的面积是多少？

请按以下格式一步步推理：
Thought: [你的思考]
Action: [你的计算]
Observation: [计算结果]
... (重复直到得出答案)
Final Answer: [最终答案]"""

result = chat(react_demo, temperature=0.0)
print(f"ReAct 推理:\n{result[:300]}...")

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] Zero-shot vs Few-shot 对比")
print("  [v] Few-shot 示例设计技巧（覆盖/格式/难度）")
print("  [v] Chain-of-Thought 思维链推理")
print("  [v] Self-Consistency 自一致性投票")
print("  [v] Tree-of-Thought 思维树")
print("  [v] ReAct 推理+行动模式")
print("=" * 60)
print("\n下一课：03_structured_output.py - 结构化输出")
