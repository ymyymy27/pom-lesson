import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：模型服务框架（vLLM / Ollama / TGI）
==============================================================================

模型服务 = 把 LLM 部署为可调用的 API
不同框架适合不同场景。

本课内容：
1. 模型服务框架对比
2. Ollama 本地服务
3. vLLM 高性能服务
4. OpenAI 兼容 API
5. 模型管理
6. 服务健康检查
==============================================================================
"""

import json
import time
import httpx

OLLAMA_URL = "http://localhost:11434"

print("=" * 60)
print("第3课：模型服务框架")
print("=" * 60)

# ============================================================================
# 1. 框架对比
# ============================================================================
print("\n--- 1. 框架对比 ---")
print("""
┌──────────────┬──────────────────────────────────────────┐
│  框架         │  特点                                     │
├──────────────┼──────────────────────────────────────────┤
│  Ollama      │  一键部署，支持 GGUF 量化                │
│              │  适合：开发/测试/个人使用                 │
│              │  CPU/GPU 均可，上手最简单                 │
├──────────────┼──────────────────────────────────────────┤
│  vLLM        │  PagedAttention，连续批处理              │
│              │  适合：生产环境高并发                     │
│              │  需要 GPU，性能最强                       │
├──────────────┼──────────────────────────────────────────┤
│  TGI         │  HuggingFace 官方，Flash Attention       │
│  (Text Gen   │  适合：HF 模型生态                       │
│   Inference) │  需要 GPU                                │
├──────────────┼──────────────────────────────────────────┤
│  llama.cpp   │  纯 CPU 推理，GGUF 格式                  │
│  (server)    │  适合：无 GPU 场景                       │
│              │  Ollama 底层就是 llama.cpp                │
├──────────────┼──────────────────────────────────────────┤
│  Triton      │  NVIDIA 官方，多模型并行                 │
│  Inference   │  适合：企业级多模型服务                  │
│  Server      │  配置复杂                                │
└──────────────┴──────────────────────────────────────────┘

选择建议：
  开发测试 → Ollama（最简单）
  生产单模型 → vLLM（最快）
  多模型服务 → Triton
  无 GPU → Ollama + GGUF
""")

# ============================================================================
# 2. Ollama
# ============================================================================
print("\n--- 2. Ollama ---")

class OllamaService:
    """Ollama 模型服务客户端"""

    def __init__(self, base_url: str = OLLAMA_URL):
        self.base_url = base_url

    def list_models(self) -> list:
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            models = resp.json().get("models", [])
            return [{"name": m["name"], "size": m.get("size", 0),
                     "modified": m.get("modified_at", "")} for m in models]
        except:
            return [{"name": "qwen2.5:7b", "size": 4_700_000_000, "modified": "模拟"}]

    def chat(self, model: str, message: str, stream: bool = False) -> dict:
        start = time.time()
        try:
            resp = httpx.post(f"{self.base_url}/api/chat", json={
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "stream": False,
                "options": {"num_predict": 100}
            }, timeout=30.0)
            data = resp.json()
            return {
                "reply": data.get("message", {}).get("content", ""),
                "model": model,
                "latency_ms": round((time.time() - start) * 1000),
                "eval_count": data.get("eval_count", 0),
                "eval_duration_ns": data.get("eval_duration", 0),
            }
        except:
            return {
                "reply": "[模拟回答]",
                "model": model,
                "latency_ms": round((time.time() - start) * 1000),
            }

    def show_model(self, model: str) -> dict:
        try:
            resp = httpx.post(f"{self.base_url}/api/show", json={"name": model}, timeout=5.0)
            data = resp.json()
            return {
                "family": data.get("details", {}).get("family", "unknown"),
                "parameter_size": data.get("details", {}).get("parameter_size", "unknown"),
                "quantization": data.get("details", {}).get("quantization_level", "unknown"),
            }
        except:
            return {"family": "qwen2.5", "parameter_size": "7B", "quantization": "Q4_K_M"}

    def health(self) -> dict:
        try:
            resp = httpx.get(f"{self.base_url}/", timeout=3.0)
            return {"status": "healthy", "code": resp.status_code}
        except:
            return {"status": "unhealthy", "error": "连接失败"}

ollama = OllamaService()

# 健康检查
health = ollama.health()
print(f"Ollama 状态: {health}")

# 列出模型
models = ollama.list_models()
print(f"可用模型: {len(models)} 个")
for m in models[:5]:
    size_gb = m['size'] / 1e9 if m['size'] else 0
    print(f"  {m['name']}: {size_gb:.1f}GB")

# 模型详情
info = ollama.show_model("qwen2.5:7b")
print(f"模型详情: {info}")

# 聊天测试
result = ollama.chat("qwen2.5:7b", "一句话介绍Docker")
print(f"聊天测试: {result['reply'][:60]}... ({result['latency_ms']}ms)")

print("""
Ollama 常用命令：
  ollama pull qwen2.5:7b      下载模型
  ollama list                  列出已下载模型
  ollama run qwen2.5:7b        交互式聊天
  ollama serve                 启动服务（默认11434）
  ollama rm qwen2.5:7b         删除模型
  ollama cp qwen2.5:7b mymodel 复制模型
