import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第4课：推理优化（量化 / 批处理 / KV Cache）
==============================================================================

推理优化 = 用更少的资源、更快的速度运行模型。
三大优化方向：量化减显存、批处理增吞吐、KV Cache 省重复计算。

本课内容：
1. 推理优化全景
2. 模型量化
3. 批处理（Batching）
4. KV Cache 与 PagedAttention
5. 性能基准测试
6. 硬件规划
==============================================================================
"""

import json
import time
import numpy as np

print("=" * 60)
print("第4课：推理优化")
print("=" * 60)

# ============================================================================
# 1. 优化全景
# ============================================================================
print("\n--- 1. 优化全景 ---")
print("""
推理性能三个维度：

  延迟 (Latency):   单请求响应时间
  吞吐 (Throughput): 每秒处理的 token 数
  显存 (Memory):     GPU 显存占用

优化技术：
┌──────────────────┬──────────┬──────────┬──────────┐
│  技术             │  降延迟   │  增吞吐   │  省显存   │
├──────────────────┼──────────┼──────────┼──────────┤
│  量化 (INT4/INT8)│  ✓       │  ✓       │  ✓✓✓    │
│  连续批处理      │          │  ✓✓✓    │          │
│  KV Cache        │  ✓✓     │  ✓       │          │
│  PagedAttention  │  ✓       │  ✓✓     │  ✓✓     │
│  Flash Attention │  ✓✓     │  ✓       │  ✓       │
│  Speculative Dec │  ✓✓     │          │          │
│  张量并行        │  ✓✓     │  ✓✓     │  ✓✓     │
└──────────────────┴──────────┴──────────┴──────────┘
""")

# ============================================================================
# 2. 量化
# ============================================================================
print("\n--- 2. 量化 ---")
print("""
量化 = 用低精度数值表示模型权重

精度对比：
  FP32:  32位浮点  → 基准（训练用）
  FP16:  16位浮点  → 显存减半，精度几乎不变
  INT8:  8位整数   → 显存1/4，精度轻微下降
  INT4:  4位整数   → 显存1/8，精度有一定下降

7B 模型显存需求：
  FP32: ~28GB  → 一般不用
  FP16: ~14GB  → A100 / RTX 4090
  INT8: ~7GB   → RTX 3090
  INT4: ~4.5GB → RTX 3060 / M1 Mac
""")

# 量化效果模拟
class QuantizationSimulator:
    """量化效果模拟器"""

    PROFILES = {
        "FP32": {"bits": 32, "quality": 1.00, "speed_factor": 0.5},
        "FP16": {"bits": 16, "quality": 0.99, "speed_factor": 1.0},
        "INT8": {"bits": 8,  "quality": 0.97, "speed_factor": 1.5},
        "INT4": {"bits": 4,  "quality": 0.93, "speed_factor": 2.0},
        "INT3": {"bits": 3,  "quality": 0.85, "speed_factor": 2.5},
    }

    def estimate(self, model_params_b: float, precision: str) -> dict:
        """估算量化后的资源需求"""
        profile = self.PROFILES.get(precision, self.PROFILES["FP16"])
        memory_gb = model_params_b * profile["bits"] / 8
        return {
            "precision": precision,
            "memory_gb": round(memory_gb, 1),
            "quality": profile["quality"],
            "speed_factor": profile["speed_factor"],
        }

    def compare_all(self, model_params_b: float) -> list:
        results = []
        for prec in self.PROFILES:
            results.append(self.estimate(model_params_b, prec))
        return results

quant = QuantizationSimulator()

print("7B 模型量化对比:")
print(f"  {'精度':<8} {'显存(GB)':>10} {'质量':>8} {'速度':>8}")
print(f"  {'-'*36}")
for r in quant.compare_all(7):
    print(f"  {r['precision']:<8} {r['memory_gb']:>10.1f} {r['quality']:>7.0%} {r['speed_factor']:>7.1f}x")

print("""
常见量化格式：
  GGUF:  llama.cpp 格式，Ollama 使用，CPU 友好
  GPTQ:  GPU 推理优化，vLLM 支持
  AWQ:   激活感知量化，精度更好，vLLM 支持
  bitsandbytes: HuggingFace 动态量化

量化工具：
```python
# GPTQ 量化
from transformers import AutoModelForCausalLM, GPTQConfig
config = GPTQConfig(bits=4, dataset="c4", tokenizer=tokenizer)
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    quantization_config=config, device_map="auto"
)

# AWQ（推荐 vLLM 使用）
# 直接下载 AWQ 量化模型
# python -m vllm.entrypoints.openai.api_server \\
#     --model Qwen/Qwen2.5-7B-Instruct-AWQ \\
#     --quantization awq
```
""")

# ============================================================================
# 3. 批处理
# ============================================================================
print("\n--- 3. 批处理 ---")
print("""
批处理 = 把多个请求合并一起推理

