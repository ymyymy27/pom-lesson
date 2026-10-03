import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：Prompt 设计模式大全
==============================================================================

设计模式 = 解决特定问题的可复用 Prompt 方案

就像编程有设计模式（工厂/单例/观察者），
Prompt 工程也有自己的设计模式。

本课内容：
1. 分解模式（Decomposition）
2. 验证模式（Verification）
3. 迭代精炼模式（Iterative Refinement）
4. 元提示模式（Meta Prompt）
5. 模板填充模式（Template）
6. 多步管道模式（Pipeline）
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
            "options": {"temperature": temperature, "num_predict": 600}
        }, timeout=30.0)
        return resp.json().get("message", {}).get("content", "")
    except:
        return "[模拟回答]"

def chat_multi(messages: list, temperature: float = 0.3) -> str:
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL, "messages": messages, "stream": False,
            "options": {"temperature": temperature, "num_predict": 600}
        }, timeout=30.0)
        return resp.json().get("message", {}).get("content", "")
    except:
        return "[模拟回答]"

print("=" * 60)
print("第5课：Prompt 设计模式")
print("=" * 60)

# ============================================================================
# 1. 分解模式
# ============================================================================
print("\n--- 1. 分解模式 ---")
print("""
核心思想：大任务 → 拆成多个小任务 → 逐个解决 → 合并

何时使用：
  任务复杂度超过模型单次处理能力

方式1：在一个 Prompt 中分步
  "请分3步完成：1.分析需求 2.设计方案 3.编写代码"

方式2：多次调用串联
  Prompt1: "分析需求" → 结果1
  Prompt2: "根据{结果1}设计方案" → 结果2
  Prompt3: "根据{结果2}编写代码" → 结果3
""")

# 分解模式演示
task = "设计一个在线书店的数据库"

# 一步到位（可能不够好）
direct = chat(f"请设计一个在线书店的数据库表结构，包含建表SQL。只给出核心3张表。")
print(f"[直接方式] {direct[:150]}...")

# 分解方式
print(f"\n[分解方式]")
step1 = chat("设计一个在线书店的数据库。第1步：列出需要哪些核心实体和它们的关系（不写SQL，只分析）。3句话以内。")
print(f"  步骤1(分析): {step1[:120]}...")

step2 = chat(f"基于以下分析，设计3张核心表的字段（不写SQL，只列字段和类型）：\n{step1}")
print(f"  步骤2(设计): {step2[:120]}...")

step3 = chat(f"根据以下表设计，写出MySQL建表SQL（简洁，只要CREATE TABLE）：\n{step2}")
print(f"  步骤3(实现): {step3[:150]}...")

# ============================================================================
# 2. 验证模式
# ============================================================================
print("\n\n--- 2. 验证模式 ---")
print("""
核心思想：生成 → 自我检查 → 修正

方式1：一次性自检
  "回答后，检查你的回答是否有以下问题：
   1. 事实是否正确？
   2. 逻辑是否一致？
   3. 是否遗漏了重要信息？
   如果有问题，请修正。"

方式2：两次调用
  Prompt1: "回答问题" → 回答
  Prompt2: "检查以下回答是否正确：{回答}" → 验证结果

方式3：对抗验证（红队）
  Prompt1: "提出方案" → 方案
  Prompt2: "作为批评者，找出以下方案的所有漏洞：{方案}" → 漏洞
  Prompt3: "根据以下批评，改进方案：{方案}{漏洞}" → 改进
""")

# 验证模式演示
print("[自检模式]")
answer = chat("Python的GIL是什么？用2句话解释。")
print(f"  初始回答: {answer[:120]}...")

verification = chat(f"""请检查以下关于Python GIL的回答是否准确：

"{answer}"

检查：
1. 技术事实是否正确？
2. 是否有误导性表述？
3. 有无重要遗漏？

如有问题，给出修正版本。""")
print(f"  验证结果: {verification[:150]}...")

# 对抗验证
print(f"\n[对抗验证]")
proposal = chat("设计一个简单的用户登录系统的安全方案。3条关键措施。", temperature=0.5)
print(f"  方案: {proposal[:120]}...")

critique = chat(f"作为安全专家，找出以下登录方案的安全漏洞（至少3个）：\n{proposal}", temperature=0.3)
print(f"  批评: {critique[:120]}...")

# ============================================================================
# 3. 迭代精炼模式
# ============================================================================
print("\n\n--- 3. 迭代精炼 ---")
print("""
核心思想：初稿 → 反馈 → 改进 → 反馈 → ... → 终稿

像人类写作一样：草稿 → 修改 → 润色

```python
def iterative_refine(task, criteria, max_rounds=3):
    draft = chat(task)
    for i in range(max_rounds):
        feedback = chat(f"根据以下标准评估并改进：\\n标准：{criteria}\\n当前版本：{draft}")
        if "满意" in feedback or "无需修改" in feedback:
            break
        draft = feedback
    return draft
```

实际应用：
  写文案 → 评估吸引力 → 改进 → 评估 → 最终版
  写代码 → 检查bug → 修复 → 检查 → 最终版
""")

# 迭代精炼演示
print("[迭代精炼]")
draft = chat("写一句产品宣传语：一款智能降噪耳机。10字以内。", temperature=0.7)
print(f"  v1: {draft[:60]}")