""")

# ============================================================================
# 3. vLLM
# ============================================================================
print("\n--- 3. vLLM ---")
print("""
vLLM = 最高性能的 LLM 推理引擎

核心技术：
  PagedAttention：KV Cache 分页管理，减少显存浪费
  连续批处理：动态合并请求，先完成先返回
  张量并行：多 GPU 并行推理

启动 vLLM 服务：
```bash
# 安装
pip install vllm

# 启动 OpenAI 兼容 API
python -m vllm.entrypoints.openai.api_server \\
    --model Qwen/Qwen2.5-7B-Instruct \\
    --dtype float16 \\
    --max-model-len 4096 \\
    --gpu-memory-utilization 0.9 \\
    --port 8000
```

Docker 部署：
```yaml
services:
  vllm:
    image: vllm/vllm-openai:latest
    ports: ["8000:8000"]
    volumes: ["./models:/models"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    command: >
      --model /models/Qwen2.5-7B-Instruct
      --dtype float16
      --max-model-len 4096
```

性能（A100 80GB, 7B 模型）：
  Ollama:  ~30 tokens/s（单请求）
  vLLM:    ~500+ tokens/s（批处理）
  差距：   ~15倍！
""")

# ============================================================================
# 4. OpenAI 兼容 API
# ============================================================================
print("\n--- 4. OpenAI 兼容 ---")
print("""
vLLM / Ollama 都提供 OpenAI 兼容 API：

  ┌──────────────────────────────────────────────────────┐
  │  你的代码                                             │
  │  from openai import OpenAI                           │
  │  client = OpenAI(base_url=..., api_key=...)          │
  │  client.chat.completions.create(...)                 │
  └──────────────┬───────────────────────────────────────┘
                 │
  ┌──────────────▼───────────────────────────────────────┐
  │  切换 base_url 即可切换后端：                         │
  │                                                      │
  │  OpenAI:   https://api.openai.com/v1                 │
  │  Ollama:   http://localhost:11434/v1                  │
  │  vLLM:     http://localhost:8000/v1                   │
  │  DeepSeek: https://api.deepseek.com/v1               │
  │                                                      │
  │  代码完全不用改！只改 base_url                        │
  └──────────────────────────────────────────────────────┘
