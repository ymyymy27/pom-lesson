import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：OpenAI Fine-tuning API
==============================================================================

OpenAI 提供云端微调服务：
- 无需 GPU
- 无需管理训练环境
- 支持 gpt-4o-mini / gpt-4o

本课内容：
1. OpenAI 微调流程
2. 数据准备与验证
3. 创建微调任务
4. 监控与管理
5. 使用微调模型
6. 成本与最佳实践
==============================================================================
"""

import json
import time
from datetime import datetime

print("=" * 60)
print("第5课：OpenAI Fine-tuning API")
print("=" * 60)

# ============================================================================
# 1. OpenAI 微调流程
# ============================================================================
print("\n--- 1. 微调流程 ---")
print("""
OpenAI 微调 5 步流程：

  ┌──────────────────────────────────────────────────────┐
  │  Step 1: 准备数据（JSONL 格式）                      │
  │  Step 2: 上传文件                                    │
  │  Step 3: 创建微调任务                                │
  │  Step 4: 等待训练完成（通常 10分钟~数小时）          │
  │  Step 5: 使用微调后的模型                            │
  └──────────────────────────────────────────────────────┘

支持的模型：
  gpt-4o-mini-2024-07-18   最便宜，推荐起步
  gpt-4o-2024-08-06        更强，更贵
  gpt-3.5-turbo            较老但便宜

价格（每百万 token）：
  gpt-4o-mini 训练: $3.00  推理输入: $0.30  推理输出: $1.20
  gpt-4o      训练: $25.00 推理输入: $3.75  推理输出: $15.00
""")

# ============================================================================
# 2. 数据准备
# ============================================================================
print("\n--- 2. 数据准备 ---")
print("""
OpenAI 要求 JSONL 格式（每行一个 JSON）：

train.jsonl:
```jsonl
{"messages":[{"role":"system","content":"你是客服"},{"role":"user","content":"退款？"},{"role":"assistant","content":"退款步骤..."}]}
{"messages":[{"role":"system","content":"你是客服"},{"role":"user","content":"改地址？"},{"role":"assistant","content":"修改步骤..."}]}
```

数据要求：
  ✅ 最少 10 条（推荐 50-100 条起步）
  ✅ 最大 50MB / 文件
  ✅ 每条最长 128K tokens
  ✅ System prompt 建议一致
""")

# 数据准备工具
class OpenAIDataPreparer:
    """OpenAI 微调数据准备"""

    def create_training_data(self, qa_pairs: list, system_prompt: str) -> list:
        data = []
        for qa in qa_pairs:
            data.append({
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": qa["question"]},
                    {"role": "assistant", "content": qa["answer"]},
                ]
            })
        return data

    def validate(self, data: list) -> dict:
        errors = []
        token_counts = []

        for i, item in enumerate(data):
            msgs = item.get("messages", [])
            if not msgs:
                errors.append(f"[{i}] 空 messages")
                continue

            roles = [m.get("role") for m in msgs]
            if "assistant" not in roles:
                errors.append(f"[{i}] 缺少 assistant 消息")

            # 估算 token 数
            total_chars = sum(len(m.get("content", "")) for m in msgs)
            est_tokens = total_chars // 2  # 粗略估算
            token_counts.append(est_tokens)

        avg_tokens = sum(token_counts) / len(token_counts) if token_counts else 0
        cost_per_epoch = sum(token_counts) * 3.0 / 1_000_000  # gpt-4o-mini

        return {
            "valid": len(errors) == 0,
            "errors": errors[:5],
            "count": len(data),
            "avg_tokens": int(avg_tokens),
            "estimated_cost_per_epoch": round(cost_per_epoch, 4),
        }

    def save_jsonl(self, data: list, path: str):
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

# 演示
preparer = OpenAIDataPreparer()
sample_qa = [
    {"question": "退款需要多久？", "answer": "退款通常在3-5个工作日内到账。如果超过5个工作日未收到，请联系客服。"},
    {"question": "如何修改收货地址？", "answer": "请在订单详情页点击'修改地址'按钮。如订单已发货，需联系快递公司修改。"},
    {"question": "能开发票吗？", "answer": "可以的。请在订单页面选择'申请发票'，支持电子发票和纸质发票。"},
    {"question": "会员有什么优惠？", "answer": "会员享有：1.95折商品折扣 2.免运费 3.优先客服 4.生日礼券"},
    {"question": "商品质量有问题怎么办？", "answer": "请在签收7天内申请退换货。拍照上传质量问题，我们会在24小时内处理。"},
]

data = preparer.create_training_data(sample_qa, "你是一个专业的电商客服，回答要简洁、友好、专业。")
report = preparer.validate(data)

print(f"数据准备:")
print(f"  条数: {report['count']}")
print(f"  平均token: {report['avg_tokens']}")
print(f"  每epoch成本: ${report['estimated_cost_per_epoch']}")
print(f"  验证: {'✅' if report['valid'] else '❌'}")

# ============================================================================
# 3. 创建微调任务
# ============================================================================
print("\n--- 3. 创建微调任务 ---")
print("""
完整 API 流程：