静态批处理（传统）：
  请求1 ──────────→ [批次1] ──→ 回复1
  请求2 ──────────→           ──→ 回复2
  请求3 ──────────→           ──→ 回复3
  ❌ 等最慢的完成，所有请求才返回

连续批处理（vLLM）：
  请求1 ──→ [推理] ──→ 回复1（先完成先返回！）
  请求2 ──→ [推理] ────────→ 回复2
  请求3 ────→ [推理] ──→ 回复3（新请求随时插入！）
  ✅ 先完成先返回，GPU 利用率最高
""")

# 批处理效果模拟
class BatchSimulator:
    """批处理效果模拟"""

    def simulate(self, num_requests: int, base_latency_ms: float,
                 batch_size: int, mode: str = "continuous") -> dict:
        np.random.seed(42)
        token_counts = np.random.randint(50, 200, num_requests)

        if mode == "none":
            # 无批处理：顺序执行
            total_time = sum(base_latency_ms * tc / 100 for tc in token_counts)
            avg_latency = total_time / num_requests
        elif mode == "static":
            # 静态批处理
            num_batches = (num_requests + batch_size - 1) // batch_size
            total_time = 0
            for b in range(num_batches):
                batch = token_counts[b*batch_size:(b+1)*batch_size]
                total_time += base_latency_ms * max(batch) / 100 * 0.4
            avg_latency = total_time / num_requests
        else:
            # 连续批处理
            total_time = base_latency_ms * np.mean(token_counts) / 100 * 0.3
            avg_latency = total_time

        total_tokens = int(np.sum(token_counts))
        throughput = total_tokens / (total_time / 1000) if total_time > 0 else 0

        return {
            "mode": mode,
            "total_time_ms": round(total_time),
            "avg_latency_ms": round(avg_latency),
            "throughput_tps": round(throughput),
        }

batch_sim = BatchSimulator()

print(f"50个请求的批处理对比 (base_latency=100ms):")
print(f"  {'模式':<12} {'总时间(ms)':>12} {'平均延迟(ms)':>14} {'吞吐(t/s)':>12}")
print(f"  {'-'*52}")
for mode in ["none", "static", "continuous"]:
    r = batch_sim.simulate(50, 100, batch_size=8, mode=mode)
    print(f"  {r['mode']:<12} {r['total_time_ms']:>12} {r['avg_latency_ms']:>14} {r['throughput_tps']:>12}")

# ============================================================================
# 4. KV Cache
# ============================================================================
print("\n--- 4. KV Cache ---")
print("""
KV Cache = 缓存已计算的 Key/Value，避免重复计算

Transformer 生成每个 token 时需要看之前所有 token。
没有 KV Cache：每生成一个 token 重算所有历史 → O(n²)
有 KV Cache：缓存历史 K/V，只算新 token → O(n)

  不用KV Cache:
    token1: 算 [t1]
    token2: 算 [t1, t2]        ← 重复算 t1
    token3: 算 [t1, t2, t3]    ← 重复算 t1, t2
    ...

  用KV Cache:
    token1: 算 [t1] → 缓存 K1,V1
    token2: 算 [t2] + 用 K1,V1 → 缓存 K2,V2
    token3: 算 [t3] + 用 K1,V1,K2,V2
    ...

PagedAttention（vLLM 核心）：
  传统 KV Cache：为每个请求预分配最大长度显存
    → 显存浪费严重（平均利用率 ~50%）

  PagedAttention：像操作系统虚拟内存一样管理 KV Cache
    → 按需分页分配，显存利用率 ~95%
    → 相同显存支持更大批次 → 更高吞吐

显存节省（7B 模型，4096 上下文）：
  传统方式:    ~20GB
  PagedAttention: ~14GB（节省 30%）
