import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：LoRA / QLoRA 原理与实践
==============================================================================

LoRA = Low-Rank Adaptation（低秩适配）
QLoRA = Quantized LoRA（量化LoRA）

核心思想：不动原始模型参数，只训练一小组"旁路"参数。
就像给模型"戴上眼镜"——眼镜很轻，但能改变视角。

本课内容：
1. LoRA 数学原理
2. LoRA 关键参数
3. QLoRA 量化原理
4. PEFT 库使用
5. 目标模块选择
6. LoRA 适配器管理
==============================================================================
"""

import json
import numpy as np

print("=" * 60)
print("第3课：LoRA / QLoRA 原理")
print("=" * 60)

# ============================================================================
# 1. LoRA 数学原理
# ============================================================================
print("\n--- 1. LoRA 原理 ---")
print("""
传统全参微调：
  W' = W + ΔW     (更新所有 d×d 参数)
  参数量 = d² = 4096² = 16,777,216

LoRA 的核心：用低秩分解近似 ΔW
  ΔW ≈ A × B
  A: (d × r)    下投影
  B: (r × d)    上投影
  r << d        r 是"秩"

  参数量 = d×r + r×d = 2×d×r = 2×4096×16 = 131,072
  压缩比 = 16,777,216 / 131,072 ≈ 128x

推理时：
  输出 = W·x + α/r · A·B·x
  α: 缩放因子（lora_alpha）
  r: 秩（rank）

  ┌──────────┐
  │  输入 x   │
  └────┬─────┘
       │
       ├─────────────────────┐
       │                     │
  ┌────▼─────┐         ┌────▼─────┐
  │ 原始权重  │         │ LoRA旁路  │
  │ W (冻结) │         │ A→B (训练)│
  │ d × d    │         │ d×r + r×d │
  └────┬─────┘         └────┬─────┘
       │                     │
       └──────────┬──────────┘
                  │ 相加
            ┌─────▼─────┐
            │  输出 y    │
            └───────────┘
""")

# 可视化 LoRA 参数压缩
d = 4096  # 典型维度
print("LoRA 参数压缩效果:")
print(f"  {'秩(r)':>6}  {'LoRA参数':>12}  {'原始参数':>12}  {'压缩比':>8}  {'占比':>8}")
print(f"  {'-'*55}")
for r in [4, 8, 16, 32, 64, 128]:
    lora_params = 2 * d * r
    full_params = d * d
    ratio = full_params / lora_params
    pct = lora_params / full_params * 100
    print(f"  {r:>6}  {lora_params:>12,}  {full_params:>12,}  {ratio:>7.0f}x  {pct:>6.2f}%")

# 模拟 LoRA 前向传播
print("\nLoRA 前向传播模拟:")
np.random.seed(42)
d_model = 8  # 小维度演示
r = 2  # 秩

W = np.random.randn(d_model, d_model) * 0.1  # 原始权重（冻结）
A = np.random.randn(d_model, r) * 0.01        # LoRA A矩阵（训练）
B = np.random.randn(r, d_model) * 0.01        # LoRA B矩阵（训练）
x = np.random.randn(1, d_model)               # 输入

alpha = 16
scaling = alpha / r

y_original = x @ W                              # 原始输出
y_lora = x @ W + scaling * (x @ A @ B)          # LoRA 输出
delta = np.linalg.norm(y_lora - y_original)

print(f"  维度: {d_model}, 秩: {r}, alpha: {alpha}")
print(f"  原始参数: {d_model*d_model}, LoRA参数: {2*d_model*r}")
print(f"  输出差异: {delta:.4f}")

# ============================================================================
# 2. LoRA 关键参数
# ============================================================================
print("\n--- 2. 关键参数 ---")
print("""
┌──────────────────┬────────┬──────────────────────────────────┐
│  参数             │ 建议值 │  说明                             │
├──────────────────┼────────┼──────────────────────────────────┤
│  r (秩)          │ 8-64   │  越大容量越大，训练越慢           │
│                  │        │  8: 轻量微调                      │
│                  │        │  16: 常用（推荐起步）              │
│                  │        │  32-64: 复杂任务                  │
├──────────────────┼────────┼──────────────────────────────────┤
│  lora_alpha      │ 2×r    │  缩放因子                         │
│                  │        │  实际缩放 = alpha/r               │
│                  │        │  alpha=32, r=16 → 缩放=2          │
├──────────────────┼────────┼──────────────────────────────────┤
│  lora_dropout    │ 0.05   │  防过拟合                         │
│                  │        │  数据少时可设 0.1                  │
│                  │        │  数据多时可设 0.0                  │
├──────────────────┼────────┼──────────────────────────────────┤
│  target_modules  │ 见下文 │  应用 LoRA 的层                   │
│                  │        │  attention层最重要                 │
├──────────────────┼────────┼──────────────────────────────────┤
│  bias            │ "none" │  是否训练偏置                     │
│                  │        │  "none"/"all"/"lora_only"         │
└──────────────────┴────────┴──────────────────────────────────┘

