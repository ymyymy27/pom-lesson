> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第3课：vLLM 快速上手 — 第一个生产级推理服务

> 上一课：[`02-第2课六大核心优化 — KV Cache批处理前缀缓存投机解码与量化.md`](<02-第2课六大核心优化 — KV Cache批处理前缀缓存投机解码与量化.md>) · 下一课：[`04-第4课SGLang 实战 — RadixAttention 与 Agent 场景.md`](<04-第4课SGLang 实战 — RadixAttention 与 Agent 场景.md>)

---

## 1. 本课定位

vLLM 的深度原理与完整生产流程见 [`learn-vllm`](../04-vLLM)（8 课专精）。本课只做**快速上手**，让你：

- 10 分钟启动 OpenAI 兼容服务
- 掌握最关键的服务参数
- 知道深度内容去哪学

---

## 2. 安装与启动

### 环境

- NVIDIA GPU + CUDA 12.x（推荐）
- Python 3.11+

```bash
pip install vllm
```

### 启动 OpenAI 兼容服务

```bash
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --dtype auto \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9 \
    --max-num-seqs 128 \
    --enable-prefix-caching \
    --port 8000
```

### 验证

```bash
curl http://localhost:8000/health
curl http://localhost:8000/v1/models
```

---

## 3. 客户端调用（与 OpenAI SDK 完全兼容）

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="unused")

resp = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct",
    messages=[{"role": "user", "content": "用三句话介绍 vLLM"}],
    stream=False,
)
print(resp.choices[0].message.content)
```

流式：

```python
stream = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct",
    messages=[{"role": "user", "content": "数到 10"}],
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
```

---

## 4. 最关键的服务参数

| 参数 | 作用 | 常见值 |
|------|------|--------|
| `--max-model-len` | 最大上下文长度，直接决定 KV Cache 上限 | 4096 / 8192 / 32768 |
| `--gpu-memory-utilization` | 显存使用上限，越大 batch 越大 | 0.85–0.95 |
| `--max-num-seqs` | 最大并发序列数，吞吐甜点靠压测找 | 64–256 |
| `--enable-prefix-caching` | 开启前缀缓存 | 建议默认开 |
| `--tensor-parallel-size` | 多卡张量并行 | 1 / 2 / 4 / 8 |
| `--quantization` | 量化方式 | awq / gptq / fp8 |
| `--served-model-name` | API 暴露的模型名，便于网关统一 | 自定义 |
| `--api-key` | 服务鉴权 | 生产必开 |

### 常见组合

```bash
# 单卡 7B 生产基线
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.92 \
    --max-num-seqs 128 \
    --enable-prefix-caching \
    --api-key sk-prod-xxx \
    --served-model-name qwen-7b
```

---

## 5. 离线推理（Python API）

适合批量评测、离线任务：

```python
from vllm import LLM, SamplingParams

llm = LLM(model="Qwen/Qwen2.5-7B-Instruct", max_model_len=4096)
params = SamplingParams(temperature=0.7, top_p=0.9, max_tokens=256)

outputs = llm.generate(
    ["介绍杭州", "介绍上海"],
    params,
)
for out in outputs:
    print(out.outputs[0].text)
```

---

## 6. 常见失败与排查

| 现象 | 原因 | 处理 |
|------|------|------|
| CUDA OOM | 上下文/并发过大 | 降 max-model-len、max-num-seqs 或量化 |
| 模型加载失败 | 网络 / HF token / 路径 | 设 `HF_ENDPOINT` 或本地 `--model /path` |
| 响应极慢 | 未开前缀缓存 / batch 太小 | 开启缓存，压测找甜点 |
| 客户端 404 | 模型名不匹配 | 用 `/v1/models` 查实际 model 名 |

---

## 7. 动手练习

1. 启动服务，用 `practice/openai_client_demo.py` 完成一次流式与非流式调用
2. 修改 `--max-num-seqs`（32/128/256），用 `practice/benchmark_client.py` 对比吞吐
3. 阅读 [`learn-vllm`](../04-vLLM) 第 1 课，确认本课遗漏了哪些深度内容

---

## 8. 自检清单

- [ ] 能独立启动 vLLM OpenAI 兼容服务
- [ ] 能解释 max-model-len / gpu-memory-utilization / max-num-seqs
- [ ] 能完成流式与非流式客户端调用
- [ ] 知道何时该去 learn-vllm 深度学习

---

## 下一课

[`04-第4课SGLang 实战 — RadixAttention 与 Agent 场景.md`](<04-第4课SGLang 实战 — RadixAttention 与 Agent 场景.md>) — SGLang：RadixAttention 与 Agent 场景
