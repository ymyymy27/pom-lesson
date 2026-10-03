import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：数据准备（格式 / 清洗 / 增强 / 验证）
==============================================================================

数据质量是微调成功的关键。
"Garbage in, garbage out" 在微调中尤其明显。

本课内容：
1. 数据格式标准
2. 数据收集方法
3. 数据清洗
4. LLM 辅助数据增强
5. 数据验证
6. 数据集管理
==============================================================================
"""

import json
import os
import tempfile
import hashlib
from datetime import datetime

print("=" * 60)
print("第2课：数据准备")
print("=" * 60)

# ============================================================================
# 1. 数据格式
# ============================================================================
print("\n--- 1. 数据格式 ---")
print("""
三种主流微调数据格式：

格式1: OpenAI Chat 格式（最通用）
```jsonl
{"messages": [
  {"role": "system", "content": "你是客服助手"},
  {"role": "user", "content": "退款流程？"},
  {"role": "assistant", "content": "退款步骤：1.登录..."}
]}
```

格式2: Alpaca 格式（学术常用）
```json
{"instruction": "翻译为英文",
 "input": "机器学习是AI的分支",
 "output": "Machine learning is a branch of AI"}
```

格式3: ShareGPT 格式（多轮对话）
```json
{"conversations": [
  {"from": "system", "value": "你是助手"},
  {"from": "human", "value": "你好"},
  {"from": "gpt", "value": "你好！有什么可以帮你？"},
  {"from": "human", "value": "介绍下Python"},
  {"from": "gpt", "value": "Python是..."}
]}
```

转换关系：Alpaca ↔ Chat ↔ ShareGPT 可以互转
""")

# 格式转换工具
def alpaca_to_chat(item: dict, system: str = "") -> dict:
    """Alpaca → Chat 格式"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    user_content = item["instruction"]
    if item.get("input"):
        user_content += f"\n{item['input']}"
    messages.append({"role": "user", "content": user_content})
    messages.append({"role": "assistant", "content": item["output"]})
    return {"messages": messages}

def chat_to_alpaca(item: dict) -> dict:
    """Chat → Alpaca 格式"""
    messages = item["messages"]
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
    assistant_msg = next((m["content"] for m in messages if m["role"] == "assistant"), "")
    return {"instruction": user_msg, "input": "", "output": assistant_msg}

def sharegpt_to_chat(item: dict) -> dict:
    """ShareGPT → Chat 格式"""
    role_map = {"system": "system", "human": "user", "gpt": "assistant"}
    messages = []
    for conv in item["conversations"]:
        role = role_map.get(conv["from"], conv["from"])
        messages.append({"role": role, "content": conv["value"]})
    return {"messages": messages}

# 演示转换
alpaca_example = {
    "instruction": "将以下文本翻译为英文",
    "input": "深度学习是机器学习的一个子领域",
    "output": "Deep learning is a subfield of machine learning"
}
chat_result = alpaca_to_chat(alpaca_example, "你是翻译专家")
print("格式转换演示:")
print(f"  Alpaca: {json.dumps(alpaca_example, ensure_ascii=False)[:80]}...")
print(f"  → Chat: {json.dumps(chat_result, ensure_ascii=False)[:80]}...")

# ============================================================================
# 2. 数据收集
# ============================================================================
print("\n--- 2. 数据收集 ---")
print("""
数据来源：

1. 人工编写（质量最高）
   - 领域专家编写QA对
   - 成本高但质量最好
   - 建议核心数据人工编写

2. 已有业务数据
   - 客服对话记录
   - FAQ 知识库
   - 标注数据
   - 需要脱敏处理

3. LLM 生成（Synthetic Data）
   - 用 GPT-4o 生成训练数据
   - 成本低、速度快
   - 需要人工审核
   - Self-Instruct / Evol-Instruct

4. 开源数据集
   - HuggingFace Datasets
   - 各种 benchmark 数据
   - 注意许可证

数据量参考：
  风格微调：100-500 条
  知识注入：1000-5000 条
  复杂任务：5000-50000 条
""")

# ============================================================================
# 3. 数据清洗
# ============================================================================
print("\n--- 3. 数据清洗 ---")

