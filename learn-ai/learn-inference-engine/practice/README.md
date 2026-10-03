# practice 动手练习

无需 GPU 即可运行的脚本：

| 脚本 | 用途 |
|------|------|
| `benchmark_simulator.py` | 模拟静态 vs 连续批处理，理解吞吐差异 |
| `openai_client_demo.py` | 连接任意 OpenAI 兼容推理服务，流式/非流式 |
| `benchmark_client.py` | 并发压测：TTFT / TPOT / 总吞吐 |

有 GPU 时可用 `docker-compose.yml` 启动 vLLM 服务。

## 环境准备

```bash
pip install -r requirements.txt
```

## 快速开始

```bash
# 1. 批处理模拟（无需服务）
python benchmark_simulator.py

# 2. 连接已启动的推理服务
python openai_client_demo.py --base-url http://localhost:8000/v1 \
    --model Qwen/Qwen2.5-7B-Instruct \
    --prompt "用三句话介绍推理引擎"

# 3. 并发压测
python benchmark_client.py --base-url http://localhost:8000/v1 \
    --model Qwen/Qwen2.5-7B-Instruct \
    --concurrency 16 --requests 64
```

## 兼容的推理服务

| 服务 | base-url | 默认模型示例 |
|------|----------|--------------|
| vLLM | `http://localhost:8000/v1` | 启动参数指定的模型 |
| SGLang | `http://localhost:30000/v1` | 启动参数指定的模型 |
| Ollama | `http://localhost:11434/v1` | `qwen2.5:7b` |
| llama.cpp | `http://127.0.0.1:8080/v1` | 启动参数指定的模型 |

## Docker 启动 vLLM（需 NVIDIA GPU）

```bash
copy .env.example .env
# 编辑 .env 设置 API Key 与模型名
docker compose up -d
curl http://localhost:8000/health
```
