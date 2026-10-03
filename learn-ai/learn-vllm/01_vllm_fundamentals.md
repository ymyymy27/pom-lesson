# 第1课：vLLM 基础 — 推理瓶颈与工程全景

> 上一课：[`00_vllm_glossary.md`](00_vllm_glossary.md) · 下一课：[`02_paged_attention_and_kv_cache.md`](02_paged_attention_and_kv_cache.md)

---

## 1. vLLM 是什么？

### 一句话解释

**vLLM = 专为 LLM 推理优化的高吞吐 serving 引擎**，通过 PagedAttention 和连续批处理，在相同 GPU 上实现数倍于朴素实现的吞吐量。

### 类比理解

| 日常概念 | vLLM 概念 |
|---------|----------|
| 餐厅翻台率 | 连续批处理：一桌吃完立刻接待下一桌 |
| 停车场按块计费 | PagedAttention：KV Cache 按需分页，不预占整段 |
| 快递分拣中心 | 调度器：waiting / running / swapped 三队列 |
| OpenAI API | vLLM 提供兼容接口，可无缝替换 |

### 为什么需要专门的推理引擎？

```
训练（Training）          推理（Inference）
─────────────────        ─────────────────
批量固定、可离线           请求随机到达、需低延迟
反向传播、优化权重         只前向、权重只读
GPU 算力是瓶颈             显存带宽 + 调度是瓶颈
```

HuggingFace `model.generate()` 适合**单请求实验**；生产环境 100+ 并发时，需要 vLLM 这类引擎做**内存管理 + 动态批处理**。

---

## 2. LLM 推理的两个阶段

```
用户请求: "请总结以下文档……" (2000 tokens)
                    │
                    ▼
            ┌───────────────┐
            │   Prefill     │  一次性处理全部输入 token
            │  (计算密集)    │  生成初始 KV Cache
            └───────┬───────┘
                    ▼
            ┌───────────────┐
            │   Decode      │  每次生成 1 个 token
            │ (带宽密集)     │  反复读 KV Cache + 算新 token
            └───────────────┘
                    │
                    ▼
            输出: "本文主要讨论……"
```

| 阶段 | 特点 | 优化方向 |
|------|------|---------|
| Prefill | 输入越长越慢，可并行算所有 token | Chunked Prefill、分离式 Prefill 节点 |
| Decode | 每步只算 1 token，但需读全部历史 KV | PagedAttention、投机解码、量化 |

**TTFT** 主要由 Prefill 决定；**TPOT** 主要由 Decode 决定。

---

## 3. 传统推理的三大瓶颈

### 3.1 KV Cache 显存浪费

传统做法：为每个请求**预分配 max_seq_len 的连续显存**。

```
请求 A：实际 500 tokens，预分配 4096 → 浪费 88%
请求 B：实际 800 tokens，预分配 4096 → 浪费 80%
→ 显存利用率 ~50%，batch 上不去
```

→ 第 2 课：**PagedAttention**

### 3.2 静态批处理

```
批次 [A, B, C, D] 一起推理
A 完成（100 tokens）→ 仍要等 B(2000 tokens) 完成
→ GPU 空等，吞吐低
```

→ 第 3 课：**Continuous Batching**

### 3.3 框架开销

Python GIL、内存拷贝、内核 launch 开销。vLLM V1 引擎通过 CUDA Graph、FlashAttention、融合 kernel 等降低 overhead。

---

## 4. vLLM 工程全景图

```
阶段 1：理解原理（本课 + 第 2、3 课）
   ↓
阶段 2：本地启动 OpenAI API（第 4 课）
   ↓
阶段 3：Python 离线推理 / Embedding（第 5 课）
   ↓
阶段 4：量化 + 多 GPU（第 6 课）
   ↓
阶段 5：Docker / K8s 生产部署（第 7 课）
   ↓
阶段 6：压测 + 调参 + 监控（第 8 课）
```

### 在 AI Hub 项目中的位置

```
stage-05: 调用 OpenAI API
    ↓
learn-vllm: 自建 vLLM 服务替代云端 API
    ↓
stage-11: FastAPI 网关 + 限流 + 缓存
    ↓
stage-12: Docker 部署 + Prometheus 监控
```

---

## 5. 最小可运行示例

```bash
# 安装（需 NVIDIA GPU + CUDA）
pip install vllm

# 启动 OpenAI 兼容服务
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --dtype auto \
    --max-model-len 4096 \
    --port 8000
```

```python
# 客户端（与 OpenAI SDK 完全兼容）
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="unused")
resp = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct",
    messages=[{"role": "user", "content": "用一句话介绍 vLLM"}],
)
print(resp.choices[0].message.content)
```

---

## 6. 常见失败模式

| 失败模式 | 表现 | 预防 |
|---------|------|------|
| 直接上生产 | OOM / 延迟爆炸 | 先压测，再定 max-num-seqs |
| 忽视 Prefill | TTFT 几秒甚至几十秒 | Chunked Prefill、限制 max-model-len |
| 量化乱配 | 输出乱码 / 崩溃 | 模型格式与 `--quantization` 一致 |
| 单机硬扛 | 70B 单卡 OOM | TP/PP 或多卡部署 |
| 无监控 | 用户投诉才发现 | 第 8 课：TTFT/TPOT/队列深度 |

---

## 7. 动手练习

1. 阅读 [vLLM 官方文档首页](https://docs.vllm.ai/)，列出 3 个你感兴趣的特性
2. 对比你当前用的推理方式（Ollama / API / HF generate），画一张「请求 → 响应」时序图
3. 若有 GPU：按第 5 节启动服务，用 curl 或 OpenAI SDK 发一条请求
4. 无 GPU：运行 `practice/benchmark_simulator.py` 理解静态 vs 连续批处理差异

---

## 8. 自检清单

- [ ] 能解释 Prefill 与 Decode 的区别及对延迟的影响
- [ ] 能说出 vLLM 解决的三个传统瓶颈
- [ ] 知道 vLLM 与 Ollama 的适用场景差异
- [ ] 理解本课程 6 个阶段的顺序
- [ ] 完成一次（或模拟一次）OpenAI 兼容 API 调用

---

## 下一课

[`02_paged_attention_and_kv_cache.md`](02_paged_attention_and_kv_cache.md) — PagedAttention 如何让 KV Cache 不再浪费显存
