import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：流式输出与 SSE
==============================================================================

流式输出 = LLM 一边生成一边发送，用户不需要等完整回复
SSE = Server-Sent Events，HTTP 流式推送协议

本课内容：
1. 为什么需要流式输出
2. SSE 协议原理
3. Ollama 流式 API
4. FastAPI 流式端点
5. 前端消费 SSE
6. 流式错误处理
==============================================================================
"""

import json
import time
import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"

print("=" * 60)
print("第2课：流式输出与 SSE")
print("=" * 60)

# ============================================================================
# 1. 为什么需要流式
# ============================================================================
print("\n--- 1. 为什么流式 ---")
print("""
非流式（同步）：
  用户发送 → 等待3-10秒 → 一次性返回全部
  ❌ 用户等待时间长，体验差
  ❌ 大段回复可能超时

流式（SSE）：
  用户发送 → 0.5秒开始接收 → 逐字/逐句显示
  ✅ 首字延迟低（<1秒）
  ✅ 用户边看边等，体验好
  ✅ 像打字机一样逐字显示

延迟对比：
  同步: [======等待5秒======] → 全部显示
  流式: [=0.5秒=] → 逐字显示...持续5秒

适用场景：
  ✅ 聊天对话（ChatGPT 风格）
  ✅ 长文本生成（文章/代码）
  ✅ RAG 问答
  ❌ 需要完整结果才能处理的场景（JSON解析）
""")

# ============================================================================
# 2. SSE 协议
# ============================================================================
print("\n--- 2. SSE 协议 ---")
print("""
SSE (Server-Sent Events) 是 HTTP 标准协议：

  请求：
    POST /chat/stream
    Content-Type: application/json
    {"message": "你好"}

  响应：
    HTTP/1.1 200 OK
    Content-Type: text/event-stream
    Cache-Control: no-cache
    Connection: keep-alive

    data: 你
    
    data: 好
    
    data: ，
    
    data: 我是
    
    data: AI助手
    
    data: [DONE]

格式规则：
  每条消息以 "data: " 开头
  消息之间用空行分隔
  "data: [DONE]" 表示结束
  可选 "event:" 字段指定事件类型
  可选 "id:" 字段用于断线重连

SSE vs WebSocket：
  SSE:       单向（服务器→客户端），HTTP协议，简单
  WebSocket: 双向，独立协议，复杂但功能更多
  → AI 聊天用 SSE 足够！
""")

# ============================================================================
# 3. Ollama 流式 API
# ============================================================================
print("\n--- 3. Ollama 流式 ---")

def stream_chat(message: str, system: str = "") -> None:
    """Ollama 流式聊天演示"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": message})

    try:
        with httpx.stream("POST", f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL,
            "messages": messages,
            "stream": True,
            "options": {"num_predict": 100}
        }, timeout=30.0) as response:
            print(f"  流式输出: ", end="")
            token_count = 0
            first_token_time = None
            start = time.time()

            for line in response.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                if content:
                    if first_token_time is None:
                        first_token_time = time.time()
                    print(content, end="", flush=True)
                    token_count += 1
                if data.get("done"):
                    break

            elapsed = time.time() - start
            ttft = (first_token_time - start) if first_token_time else 0
            print(f"\n  统计: {token_count}个token, "
                  f"首token {ttft*1000:.0f}ms, 总耗时 {elapsed*1000:.0f}ms")
            return

    except Exception as e:
        print(f"  [模拟流式] 这是 一个 流式 输出 的 模拟 回答。")
        print(f"  （Ollama 不可用: {type(e).__name__}）")

stream_chat("用一句话介绍 Python", "简洁回答")

# ============================================================================
# 4. FastAPI 流式端点
# ============================================================================
print("\n\n--- 4. FastAPI 流式 ---")
print("""
FastAPI 流式端点实现：

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx, json

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    model: str = "qwen2.5:7b"

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def generate():
        async with httpx.AsyncClient() as client:
            async with client.stream("POST",
                "http://localhost:11434/api/chat",
                json={
                    "model": req.model,
                    "messages": [{"role": "user", "content": req.message}],
                    "stream": True,
                }
            ) as response:
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield f"data: {json.dumps({'content': content})}\\n\\n"
                    if data.get("done"):
                        yield "data: [DONE]\\n\\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )
```

OpenAI 兼容格式：
```python
@app.post("/v1/chat/completions")
async def openai_compatible(req: ChatRequest):
    async def generate():
        # ... 调用 LLM 获取流式响应 ...
        for token in tokens:
            chunk = {
                "id": "chatcmpl-xxx",
                "object": "chat.completion.chunk",
                "choices": [{"delta": {"content": token}, "index": 0}]
            }
            yield f"data: {json.dumps(chunk)}\\n\\n"
        yield "data: [DONE]\\n\\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```
""")

