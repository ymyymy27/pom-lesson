import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第4课：训练实战（SFTTrainer / 超参数 / 监控）
==============================================================================

用 HuggingFace TRL 库的 SFTTrainer 进行实际微调训练。

本课内容：
1. SFTTrainer 完整流程
2. 超参数调优指南
3. 训练监控与调试
4. 常见问题排查
5. 分布式训练
6. Unsloth 加速方案
==============================================================================
"""

import json
import numpy as np

print("=" * 60)
print("第4课：训练实战")
print("=" * 60)

# ============================================================================
# 1. SFTTrainer 完整流程
# ============================================================================
print("\n--- 1. SFTTrainer ---")
print("""
SFTTrainer（Supervised Fine-Tuning Trainer）是 TRL 库提供的微调训练器。

完整流程：

```python
import torch
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    TrainingArguments, BitsAndBytesConfig,
)
from peft import LoraConfig, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import load_dataset

# ============ Step 1: 加载模型 ============
model_name = "Qwen/Qwen2.5-7B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token  # 确保有 pad token

# QLoRA 量化配置
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)
model = prepare_model_for_kbit_training(model)

# ============ Step 2: LoRA 配置 ============
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# ============ Step 3: 数据 ============
dataset = load_dataset("json", data_files={
    "train": "train.jsonl",
    "validation": "val.jsonl",
})

def format_chat(example):
    text = tokenizer.apply_chat_template(
        example["messages"],
        tokenize=False,
        add_generation_prompt=False
    )
    return {"text": text}

dataset = dataset.map(format_chat)

# ============ Step 4: 训练参数 ============
training_args = TrainingArguments(
    output_dir="./output",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=4,     # 有效batch=2×4=8
    learning_rate=2e-4,
    warmup_steps=10,
    lr_scheduler_type="cosine",
    logging_steps=10,
    eval_steps=50,
    save_steps=100,
    save_total_limit=3,
    fp16=True,
    optim="paged_adamw_8bit",
    report_to="none",                  # 或 "wandb"
    evaluation_strategy="steps",
    load_best_model_at_end=True,
)

# ============ Step 5: 训练 ============
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    peft_config=lora_config,
    args=training_args,
    dataset_text_field="text",
    max_seq_length=2048,
    tokenizer=tokenizer,
)

trainer.train()

# ============ Step 6: 保存 ============
trainer.save_model("./final-adapter")
tokenizer.save_pretrained("./final-adapter")
```
""")

# ============================================================================
# 2. 超参数调优
# ============================================================================
print("\n--- 2. 超参数调优 ---")
print("""
┌──────────────────────┬─────────────┬──────────────────────────────┐
│  参数                 │  建议范围    │  说明                         │
├──────────────────────┼─────────────┼──────────────────────────────┤
│  learning_rate       │ 1e-4 ~ 5e-4│  QLoRA 可稍大                │
│                      │             │  全参微调: 1e-5 ~ 5e-5       │
├──────────────────────┼─────────────┼──────────────────────────────┤
│  num_train_epochs    │ 1 ~ 5      │  数据少: 3-5轮               │
│                      │             │  数据多(>5000): 1-2轮        │
├──────────────────────┼─────────────┼──────────────────────────────┤
│  batch_size(有效)    │ 4 ~ 32     │  per_device × accumulation   │
│                      │             │  显存不够就用 accumulation   │
├──────────────────────┼─────────────┼──────────────────────────────┤
│  max_seq_length      │ 512 ~ 4096 │  看数据长度分布决定          │
│                      │             │  太长浪费显存，太短截断数据  │
├──────────────────────┼─────────────┼──────────────────────────────┤
│  warmup_steps        │ 5 ~ 50     │  总步数的 3%-10%             │
├──────────────────────┼─────────────┼──────────────────────────────┤
│  lr_scheduler        │ cosine     │  cosine 最稳定               │
│                      │ linear     │  linear 也常用               │
├──────────────────────┼─────────────┼──────────────────────────────┤
│  gradient_checkpointing│ True     │  省显存(牺牲~20%速度)        │
└──────────────────────┴─────────────┴──────────────────────────────┘

