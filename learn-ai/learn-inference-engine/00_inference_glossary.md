# 推理引擎术语表与选型速查

## 1. 核心术语

| 术语 | 英文 | 一句话解释 |
|------|------|-----------|
| 推理 | Inference | 用已训练模型生成输出（区别于训练/微调） |
| 推理引擎 | Inference Engine | 把模型权重变成高效在线服务的系统（调度、显存、批处理） |
| Serving | Serving | 以 API 形式对外提供模型能力，含网关、并发、可观测性 |
| Prefill | — | 一次性处理输入 prompt、生成初始 KV Cache 的阶段（计算密集） |
| Decode | — | 逐 token 生成输出的阶段（显存带宽密集） |
| KV Cache | Key-Value Cache | 缓存已算过的 K/V 向量，避免重复计算历史 token |
| PagedAttention | — | 像 OS 虚拟内存一样分页管理 KV Cache（vLLM 提出） |
| RadixAttention | — | 用基数树复用公共前缀的 KV Cache（SGLang 提出） |
| 连续批处理 | Continuous Batching | 每个 decode 步动态增删请求，不等整批完成 |
| Chunked Prefill | — | 长 prompt 分块 prefill，与 decode 交错执行 |
| 前缀缓存 | Prefix Caching | 相同 prompt 前缀复用 KV Cache 块，省 prefill 时间 |
| 投机解码 | Speculative Decoding | 小模型草稿 + 大模型验证，加速 decode |
| 分离式推理 | PD Disaggregation | Prefill 与 Decode 节点独立部署、独立扩缩容 |
| TTFT | Time To First Token | 首 token 延迟 |
| TPOT | Time Per Output Token | 每个输出 token 的平均生成时间 |
| ITL | Inter-Token Latency | 相邻两个输出 token 的间隔（流式体感） |
| 吞吐 | Throughput | 单位时间处理的 token 数（tokens/s） |
| 张量并行 | Tensor Parallelism (TP) | 单层权重切分到多 GPU |
| 流水线并行 | Pipeline Parallelism (PP) | 不同层分配到不同 GPU |
| 专家并行 | Expert Parallelism (EP) | MoE 模型的专家分片到多 GPU |
| 量化 | Quantization | 用低精度（FP8/INT8/INT4）表示权重，省显存提速度 |
| GGUF | — | llama.cpp 生态的模型格式，内嵌量化与元数据 |
| 思考链 | Chain-of-Thought (CoT) | 模型正式回答前输出的一段推理过程 |
| Budget Forcing | — | 用 prompt 或参数限制/延长思考 token 预算（R1 蒸馏论文术语） |

---

## 2. 主流引擎对比

| 维度 | vLLM | SGLang | TensorRT-LLM | LMDeploy | llama.cpp / Ollama | TGI |
|------|------|--------|--------------|----------|--------------------|-----|
| 定位 | 生产级通用推理引擎 | 高性能推理 + 复杂控制流 | NVIDIA 生态极致优化 | InternLM 系 + 国产芯片适配 | CPU / 边缘 / 本地 | HuggingFace 生产服务 |
| GPU 吞吐 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐（GPU 单机可用） | ⭐⭐⭐ |
| 上手难度 | 中 | 中高 | 高（需 build engine） | 中 | 低 | 中 |
| OpenAI API | ✅ 原生 | ✅ 原生 | ✅ 原生 | ✅ 原生 | ✅ 兼容 | ✅ 原生 |
| CPU 推理 | ❌ 非重点 | ❌ 非重点 | ❌ | ❌ | ✅ 强 | 有限 |
| 前缀缓存 | ✅ | ✅（RadixAttention） | ✅ | ✅ | ✅ | ✅ |
| 结构化输出 | ✅（Outlines/XGrammar） | ✅（XGrammar 深度集成） | ✅ | ✅ | ✅ | ✅ |
| 多 GPU | TP/PP/EP | TP/PP/EP + DP | TP/PP/EP | TP/PP/EP | 有限 | ✅ |
| 典型场景 | 高并发通用 API | Agent、多步推理、JSON 密集 | NVIDIA 底座、边缘盒子 | 国产卡、轻量私有化 | 本地开发、无 GPU 环境 | HF 生态部署 |

### 选型决策树

```
需要生产级 GPU 服务？
  ├─ 是 → 继续
  └─ 否 → 本地/CPU/边缘？
       ├─ 是 → llama.cpp / Ollama
       └─ 否 → 先用 API（OpenAI/云厂商）

生产级 GPU 服务中：
  ├─ 模型以 Qwen/DeepSeek/Llama 为主、要省心 → vLLM
  ├─ Agent 多步推理 / 结构化 JSON 密集 / 前缀复用高 → SGLang
  ├─ NVIDIA 硬件栈、要榨干单卡性能 / NIM → TensorRT-LLM
  ├─ 国产芯片或轻量私有化部署 → LMDeploy
  └─ 已在 HF 生态且并发中等 → TGI
```

> 实际项目常以 vLLM / SGLang 为默认起点，用 benchmark 数据而不是直觉做最终选型。

---

## 3. 关键指标速查

```
TTFT  = 首 token 时间         ← Prefill 决定，用户体感「开始响应」
TPOT  = 每个输出 token 时间    ← Decode 决定，约等于 ITL
吞吐   = 总输出 token / 墙钟时间（含失败与超时则看 goodput）
并发   = 同时处理中的请求数（不是 QPS）
```

### 显存估算公式（7B 模型参考）

```
模型权重（FP16）≈ 参数量(B) × 2 GB
  7B FP16 ≈ 14 GB；INT4 量化后 ≈ 3.5–4 GB

KV Cache ≈ 2 × num_layers × hidden_size × seq_len × batch × dtype_bytes
  7B, seq=4096, batch=1, FP16 ≈ 1–2 GB
  7B, seq=4096, batch=32, FP16 ≈ 30+ GB

总显存 ≈ 权重 + KV Cache + 激活 + 框架开销
生产建议 gpu-memory-utilization 0.85–0.95，留余量给峰值
```

---

## 4. 量化格式速查

| 精度 | 显存（7B 参考） | 质量 | 适用引擎 |
|------|-----------------|------|----------|
| FP16 / BF16 | ~14 GB | 基准 | vLLM / SGLang / TRT-LLM |
| FP8 | ~7 GB | 接近无损 | vLLM / TRT-LLM / LMDeploy |
| INT8 / W8A8 | ~7 GB | 接近无损 | 各引擎 |
| AWQ / GPTQ（INT4） | ~4 GB | 可用 | vLLM / SGLang / LMDeploy |
| GGUF Q4_K_M | ~4.4 GB | 可用 | llama.cpp / Ollama |

---

## 5. 常见坑速查

| 现象 | 可能原因 | 处理 |
|------|---------|------|
| CUDA OOM | max-model-len 过大 / 并发过高 | 降上下文、限 max-num-seqs、换量化 |
| 首 token 极慢 | 冷启动 + 长 prefill | 前缀缓存、Chunked Prefill、PD 分离 |
| 流式卡顿 | TPOT 高 / 网络缓冲 | 查 ITL、调 batch、开投机解码 |
| 输出乱码 | 量化格式与引擎不匹配 | 让 `--quantization` 与模型格式一致 |
| 思考模型不输出 reasoning | 接口未启用 reasoning 字段 | 用支持 reasoning 的接口/版本并开启参数 |
| 压测数字虚高 | 未预热 / 忽略失败与超时 | 预热后再测，统计 goodput 与 P99 延迟 |

---

**下一课** → [`01_engine_fundamentals.md`](01_engine_fundamentals.md)
