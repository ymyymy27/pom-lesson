# 大模型推理引擎 从全景到生产

独立专课，与 [`learn-vllm/`](../learn-vllm/) 和 [`stage-12-mlops/`](../stage-12-mlops/) 互补：

- **本课程**：推理引擎**全景与选型**、通用优化原理、多引擎实战（vLLM / SGLang / TensorRT-LLM / llama.cpp / LMDeploy）、服务架构、压测调优、思考型模型推理服务、生产部署
- **learn-vllm**：vLLM 单一引擎深潜（PagedAttention → 生产运维），本课程第 3 课做快速上手并交叉引用
- **stage-12 MLOps**：Docker、MLflow、监控体系等更广泛的 MLOps 全景

Markdown 文档 + 可选 GPU 动手练习，默认技术栈：**Python 3.11+ · NVIDIA GPU（可选）· vLLM / SGLang / TensorRT-LLM / llama.cpp**。

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 参考 | `00_inference_glossary.md` | 术语表、引擎对比、选型速查 |
| 第1课 | `01_engine_fundamentals.md` | 推理引擎是什么、推理全流程、瓶颈、引擎/框架/服务分层 |
| 第2课 | `02_core_optimizations.md` | KV Cache、分页与前缀缓存、连续批处理、Chunked Prefill、投机解码、量化 |
| 第3课 | `03_vllm_quickstart.md` | vLLM 快速上手：OpenAI API、离线推理、关键参数（深潜见 learn-vllm） |
| 第4课 | `04_sglang_practice.md` | SGLang：RadixAttention、结构化输出、Agent 与多步推理 |
| 第5课 | `05_tensorrt_llm.md` | TensorRT-LLM：engine 构建、FP8、CUDA Graph、NVIDIA 生态 |
| 第6课 | `06_cpu_edge_engines.md` | llama.cpp / GGUF / Ollama、LMDeploy、边缘端推理 |
| 第7课 | `07_serving_architecture.md` | 服务架构：并发调度、PD 分离、LoRA、多模态、网关 |
| 第8课 | `08_benchmark_and_tuning.md` | 指标、压测、参数调优、监控 |
| 第9课 | `09_reasoning_models_serving.md` | 思考型模型（o3 / R1 / Qwen3 风格）推理服务：长 CoT、预算控制、流式 |
| 第10课 | `10_production_deployment.md` | Docker / K8s、GPU 共享、弹性扩缩容、成本与安全 |

## 学习目标

- 能说清推理引擎要解决的三大瓶颈，并读懂 TTFT / TPOT / 吞吐指标
- 能按场景在 vLLM、SGLang、TensorRT-LLM、llama.cpp、LMDeploy 之间做选型
- 至少能启动两个引擎的 OpenAI 兼容服务并完成客户端调用
- 理解前缀缓存、连续批处理、PD 分离、投机解码的适用条件
- 能为思考型模型设计服务参数（长 CoT、预算控制、流式展示）
- 能设计压测方案、解读指标并做参数调优

## 学习方式

- Markdown 文档 + 终端 / Python 动手练习
- 建议前置：[`stage-04-llm-basics`](../stage-04-llm-basics/)（Prompt）、[`stage-05-llm-api`](../stage-05-llm-api/)（OpenAI API）
- GPU 环境：8GB 显存可跑 7B INT4；16GB+ 可跑 7B FP16（第 6 课 CPU 练习无需 GPU）
- 每课末尾有**自检清单**；`practice/` 提供无需 GPU 的模拟器和通用客户端脚本

## 环境准备

```bash
cd practice
pip install -r requirements.txt
python benchmark_simulator.py        # 无需 GPU：理解静态 vs 连续批处理
python openai_client_demo.py         # 连接任一 OpenAI 兼容推理服务
```

有 NVIDIA GPU 时：

```bash
pip install vllm sglang
# vLLM 启动示例
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --max-model-len 4096 --port 8000
```

无 GPU 时：仍可阅读全部文档，并用 llama.cpp / Ollama 完成第 6 课 CPU 练习。

## 学习顺序建议

```
stage-05 LLM API → learn-inference-engine（本课程）
                        │
                        ├─ learn-vllm（vLLM 深潜，可与第 3 课并行）
                        ├─ stage-11 AI 工程化（FastAPI 网关封装）
                        ├─ stage-12 MLOps（容器 + 监控体系）
                        └─ learn-se 性能工程（延迟分布、压测方法论）
```

## 与相邻课程的分工

| 主题 | 权威来源 | 说明 |
|------|----------|------|
| vLLM PagedAttention / 调度器深潜 | learn-vllm 第 2、3 课 | 本课程第 2 课只讲通用原理 |
| vLLM 安装 / API / 量化 / 多 GPU | learn-vllm 第 4–6 课 | 本课程第 3 课做快速上手 |
| 多引擎对比与选型 | 本课程第 1、00 课 | learn-vllm 仅一节速查 |
| SGLang / TensorRT-LLM / llama.cpp | 本课程第 4–6 课 | learn-vllm 不做展开 |
| Docker / MLflow / 监控体系 | stage-12 | 本课程第 8、10 课做推理专项 |
| 思考型模型服务 | 本课程第 9 课 | 随 o3 / R1 / Qwen3 生态更新 |

## 推荐资源

- [vLLM 官方文档](https://docs.vllm.ai/)
- [SGLang 官方文档](https://docs.sglang.ai/)
- [TensorRT-LLM GitHub](https://github.com/NVIDIA/TensorRT-LLM)
- [llama.cpp GitHub](https://github.com/ggml-org/llama.cpp)
- [LMDeploy GitHub](https://github.com/InternLM/lmdeploy)
- [DeepSeek-R1 技术报告](https://arxiv.org/abs/2501.12948)