# ============================================================================
# 5. 前端消费 SSE
# ============================================================================
print("\n--- 5. 前端消费 ---")
print("""
JavaScript 前端消费 SSE：

```javascript
// 方式1: fetch + ReadableStream（推荐）
async function streamChat(message) {
    const response = await fetch('/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\\n');
        buffer = lines.pop();  // 未完成的行放回 buffer

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') return;
                const parsed = JSON.parse(data);
                document.getElementById('output').textContent += parsed.content;
            }
        }
    }
}

// 方式2: EventSource（仅支持 GET）
const source = new EventSource('/events');
source.onmessage = (event) => {
    console.log(event.data);
};
```

Python 客户端：
```python
import httpx

with httpx.stream("POST", "http://localhost:8000/chat/stream",
                   json={"message": "你好"}) as resp:
    for line in resp.iter_lines():
        if line.startswith("data: ") and line != "data: [DONE]":
            data = json.loads(line[6:])
            print(data["content"], end="", flush=True)
```
""")

# ============================================================================
# 6. 流式错误处理
# ============================================================================
print("\n--- 6. 错误处理 ---")
print("""
流式场景的错误处理：

1. 连接中断
```python
async def generate():
    try:
        async for token in stream_llm():
            yield f"data: {token}\\n\\n"
    except Exception as e:
        # 发送错误事件
        yield f"data: {json.dumps({'error': str(e)})}\\n\\n"
    finally:
        yield "data: [DONE]\\n\\n"
```

2. 超时处理
```python
import asyncio

async def generate_with_timeout():
    try:
        async with asyncio.timeout(30):  # 30秒超时
            async for token in stream_llm():
                yield f"data: {token}\\n\\n"
    except asyncio.TimeoutError:
        yield 'data: {"error": "生成超时"}\\n\\n'
```

3. 客户端断开检测
```python
from fastapi import Request

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request):
    async def generate():
        async for token in stream_llm():
            if await request.is_disconnected():
                break  # 客户端已断开，停止生成
            yield f"data: {token}\\n\\n"
    return StreamingResponse(generate(), ...)
```

4. 心跳保活
```python
async def generate():
    last_data = time.time()
    async for token in stream_llm():
        yield f"data: {token}\\n\\n"
        last_data = time.time()
    # 如果长时间无数据，发送心跳
    if time.time() - last_data > 15:
        yield ": heartbeat\\n\\n"
```
""")

# 流式 vs 同步性能对比
print("流式 vs 同步性能对比:")

def sync_chat(message: str) -> tuple:
    start = time.time()
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL,
            "messages": [{"role": "user", "content": message}],
            "stream": False,
            "options": {"num_predict": 50}
        }, timeout=30.0)
        text = resp.json().get("message", {}).get("content", "")
    except:
        text = "[模拟回答]"
        time.sleep(0.5)
    return text, time.time() - start

def stream_chat_timed(message: str) -> tuple:
    start = time.time()
    first_token = None
    text = ""
    try:
        with httpx.stream("POST", f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL,
            "messages": [{"role": "user", "content": message}],
            "stream": True,
            "options": {"num_predict": 50}
        }, timeout=30.0) as response:
            for line in response.iter_lines():
                if not line: continue
                data = json.loads(line)
                c = data.get("message", {}).get("content", "")
                if c and first_token is None:
                    first_token = time.time() - start
                text += c
                if data.get("done"): break
    except:
        text = "[模拟回答]"
        first_token = 0.1
    return text, time.time() - start, first_token or 0

msg = "一句话介绍AI"
sync_text, sync_time = sync_chat(msg)
stream_text, stream_time, ttft = stream_chat_timed(msg)

print(f"  同步: 总耗时 {sync_time*1000:.0f}ms")
print(f"  流式: 首token {ttft*1000:.0f}ms, 总耗时 {stream_time*1000:.0f}ms")
print(f"  → 流式首token比同步快 {max(0, (sync_time - ttft)/sync_time*100):.0f}%")

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] 流式输出的价值（首字延迟低）")
print("  [v] SSE 协议格式")
print("  [v] Ollama 流式 API 调用")
print("  [v] FastAPI StreamingResponse")
print("  [v] JavaScript/Python 客户端消费")
print("  [v] 流式错误处理（超时/断开/心跳）")
print("=" * 60)
print("\n下一课：03_session_and_cache.py - 会话与缓存")
