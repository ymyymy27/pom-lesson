> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第5课：离线推理与 Python API

> 上一课：[`04-第4课安装与 OpenAI 兼容 API.md`](<04-第4课安装与 OpenAI 兼容 API.md>) · 下一课：[`06-第6课量化与多 GPU 并行.md`](<06-第6课量化与多 GPU 并行.md>)

---

## 1. 两种使用模式

| 模式 | 适用场景 |
|------|---------|
| **OpenAI API Server** | 多客户端、微服务、LangChain 集成 |
| **Python LLM 类** | 批处理脚本、Notebook 实验、离线评测 |

两者底层引擎相同，共享 PagedAttention 与连续批处理。

---

## 2. LLM 类基础用法

```python
from vllm import LLM, SamplingParams

llm = LLM(
    model="Qwen/Qwen2.5-7B-Instruct",
    dtype="auto",
    max_model_len=4096,
    gpu_memory_utilization=0.9,
)

params = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    max_tokens=256,
    stop=["<|endoftext|>", ""],
)

prompts = [
    "解释什么是向量数据库",
    "写一段 Python 快速排序",
    "将 'Hello' 翻译成中文",
]

outputs = llm.generate(prompts, params)

for prompt, output in zip(prompts, outputs):
    text = output.outputs[0].text
    print(f"Q: {prompt[:30]}...")
    print(f"A: {text[:100]}...\n")
```

---

## 3. SamplingParams 详解

| 参数 | 含义 | 典型值 |
|------|------|--------|
| `temperature` | 随机性，0=贪婪 | 0–1 |
| `top_p` | 核采样阈值 | 0.9 |
| `top_k` | 只从 top-k token 采样 | 50 |
| `max_tokens` | 最大生成 token 数 | 128–2048 |
| `stop` | 停止字符串列表 | 模型 eos token |
| `presence_penalty` | 重复惩罚 | 0–2 |
| `frequency_penalty` | 频率惩罚 | 0–2 |
| `n` | 每个 prompt 生成几条 | 1（beam 时 >1） |
| `seed` | 随机种子（可复现） | 42 |

```python
# 确定性输出（评测常用）
deterministic = SamplingParams(temperature=0, max_tokens=512)

# 创意写作
creative = SamplingParams(temperature=0.9, top_p=0.95, max_tokens=1024)
```

---

## 4. Chat 模板

指令模型需要正确的 chat template：

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

messages = [
    {"role": "system", "content": "你是编程助手"},
    {"role": "user", "content": "用 Python 读 CSV"},
]
prompt = tokenizer.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)

outputs = llm.generate([prompt], params)
print(outputs[0].outputs[0].text)
```

**注意：** OpenAI API Server 内部自动处理 template；离线 API 需手动 apply。

---

## 5. Embedding 模型

```python
from vllm import LLM

llm = LLM(
    model="BAAI/bge-small-en-v1.5",
    task="embed",
    dtype="float16",
)

outputs = llm.embed(["Hello world", "vLLM is fast"])
for i, out in enumerate(outputs):
    vec = out.outputs.embedding
    print(f"文本 {i}: dim={len(vec)}, 前3维={vec[:3]}")
```

RAG 流水线中，embedding 与 generation 可分别部署不同 vLLM 实例。

---

## 6. 结构化输出（JSON Mode）

```python
from pydantic import BaseModel
from vllm import LLM
from vllm.sampling_params import GuidedDecodingParams

class Sentiment(BaseModel):
    label: str
    score: float

llm = LLM(model="Qwen/Qwen2.5-7B-Instruct")
guided = GuidedDecodingParams(json=Sentiment.model_json_schema())
params = SamplingParams(max_tokens=128, guided_decoding=guided)

outputs = llm.generate(
    ['分析情感: "这个产品太棒了!"'],
    params,
)
print(outputs[0].outputs[0].text)
```

（具体 API 随 vLLM 版本演进，以[官方文档](https://docs.vllm.ai/)为准。）

---

## 7. API Server vs LLM 类选型

```
需要 HTTP / 多进程客户端 / 与 LangChain 集成？
  └─ OpenAI API Server

批量离线评测 / Notebook / 单进程脚本？
  └─ LLM 类

同一机器两者不要同时加载同一模型（显存双倍）
```

---

## 8. 动手练习

1. 用 `LLM` 类对 100 条 prompt 批量推理，统计总耗时与 tokens/s
2. 对比 `temperature=0` 与 `0.9` 的输出差异
3. 用 `apply_chat_template` 构造多轮对话 prompt
4. （可选）加载 embedding 模型，对 10 段文本生成向量

---

## 9. 自检清单

- [ ] 能用 LLM + SamplingParams 完成批量推理
- [ ] 理解 temperature / top_p / max_tokens 的作用
- [ ] 知道 chat 模型需 apply_chat_template
- [ ] 了解 embed task 的基本用法
- [ ] 能判断何时用 API Server vs LLM 类

---

## 下一课

[`06-第6课量化与多 GPU 并行.md`](<06-第6课量化与多 GPU 并行.md>) — 量化与多 GPU 并行