```python
from openai import OpenAI
client = OpenAI()

# Step 1: 上传文件
train_file = client.files.create(
    file=open("train.jsonl", "rb"),
    purpose="fine-tune"
)
print(f"File ID: {train_file.id}")

# 可选：上传验证集
val_file = client.files.create(
    file=open("val.jsonl", "rb"),
    purpose="fine-tune"
)

# Step 2: 创建微调任务
job = client.fine_tuning.jobs.create(
    training_file=train_file.id,
    validation_file=val_file.id,       # 可选
    model="gpt-4o-mini-2024-07-18",
    hyperparameters={
        "n_epochs": 3,                  # 训练轮数
        "learning_rate_multiplier": 1.8, # 学习率倍率
        "batch_size": 4,                 # 批次大小
    },
    suffix="my-customer-service",        # 模型后缀名
)

print(f"Job ID: {job.id}")
print(f"Status: {job.status}")  # pending → running → succeeded
```

超参数说明：
  n_epochs: 1-10, 自动推荐（基于数据量）
  learning_rate_multiplier: 0.02-5.0, 默认自动
  batch_size: 1-256, 默认自动
""")

# ============================================================================
# 4. 监控与管理
# ============================================================================
print("\n--- 4. 监控管理 ---")
print("""
```python
# 查看任务状态
job = client.fine_tuning.jobs.retrieve("ftjob-abc123")
print(f"Status: {job.status}")
print(f"Model: {job.fine_tuned_model}")

# 查看训练事件（日志）
events = client.fine_tuning.jobs.list_events(
    fine_tuning_job_id="ftjob-abc123",
    limit=10
)
for event in events.data:
    print(f"[{event.created_at}] {event.message}")
    # "Step 10: training loss=0.234"
    # "New fine-tuned model created: ft:gpt-4o-mini:org:name:id"

# 列出所有微调任务
jobs = client.fine_tuning.jobs.list(limit=10)
for j in jobs.data:
    print(f"{j.id}: {j.status} → {j.fine_tuned_model or 'N/A'}")

# 取消任务
client.fine_tuning.jobs.cancel("ftjob-abc123")

# 删除微调模型（节省存储费）
client.models.delete("ft:gpt-4o-mini:org:name:id")
```

监控要点：
  训练 loss 应逐步下降
  验证 loss 不应持续上升（过拟合信号）
  通常 10分钟~1小时完成
