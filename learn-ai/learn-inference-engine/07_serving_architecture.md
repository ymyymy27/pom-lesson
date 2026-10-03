# 第7课：服务架构 — 并发、PD 分离、LoRA 与多模态

> 上一课：[`06_cpu_edge_engines.md`](06_cpu_edge_engines.md) · 下一课：[`08_benchmark_and_tuning.md`](08_benchmark_and_tuning.md)

---

## 1. 从单卡到服务架构

```
单卡单模型                    生产多模型
──────────────              ──────────────────────
vLLM 服务                   网关（路由/限流/缓存）
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
                推理服务A    推理服务B   推理服务C
                 (聊天)      (RAG)      (思考模型)
                    │          │          │
                    └──── 共享 GPU 资源池 ───┘
```

---

## 2. 并发模型：QPS ≠ 并发

| 概念 | 说明 |
|------|------|
| QPS | 每秒请求数（入口指标） |
| 并发（in-flight） | 同时处理中的请求数 |
| 排队深度 | 等待调度器接收的请求数 |

**吞吐由并发决定，不直接由 QPS 决定**。高 QPS 但请求短，可能低并发就够；单个长输出请求也会长期占用并发槽。

引擎侧两个关键参数：

- `--max-num-seqs`：最大并发序列（vLLM）
- `--max-running-requests`：同时运行请求数（SGLang）

压测时观察：并发加到多少后吞吐不再涨、延迟开始飙升，那就是甜点。

---

## 3. PD 分离（Disaggregated Prefill/Decode）

### 为什么拆

Prefill 是计算密集型（吃算力），Decode 是带宽密集型（吃显存带宽）。混在一起时：

- 长 prompt 请求会挤占 decode 资源
- 两类负载难以独立扩缩容

### 怎么拆

```
客户端 → 网关 → Prefill 节点（长 prompt 快速处理）
                → 缓存中间 KV → Decode 节点（持续输出）
```

实现方式：

- vLLM 原生 disaggregated prefill（v0.8+，持续演进）
- 云方案：Mooncake、Dynamo、SGLang DeepEP 等
- 团队自研：KV 传输 + 调度网关

### 适用判断

| 信号 | 是否该上 PD 分离 |
|------|------------------|
| 长上下文 RAG / 长文档问答 | ✅ 强烈考虑 |
| 短 prompt、短输出 | ❌ 收益小 |
| decode 节点 GPU 利用率高 | ✅ |
| prefill 偶发尖峰 | ✅（独立扩缩容） |

---

## 4. 多模型与 LoRA 服务

### 多模型共卡

把多个小模型放同一 GPU，用 vLLM 多模型服务或独立容器 + GPU 调度。注意显存隔离与故障爆炸半径。

### LoRA 动态加载

一个基座模型 + 多个 LoRA 适配器：

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="unused")
resp = client.chat.completions.create(
    model="base-model",
    messages=[{"role": "user", "content": "你好"}],
    extra_body={"add_lora": "my-domain-lora"},
)
```

优势：一份基座显存服务 N 个专属风格；适合多租户/多业务线。

---

## 5. 多模态推理服务

现代引擎支持视觉、音频输入：

```bash
# vLLM 启动视觉模型
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-VL-7B-Instruct \
    --max-model-len 8192 --port 8000
```

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="unused")
resp = client.chat.completions.create(
    model="Qwen/Qwen2.5-VL-7B-Instruct",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "这张图里有什么？"},
                {"type": "image_url", "image_url": {"url": "file:///tmp/photo.png"}},
            ],
        }
    ],
)
print(resp.choices[0].message.content)
```

注意：多模态输入的 prefill 更长（图像 token 多），更依赖前缀缓存与长上下文优化。

---

## 6. 网关层职责

不要把鉴权、限流、路由塞进推理引擎：

| 职责 | 工具/方案 |
|------|----------|
| 路由与多模型暴露 | FastAPI 网关 / Nginx / Envoy |
| 鉴权与配额 | API Key、OAuth、Redis 限流 |
| 缓存 | 语义缓存（相似问题复用答案） |
| 超时与重试 | 按 TTFT/TPOT 设置合理超时 |
| 观测 | 统一 trace、日志、指标聚合 |

---

## 7. 动手练习

1. 画一张「网关 + 3 个推理服务 + 共享 GPU 池」的部署图，标注每个组件职责
2. 用 vLLM 起两个模型（如 3B 与 7B），通过简单 FastAPI 网关按模型名路由
3. 思考：你的场景中，什么信号出现时该考虑 PD 分离？

---

## 8. 自检清单

- [ ] 能区分 QPS 与并发，解释并发对吞吐的决定作用
- [ ] 能画出 PD 分离架构并说明收益
- [ ] 知道 LoRA 服务多租户的价值
- [ ] 能给多模态服务设计 prefill 优化策略
- [ ] 知道网关层与引擎层的职责边界

---

## 下一课

[`08_benchmark_and_tuning.md`](08_benchmark_and_tuning.md) — 压测、指标与参数调优
