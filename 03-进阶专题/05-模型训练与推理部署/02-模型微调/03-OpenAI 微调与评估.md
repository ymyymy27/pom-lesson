> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# OpenAI 微调与评估

## 学习目标

- 掌握 OpenAI Fine-tuning API 的使用
- 学会系统化评估微调模型
- 了解何时选择微调 vs RAG vs Prompt Engineering

## 1. OpenAI Fine-tuning

### 数据格式

```jsonl
{"messages": [{"role": "system", "content": "你是客服助手"}, {"role": "user", "content": "退款流程是什么？"}, {"role": "assistant", "content": "退款流程如下：1. 登录..."}]}
{"messages": [{"role": "system", "content": "你是客服助手"}, {"role": "user", "content": "如何修改收货地址？"}, {"role": "assistant", "content": "修改地址步骤：1. 进入..."}]}
```

### 训练流程

```python
from openai import OpenAI
client = OpenAI()

# 1. 上传文件
file = client.files.create(
    file=open("train.jsonl", "rb"),
    purpose="fine-tune"
)

# 2. 创建微调任务
job = client.fine_tuning.jobs.create(
    training_file=file.id,
    model="gpt-4o-mini-2024-07-18",
    hyperparameters={
        "n_epochs": 3,
        "learning_rate_multiplier": 1.8,
    }
)
print(f"Job ID: {job.id}")

# 3. 查看状态
job = client.fine_tuning.jobs.retrieve(job.id)
print(f"Status: {job.status}")
# pending → running → succeeded

# 4. 使用微调模型
response = client.chat.completions.create(
    model=job.fine_tuned_model,  # ft:gpt-4o-mini-2024-07-18:org:name:id
    messages=[{"role": "user", "content": "退款要多久？"}]
)
```

## 2. 系统化评估框架

```python
import json
from openai import OpenAI

class ModelEvaluator:
    def __init__(self, test_data_path: str):
        self.client = OpenAI()
        with open(test_data_path) as f:
            self.test_data = [json.loads(line) for line in f]

    def evaluate(self, model: str) -> dict:
        results = []
        for item in self.test_data:
            messages = item["messages"][:-1]  # 去掉 assistant 回复
            expected = item["messages"][-1]["content"]

            response = self.client.chat.completions.create(
                model=model, messages=messages
            )
            generated = response.choices[0].message.content

            results.append({
                "input": messages[-1]["content"],
                "expected": expected,
                "generated": generated,
            })

        return results

    def auto_score(self, results: list, judge_model="gpt-4o") -> list:
        """LLM-as-Judge 自动评分"""
        scored = []
        for r in results:
            response = self.client.chat.completions.create(
                model=judge_model,
                messages=[{
                    "role": "user",
                    "content": f"""评估以下回答的质量（JSON 格式）：
问题：{r['input']}
参考答案：{r['expected']}
模型回答：{r['generated']}

输出格式：{{"score": 1-5, "accuracy": 1-5, "completeness": 1-5, "reason": "..."}}"""
                }],
                response_format={"type": "json_object"},
            )
            score = json.loads(response.choices[0].message.content)
            scored.append({**r, **score})
        return scored
```

## 3. 微调 vs RAG vs Prompt Engineering

| 维度 | Prompt Engineering | RAG | 微调 |
|------|-------------------|-----|------|
| 知识更新 | 每次传入 | 实时检索 | 需重新训练 |
| 成本 | 推理贵（长 prompt） | 中等 | 训练贵，推理便宜 |
| 定制化 | 低 | 中 | 高 |
| 实现难度 | 简单 | 中等 | 复杂 |
| 适用场景 | 通用任务 | 知识库问答 | 风格/格式/专业领域 |

### 决策流程

```
需要最新/外部知识？ → RAG
需要特定输出格式/风格？ → 微调
需要领域专业知识？ → 微调 + RAG
简单任务，数据少？ → Prompt Engineering
```

## 练习

1. 准备 50 条训练数据，在 OpenAI 上微调 gpt-4o-mini
2. 用 20 条测试数据对比微调前后的效果
3. 实现 LLM-as-Judge 自动评分系统
4. 思考你的场景更适合 RAG 还是微调，写出理由

## 阶段总结

本阶段你已掌握：
- ✅ 微调原理与数据准备
- ✅ LoRA/QLoRA 本地微调
- ✅ OpenAI Fine-tuning API
- ✅ 模型评估与方案选型

→ 下一阶段：[stage-07 向量数据库与 Embedding](../../../02-方向选修/02-AI应用/参考资料/03-向量检索)
