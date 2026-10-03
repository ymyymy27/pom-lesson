import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第1课：FastAPI 构建 AI 服务
==============================================================================

FastAPI 是构建 AI 后端的首选框架：
  异步高性能、自动文档、类型校验、原生支持流式

本课内容：
1. FastAPI 核心概念
2. AI 聊天 API 设计
3. 请求/响应模型
4. 异步 LLM 调用
5. 错误处理
6. API 文档与测试
==============================================================================
"""

import json
import time
import hashlib
from datetime import datetime

import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"

print("=" * 60)
print("第1课：FastAPI 构建 AI 服务")
print("=" * 60)

# ============================================================================
# 1. FastAPI 核心概念
# ============================================================================
print("\n--- 1. 核心概念 ---")
print("""
FastAPI 为什么适合 AI 服务？

  ✅ 异步支持：原生 async/await，高并发 LLM 调用
  ✅ 类型校验：Pydantic 自动验证请求/响应
  ✅ 自动文档：Swagger UI + ReDoc
  ✅ 流式输出：StreamingResponse 支持 SSE
  ✅ 中间件：认证、限流、日志等
  ✅ 生态丰富：与 LangChain/OpenAI SDK 无缝集成

基本结构：
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="AI Service", version="1.0")

class ChatRequest(BaseModel):
    message: str
    model: str = "qwen2.5:7b"
    temperature: float = 0.7

@app.post("/chat")
async def chat(req: ChatRequest):
    # 调用 LLM
    result = await call_llm(req.message, req.model)
    return {"reply": result}
```

启动：
```bash
pip install fastapi uvicorn
uvicorn app:app --reload --port 8000
# 访问 http://localhost:8000/docs 查看文档
```
""")

# ============================================================================
# 2. AI 聊天 API 设计
# ============================================================================
print("\n--- 2. API 设计 ---")

class ChatRequest:
    """聊天请求模型（模拟 Pydantic BaseModel）"""
    def __init__(self, message: str, model: str = MODEL,
                 temperature: float = 0.7, max_tokens: int = 500,
                 system_prompt: str = ""):
        self.message = message
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt

class ChatResponse:
    """聊天响应模型"""
    def __init__(self, reply: str, model: str, latency: float, usage: dict):
        self.reply = reply
        self.model = model
        self.latency = latency
        self.usage = usage

    def to_dict(self):
        return {
            "reply": self.reply,
            "model": self.model,
            "latency_ms": round(self.latency * 1000),
            "usage": self.usage,
        }

print("""
API 端点设计：

  POST /chat              同步聊天
  POST /chat/stream       流式聊天（SSE）
  POST /chat/session      多轮会话
  POST /upload            上传文档
  GET  /models            可用模型列表
  GET  /health            健康检查

请求模型：
  message: str            用户消息（必填）
  model: str              模型名称
  temperature: float      生成温度
  max_tokens: int         最大输出token
  system_prompt: str      系统提示词

响应模型：
  reply: str              AI 回复
  model: str              使用的模型
  latency_ms: int         延迟（毫秒）
  usage: dict             token 用量
""")

# ============================================================================
# 3. LLM 调用封装
# ============================================================================
print("\n--- 3. LLM 调用 ---")

class LLMClient:
    """LLM 客户端（封装 Ollama API）"""

    def __init__(self, base_url: str = OLLAMA_URL, default_model: str = MODEL):
        self.base_url = base_url
        self.default_model = default_model
        self.call_count = 0
        self.total_latency = 0

    def chat(self, request: ChatRequest) -> ChatResponse:
        """同步聊天"""
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.message})

        start = time.time()
        try:
            resp = httpx.post(f"{self.base_url}/api/chat", json={
                "model": request.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens,
                }
            }, timeout=30.0)
            data = resp.json()
            reply = data.get("message", {}).get("content", "")
            usage = {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            }
        except Exception as e:
            reply = f"[模拟回答] 关于 '{request.message[:20]}' 的回答"
            usage = {"prompt_tokens": 0, "completion_tokens": 0}

        latency = time.time() - start
        self.call_count += 1
        self.total_latency += latency

        return ChatResponse(reply=reply, model=request.model,
                           latency=latency, usage=usage)

    def get_stats(self) -> dict:
        avg = self.total_latency / self.call_count if self.call_count else 0
        return {
            "calls": self.call_count,
            "avg_latency_ms": round(avg * 1000),
            "total_latency_s": round(self.total_latency, 2),
        }

client = LLMClient()

# 测试调用
req = ChatRequest("什么是 FastAPI？简要回答。", system_prompt="你是技术助手，回答简洁。")
resp = client.chat(req)
print(f"调用测试:")
print(f"  请求: {req.message}")
print(f"  响应: {resp.reply[:80]}...")
print(f"  延迟: {resp.latency*1000:.0f}ms")
print(f"  用量: {resp.usage}")

# ============================================================================
# 4. 错误处理
# ============================================================================
print("\n--- 4. 错误处理 ---")
print("""
AI 服务的错误处理策略：

```python
from fastapi import HTTPException
from tenacity import retry, stop_after_attempt, wait_exponential