""")

# 演示 OpenAI 兼容调用
class OpenAICompatClient:
    """OpenAI 兼容客户端"""

    def __init__(self, base_url: str, api_key: str = "ollama"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def chat(self, model: str, messages: list, **kwargs) -> dict:
        try:
            resp = httpx.post(f"{self.base_url}/v1/chat/completions", json={
                "model": model, "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 100),
                "temperature": kwargs.get("temperature", 0.7),
            }, headers={"Authorization": f"Bearer {self.api_key}"},
               timeout=30.0)
            return resp.json()
        except:
            return {"choices": [{"message": {"content": "[模拟回答]"}}]}

    def list_models(self) -> list:
        try:
            resp = httpx.get(f"{self.base_url}/v1/models",
                           headers={"Authorization": f"Bearer {self.api_key}"},
                           timeout=5.0)
            return [m["id"] for m in resp.json().get("data", [])]
        except:
            return ["qwen2.5:7b"]

# Ollama OpenAI 兼容
compat = OpenAICompatClient(OLLAMA_URL)
models = compat.list_models()
print(f"OpenAI 兼容模型列表: {models[:3]}")

result = compat.chat("qwen2.5:7b", [{"role": "user", "content": "Hello"}])
reply = result.get("choices", [{}])[0].get("message", {}).get("content", "")
print(f"OpenAI 兼容调用: {reply[:60]}...")

# ============================================================================
# 5. 模型管理
# ============================================================================
print("\n--- 5. 模型管理 ---")
print("""
生产环境模型管理：

1. 模型仓库
   HuggingFace Hub → 下载到本地
   ModelScope → 国内镜像
   自建模型仓库 → MinIO / S3

2. 版本管理
   模型名:标签 → qwen2.5:7b-v2
   按日期标记 → model-20240301
   Git LFS → 大文件版本控制

3. 模型缓存
   首次下载后本地缓存
   Ollama: ~/.ollama/models/
   HuggingFace: ~/.cache/huggingface/

4. 多模型管理
   同时加载多个模型（显存允许时）
   模型热切换（不停服更新）
   灰度发布（10%流量用新模型）

5. 资源规划
   ┌──────────┬────────┬────────┬──────────┐
   │  模型     │  FP16  │  INT4  │  推荐GPU  │
   ├──────────┼────────┼────────┼──────────┤
   │  1.5B    │  3GB   │  1.5GB │  任意     │
   │  7B      │  14GB  │  4.5GB │  RTX 3090 │
   │  14B     │  28GB  │  9GB   │  A100 40G │
   │  70B     │  140GB │  40GB  │  A100 80G │
   └──────────┴────────┴────────┴──────────┘
""")

# ============================================================================
# 6. 健康检查
# ============================================================================
print("\n--- 6. 健康检查 ---")

class ModelServiceMonitor:
    """模型服务监控"""

    def __init__(self, services: dict):
        self.services = services

    def check_all(self) -> dict:
        results = {}
        for name, url in self.services.items():
            start = time.time()
            try:
                resp = httpx.get(url, timeout=3.0)
                latency = round((time.time() - start) * 1000)
                results[name] = {
                    "status": "healthy" if resp.status_code < 400 else "degraded",
                    "latency_ms": latency,
                }
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "error": type(e).__name__,
                }
        return results

monitor = ModelServiceMonitor({
    "ollama": f"{OLLAMA_URL}/",
    "ollama_api": f"{OLLAMA_URL}/api/tags",
})

health = monitor.check_all()
print(f"健康检查:")
for name, result in health.items():
    status = result["status"]
    icon = "✓" if status == "healthy" else "✗"
    extra = f" {result.get('latency_ms', '?')}ms" if status == "healthy" else f" {result.get('error', '')}"
    print(f"  {icon} {name}: {status}{extra}")

print("\n" + "=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] 模型服务框架对比（Ollama/vLLM/TGI）")
print("  [v] Ollama 模型管理与调用")
print("  [v] vLLM 高性能部署")
print("  [v] OpenAI 兼容 API（一套代码多后端）")
print("  [v] 生产模型管理（版本/缓存/资源规划）")
print("  [v] 服务健康检查")
print("=" * 60)
print("\n下一课：04_inference_optimization.py - 推理优化")
