# vLLM 大模型推理与服务 从零到生产

独立专课，与 [`stage-12-mlops/`](../stage-12-mlops/) 互补：

- **本课程**：如何**理解、部署、调优** vLLM 推理引擎（PagedAttention → 连续批处理 → OpenAI API → 量化 → 生产运维）
- **stage-12 MLOps**：Docker 容器化、MLflow、监控体系等更广泛的 MLOps 全景

Markdown 文档 + 可选 GPU 动手练习，默认技术栈：**Python 3.11+ · CUDA GPU · vLLM V1 引擎**。

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 参考 | `00_vllm_glossary.md` | 术语表、vLLM vs Ollama/TGI、选型速查 |
| 第1课 | `01_vllm_fundamentals.md` | vLLM 是什么、推理瓶颈、工程全景图 |
| 第2课 | `02_paged_attention_and_kv_cache.md` | KV Cache、PagedAttention、显存管理 |
| 第3课 | `03_continuous_batching_and_scheduler.md` | 连续批处理、调度器、Chunked Prefill |
| 第4课 | `04_installation_and_openai_api.md` | 安装、OpenAI 兼容 API、流式输出 |
| 第5课 | `05_offline_inference_python_api.md` | LLM 类、SamplingParams、Embedding |
| 第6课 | `06_quantization_and_multi_gpu.md` | FP8/AWQ/GPTQ、张量并行、Pipeline 并行 |
| 第7课 | `07_production_deployment.md` | Docker、K8s、分离式 Prefill/Decode |
| 第8课 | `08_performance_tuning_and_observability.md` | 参数调优、基准测试、监控指标 |

## 学习目标

- 理解 vLLM 的核心优化原理（PagedAttention + 连续批处理）
- 能独立启动 OpenAI 兼容的 vLLM 服务并完成客户端调用
- 掌握量化、多 GPU 并行等生产级配置
- 能设计基准测试方案并解读 TTFT/TPOT/吞吐指标
- 知道 vLLM 与 Ollama、TGI、SGLang 的选型边界

## 学习方式

- Markdown 文档 + 终端 / Python 动手练习
- 建议前置：[`stage-04-llm-basics`](../stage-04-llm-basics/)（Prompt）、[`stage-05-llm-api`](../stage-05-llm-api/)（OpenAI API）
- GPU 环境：至少 8GB 显存可跑 7B INT4；16GB+ 可跑 7B FP16
- 每课末尾有**自检清单**；第 4、8 课有 `practice/` 可运行脚本

## 环境准备

```bash
# 推荐：NVIDIA GPU + CUDA 12.x
pip install vllm openai httpx

# 启动服务（需 GPU）
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --dtype auto \
    --max-model-len 4096 \
    --port 8000

# 客户端测试
cd practice
pip install -r requirements.txt
python openai_client_demo.py
```

无 GPU 时：仍可阅读文档，用 `practice/benchmark_simulator.py` 理解调度与显存概念。

## 学习顺序建议

```
stage-05 LLM API  →  learn-vllm (本课程)
                         │
                         ├─ stage-11 AI 工程化（FastAPI 封装 vLLM）
                         ├─ stage-12 MLOps（Docker + 监控）
                         └─ learn-se 性能工程（延迟分布、压测方法论）
```

## 与 stage-12 的分工

| 主题 | 权威来源 | 说明 |
|------|----------|------|
| PagedAttention / 连续批处理 | 本课第 2、3 课 | stage-12 仅概览 |
| vLLM 安装与 OpenAI API | 本课第 4 课 | stage-12 有基础示例 |
| 量化与多 GPU | 本课第 6 课 | stage-12 覆盖通用量化概念 |
| Docker / MLflow / 监控体系 | stage-12 | 本课第 7、8 课做 vLLM 专项 |
| 推理框架选型 | 本课第 1、8 课 | vLLM vs TGI vs SGLang |

## 推荐资源

- [vLLM 官方文档](https://docs.vllm.ai/)
- [PagedAttention 论文 (SOSP 2023)](https://arxiv.org/abs/2309.06180)
- [vLLM GitHub](https://github.com/vllm-project/vllm)