调参优先级（从高到低）：
  1. learning_rate（最重要）
  2. num_epochs（第二重要）
  3. r 和 target_modules（LoRA容量）
  4. batch_size
  5. max_seq_length
""")

# 模拟训练日志
class TrainingSimulator:
    """模拟训练过程"""

    def simulate(self, config: dict) -> list:
        np.random.seed(42)
        steps_per_epoch = config.get("steps_per_epoch", 100)
        epochs = config.get("epochs", 3)
        lr = config.get("lr", 2e-4)
        total_steps = steps_per_epoch * epochs

        log = []
        loss = 2.5  # 初始 loss
        for step in range(1, total_steps + 1):
            progress = step / total_steps
            # 学习率 cosine 衰减
            current_lr = lr * 0.5 * (1 + np.cos(np.pi * progress))
            # loss 下降 + 噪声
            loss = max(0.3, loss - 0.005 + np.random.normal(0, 0.02))
            # eval loss（略高于 train loss）
            eval_loss = loss + 0.1 + np.random.normal(0, 0.03)

            if step % 50 == 0 or step == 1:
                log.append({
                    "step": step, "epoch": step / steps_per_epoch,
                    "train_loss": round(loss, 4),
                    "eval_loss": round(eval_loss, 4),
                    "lr": round(current_lr, 8),
                })
        return log

sim = TrainingSimulator()
logs = sim.simulate({"steps_per_epoch": 100, "epochs": 3, "lr": 2e-4})

print("\n模拟训练日志:")
print(f"  {'Step':>6} {'Epoch':>6} {'Train Loss':>12} {'Eval Loss':>12} {'LR':>12}")
print(f"  {'-'*55}")
for entry in logs:
    print(f"  {entry['step']:>6} {entry['epoch']:>6.1f} "
          f"{entry['train_loss']:>12.4f} {entry['eval_loss']:>12.4f} "
          f"{entry['lr']:>12.8f}")

# ============================================================================
# 3. 训练监控
# ============================================================================
print("\n--- 3. 训练监控 ---")
print("""
关键指标监控：

1. Training Loss
   正常：持续下降
   异常：突然上升 → lr 太大 / 数据质量问题
   异常：不下降 → lr 太小 / 模型冻结

2. Eval Loss
   正常：与 train loss 同步下降
   异常：train↓ eval↑ → 过拟合！

3. Learning Rate
   cosine: 先升后降
   linear: 均匀下降

过拟合信号及应对：
  ┌──────────────────────┬──────────────────────────────┐
  │  信号                 │  应对                         │
  ├──────────────────────┼──────────────────────────────┤
  │  train_loss↓eval↑    │  减少 epochs / 增大 dropout  │
  │  输出变成复述训练数据│  减小 r / 增加数据量         │
  │  输出格式非常统一    │  增加数据多样性              │
  │  对新问题答不上来    │  减少 epochs / 降低 lr       │
  └──────────────────────┴──────────────────────────────┘

使用 W&B 监控：
```python
# pip install wandb
import wandb
wandb.init(project="my-finetune")

training_args = TrainingArguments(
    ...,
    report_to="wandb",
)
```
""")

# ============================================================================
# 4. 常见问题
# ============================================================================
print("\n--- 4. 常见问题 ---")
print("""
┌──────────────────────────┬──────────────────────────────────┐
│  问题                     │  解决方案                         │
├──────────────────────────┼──────────────────────────────────┤
│  OOM (显存不足)          │  减小 batch_size                  │
│                          │  开启 gradient_checkpointing     │
│                          │  减小 max_seq_length             │
│                          │  用 QLoRA 代替 LoRA              │
├──────────────────────────┼──────────────────────────────────┤
│  loss 不下降             │  检查数据格式是否正确            │
│                          │  增大 learning_rate              │
│                          │  检查 LoRA 是否正确应用          │
├──────────────────────────┼──────────────────────────────────┤
│  loss NaN                │  降低 learning_rate              │
│                          │  检查数据中是否有异常值          │
│                          │  用 fp32 代替 fp16               │
├──────────────────────────┼──────────────────────────────────┤
│  微调后效果变差          │  数据质量问题 → 审核数据         │
│                          │  过拟合 → 减少 epochs            │
│                          │  lr 太大 → 降低 lr               │
├──────────────────────────┼──────────────────────────────────┤
│  训练太慢                │  增大 batch_size                  │
│                          │  使用 Unsloth 加速               │
│                          │  减小 max_seq_length             │
├──────────────────────────┼──────────────────────────────────┤
│  输出重复/乱码          │  检查 tokenizer 配置             │
│                          │  检查 chat template              │
│                          │  减少 epochs                     │
└──────────────────────────┴──────────────────────────────────┘