class DataCleaner:
    """微调数据清洗器"""

    def __init__(self):
        self.stats = {"total": 0, "kept": 0, "removed": 0, "reasons": {}}

    def clean(self, data: list) -> list:
        """清洗数据集"""
        cleaned = []
        seen_hashes = set()

        for item in data:
            self.stats["total"] += 1
            messages = item.get("messages", [])

            # 检查1: 基本结构
            if not messages or len(messages) < 2:
                self._remove("结构不完整")
                continue

            # 检查2: 角色正确
            roles = [m["role"] for m in messages]
            if "user" not in roles or "assistant" not in roles:
                self._remove("缺少必要角色")
                continue

            # 检查3: 内容非空
            if any(not m["content"].strip() for m in messages):
                self._remove("存在空内容")
                continue

            # 检查4: 内容长度
            assistant_msgs = [m for m in messages if m["role"] == "assistant"]
            for am in assistant_msgs:
                if len(am["content"]) < 10:
                    self._remove("回答太短(<10字)")
                    continue
                if len(am["content"]) > 10000:
                    self._remove("回答太长(>10000字)")
                    continue

            # 检查5: 去重
            content_hash = hashlib.md5(
                json.dumps(messages, ensure_ascii=False).encode()
            ).hexdigest()
            if content_hash in seen_hashes:
                self._remove("重复数据")
                continue
            seen_hashes.add(content_hash)

            # 检查6: 质量检查（简单启发式）
            assistant_text = " ".join(m["content"] for m in assistant_msgs)
            if assistant_text.count("...") > 5:
                self._remove("回答质量低（过多省略号）")
                continue

            cleaned.append(item)
            self.stats["kept"] += 1

        return cleaned

    def _remove(self, reason: str):
        self.stats["removed"] += 1
        self.stats["reasons"][reason] = self.stats["reasons"].get(reason, 0) + 1

    def report(self) -> str:
        lines = [f"总数: {self.stats['total']}, 保留: {self.stats['kept']}, "
                 f"移除: {self.stats['removed']}"]
        for reason, count in self.stats["reasons"].items():
            lines.append(f"  - {reason}: {count}")
        return "\n".join(lines)

# 测试数据清洗
test_data = [
    {"messages": [
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "什么是Python？"},
        {"role": "assistant", "content": "Python是一种通用编程语言，以简洁易读著称。"}
    ]},
    {"messages": [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！"}  # 太短
    ]},
    {"messages": []},  # 空
    {"messages": [
        {"role": "user", "content": "解释机器学习"},
        {"role": "assistant", "content": ""}  # 空内容
    ]},
    {"messages": [
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "什么是Python？"},
        {"role": "assistant", "content": "Python是一种通用编程语言，以简洁易读著称。"}
    ]},  # 重复
    {"messages": [
        {"role": "user", "content": "什么是深度学习？"},
        {"role": "assistant", "content": "深度学习是机器学习的一个子领域，使用多层神经网络来学习数据中的复杂模式和表示。"}
    ]},
]

cleaner = DataCleaner()
cleaned = cleaner.clean(test_data)
print(f"清洗结果:\n{cleaner.report()}")

# ============================================================================
# 4. LLM 数据增强
# ============================================================================
print("\n--- 4. 数据增强 ---")
print("""
用 LLM 生成训练数据（Synthetic Data）：

方法1: Self-Instruct
  给 LLM 几个示例 → 让它生成更多类似的QA对

方法2: Evol-Instruct（WizardLM 方法）
  简单指令 → LLM 进化为更复杂的指令

方法3: 主题扩展
  给定主题列表 → 为每个主题生成多个QA对

```python
def generate_training_data(topic: str, n: int = 5) -> list:
    prompt = f'''为"{topic}"领域生成{n}个高质量的问答训练数据。

要求：
1. 问题要多样（概念题/操作题/比较题/场景题）
2. 回答要专业、准确、适中长度
3. 以 JSON 数组格式输出

格式：
[{{"question": "...", "answer": "..."}}]
'''
    result = llm.chat(prompt)
    return json.loads(result)
```
""")

import httpx

OLLAMA_URL = "http://localhost:11434"

def generate_qa(topic: str, n: int = 3) -> list:
    """用 LLM 生成训练数据"""
    prompt = f"""为"{topic}"生成{n}个问答训练数据。
以JSON数组输出：[{{"question":"...", "answer":"..."}}]
只输出JSON。"""
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": "qwen2.5:7b",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False, "format": "json",
            "options": {"temperature": 0.7, "num_predict": 800}
        }, timeout=30.0)
        content = resp.json().get("message", {}).get("content", "[]")
        result = json.loads(content)
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        if isinstance(result, list):
            return result
        return [result]
    except:
        return [{"question": f"关于{topic}的问题", "answer": f"关于{topic}的专业回答"}]

print("LLM 数据增强演示:")
qa_pairs = generate_qa("Python装饰器", 3)
for i, qa in enumerate(qa_pairs[:3], 1):
    q = qa.get("question", "")
    a = qa.get("answer", "")
    print(f"  {i}. Q: {str(q)[:50]}...")
    print(f"     A: {str(a)[:50]}...")

# ============================================================================
# 5. 数据验证
# ============================================================================
print("\n--- 5. 数据验证 ---")

