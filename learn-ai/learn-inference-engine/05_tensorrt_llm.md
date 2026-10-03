# 第5课：TensorRT-LLM — NVIDIA 生态的极致优化

> 上一课：[`04_sglang_practice.md`](04_sglang_practice.md) · 下一课：[`06_cpu_edge_engines.md`](06_cpu_edge_engines.md)

---

## 1. TensorRT-LLM 是什么

**TensorRT-LLM（TRT-LLM）= NVIDIA 官方的 LLM 推理引擎**，把模型编译成 TensorRT engine，深度利用 CUDA Graph、FP8、融合算子。

适用场景：

- NVIDIA 硬件栈（A100/H100/H200/B200、边缘 Jetson）
- 要榨干单卡/整机性能
- NVIDIA NIM 私有化部署
- 对 PyTorch 依赖敏感的生产环境

代价：**上手门槛高**——需要 `trtllm-build` 构建 engine、绑定 GPU 与 CUDA 版本、按模型架构定制。

---

## 2. 工作流程：从权重到服务

```
模型权重 (HF) ──> trtllm-build ──> TensorRT engine（与 GPU 架构绑定）
                                          │
                                          ▼
                              TRT-LLM 服务 / NIM / Triton
```

与 vLLM/SGLang 的最大差异：**先编译，后运行**。engine 与 GPU 型号绑定，换卡需重新 build。

---

## 3. 最小示例（概念）

```bash
# 1. 转换权重（以 Llama 系为例）
python convert_checkpoint.py --model_dir ./model \
    --output_dir ./tllm_checkpoint --dtype float16

# 2. 构建 engine（指定 GPU 架构，如 sm_90 = H100）
trtllm-build --checkpoint_dir ./tllm_checkpoint \
    --output_dir ./engine --gpt_attention_plugin float16 \
    --gemm_plugin float16 --max_batch_size 128 \
    --max_input_len 4096 --max_seq_len 8192

# 3. 启动 OpenAI 兼容服务
python examples/summarize.py --engine_dir ./engine
```

> 具体命令随版本变化，以官方仓库 README 为准。日常工作中优先用 NVIDIA 提供的模型转换脚本与容器镜像。

---

## 4. TRT-LLM 与 vLLM 对比

| 维度 | TensorRT-LLM | vLLM |
|------|--------------|------|
| 运行方式 | 先编译 engine | 动态加载，即装即用 |
| 峰值性能 | 极致（同硬件通常最优或并列） | 很高 |
| 部署复杂度 | 高（版本/架构绑定） | 低 |
| 多模型灵活切换 | 每个模型一套 engine | 模型即路径，切换方便 |
| 生态 | NVIDIA NIM / Triton | 开源社区、云厂商 |
| 调试体验 | 编译错误晦涩 | 相对友好 |

**选型结论**：

- 追求极致性能、硬件固定、团队有 NVIDIA 经验 → TRT-LLM
- 快速迭代、多模型、开源优先 → vLLM / SGLang

---

## 5. 关键优化特性

### 5.1 CUDA Graph

把一组 kernel 编译为固定图，减少启动开销。TRT-LLM 原生集成，vLLM V1 也支持。

### 5.2 FP8

H100 起支持 FP8 张量核心；FP8 权重 + FP8 KV Cache 可显著降显存、提吞吐，质量损失小。

### 5.3 In-flight Batching（连续批处理）

TRT-LLM 同样支持请求级动态批处理，与 vLLM 连续批处理等价。

### 5.4 Paged KV Cache

TRT-LLM 有 paged KV cache 实现，注意与 vLLM 的显存管理粒度不同。

---

## 6. 与 NVIDIA NIM 的关系

NVIDIA NIM（NVIDIA Inference Microservices）把 TRT-LLM/Triton 封装成微服务容器，提供 OpenAI 兼容 API：

```
API 请求 → NIM 容器（TRT-LLM engine + Triton）→ GPU
```

适合不想手工 build engine 的企业用户；但 license、镜像下载与硬件绑定需按 NVIDIA 条款评估。

---

## 7. 常见坑

| 现象 | 原因 | 处理 |
|------|------|------|
| engine 加载失败 | GPU 架构不匹配 | 用与目标 GPU 一致的容器重新 build |
| 转换脚本报错 | 模型架构/版本不支持 | 查官方支持矩阵 |
| 内存不足 | max_batch/seq_len 过大 | 降参数，或开 paged KV + FP8 |
| 编译很久 | 大模型正常现象 | 缓存 build 产物，CI 中固化 |

---

## 8. 动手练习

1. 阅读官方仓库 README，列出 3 个支持 OpenChat/JSON 模式的特性
2. 有 GPU 时：用官方示例容器 build 一个小模型（如 Llama-3.2-1B）engine
3. 比较 build 后的 engine 启动与 vLLM 冷启动的时间差异

---

## 9. 自检清单

- [ ] 能说出 TRT-LLM 与 vLLM 的架构差异（编译 vs 动态）
- [ ] 能解释为什么 engine 与 GPU 型号绑定
- [ ] 知道 NIM 与 TRT-LLM 的关系
- [ ] 能判断自己的项目该不该用 TRT-LLM

---

## 下一课

[`06_cpu_edge_engines.md`](06_cpu_edge_engines.md) — llama.cpp / Ollama / LMDeploy：CPU 与边缘