# 1. 输入验证
@app.post("/chat")
async def chat(req: ChatRequest):
    if len(req.message) > 10000:
        raise HTTPException(400, "消息过长，最多10000字符")
    if req.temperature < 0 or req.temperature > 2:
        raise HTTPException(400, "temperature 需在 0-2 之间")

# 2. LLM 调用重试
@retry(stop=stop_after_attempt(3),
       wait=wait_exponential(min=1, max=10))
async def call_llm_with_retry(messages, model):
    return await client.chat.completions.create(
        model=model, messages=messages
    )

# 3. 超时处理
import asyncio
try:
    result = await asyncio.wait_for(call_llm(...), timeout=30)
except asyncio.TimeoutError:
    raise HTTPException(504, "LLM 响应超时")

# 4. 降级策略
try:
    result = await call_llm(model="gpt-4o")
except:
    result = await call_llm(model="gpt-4o-mini")  # 降级到便宜模型

# 5. 全局异常处理
@app.exception_handler(Exception)
async def handle_exception(request, exc):
    logger.error(f"未处理异常: {exc}")
    return JSONResponse(status_code=500,
        content={"error": "服务暂时不可用"})
```
""")

# 模拟错误处理
class AIServiceError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

def validate_request(req: ChatRequest):
    errors = []
    if not req.message.strip():
        errors.append("消息不能为空")
    if len(req.message) > 10000:
        errors.append("消息过长")
    if req.temperature < 0 or req.temperature > 2:
        errors.append("temperature 范围 0-2")
    return errors

# 测试验证
for msg, temp in [("", 0.7), ("正常消息", 0.7), ("x"*10001, 0.7), ("测试", 3.0)]:
    errs = validate_request(ChatRequest(msg, temperature=temp))
    status = "✓" if not errs else f"✗ {errs}"
    print(f"  msg='{msg[:10]}...' temp={temp}: {status}")

# ============================================================================
# 5. 完整 API 模拟
# ============================================================================
print("\n--- 5. 完整 API ---")

class AIService:
    """AI 服务（模拟 FastAPI 应用）"""

    def __init__(self):
        self.client = LLMClient()
        self.models = [
            {"name": "qwen2.5:7b", "provider": "ollama", "status": "available"},
            {"name": "gpt-4o-mini", "provider": "openai", "status": "available"},
        ]

    def post_chat(self, message: str, **kwargs) -> dict:
        """POST /chat"""
        req = ChatRequest(message, **kwargs)
        errors = validate_request(req)
        if errors:
            return {"error": errors, "status": 400}
        resp = self.client.chat(req)
        return {"status": 200, **resp.to_dict()}

    def get_models(self) -> dict:
        """GET /models"""
        return {"models": self.models}

    def get_health(self) -> dict:
        """GET /health"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "stats": self.client.get_stats(),
        }

service = AIService()

# 模拟 API 调用
print("POST /chat:")
result = service.post_chat("Python 有什么特点？", system_prompt="简要回答")
print(f"  status: {result['status']}")
print(f"  reply: {result.get('reply', '')[:60]}...")
print(f"  latency: {result.get('latency_ms', 0)}ms")

print(f"\nGET /models: {service.get_models()}")
print(f"GET /health: {service.get_health()}")

# ============================================================================
# 6. API 文档
# ============================================================================
print("\n--- 6. API 文档 ---")
print("""
FastAPI 自动生成 OpenAPI 文档：

  http://localhost:8000/docs     → Swagger UI（交互式）
  http://localhost:8000/redoc    → ReDoc（只读）
  http://localhost:8000/openapi.json → OpenAPI JSON

文档增强：
```python
@app.post("/chat",
    summary="AI 聊天",
    description="发送消息给 AI，获取回复",
    tags=["聊天"],
    response_model=ChatResponse,
)
async def chat(
    req: ChatRequest = Body(..., examples=[{
        "message": "你好",
        "model": "qwen2.5:7b",
        "temperature": 0.7,
    }])
):
    ...
```

客户端调用：
```python
import httpx
resp = httpx.post("http://localhost:8000/chat", json={
    "message": "你好",
    "temperature": 0.7,
})
print(resp.json()["reply"])
```
""")

print("=" * 60)
print("[完成] 第1课完成！你已经学会了：")
print("  [v] FastAPI 为什么适合 AI 服务")
print("  [v] AI 聊天 API 端点设计")
print("  [v] 请求/响应 Pydantic 模型")
print("  [v] LLM 调用封装（同步+统计）")
print("  [v] 错误处理（验证/重试/降级）")
print("  [v] API 文档自动生成")
print("=" * 60)
print("\n下一课：02_streaming_sse.py - 流式输出")
