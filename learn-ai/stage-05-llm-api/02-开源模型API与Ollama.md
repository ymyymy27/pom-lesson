# 开源模型 API 与 Ollama

## 学习目标

- 掌握 Ollama 本地部署和 API 调用
- 学会使用开源模型（Qwen、LLaMA、DeepSeek）
- 了解模型量化和本地推理优化

## 1. Ollama 深入使用

```bash
# 管理模型
ollama pull qwen2.5:7b         # 下载模型
ollama pull deepseek-r1:8b     # 推理模型
ollama list                     # 已下载模型
ollama rm qwen2.5:7b           # 删除模型
ollama show qwen2.5:7b         # 模型信息

# 运行模型（交互式）
ollama run qwen2.5:7b

# 自定义模型（Modelfile）
# 创建文件 Modelfile：
# FROM qwen2.5:7b
# SYSTEM "你是一个专业的Python编程助手"
# PARAMETER temperature 0.3

ollama create my-coder -f Modelfile
ollama run my-coder
```

## 2. Ollama API 调用

```python
import requests
import json

# 生成接口
def ollama_generate(prompt, model="qwen2.5:7b"):
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False,
    })
    return response.json()["response"]

# Chat 接口（支持多轮对话）
def ollama_chat(messages, model="qwen2.5:7b"):
    response = requests.post("http://localhost:11434/api/chat", json={
        "model": model,
        "messages": messages,
        "stream": False,
    })
    return response.json()["message"]["content"]

# 多轮对话
messages = [
    {"role": "system", "content": "你是一个 Python 专家"},
    {"role": "user", "content": "什么是列表推导式？"},
]
reply = ollama_chat(messages)
print(reply)

# 流式输出
def ollama_stream(prompt, model="qwen2.5:7b"):
    response = requests.post("http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": True},
        stream=True
    )
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            if not data.get("done"):
                print(data["response"], end="", flush=True)
    print()
```

## 3. 用 OpenAI 兼容接口调 Ollama

Ollama 提供 OpenAI 兼容接口，可以直接用 openai 库。

```python
from openai import OpenAI

# Ollama 的 OpenAI 兼容端点
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # Ollama 不需要真正的 key
)

response = client.chat.completions.create(
    model="qwen2.5:7b",
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": "解释一下什么是 RAG"},
    ],
    temperature=0.7,
)
print(response.choices[0].message.content)

# 好处：代码几乎不用改，切换模型只需改 base_url 和 model
```

## 4. Embedding 模型

```python
# Ollama embedding
response = requests.post("http://localhost:11434/api/embed", json={
    "model": "nomic-embed-text",
    "input": "什么是机器学习？"
})
embedding = response.json()["embeddings"][0]
print(f"向量维度: {len(embedding)}")

# 批量 embedding
texts = ["句子1", "句子2", "句子3"]
response = requests.post("http://localhost:11434/api/embed", json={
    "model": "nomic-embed-text",
    "input": texts
})
embeddings = response.json()["embeddings"]
```

## 5. 模型量化知识

```
模型参数精度：
- FP32（32位浮点）：原始精度，显存占用大
- FP16（16位浮点）：精度损失小，显存减半
- INT8（8位整数）：显存减少 4x，轻微精度损失
- INT4（4位整数）：显存减少 8x，适合消费级显卡

7B 模型显存需求：
- FP32: ~28GB
- FP16: ~14GB
- INT8: ~7GB
- INT4: ~4GB ← 普通电脑可跑

Ollama 默认使用 4-bit 量化 (Q4_0)
```

## 6. 多模型调度

```python
class ModelRouter:
    """根据任务类型选择最优模型"""

    def __init__(self):
        self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

    def route(self, task_type: str, message: str) -> str:
        model_map = {
            "chat": "qwen2.5:7b",
            "code": "deepseek-coder-v2:16b",
            "reasoning": "deepseek-r1:8b",
            "translation": "qwen2.5:7b",
        }
        model = model_map.get(task_type, "qwen2.5:7b")

        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": message}],
        )
        return response.choices[0].message.content

router = ModelRouter()
print(router.route("code", "用 Python 实现二分查找"))
print(router.route("reasoning", "9.11 和 9.9 哪个大？"))
```

## 练习

1. 用 Ollama 部署 Qwen2.5:7b，通过 API 实现多轮对话
2. 用 OpenAI 兼容接口封装，实现一键切换 OpenAI/Ollama
3. 测试同一问题在不同模型上的输出质量对比
4. 实现一个简单的模型路由，根据问题类型选择模型

## 下一节

→ [03-LangChain入门](03-LangChain入门.md)
