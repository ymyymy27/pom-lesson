# LoRA 与 QLoRA 微调

## 学习目标

- 深入理解 LoRA 原理
- 用 PEFT + Transformers 实现 LoRA/QLoRA 微调
- 掌握训练参数调优和评估

## 1. LoRA 原理

LoRA（Low-Rank Adaptation）的核心思想：冻结原始模型参数，只训练小的低秩矩阵。

```
原始权重矩阵 W (d × d)
LoRA 分解：ΔW = A × B
  A: (d × r)  r << d
  B: (r × d)

训练参数量对比（7B 模型）：
- 全参微调：~7B 参数
- LoRA (r=8)：~4M 参数（减少 1000x）

QLoRA 在 LoRA 基础上增加：
- 4-bit 量化基座模型（减少显存）
- 双重量化
- 分页优化器
```

## 2. 环境搭建

```bash
pip install torch transformers datasets peft accelerate bitsandbytes trl
```

## 3. LoRA 微调实战

```python
import torch
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    TrainingArguments, BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import load_dataset

# 1. 加载模型和 tokenizer
model_name = "Qwen/Qwen2.5-7B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

# QLoRA: 4-bit 量化加载
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

# 2. 配置 LoRA
lora_config = LoraConfig(
    r=16,                      # 秩（越大容量越大，但也越慢）
    lora_alpha=32,             # 缩放因子
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# 可训练参数约占总参数的 0.1%

# 3. 准备数据
dataset = load_dataset("json", data_files="train.json")

def format_chat(example):
    """将 messages 格式转为模型输入"""
    text = tokenizer.apply_chat_template(
        example["messages"],
        tokenize=False,
        add_generation_prompt=False
    )
    return {"text": text}

dataset = dataset.map(format_chat)

# 4. 训练配置
training_args = TrainingArguments(
    output_dir="./output",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_steps=10,
    logging_steps=10,
    save_steps=100,
    save_total_limit=3,
    fp16=True,
    optim="paged_adamw_8bit",
    lr_scheduler_type="cosine",
    report_to="none",
)

# 5. 开始训练
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    args=training_args,
    dataset_text_field="text",
    max_seq_length=2048,
    tokenizer=tokenizer,
)

trainer.train()

# 6. 保存 LoRA 适配器
model.save_pretrained("./lora-adapter")
tokenizer.save_pretrained("./lora-adapter")
```

## 4. 使用微调后的模型

```python
from peft import PeftModel

# 加载基座 + LoRA 适配器
base_model = AutoModelForCausalLM.from_pretrained(
    model_name, device_map="auto", torch_dtype=torch.float16
)
model = PeftModel.from_pretrained(base_model, "./lora-adapter")

# 推理
messages = [
    {"role": "system", "content": "你是一个专业助手。"},
    {"role": "user", "content": "你的问题"},
]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
outputs = model.generate(inputs, max_new_tokens=256, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))

# 合并权重（部署用）
merged_model = model.merge_and_unload()
merged_model.save_pretrained("./merged-model")
```

## 5. 超参数调优指南

| 参数 | 建议值 | 说明 |
|------|--------|------|
| r | 8-64 | 秩越大容量越大，通常 16 够用 |
| lora_alpha | 2×r | 缩放因子 |
| learning_rate | 1e-4 ~ 5e-4 | QLoRA 可稍大 |
| epochs | 1-5 | 数据少可多跑几轮 |
| batch_size | 2-8 | 受显存限制 |
| max_seq_length | 512-4096 | 视数据长度定 |

## 6. 评估微调效果

```python
# 1. 人工评估（最重要）
# 准备 20-50 个测试问题，对比微调前后的输出

# 2. 自动指标
from rouge_score import rouge_scorer

scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
scores = scorer.score(reference, generated)

# 3. LLM-as-Judge
judge_prompt = """请评估以下回答的质量（1-5分）：
问题：{question}
回答：{answer}
评分标准：准确性、完整性、专业性
请给出分数和理由。"""
```

## 练习

1. 用 QLoRA 在 Qwen2.5-7B 上微调一个领域助手
2. 对比微调前后在 10 个测试问题上的表现
3. 尝试不同的 r 值（4, 8, 16, 32），观察效果差异
4. 将微调后的模型用 Ollama 部署

## 下一节

→ [03-OpenAI微调与评估](03-OpenAI微调与评估.md)
