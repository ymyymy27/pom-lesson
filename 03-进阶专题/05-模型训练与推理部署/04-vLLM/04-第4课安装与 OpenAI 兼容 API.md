> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第4课：安装与 OpenAI 兼容 API

> 上一课：[`03-第3课连续批处理与调度器.md`](03-第3课连续批处理与调度器.md) · 下一课：[`05-第5课离线推理与 Python API.md`](<05-第5课离线推理与 Python API.md>)

---

## 1. 环境要求

| 组件 | 要求 |
|------|------|
| GPU | NVIDIA，Compute Capability ≥ 7.0（V100+） |
| CUDA | 11.8+ 或 12.x（与 PyTorch 匹配） |
| Python | 3.10 – 3.12 |
| 显存 | 7B INT4 ≥ 8GB；7B FP16 ≥ 16GB |
| 系统 | Linux 推荐；Windows WSL2 可用 |

```bash
# 检查 GPU
nvidia-smi

# 推荐：独立 venv
python -m venv .venv && source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

pip install vllm openai httpx
```

---

## 2. 启动 OpenAI 兼容 API Server

### 基础启动

```bash
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --dtype auto \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9 \
    --port 8000
```

### 常用增强参数

```bash
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --dtype auto \
    --max-model-len 8192 \
    --max-num-seqs 128 \
    --enable-prefix-caching \
    --served-model-name qwen-7b \
    --api-key my-secret-key \
    --port 8000
```

| 参数 | 说明 |
|------|------|
| `--served-model-name` | 客户端 `model=` 字段使用的名称 |
| `--api-key` | 启用 Bearer 认证 |
| `--trust-remote-code` | 部分模型需要 |

### 使用本地模型

```bash
python -m vllm.entrypoints.openai.api_server \
    --model /data/models/Qwen2.5-7B-Instruct \
    --tokenizer /data/models/Qwen2.5-7B-Instruct \
    --port 8000
```

---

## 3. API 调用方式

### curl

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my-secret-key" \
  -d '{
    "model": "qwen-7b",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 128,
    "temperature": 0.7
  }'
```

### OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="my-secret-key",
)

response = client.chat.completions.create(
    model="qwen-7b",
    messages=[
        {"role": "system", "content": "你是简洁的助手"},
        {"role": "user", "content": "解释 PagedAttention"},
    ],
    max_tokens=256,
    temperature=0.7,
)
print(response.choices[0].message.content)
print(response.usage)  # prompt/completion tokens
```

### 流式输出

```python
stream = client.chat.completions.create(
    model="qwen-7b",
    messages=[{"role": "user", "content": "写一首短诗"}],
    max_tokens=200,
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
```

---

## 4. 支持的 API 端点

| 端点 | 用途 |
|------|------|
| `POST /v1/chat/completions` | 对话（最常用） |
| `POST /v1/completions` | 文本补全 |
| `POST /v1/embeddings` | 向量嵌入（需 embedding 模型） |
| `GET /v1/models` | 列出已加载模型 |
| `GET /health` | 健康检查 |

---

## 5. Docker 部署

```yaml
# practice/docker-compose.yml
services:
  vllm:
    image: vllm/vllm-openai:latest
    ports:
      - "8000:8000"
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    command: >
      --model Qwen/Qwen2.5-7B-Instruct
      --dtype auto
      --max-model-len 4096
      --gpu-memory-utilization 0.9
```

```bash
cd practice && docker compose up -d
```

---

## 6. 与 LangChain / LlamaIndex 集成

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="my-secret-key",
    model="qwen-7b",
    temperature=0.7,
)
response = llm.invoke("什么是 RAG？")
print(response.content)
```

只需改 `base_url`，现有 OpenAI 代码**零改动**迁移到 vLLM。

---

## 7. 常见问题排查

| 问题 | 排查 |
|------|------|
| 连接拒绝 | 服务是否启动、`--port` 是否一致 |
| 401 Unauthorized | `--api-key` 与客户端 key 是否匹配 |
| 404 model not found | 使用 `--served-model-name` 或 HF 全名 |
| 首次请求极慢 | 模型加载 + 冷启动，属正常 |
| HF 下载慢 | 设 `HF_ENDPOINT=https://hf-mirror.com` 或预下载 |

---

## 8. 动手练习

1. 按第 2 节启动服务，用 curl 和 OpenAI SDK 各发一次请求
2. 实现流式输出，测量首 token 到达时间（TTFT）
3. 运行 `practice/openai_client_demo.py`（需服务已启动）
4. 将 stage-05 的 LangChain 示例改为连接本地 vLLM

---

## 9. 自检清单

- [ ] 成功安装 vLLM 并启动 api_server
- [ ] 能用 OpenAI SDK 完成 chat completions 调用
- [ ] 能实现 stream=True 流式输出
- [ ] 知道 served-model-name 与 api-key 的配置方式
- [ ] 了解 Docker 部署的基本 compose 结构

---

## 下一课

[`05-第5课离线推理与 Python API.md`](<05-第5课离线推理与 Python API.md>) — 不启 HTTP 服务，直接用 Python API 推理