r 的选择策略：
  先用 r=16 跑一版 → 效果不够 → 增大到 32/64
  不要一开始就用很大的 r，容易过拟合
""")

# ============================================================================
# 3. QLoRA 量化原理
# ============================================================================
print("\n--- 3. QLoRA ---")
print("""
QLoRA = 量化基座 + LoRA 训练

三大创新：
1. NF4 量化（NormalFloat 4-bit）
   FP16 (16bit) → NF4 (4bit)
   显存减少 4x
   精度几乎无损（因为是对正态分布优化的量化）

2. 双重量化（Double Quantization）
   先量化权重，再量化量化常数
   进一步节省 ~0.4GB/billion参数

3. 分页优化器（Paged Optimizers）
   优化器状态超出显存时自动转移到CPU
   避免 OOM（显存不足）

显存对比（7B 模型）：
  全参 FP16:   ~60GB（训练）
  LoRA FP16:   ~16GB（训练）
  QLoRA NF4:   ~6GB（训练）← 消费级显卡可用！
  推理 NF4:    ~4GB

```python
from transformers import BitsAndBytesConfig
import torch

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,                 # 4-bit 量化
    bnb_4bit_quant_type="nf4",         # NF4 量化类型
    bnb_4bit_compute_dtype=torch.float16,  # 计算精度
    bnb_4bit_use_double_quant=True,    # 双重量化
)

model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    quantization_config=bnb_config,
    device_map="auto",
)
```
""")

# 量化效果模拟
print("量化效果模拟:")
model_sizes = [
    ("1.5B", 1.5e9),
    ("7B", 7e9),
    ("13B", 13e9),
    ("70B", 70e9),
]
print(f"  {'模型':>6}  {'FP16':>8}  {'INT8':>8}  {'NF4':>8}  {'NF4训练':>10}")
print(f"  {'-'*50}")
for name, params in model_sizes:
    fp16 = params * 2 / 1e9
    int8 = params * 1 / 1e9
    nf4 = params * 0.5 / 1e9
    nf4_train = nf4 * 1.5  # 训练约1.5倍推理显存
    print(f"  {name:>6}  {fp16:>6.1f}GB  {int8:>6.1f}GB  {nf4:>6.1f}GB  {nf4_train:>8.1f}GB")

# ============================================================================
# 4. PEFT 库使用
# ============================================================================
print("\n--- 4. PEFT 库 ---")
print("""
PEFT (Parameter-Efficient Fine-Tuning) 是 HuggingFace 的高效微调库。

```python
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# 1. QLoRA: 准备量化模型
model = prepare_model_for_kbit_training(model)

# 2. 配置 LoRA
lora_config = LoraConfig(
    r=16,                          # 秩
    lora_alpha=32,                 # 缩放因子
    target_modules=[               # 目标层
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_dropout=0.05,             # Dropout
    bias="none",                   # 不训练偏置
    task_type="CAUSAL_LM",         # 任务类型
)

# 3. 应用 LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# trainable params: 4,194,304 || all params: 7,615,808,512 || 0.055%

# 4. 训练后保存
model.save_pretrained("./my-lora-adapter")
# 只保存了 ~16MB 的 LoRA 权重！

# 5. 加载使用
from peft import PeftModel
base_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
model = PeftModel.from_pretrained(base_model, "./my-lora-adapter")
```

LoRA 适配器文件很小（~16MB），可以轻松分享和切换。
同一个基座模型可以挂载不同的 LoRA 适配器 → 不同的"技能"。
""")

# ============================================================================
# 5. 目标模块选择
# ============================================================================
print("\n--- 5. 目标模块 ---")
print("""
选择哪些层应用 LoRA：

