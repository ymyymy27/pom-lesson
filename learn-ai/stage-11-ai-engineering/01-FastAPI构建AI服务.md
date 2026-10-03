# FastAPI 构建 AI 服务

## 学习目标

- 用 FastAPI 构建生产级 AI API 服务
- 掌握流式输出（SSE）、异步处理、并发控制
- 实现完整的 AI 后端架构

## 1. FastAPI 基础回顾

```bash
pip install fastapi uvicorn python-multipart
```

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="AI Service", version="1.0")

class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000

class ChatResponse(BaseModel):
    reply: str
    model: str
    usage: dict

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    from openai import AsyncOpenAI
    client = AsyncOpenAI()
    
    response = await client.chat.completions.create(
        model=req.model,
        messages=[{"role": "user", "content": req.message}],
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    
    return ChatResponse(
        reply=response.choices[0].message.content,
        model=req.model,
        usage={
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 2. 流式输出（SSE）

```python
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI

client = AsyncOpenAI()

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def generate():
        stream = await client.chat.completions.create(
            model=req.model,
            messages=[{"role": "user", "content": req.message}],
            temperature=req.temperature,
            stream=True,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield f"data: {content}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
```

### 前端消费 SSE

```javascript
// JavaScript 前端
const response = await fetch('/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: '你好' }),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const text = decoder.decode(value);
    const lines = text.split('\n');
    for (const line of lines) {
        if (line.startsWith('data: ') && line !== 'data: [DONE]') {
            const content = line.slice(6);
            document.getElementById('output').textContent += content;
        }
    }
}
```

## 3. 会话管理

```python
from fastapi import Depends
from typing import Optional
import uuid

# 内存会话存储（生产环境用 Redis）
sessions: dict[str, list] = {}

class SessionChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    system_prompt: str = "你是一个有帮助的 AI 助手。"

@app.post("/chat/session")
async def session_chat(req: SessionChatRequest):
    # 创建或获取会话
    if not req.session_id:
        req.session_id = str(uuid.uuid4())
        sessions[req.session_id] = [
            {"role": "system", "content": req.system_prompt}
        ]

    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # 添加用户消息
    sessions[req.session_id].append({"role": "user", "content": req.message})

    # 调用 LLM
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=sessions[req.session_id],
    )

    reply = response.choices[0].message.content
    sessions[req.session_id].append({"role": "assistant", "content": reply})

    return {
        "session_id": req.session_id,
        "reply": reply,
        "history_length": len(sessions[req.session_id]),
    }
```

## 4. 并发与限流

```python
import asyncio
from fastapi import Request
from collections import defaultdict
import time

# 信号量控制并发
semaphore = asyncio.Semaphore(10)  # 最多 10 个并发 LLM 调用

@app.post("/chat/controlled")
async def controlled_chat(req: ChatRequest):
    async with semaphore:
        response = await client.chat.completions.create(
            model=req.model,
            messages=[{"role": "user", "content": req.message}],
        )
        return {"reply": response.choices[0].message.content}

# 简单限流
rate_limits: dict[str, list] = defaultdict(list)

async def rate_limit(request: Request, limit: int = 10, window: int = 60):
    """每个 IP 每分钟最多 limit 次请求"""
    ip = request.client.host
    now = time.time()
    rate_limits[ip] = [t for t in rate_limits[ip] if now - t < window]

    if len(rate_limits[ip]) >= limit:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    rate_limits[ip].append(now)
```

## 5. 错误处理与重试

```python
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def call_llm_with_retry(messages: list, model: str = "gpt-4o-mini"):
    """带重试的 LLM 调用"""
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM 调用失败: {e}")
        raise

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return {"error": "服务器内部错误", "detail": str(exc)}
```

## 6. 缓存

```python
from functools import lru_cache
import hashlib
import json

# 简单内存缓存
response_cache: dict[str, str] = {}

def cache_key(messages: list, model: str) -> str:
    content = json.dumps(messages, sort_keys=True) + model
    return hashlib.md5(content.encode()).hexdigest()

async def cached_llm_call(messages: list, model: str = "gpt-4o-mini") -> str:
    key = cache_key(messages, model)
    if key in response_cache:
        return response_cache[key]

    response = await client.chat.completions.create(
        model=model, messages=messages
    )
    result = response.choices[0].message.content
    response_cache[key] = result
    return result

# 生产环境推荐用 Redis 缓存
# import redis
# cache = redis.Redis()
# cache.setex(key, 3600, result)  # 缓存 1 小时
```

## 练习

1. 用 FastAPI 构建一个支持流式输出的聊天 API
2. 实现会话管理，支持多轮对话
3. 添加并发控制和限流中间件
4. 实现 LLM 响应缓存，减少重复调用

## 下一节

→ [02-AI应用架构模式](02-AI应用架构模式.md)
