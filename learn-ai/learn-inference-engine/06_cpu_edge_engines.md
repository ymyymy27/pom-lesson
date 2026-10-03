# 第6课：CPU 与边缘 — llama.cpp、Ollama、LMDeploy

> 上一课：[`05_tensorrt_llm.md`](05_tensorrt_llm.md) · 下一课：[`07_serving_architecture.md`](07_serving_architecture.md)

---

## 1. 为什么需要 CPU / 边缘推理

- 本地开发、无 GPU 环境
- 隐私敏感、数据不出设备
- 边缘盒子、嵌入式设备
- 成本敏感的低并发场景

**没有 GPU 不代表不能学推理引擎**——llama.cpp 就是最好的入门引擎：单文件、可量化、可读性强。

---

## 2. llama.cpp + GGUF

### 核心概念

- **GGUF**：llama.cpp 生态的模型格式，包含权重、量化参数、tokenizer 元数据
- 量化档位：`Q4_K_M`（性价比）、`Q5_K_M`、`Q8_0`、`F16`
- 纯 C/C++ 实现，CPU/GPU 混合推理

### 获取模型

从 HuggingFace 下载 GGUF 文件（如 `Qwen/Qwen2.5-7B-Instruct-GGUF`）。

### 运行（CLI）

```bash
./llama-cli -m qwen2.5-7b-instruct-q4_k_m.gguf \
    -p "用一句话介绍推理引擎" -n 256
```

### OpenAI 兼容服务

```bash
./llama-server -m qwen2.5-7b-instruct-q4_k_m.gguf \
    --host 127.0.0.1 --port 8080

curl http://127.0.0.1:8080/v1/models
```

---

## 3. Ollama：用户友好的封装

Ollama 基于 llama.cpp，但把模型管理、API、量化下载全部封装好：

```bash
ollama pull qwen2.5:7b
ollama run qwen2.5:7b "用一句话介绍推理引擎"
```

兼容 OpenAI API：

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
resp = client.chat.completions.create(
    model="qwen2.5:7b",
    messages=[{"role": "user", "content": "你好"}],
)
print(resp.choices[0].message.content)
```

适合：开发调试、原型验证、离线演示。生产高并发不是它的主场。

---

## 4. LMDeploy：轻量私有化与国产芯片

LMDeploy 由 InternLM 团队维护，特点：

- TurboMind / PyTorch 双引擎
- AWQ 4-bit 量化成熟，W4A16 加速明显
- 支持国产加速卡（如华为昇腾等，具体以官方文档为准）
- OpenAI 兼容 API，一行启动

```bash
lmdeploy serve api_server Qwen/Qwen2.5-7B-Instruct \
    --server-port 23333
```

适合：轻量私有化、国产化替代、InternLM/Qwen 系模型。

---

## 5. 引擎选型（CPU / 边缘场景）

| 需求 | 推荐 |
|------|------|
| 本地调试 / 无 GPU | Ollama 或 llama.cpp |
| 嵌入式 / Jetson | TensorRT-LLM（Jetson）或 llama.cpp |
| 国产芯片私有化 | LMDeploy（按支持矩阵） |
| 低资源服务器 | llama.cpp Q4 + 限制并发 |
| 桌面应用内嵌 | llama.cpp 库 / ggml |

---

## 6. 性能预期管理

CPU 推理的现实：

```
7B Q4 在主流桌面 CPU：约 5–15 tokens/s（单用户可用）
32B Q4：通常 < 5 tokens/s，体验一般
高并发 CPU：不现实，建议用 GPU 或 API
```

优化手段：

- 更低量化（Q4_K_M）与更短上下文
- 批大小 = 1（CPU 场景批处理收益低）
- 开启 GPU offload（`-ngl 32` 等，按显存分配层数）
- 用 `--threads` 匹配物理核数

---

## 7. 动手练习

1. 用 Ollama 拉取一个 3B 以下模型，完成 OpenAI 兼容调用（无 GPU 也能跑）
2. 对比同一模型 `Q8_0` 与 `Q4_K_M` 的速度和回答质量
3. 用 `practice/openai_client_demo.py` 连接 Ollama，验证代码复用性

---

## 8. 自检清单

- [ ] 能解释 GGUF 与 HF safetensors 的区别
- [ ] 能启动 llama.cpp 或 Ollama 服务
- [ ] 知道 CPU 推理的性能边界与适用场景
- [ ] 能判断 LMDeploy 适合哪种私有化需求

---

## 下一课

[`07_serving_architecture.md`](07_serving_architecture.md) — 服务架构：从单卡到分布式