class DataValidator:
    """微调数据验证器"""

    def validate(self, data: list, format_type: str = "chat") -> dict:
        errors = []
        warnings = []
        stats = {
            "total": len(data),
            "avg_turns": 0,
            "avg_assistant_len": 0,
            "system_prompt_count": 0,
        }

        total_turns = 0
        total_assistant_len = 0
        assistant_count = 0

        for i, item in enumerate(data):
            messages = item.get("messages", [])

            # 错误检查
            if not messages:
                errors.append(f"[{i}] messages 为空")
                continue

            for j, msg in enumerate(messages):
                if "role" not in msg:
                    errors.append(f"[{i}][{j}] 缺少 role")
                if "content" not in msg:
                    errors.append(f"[{i}][{j}] 缺少 content")
                if msg.get("role") not in ("system", "user", "assistant"):
                    errors.append(f"[{i}][{j}] 无效 role: {msg.get('role')}")

            # 统计
            roles = [m.get("role") for m in messages]
            if "system" in roles:
                stats["system_prompt_count"] += 1

            turns = sum(1 for r in roles if r == "user")
            total_turns += turns

            for m in messages:
                if m.get("role") == "assistant":
                    total_assistant_len += len(m.get("content", ""))
                    assistant_count += 1

            # 警告
            assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
            for am in assistant_msgs:
                if len(am.get("content", "")) < 20:
                    warnings.append(f"[{i}] 回答较短 ({len(am['content'])}字)")
                if len(am.get("content", "")) > 5000:
                    warnings.append(f"[{i}] 回答较长 ({len(am['content'])}字)")

        stats["avg_turns"] = total_turns / len(data) if data else 0
        stats["avg_assistant_len"] = total_assistant_len / assistant_count if assistant_count else 0

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings[:10],
            "stats": stats,
        }

validator = DataValidator()
report = validator.validate(cleaned)
print(f"验证结果: {'✅ 通过' if report['valid'] else '❌ 失败'}")
print(f"  统计: {json.dumps(report['stats'], ensure_ascii=False)}")
if report["errors"]:
    print(f"  错误: {report['errors'][:3]}")
if report["warnings"]:
    print(f"  警告: {report['warnings'][:3]}")

# ============================================================================
# 6. 数据集管理
# ============================================================================
print("\n--- 6. 数据集管理 ---")

class DatasetManager:
    """数据集管理器"""

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or tempfile.mkdtemp(prefix="ft_data_")
        os.makedirs(self.base_dir, exist_ok=True)

    def save_jsonl(self, data: list, filename: str) -> str:
        path = os.path.join(self.base_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        return path

    def load_jsonl(self, filename: str) -> list:
        path = os.path.join(self.base_dir, filename)
        data = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                data.append(json.loads(line.strip()))
        return data

    def split_train_val(self, data: list, val_ratio: float = 0.1) -> tuple:
        import random
        random.seed(42)
        shuffled = data[:]
        random.shuffle(shuffled)
        split_idx = int(len(shuffled) * (1 - val_ratio))
        return shuffled[:split_idx], shuffled[split_idx:]

    def prepare_dataset(self, data: list, name: str) -> dict:
        """完整数据准备流水线"""
        # 1. 清洗
        cleaner = DataCleaner()
        cleaned = cleaner.clean(data)

        # 2. 验证
        validator = DataValidator()
        report = validator.validate(cleaned)

        # 3. 分割
        train, val = self.split_train_val(cleaned)

        # 4. 保存
        train_path = self.save_jsonl(train, f"{name}_train.jsonl")
        val_path = self.save_jsonl(val, f"{name}_val.jsonl")

        return {
            "name": name,
            "original_size": len(data),
            "cleaned_size": len(cleaned),
            "train_size": len(train),
            "val_size": len(val),
            "train_path": train_path,
            "val_path": val_path,
            "validation": report,
        }

manager = DatasetManager()
result = manager.prepare_dataset(test_data, "demo")
print(f"数据集准备完成:")
print(f"  原始: {result['original_size']} → 清洗: {result['cleaned_size']}")
print(f"  训练: {result['train_size']}, 验证: {result['val_size']}")
print(f"  路径: {result['train_path']}")

# 清理
import shutil
shutil.rmtree(manager.base_dir, ignore_errors=True)

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] 三种数据格式（Chat/Alpaca/ShareGPT）及转换")
print("  [v] 数据收集方法（人工/业务/LLM生成/开源）")
print("  [v] 数据清洗（去重/质量/完整性检查）")
print("  [v] LLM 辅助数据增强")
print("  [v] 数据验证框架")
print("  [v] 数据集管理（分割/保存/流水线）")
print("=" * 60)
print("\n下一课：03_lora_and_qlora.py - LoRA / QLoRA 原理与实践")
