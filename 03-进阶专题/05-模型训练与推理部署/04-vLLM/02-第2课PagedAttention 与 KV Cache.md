> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第2课：PagedAttention 与 KV Cache

> 上一课：[`01-第1课vLLM 基础 — 推理瓶颈与工程全景.md`](<01-第1课vLLM 基础 — 推理瓶颈与工程全景.md>) · 下一课：[`03-第3课连续批处理与调度器.md`](03-第3课连续批处理与调度器.md)

---

## 1. KV Cache 是什么？

### 一句话解释

**KV Cache = 生成过程中缓存每个 token 的 Key/Value 向量**，避免每步重复计算历史 token 的注意力。

### 不用 KV Cache 的问题

```
生成 token 3 时需要 attend 到 token 1, 2, 3
生成 token 4 时需要 attend 到 token 1, 2, 3, 4  ← 重复算了 1,2,3
...
→ 复杂度 O(n²)，长序列极慢
```

### 使用 KV Cache

```
Step 1: 算 token1 → 存 K1, V1
Step 2: 算 token2 + 用 K1,V1 → 存 K2, V2
Step 3: 算 token3 + 用 K1,V1,K2,V2 → 存 K3, V3
...
→ 每步只算 1 个新 token，复杂度 O(n)
```

---

## 2. 传统 KV Cache 的显存问题

传统实现为每个序列分配**连续、固定大小**的 buffer：

```
┌─────────────────────────────────────────┐
│  Request A: [used 500 | wasted 3596 ]   │  max_len=4096
├─────────────────────────────────────────┤
│  Request B: [used 1200 | wasted 2896 ]  │
├─────────────────────────────────────────┤
│  Request C: [used 200 | wasted 3896 ]   │
└─────────────────────────────────────────┘
         ↑ 内部碎片 + 预分配浪费
```

**后果：**
- 显存利用率低（常见 ~50%）
- 并发 batch 小 → 吞吐上不去
- 序列长度差异大时浪费更严重

---

## 3. PagedAttention 原理

灵感来自 **OS 虚拟内存**：逻辑地址连续，物理页可分散。

```
逻辑 KV Cache（按 token 顺序）     物理 GPU 显存块（Block Pool）
────────────────────────────     ─────────────────────────────
Token 0-15  → Block Table →      [Block 3][Block 7][Block 1]...
Token 16-31 →              →      非连续，按需分配
Token 32-47 →              →      释放后立即回收到 free list
```

### 核心机制

| 组件 | 作用 |
|------|------|
| Block | 固定大小（如 16 tokens）的 KV 存储单元 |
| Block Table | 每个请求的逻辑 block → 物理 block 映射 |
| Block Allocator | 从 free list 分配 / 回收 block |
| Copy-on-Write | 并行采样（beam search）时共享 block |

### 效果

- 显存利用率 **~95%**（vs 传统 ~50%）
- 相同 GPU 可跑 **更大 batch** → 吞吐 2–4x
- 序列结束 → block 立刻回收 → 支持高并发

---

## 4. 显存估算实战

```python
def estimate_kv_cache_gb(
    num_layers: int,
    hidden_size: int,
    seq_len: int,
    batch_size: int,
    dtype_bytes: int = 2,  # FP16
) -> float:
    """简化估算：每层 K+V，hidden_size 维"""
    kv_per_token = 2 * num_layers * hidden_size * dtype_bytes
    total_bytes = kv_per_token * seq_len * batch_size
    return total_bytes / 1e9

# Qwen2.5-7B 近似：28 layers, hidden 3584
for batch, seq in [(1, 4096), (8, 4096), (32, 2048)]:
    gb = estimate_kv_cache_gb(28, 3584, seq, batch)
    print(f"batch={batch:>2}, seq={seq:>5} → KV Cache ≈ {gb:.2f} GB")
```

**7B FP16 权重 ~14GB**，加上 KV Cache 后：
- batch=1, seq=4096 → 总显存 ~16GB（RTX 4090 可跑）
- batch=32, seq=2048 → KV  alone 可能 30GB+，需多卡或降并发

---

## 5. Prefix Caching（前缀缓存）

RAG / 多轮对话中，**system prompt 或检索上下文常重复**：

```
请求1: [System + Doc A] + 问题1
请求2: [System + Doc A] + 问题2   ← 前缀相同
请求3: [System + Doc B] + 问题3
```

启用 `--enable-prefix-caching` 后：
- 相同前缀的 KV block **只算一次**
- 后续请求直接命中缓存 block
- Prefill 时间大幅下降

**适用：** RAG（相同文档多问题）、固定 system prompt 的 Agent。

---

## 6. 与 FlashAttention 的关系

| 技术 | 解决什么 |
|------|---------|
| FlashAttention | 单次 attention 计算的**速度和显存**（IO 优化） |
| PagedAttention | **多请求间** KV Cache 的**分配与复用** |
| Prefix Caching | **跨请求** 相同前缀的 KV **复用** |

三者互补，vLLM 同时集成。

---

## 7. 动手练习

1. 用第 4 节公式，估算你目标模型在 batch=16、seq=8192 时的 KV 显存
2. 启动 vLLM 时分别开关 `--enable-prefix-caching`，对同一长 system prompt 发 10 次请求，对比 TTFT
3. 阅读 [PagedAttention 设计文档](https://docs.vllm.ai/en/latest/design/paged_attention/)

---

## 8. 自检清单

- [ ] 能解释 KV Cache 为何将生成从 O(n²) 降到 O(n)
- [ ] 能说明传统连续分配 vs PagedAttention 的差异
- [ ] 能估算给定 batch/seq 下的 KV Cache 显存
- [ ] 知道 Prefix Caching 的典型应用场景
- [ ] 理解 PagedAttention 与 FlashAttention 的分工

---

## 下一课

[`03-第3课连续批处理与调度器.md`](03-第3课连续批处理与调度器.md) — 调度器如何让 GPU 始终满载
