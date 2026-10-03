> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# vLLM 术语表与选型速查

## 1. 核心术语

| 术语 | 英文 | 一句话解释 |
|------|------|-----------|
| 推理 | Inference | 用已训练模型生成输出（区别于训练/微调） |
| KV Cache | Key-Value Cache | 缓存已算过的 K/V 向量，避免重复计算历史 token |
| PagedAttention | — | 像 OS 虚拟内存一样分页管理 KV Cache，消除显存碎片 |
| 连续批处理 | Continuous Batching | 每个 decode 步动态增删请求，不等整批完成 |
| Prefill | — | 处理输入 prompt 的阶段（计算密集） |
| Decode | — | 逐 token 生成的阶段（内存带宽密集） |
| TTFT | Time To First Token | 首 token 延迟（用户感知的「开始响应」时间） |
| TPOT | Time Per Output Token | 每个输出 token 的平均生成时间 |
| 吞吐 | Throughput | 单位时间处理的 token 数（tokens/s） |
| 张量并行 | Tensor Parallelism (TP) | 单层权重切分到多 GPU |
| 流水线并行 | Pipeline Parallelism (PP) | 不同层分配到不同 GPU |
| 前缀缓存 | Prefix Caching | 相同 prompt 前缀复用 KV Cache 块 |
| Chunked Prefill | — | 长 prompt 分块 prefill，与 decode 共存 |
| 分离式推理 | Disaggregated Serving | Prefill 与 Decode 节点独立扩缩容 |
| 投机解码 | Speculative Decoding | 小模型草稿 + 大模型验证，加速 decode |

---

## 2. vLLM vs 其他框架

| 维度 | vLLM | Ollama | TGI | SGLang |
|------|------|--------|-----|--------|
| 定位 | 生产级 GPU 推理引擎 | 本地开发/轻量部署 | HuggingFace 生产服务 | 高性能推理 + 复杂控制流 |
| GPU 吞吐 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 上手难度 | 中 | 低 | 中 | 中高 |
| OpenAI API | ✅ 原生 | ✅ 兼容 | ✅ 兼容 | ✅ 兼容 |
| CPU 推理 | ❌ 非重点 | ✅ 强 | 有限 | 有限 |
| 多 GPU | TP/PP/EP | 有限 | ✅ | ✅ |
| 典型场景 | 高并发 API 服务 | 个人本地开发 | HF 生态部署 | Agent/多步推理 |

### 选型决策树

```
需要 GPU 高并发生产服务？
  ├─ 是 → vLLM 或 SGLang（复杂 Agent 控制流偏 SGLang）
  └─ 否 → 继续

只是本地开发/调试？
  ├─ 是 → Ollama（最简单）
  └─ 否 → 继续

已在 HuggingFace 生态且并发中等？
  ├─ 是 → TGI
  └─ 否 → vLLM
```

---

## 3. 关键 CLI 参数速查

| 参数 | 含义 | 典型值 |
|------|------|--------|
| `--model` | HuggingFace 模型 ID 或本地路径 | `Qwen/Qwen2.5-7B-Instruct` |
| `--dtype` | 权重精度 | `auto` / `float16` / `bfloat16` |
| `--max-model-len` | 最大上下文长度 | `4096` / `8192` / `32768` |
| `--gpu-memory-utilization` | GPU 显存使用上限比例 | `0.85`–`0.95` |
| `--max-num-seqs` | 最大并发序列数 | `64`–`256` |
| `--max-num-batched-tokens` | 单步最大 batched token 数 | `4096`–`16384` |
| `--tensor-parallel-size` | 张量并行 GPU 数 | `1` / `2` / `4` / `8` |
| `--quantization` | 量化方式 | `awq` / `gptq` / `fp8` |
| `--enable-prefix-caching` | 开启前缀缓存 | flag |
| `--port` | API 端口 | `8000` |

---

## 4. 显存估算公式（7B 模型参考）

```
模型权重 (FP16) ≈ 参数量(B) × 2 GB
  7B FP16 ≈ 14 GB

KV Cache ≈ 2 × num_layers × hidden_size × seq_len × batch × dtype_bytes
  7B, seq=4096, batch=1, FP16 ≈ 1–2 GB
  7B, seq=4096, batch=32, FP16 ≈ 30+ GB

总显存 ≈ 权重 + KV Cache + 激活 + 框架开销
安全余量：gpu-memory-utilization 设 0.9，留 10% 给碎片与峰值
```

---

## 5. 常见错误码

| 现象 | 可能原因 | 处理 |
|------|---------|------|
| CUDA OOM | max-model-len 过大 / 并发过高 | 降 max-model-len、max-num-seqs 或换量化模型 |
| 模型加载失败 | 网络/HF token/路径错误 | 设 `HF_ENDPOINT` 或本地 `--model /path` |
| 首 token 极慢 | 冷启动 + 长 prefill | Chunked Prefill、前缀缓存 |
| 吞吐低 | 并发不足 / batch 参数过小 | 提高 max-num-seqs，压测找甜点 |
| 精度异常 | 量化模型不匹配 | `--quantization` 与模型格式一致 |

---

**下一课** → [`01-第1课vLLM 基础 — 推理瓶颈与工程全景.md`](<01-第1课vLLM 基础 — 推理瓶颈与工程全景.md>)