""")

# 模拟微调任务
class MockFineTuningJob:
    """模拟 OpenAI 微调任务"""

    def __init__(self, data_size: int, epochs: int):
        self.job_id = f"ftjob-{hash(time.time()) % 100000:05d}"
        self.status = "running"
        self.data_size = data_size
        self.epochs = epochs
        self.steps = []
        self._simulate()

    def _simulate(self):
        import numpy as np
        np.random.seed(42)
        total_steps = self.data_size * self.epochs // 4  # batch_size=4
        loss = 2.0
        for step in range(1, total_steps + 1):
            loss = max(0.3, loss - 0.1 + np.random.normal(0, 0.02))
            if step % max(1, total_steps // 10) == 0:
                self.steps.append({"step": step, "loss": round(loss, 4)})
        self.status = "succeeded"
        self.model_id = f"ft:gpt-4o-mini:org:custom:{self.job_id[-5:]}"

    def get_events(self) -> list:
        events = [f"[开始] 训练数据: {self.data_size}条, epochs: {self.epochs}"]
        for s in self.steps:
            events.append(f"[Step {s['step']}] training loss = {s['loss']}")
        events.append(f"[完成] 模型: {self.model_id}")
        return events

job = MockFineTuningJob(len(sample_qa), 3)
print("模拟微调任务:")
print(f"  Job ID: {job.job_id}")
print(f"  Status: {job.status}")
for event in job.get_events():
    print(f"  {event}")

# ============================================================================
# 5. 使用微调模型
# ============================================================================
print("\n--- 5. 使用微调模型 ---")
print("""
```python
# 使用微调后的模型（和普通 API 调用完全一样）
response = client.chat.completions.create(
    model="ft:gpt-4o-mini:org:my-customer-service:abc123",
    messages=[
        {"role": "system", "content": "你是客服助手"},
        {"role": "user", "content": "退款要多久？"},
    ]
)
print(response.choices[0].message.content)

# 微调模型的优势
# 1. 不需要长 System Prompt（已学会风格）
# 2. 输出更稳定（格式一致）
# 3. 更便宜（更短的 Prompt）
# 4. 更快（更少的 token）

# 对比：
# 微调前: 需要500 token的System Prompt + 示例
# 微调后: 只需要简短的System Prompt（或不需要）
```

微调模型也支持：
  ✅ 流式输出
  ✅ Function Calling
  ✅ JSON mode
  ✅ Vision（gpt-4o 微调）
  ❌ 不支持 Structured Outputs（暂时）
""")

# ============================================================================
# 6. 成本与最佳实践
# ============================================================================
print("\n--- 6. 最佳实践 ---")
print("""
成本控制：
┌─────────────────────────┬──────────────────────────────┐
│  项目                    │  说明                         │
├─────────────────────────┼──────────────────────────────┤
│  训练费                  │  按训练 token 数计费          │
│  推理费                  │  比基础模型略贵               │
│  存储费                  │  免费（模型存储不收费）       │
│  最小数据量              │  10条，推荐50+               │
└─────────────────────────┴──────────────────────────────┘

成本估算示例：
  500条数据，平均500token/条，3 epochs
  训练token = 500 × 500 × 3 = 750,000
  训练费 = 0.75M × $3.00/M = $2.25

最佳实践：
  1. 先用 gpt-4o-mini（便宜试错）
  2. 效果好再考虑 gpt-4o
  3. 数据质量 > 数量（100条好数据 > 1000条差数据）
  4. 一定要准备验证集（至少20%）
  5. n_epochs 从 3 开始，看 eval loss 决定增减
  6. 微调后用 LLM-as-Judge 评估
  7. 保留原始模型对比（确认微调确实提升了）

OpenAI vs 本地微调：
  ┌────────────────┬──────────────────┬──────────────────┐
  │                │  OpenAI          │  本地(QLoRA)      │
  ├────────────────┼──────────────────┼──────────────────┤
  │  门槛          │  只需API Key     │  需要GPU          │
  │  模型          │  GPT-4o系列     │  任意开源模型      │
  │  训练成本      │  ~$2-50         │  电费             │
  │  推理成本      │  按token计费     │  免费（自己的GPU）│
  │  数据隐私      │  上传到OpenAI   │  完全本地          │
  │  灵活性        │  参数有限       │  完全控制          │
  │  最大数据量    │  50MB/文件      │  无限制            │
  └────────────────┴──────────────────┴──────────────────┘
""")

print("\n" + "=" * 60)
print("[完成] 第5课完成！你已经学会了：")
print("  [v] OpenAI 微调 5 步流程")
print("  [v] JSONL 数据准备与验证")
print("  [v] 创建微调任务（API + 超参数）")
print("  [v] 监控训练进度（事件/日志）")
print("  [v] 使用微调模型（与普通API相同）")
print("  [v] 成本控制与 OpenAI vs 本地对比")
print("=" * 60)
print("\n下一课：06_evaluation.py - 评估与对比")