Transformer 层的组成：
  ┌─────────────────────────────────────────┐
  │  Self-Attention                          │
  │  ├── q_proj (Query投影)    ← LoRA ✅   │
  │  ├── k_proj (Key投影)      ← LoRA ✅   │
  │  ├── v_proj (Value投影)    ← LoRA ✅   │
  │  └── o_proj (Output投影)   ← LoRA ✅   │
  │                                         │
  │  FFN (Feed-Forward Network)             │
  │  ├── gate_proj             ← LoRA ✅   │
  │  ├── up_proj               ← LoRA ✅   │
  │  └── down_proj             ← LoRA ✅   │
  └─────────────────────────────────────────┘

推荐策略：
┌────────────────────┬──────────────────────────────────┐
│  场景               │  target_modules                   │
├────────────────────┼──────────────────────────────────┤
│  最小化(省显存)    │  ["q_proj", "v_proj"]            │
│  标准(推荐)        │  ["q_proj","k_proj","v_proj",    │
│                    │   "o_proj"]                       │
│  完整(最佳效果)    │  ["q_proj","k_proj","v_proj",    │
│                    │   "o_proj","gate_proj",           │
│                    │   "up_proj","down_proj"]          │
└────────────────────┴──────────────────────────────────┘

不同模型的模块名称不同：
  Qwen:   q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
  LLaMA:  同上
  Mistral: 同上
  GPT-2:  c_attn, c_proj, c_fc

如何找到模块名：
```python
for name, module in model.named_modules():
    if "Linear" in str(type(module)):
        print(name)
```
""")

# 模拟参数量计算
def calc_lora_params(d_model: int, r: int, n_layers: int,
                     modules_per_layer: int) -> dict:
    params_per_module = 2 * d_model * r
    total_lora = params_per_module * modules_per_layer * n_layers
    total_model = d_model * d_model * modules_per_layer * n_layers
    return {
        "lora_params": total_lora,
        "model_params": total_model,
        "ratio": total_lora / total_model * 100,
        "lora_size_mb": total_lora * 2 / 1024 / 1024,  # FP16
    }

print("LoRA 参数量估算:")
configs = [
    ("7B最小(qv)", 4096, 16, 32, 2),
    ("7B标准(qkvo)", 4096, 16, 32, 4),
    ("7B完整(all)", 4096, 16, 32, 7),
    ("13B完整(all)", 5120, 16, 40, 7),
]
print(f"  {'配置':<18} {'LoRA参数':>12} {'占比':>8} {'文件大小':>10}")
print(f"  {'-'*55}")
for name, d, r, layers, mods in configs:
    result = calc_lora_params(d, r, layers, mods)
    print(f"  {name:<18} {result['lora_params']:>10,} {result['ratio']:>6.2f}% {result['lora_size_mb']:>8.1f}MB")

# ============================================================================
# 6. LoRA 适配器管理
# ============================================================================
print("\n--- 6. 适配器管理 ---")
print("""
LoRA 适配器的独特优势：文件小，可以像"插件"一样管理。

多适配器切换：
```python
from peft import PeftModel

base_model = load_base_model("Qwen/Qwen2.5-7B-Instruct")

# 加载客服适配器
model = PeftModel.from_pretrained(base_model, "./lora-customer-service")
response = generate(model, "退款流程？")

# 切换到医疗适配器
model.load_adapter("./lora-medical", adapter_name="medical")
model.set_adapter("medical")
response = generate(model, "头痛怎么办？")

# 切换回客服
model.set_adapter("default")
```

适配器合并（部署用）：
```python
# 合并 LoRA 到基座（变成普通模型）
merged = model.merge_and_unload()
merged.save_pretrained("./merged-model")
# 合并后不再需要 PEFT，推理速度无损
```

适配器叠加（实验性）：
```python
# 同时使用多个 LoRA
model.load_adapter("./lora-style", adapter_name="style")
model.load_adapter("./lora-domain", adapter_name="domain")
model.set_adapter(["style", "domain"])  # 叠加
```

管理策略：
  开发：保留独立适配器（灵活切换）
  部署：合并为单一模型（性能最优）
""")

print("\n" + "=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] LoRA 低秩分解数学原理")
print("  [v] LoRA 关键参数（r/alpha/dropout/target）")
print("  [v] QLoRA 三大创新（NF4/双重量化/分页优化器）")
print("  [v] PEFT 库的完整使用流程")
print("  [v] 目标模块选择策略")
print("  [v] LoRA 适配器管理（切换/合并/叠加）")
print("=" * 60)
print("\n下一课：04_training_practice.py - 训练实战")