v2 = chat(f"以下宣传语不够有冲击力，请改进（更简洁、更有力、突出'静'的概念）：\n{draft}\n只输出新版本，10字以内。", temperature=0.7)
print(f"  v2: {v2[:60]}")

v3 = chat(f"以下宣传语还可以更好，请让它更朗朗上口、有韵律感：\n{v2}\n只输出新版本，10字以内。", temperature=0.7)
print(f"  v3: {v3[:60]}")

# ============================================================================
# 4. 元提示模式
# ============================================================================
print("\n--- 4. 元提示模式 ---")
print("""
元提示 = 让 LLM 帮你写 Prompt

"我想要一个用于[任务]的 Prompt，请帮我设计。"

也叫"Prompt 生成器"——用 AI 来优化 AI 的输入。
""")

meta_prompt = """你是 Prompt Engineering 专家。

用户需要一个用于"从新闻文章中提取结构化信息"的 Prompt。

请设计一个高质量的 Prompt，包含：
1. System Prompt（角色+规则）
2. 输出格式（JSON Schema）
3. 2个 Few-shot 示例
4. 边界情况处理说明

输出完整可用的 Prompt。"""

result = chat(meta_prompt, temperature=0.5)
print(f"元提示生成:\n{result[:400]}...")

# ============================================================================
# 5. 模板填充模式
# ============================================================================
print("\n\n--- 5. 模板填充 ---")
print("""
核心思想：定义通用模板 + 变量 → 批量生成

适合：需要大量类似但不同的 Prompt（如批量处理）
""")

# 模板系统
class PromptTemplate:
    """简单的 Prompt 模板系统"""

    def __init__(self, template: str, system: str = ""):
        self.template = template
        self.system = system

    def format(self, **kwargs) -> str:
        return self.template.format(**kwargs)

    def run(self, **kwargs) -> str:
        prompt = self.format(**kwargs)
        return chat(prompt, system=self.system, temperature=0.3)

# 定义模板
email_template = PromptTemplate(
    template="写一封{tone}的邮件，主题：{subject}，收件人：{recipient}。邮件正文不超过3句话。",
    system="你是商务邮件专家，输出格式：主题行 + 正文。"
)

review_template = PromptTemplate(
    template="用1句话评价以下{category}：{item}。评价要{style}。",
)

# 批量生成
print("模板批量生成:")

emails = [
    {"tone": "正式", "subject": "会议邀请", "recipient": "客户"},
    {"tone": "友好", "subject": "项目进展更新", "recipient": "团队成员"},
    {"tone": "紧急", "subject": "系统故障通知", "recipient": "技术负责人"},
]
for params in emails:
    result = email_template.run(**params)
    print(f"\n  [{params['tone']}] → {result[:100]}...")

# ============================================================================
# 6. 多步管道模式
# ============================================================================
print("\n\n--- 6. 多步管道 ---")
print("""
管道 = 多个 Prompt 串联，前一步的输出作为后一步的输入

  输入 → [提取] → [分析] → [生成] → [格式化] → 输出

适合：复杂的端到端任务
""")

class PromptPipeline:
    """Prompt 管道"""

    def __init__(self):
        self.steps = []

    def add_step(self, name: str, prompt_template: str, system: str = ""):
        self.steps.append({"name": name, "template": prompt_template, "system": system})

    def run(self, initial_input: str, verbose: bool = True) -> str:
        current = initial_input
        for step in self.steps:
            prompt = step["template"].replace("{input}", current)
            result = chat(prompt, system=step["system"], temperature=0.3)
            if verbose:
                print(f"    [{step['name']}] {result[:80]}...")
            current = result
        return current

# 构建文章分析管道
pipeline = PromptPipeline()
pipeline.add_step("提取", "从以下文本中提取关键信息（人物/事件/时间/地点），只列要点：\n{input}")
pipeline.add_step("分析", "根据以下要点分析事件的影响和意义，2句话：\n{input}")
pipeline.add_step("总结", "将以下分析写成一段50字以内的新闻摘要：\n{input}")

article = "2024年3月，OpenAI发布了GPT-4o模型，这是首个原生多模态模型，能同时处理文本、图像和音频。该模型在多个基准测试中超越了前代，并且推理速度提升了2倍。"

print("文章分析管道:")
print(f"  输入: {article[:60]}...")
final = pipeline.run(article)
print(f"  最终: {final[:100]}...")

print("\n--- 设计模式总结 ---")
print("""
┌──────────────────┬──────────────────────────────────────┐
│  模式             │  适用场景                             │
├──────────────────┼──────────────────────────────────────┤
│  分解             │  复杂任务拆解为子任务               │
│  验证             │  需要高准确度/安全性                 │
│  迭代精炼        │  创意生成/文案优化                   │
│  元提示          │  让AI帮你写Prompt                    │
│  模板填充        │  批量处理同类任务                    │
│  多步管道        │  端到端复杂流程                      │
└──────────────────┴──────────────────────────────────────┘
""")

print("=" * 60)
print("[完成] 第5课完成！你已经学会了：")
print("  [v] 分解模式（大任务拆小任务）")
print("  [v] 验证模式（自检+对抗验证）")
print("  [v] 迭代精炼（草稿→反馈→改进）")
print("  [v] 元提示（用AI写Prompt）")
print("  [v] 模板填充（批量处理）")
print("  [v] 多步管道（串联多个Prompt）")
print("=" * 60)
print("\n下一课：06_prompt_optimization.py - Prompt 优化与评估")
