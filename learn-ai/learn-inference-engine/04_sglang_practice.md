# 第4课：SGLang 实战 — RadixAttention 与 Agent 场景

> 上一课：[`03_vllm_quickstart.md`](03_vllm_quickstart.md) · 下一课：[`05_tensorrt_llm.md`](05_tensorrt_llm.md)

---

## 1. SGLang 是什么

**SGLang = 高性能推理引擎 + 结构化生成与复杂控制流**。核心特色：

- **RadixAttention**：基数树前缀缓存，RAG / 多轮 / Agent 场景命中率极高
- **XGrammar 结构化输出**：JSON Schema / 正则约束，生成过程零非法输出
- **Agent 控制流**：原生支持多步推理、工具调用、并行生成

> 如果你的场景是「请求前缀高度重复」或「JSON 密集 / 多步 Agent」，SGLang 常比 vLLM 吞吐更高；通用场景两者差距需要实测。

---

## 2. 安装与启动

```bash
pip install sglang
```

```bash
python -m sglang.launch_server \
    --model-path Qwen/Qwen2.5-7B-Instruct \
    --host 0.0.0.0 \
    --port 30000 \
    --mem-fraction-static 0.85
```

OpenAI 兼容验证：

```bash
curl http://localhost:30000/health
curl http://localhost:30000/v1/models
```

---

## 3. 快速对比：vLLM 与 SGLang

| 维度 | vLLM | SGLang |
|------|------|--------|
| 前缀缓存 | 自动前缀缓存（块级） | RadixAttention（基数树） |
| 结构化输出 | Outlines / XGrammar | XGrammar 深度集成 |
| Agent 控制流 | 由上层框架（LangGraph 等）做 | 引擎层支持多步/并行 |
| 生态成熟度 | 最大、企业案例多 | 增长最快，论文驱动 |
| 学习曲线 | 中 | 中高（概念更多） |

**建议**：默认先用 vLLM；前缀复用高或 JSON 密集时，用同一模型分别压测再选。

---

## 4. 结构化输出：JSON Mode

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:30000/v1", api_key="unused")

schema = {
    "type": "object",
    "properties": {
        "city": {"type": "string"},
        "temperature": {"type": "number"},
        "advice": {"type": "string"},
    },
    "required": ["city", "temperature", "advice"],
}

resp = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct",
    messages=[{"role": "user", "content": "杭州今天适合穿什么？返回 JSON。"}],
    extra_body={"response_format": {"type": "json_schema", "json_schema": schema}},
)
print(resp.choices[0].message.content)
```

特点：由 XGrammar 在解码期约束 token，**结果 100% 合法 JSON**，比「生成后解析重试」更快更稳。

---

## 5. Agent / 多步推理场景

SGLang 原生支持多步生成与工具调用，适合高频小步推理：

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:30000/v1", api_key="unused")

# 第一步：生成搜索词
resp1 = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct",
    messages=[{"role": "user", "content": "把问题改写为 3 个搜索关键词，输出 JSON 数组"}],
    extra_body={"response_format": {"type": "json_object"}},
)
print(resp1.choices[0].message.content)

# 第二步：携带检索结果继续推理
resp2 = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct",
    messages=[
        {"role": "user", "content": "问题：杭州最佳旅行季节？"},
        {"role": "assistant", "content": resp1.choices[0].message.content},
        {"role": "user", "content": "检索结果：春季（3-5月）气温 15-25℃，适合户外。"},
    ],
)
print(resp2.choices[0].message.content)
```

> 每一步的 prompt 前缀会被 RadixAttention 复用，因此 Agent 多轮循环的增量开销远小于普通引擎。

---

## 6. 关键启动参数

| 参数 | 作用 | 常见值 |
|------|------|--------|
| `--mem-fraction-static` | 静态显存比例（类似 vLLM gpu-util） | 0.80–0.90 |
| `--tp` | 张量并行 GPU 数 | 1 / 2 / 4 / 8 |
| `--enable-mixed-chunk` | 混合 Chunked Prefill | 建议开启 |
| `--schedule-policy` | 调度策略（lpm / random / fcfs） | lpm |
| `--stream-interval` | 流式返回间隔 | 默认即可 |

---

## 7. 常见坑

| 现象 | 原因 | 处理 |
|------|------|------|
| JSON 输出格式错误 | 未用 response_format 约束 | 始终带 schema |
| 前缀缓存未命中 | 提示词模板不一致 | 固定 system prompt 与消息格式 |
| Agent 每步很慢 | 每步都重新 prefill | 检查是否命中缓存，必要时合并步骤 |
| 与 vLLM 指标差异大 | 配置不对等 | 用同模型、同并发、同 max_tokens 压测 |

---

## 8. 动手练习

1. 启动 SGLang，用 JSON Schema 完成一次结构化输出
2. 对比相同请求下 vLLM 与 SGLang 的 TTFT（前缀缓存命中/未命中各测 5 次取中位数）
3. 设计一个 3 步 Agent 循环，观察第 2、3 步是否命中前缀缓存

---

## 9. 自检清单

- [ ] 能解释 RadixAttention 与 PagedAttention 的区别
- [ ] 能启动 SGLang 并完成 OpenAI 兼容调用
- [ ] 能用 response_format 输出合法 JSON
- [ ] 能判断自己的场景适不适合 SGLang

---

## 下一课

[`05_tensorrt_llm.md`](05_tensorrt_llm.md) — TensorRT-LLM：NVIDIA 极致优化
