# 第2课：六大核心优化 — KV Cache、批处理、前缀缓存、投机解码与量化

> 上一课：[`01_engine_fundamentals.md`](01_engine_fundamentals.md) · 下一课：[`03_vllm_quickstart.md`](03_vllm_quickstart.md)

---

## 1. 优化全景图

```
显存维度                    计算维度
─────────────────────────  ─────────────────────────
KV Cache 管理               连续批处理
  ├─ 分页（PagedAttention）   Chunked Prefill
  ├─ 基数树（RadixAttention） 投机解码
  └─ 量化                    CUDA Graph / 融合 kernel
```

本课讲通用原理；vLLM 的深度实现见 [`learn-vllm`](../learn-vllm/) 第 2、3 课。

---

## 2. KV Cache：一切优化的起点

Transformer 生成第 N 个 token 时需要前面所有 token 的 K/V；与其重算，不如缓存：

```
每生成 1 token：只算新 token 的 K/V + 读历史 KV
KV 总量 ≈ 2 × layers × hidden × seq_len × batch × dtype
```

KV Cache 是「读多写少」的显存结构，于是出现两个核心问题：

- **怎么存**才能不浪费、不碎片（→ 分页）
- **怎么复用**才能不重算（→ 前缀缓存）

---

## 3. 分页 KV Cache：PagedAttention 与 RadixAttention

### PagedAttention（vLLM，SOSP 2023）

像 OS 虚拟内存：KV 按固定块大小（如 16 token/块）分配，逻辑连续、物理不连续：

```
传统：预分配整段 [....................]  浪费
分页：按需挂块 [块1][块2] · [块3]       几乎不浪费
```

效果：显存利用率大幅提升 → 同卡能装更大 batch → 吞吐数倍提升。

### RadixAttention（SGLang）

把「共享前缀」的 KV 存进一棵基数树，新请求自动复用最长匹配前缀：

```
请求1：今天天气如何？→ 讲上海
请求2：今天天气如何？→ 讲北京   ← 前缀完全复用

RAG 场景：系统提示词 + 文档片段常为公共前缀，命中率极高
```

**PagedAttention 解决碎片，RadixAttention 解决复用；两者思想互补，现代引擎都在做前缀缓存。**

---

## 4. 连续批处理与 Chunked Prefill

### 连续批处理

每步动态增删请求：完成一个立刻补一个，GPU 永远满载：

```
静态： [A B C D] 全部等最长者
连续： A 完成 → 立刻让 E 进队
```

### Chunked Prefill

长 prompt 的 prefill 拆成小块，与 decode 交错执行，避免「一个大 prefill 卡住所有 decode」：

```
没有 Chunked Prefill：      [=========长 prefill=========] [decode…]
有 Chunked Prefill：       [P1][D D][P2][D D][P3][D D]   首 token 更快
```

---

## 5. 前缀缓存与 KV 复用

适用场景：

- 多轮对话（历史消息重复）
- RAG（系统提示词 + 文档块）
- Agent（工具说明、上下文模板）
- 批量评测（同一 prompt 不同温度）

注意：

- 缓存有显存成本，命中率低时可能拖累性能
- 需要引擎支持（vLLM 自动前缀缓存、SGLang RadixAttention、TGI prefix cache）
- 换模型、换批次参数时缓存会失效

---

## 6. 投机解码：用便宜模型加速贵模型

```
小模型（草稿）快速猜 3~5 个 token
大模型（验证）一次并行验证 → 全对就赚了，错了退回
```

变体：

| 方案 | 思路 | 引擎支持 |
|------|------|----------|
| 独立草稿模型 | 小模型 + 大模型 | vLLM / SGLang |
| Medusa / EAGLE | 大模型头部加轻量预测头 | vLLM（EAGLE） |
| MTP（多 token 预测） | 训练阶段就学多 token 预测（DeepSeek） | DeepSeek 系列原生 |

适用条件：草稿足够快、接受率高、显存有余量。短输出或 CPU 场景收益有限。

---

## 7. 量化：显存换精度

```
FP16/BF16（基准） → FP8（接近无损） → INT8（接近无损） → INT4（可用）
显存约减半 / 减半 / 减到 1/4，速度通常更快
```

| 格式 | 典型引擎 | 注意 |
|------|----------|------|
| FP8 | TRT-LLM / vLLM | 新一代 GPU 友好 |
| AWQ / GPTQ | vLLM / SGLang / LMDeploy | 需下载对应量化模型 |
| GGUF | llama.cpp / Ollama | CPU/边缘主力 |

量化后务必跑一遍代表性请求，检查质量与数值稳定性。

---

## 8. 把优化串起来：一个 RAG 请求的旅程

```
请求（长系统提示词 + 文档块）
  │
  ├─ 前缀缓存命中 → 跳过大部分 prefill
  ├─ 未命中部分 Chunked Prefill，与 decode 交错
  ├─ KV Cache 按页分配，物理碎片≈0
  ├─ 连续批处理与其他请求共享 GPU
  └─ 若开启投机解码，decode 速度进一步提升
```

---

## 9. 动手练习

1. 打开 `practice/benchmark_simulator.py`，把批大小从 8 改成 4 / 16，观察差距
2. 用搜索引擎查 1 篇 PagedAttention 论文摘要，用自己的话写 3 句总结
3. 设计一个「前缀命中率最高」的业务场景，说明为什么适合前缀缓存
4. 有 GPU 时：vLLM 开/关 `--enable-prefix-caching`，用相同多轮请求对比 TTFT

---

## 10. 自检清单

- [ ] 能推导 KV Cache 的显存公式
- [ ] 能区分 PagedAttention 与 RadixAttention 的侧重点
- [ ] 能解释连续批处理与 Chunked Prefill 各解决什么问题
- [ ] 能说出前缀缓存的适用场景与失效条件
- [ ] 能判断投机解码在什么情况下收益大
- [ ] 能量化讲出 FP16 → FP8 → INT4 的显存变化

---

## 下一课

[`03_vllm_quickstart.md`](03_vllm_quickstart.md) — 用 vLLM 30 分钟跑起第一个生产级推理服务