""")

# KV Cache 显存计算
class KVCacheCalculator:
    """KV Cache 显存计算器"""

    def estimate(self, num_layers: int, hidden_size: int,
                 num_heads: int, seq_len: int,
                 batch_size: int, dtype_bytes: int = 2) -> dict:
        """估算 KV Cache 显存"""
        head_dim = hidden_size // num_heads
        kv_per_token = 2 * num_layers * num_heads * head_dim * dtype_bytes  # K + V
        cache_per_seq = kv_per_token * seq_len
        total = cache_per_seq * batch_size
        return {
            "kv_per_token_bytes": kv_per_token,
            "per_sequence_mb": round(cache_per_seq / 1e6, 1),
            "total_gb": round(total / 1e9, 2),
            "batch_size": batch_size,
            "seq_len": seq_len,
        }

calc = KVCacheCalculator()

# 7B 模型: 32 layers, 4096 hidden, 32 heads
print("\nKV Cache 显存估算 (7B 模型, FP16):")
for batch, seq in [(1, 2048), (1, 4096), (8, 2048), (8, 4096), (32, 2048)]:
    r = calc.estimate(32, 4096, 32, seq, batch)
    print(f"  batch={batch:>2}, seq={seq:>5}: {r['total_gb']:.2f}GB")

# ============================================================================
# 5. 性能基准
# ============================================================================
print("\n--- 5. 性能基准 ---")
print("""
性能基准测试指标：

  TTFT (Time To First Token):  首 token 延迟
  TPOT (Time Per Output Token): 每个 token 生成时间
  总延迟 = TTFT + TPOT × 输出token数
  吞吐量 = 总输出token / 总时间

基准测试脚本：
```python
import asyncio, time
from openai import AsyncOpenAI

async def benchmark(url, model, n=50, prompt="写100字自我介绍"):
    client = AsyncOpenAI(base_url=url, api_key="token")
    latencies, tps_list = [], []

    async def single():
        start = time.time()
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        elapsed = time.time() - start
        tokens = resp.usage.completion_tokens
        latencies.append(elapsed)
        tps_list.append(tokens / elapsed)

    start = time.time()
    await asyncio.gather(*[single() for _ in range(n)])
    total = time.time() - start

    print(f"QPS: {n/total:.1f}")
    print(f"Avg latency: {sum(latencies)/len(latencies):.2f}s")
    print(f"P95 latency: {sorted(latencies)[int(0.95*n)]:.2f}s")
    print(f"Avg throughput: {sum(tps_list)/len(tps_list):.0f} t/s")
```
""")

# 模拟基准测试
np.random.seed(42)
frameworks = {
    "Ollama (CPU)":     {"base_tps": 8, "latency_base": 2.0},
    "Ollama (GPU)":     {"base_tps": 35, "latency_base": 0.5},
    "vLLM (GPU)":       {"base_tps": 120, "latency_base": 0.3},
    "vLLM (batched)":   {"base_tps": 500, "latency_base": 0.8},
}

print(f"模拟基准对比 (7B 模型):")
print(f"  {'框架':<20} {'吞吐(t/s)':>10} {'单请求延迟':>12} {'并发QPS':>10}")
print(f"  {'-'*54}")
for name, profile in frameworks.items():
    tps = profile["base_tps"] + np.random.randint(-3, 3)
    latency = profile["latency_base"] + np.random.uniform(-0.1, 0.1)
    qps = round(tps / 100 * 10, 1)
    print(f"  {name:<20} {tps:>10} {latency:>11.2f}s {qps:>10}")

# ============================================================================
# 6. 硬件规划
# ============================================================================
print("\n--- 6. 硬件规划 ---")
print("""
硬件选型指南：

┌──────────────┬──────────┬──────────┬──────────────────┐
│  场景         │  GPU      │  模型     │  预算             │
├──────────────┼──────────┼──────────┼──────────────────┤
│  开发测试    │  无/集显  │  7B INT4 │  免费（Ollama）   │
│  个人项目    │  RTX 3060│  7B INT4 │  ~2000元          │
│  小团队      │  RTX 4090│  7B FP16 │  ~15000元         │
│  中型服务    │  A100 40G│  14B FP16│  ~10万元/云GPU    │
│  大型服务    │  A100 80G│  70B INT4│  ~20万元/云GPU    │
│  超大规模    │  8×A100  │  70B FP16│  ~100万元         │
└──────────────┴──────────┴──────────┴──────────────────┘

云 GPU 服务（按需租用）：
  AWS:     p4d.24xlarge (8×A100)
  阿里云:  GPU 计算型实例
  AutoDL:  按小时计费（便宜）
  RunPod:  社区 GPU 云

容量规划公式：
  所需 GPU 数 = 峰值 QPS × 平均延迟 / 单 GPU 并发数
  示例: 50 QPS × 2秒 / 10并发 = 10 GPU
""")

print("=" * 60)
print("[完成] 第4课完成！你已经学会了：")
print("  [v] 推理优化三维度（延迟/吞吐/显存）")
print("  [v] 量化（FP16/INT8/INT4/GGUF/GPTQ/AWQ）")
print("  [v] 批处理（静态 vs 连续批处理）")
print("  [v] KV Cache 与 PagedAttention")
print("  [v] 性能基准测试方法")
print("  [v] 硬件规划与成本估算")
print("=" * 60)
print("\n下一课：05_monitoring.py - 监控体系")