调试技巧：
  先用少量数据(10条)跑通全流程
  确认 loss 能下降再用全量数据
  每次只改一个参数
""")

# ============================================================================
# 5. 分布式训练
# ============================================================================
print("\n--- 5. 分布式训练 ---")
print("""
多 GPU 训练方案：

1. Accelerate（HuggingFace 官方）
```bash
# 配置
accelerate config

# 启动（自动分布式）
accelerate launch train.py
```

2. DeepSpeed（微软，大模型首选）
```python
training_args = TrainingArguments(
    ...,
    deepspeed="ds_config.json",
)
```

ds_config.json:
```json
{
  "zero_optimization": {
    "stage": 2,
    "offload_optimizer": {"device": "cpu"}
  },
  "fp16": {"enabled": true},
  "train_micro_batch_size_per_gpu": 2
}
```

DeepSpeed ZeRO 阶段：
  Stage 1: 优化器状态分片（省1/3显存）
  Stage 2: + 梯度分片（省2/3显存）
  Stage 3: + 参数分片（省更多，但通信多）

推荐：LoRA + ZeRO Stage 2（最佳性价比）
""")

# ============================================================================
# 6. Unsloth 加速
# ============================================================================
print("\n--- 6. Unsloth 加速 ---")
print("""
Unsloth = 2x 加速 + 60% 显存节省的 LoRA 微调库

原理：手写 CUDA 内核优化 Attention 和 LoRA 计算

```python
from unsloth import FastLanguageModel

# 加载（自动量化 + 优化）
model, tokenizer = FastLanguageModel.from_pretrained(
    "unsloth/Qwen2.5-7B-Instruct-bnb-4bit",
    max_seq_length=2048,
    load_in_4bit=True,
)

# LoRA 配置
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
)

# 训练（与标准 SFTTrainer 完全兼容）
from trl import SFTTrainer
trainer = SFTTrainer(model=model, ...)
trainer.train()

# 保存（多种格式）
model.save_pretrained_merged("output", tokenizer)          # 合并保存
model.save_pretrained_gguf("output", tokenizer, "q4_k_m")  # GGUF格式(Ollama)
```

Unsloth 的优势：
  ✅ 训练速度 2x（相比原生HF）
  ✅ 显存节省 60%
  ✅ 兼容 SFTTrainer（零改动迁移）
  ✅ 支持直接导出 GGUF（Ollama可用）
  ✅ 免费开源

最佳实践：
  开发调试 → 标准 HF（更灵活）
  正式训练 → Unsloth（更快更省）
""")

print("\n" + "=" * 60)
print("[完成] 第4课完成！你已经学会了：")
print("  [v] SFTTrainer 完整 6 步训练流程")
print("  [v] 超参数调优指南（优先级+建议值）")
print("  [v] 训练监控（loss/过拟合检测）")
print("  [v] 常见问题排查（OOM/NaN/效果差）")
print("  [v] 分布式训练（Accelerate/DeepSpeed）")
print("  [v] Unsloth 2x 加速方案")
print("=" * 60)
print("\n下一课：05_openai_fine_tuning.py - OpenAI Fine-tuning API")
