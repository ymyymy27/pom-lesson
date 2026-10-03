> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第6课：AI 团队 Docker 协作开发实战

## 1. 问题场景

### AI 团队的典型痛点

```
团队A（视觉组）：torch + torchvision + opencv + ultralytics
团队B（语音组）：torch + torchaudio + whisper + edge-tts
团队C（NLP组）：  transformers + langchain + faiss-gpu
团队D（编排组）：langchain + langgraph + fastapi

问题：
1. 各组依赖互相冲突（torch 版本不同、CUDA 版本不同）
2. 本地开发只装自己的依赖，跑不了别人的模块
3. 集成测试要装全部依赖 → 冲突爆炸
4. 新人入职配环境要一天
```

### 解决思路

```
核心原则：模块间通过 HTTP API 通信，而不是 import

每个模块 = 一个独立的 Docker 容器 = 一个独立的 FastAPI 服务

┌────────────────────────────────────────────────┐
│              docker compose up                  │
│                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ 视觉服务  │  │ 语音服务  │  │ NLP服务  │     │
│  │ :8001    │  │ :8002    │  │ :8003    │     │
│  │ torch    │  │ whisper  │  │ langchain│     │
│  │ opencv   │  │ torchaudio│ │ faiss    │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │              │              │           │
│       └──────────┬───┘──────────────┘           │
│                  │                              │
│           ┌──────┴──────┐                       │
│           │  编排服务    │                       │
│           │  :8000      │                       │
│           │  Agent/API  │                       │
│           └─────────────┘                       │
└────────────────────────────────────────────────┘

每个人只需要 docker compose up 就能跑完整流程！
```

---

## 2. 项目结构设计

### 推荐目录结构

```
ai-platform/
├── services/
│   ├── vision/                 # 视觉服务（团队A负责）
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── models/             # 模型文件（gitignore）
│   │
│   ├── voice/                  # 语音服务（团队B负责）
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── models/
│   │
│   ├── nlp/                    # NLP服务（团队C负责）
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── models/
│   │
│   └── orchestrator/           # 编排服务（团队D负责）
│       ├── app.py
│       ├── requirements.txt
│       └── Dockerfile
│
├── shared/
│   ├── schemas.py              # 统一接口定义（Pydantic 模型）
│   └── client.py               # 服务调用客户端
│
├── docker-compose.yml          # 完整编排
├── docker-compose.dev.yml      # 开发环境覆盖
├── .env                        # 环境变量
├── .env.example
├── .gitignore
├── Makefile                    # 快捷命令
└── README.md
```

### 为什么这样设计？

| 设计决策 | 原因 |
|---------|------|
| 每个服务独立目录 | 各团队独立开发，互不干扰 |
| 各自有 `requirements.txt` | 依赖完全隔离，不会冲突 |
| 各自有 `Dockerfile` | 可以用不同基础镜像（GPU/CPU） |
| `shared/schemas.py` | 统一接口契约，保证兼容性 |
| `docker-compose.yml` | 一键拉起所有服务 |

---

## 3. 统一接口定义

### shared/schemas.py

所有团队共同维护这个文件，定义 API 的输入输出格式：

```python
# shared/schemas.py
from pydantic import BaseModel
from typing import Optional

# ==================== 通用响应 ====================
class HealthResponse(BaseModel):
    service: str
    status: str  # "healthy" | "unhealthy"
    version: str

# ==================== 视觉服务 ====================
class VisionRequest(BaseModel):
    image_url: str                  # 图片URL或Base64
    task: str = "detect"            # detect | classify | ocr
    options: dict = {}

class VisionResult(BaseModel):
    task: str
    objects: list[dict] = []        # [{"label": "cat", "confidence": 0.95, "bbox": [...]}]
    text: str = ""                  # OCR 结果
    labels: list[str] = []          # 分类标签

# ==================== 语音服务 ====================
class VoiceRequest(BaseModel):
    audio_url: str = ""             # 音频URL（ASR用）
    text: str = ""                  # 文本（TTS用）
    task: str = "asr"               # asr | tts
    language: str = "zh"

class VoiceResult(BaseModel):
    task: str
    text: str = ""                  # ASR 转写结果
    audio_url: str = ""             # TTS 生成的音频URL
    duration: float = 0.0

# ==================== NLP 服务 ====================
class NLPRequest(BaseModel):
    query: str
    task: str = "chat"              # chat | embedding | rag
    context: list[str] = []         # RAG 上下文
    history: list[dict] = []        # 对话历史

class NLPResult(BaseModel):
    task: str
    answer: str = ""
    embedding: list[float] = []
    sources: list[str] = []         # RAG 来源
```

### 关键原则

```
1. 所有服务必须实现 GET /health 接口
2. 所有请求/响应必须用 Pydantic 模型（有类型、有校验）
3. 接口变更必须同步更新 schemas.py 并通知所有团队
4. 用版本号管理接口变更（v1, v2）
```

---

## 4. 各模块服务实现

### 4.1 视觉服务（services/vision/）

**services/vision/requirements.txt**
```
fastapi==0.115.0
uvicorn==0.30.0
python-multipart==0.0.9
Pillow==10.4.0
# torch==2.4.0          # GPU 版在 Dockerfile 中安装
# ultralytics==8.2.0    # YOLO
```

**services/vision/Dockerfile**
```dockerfile
# GPU 版本（团队A用）
FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime

WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**services/vision/app.py**
```python
from fastapi import FastAPI
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

app = FastAPI(title="Vision Service", version="1.0.0")

SERVICE_NAME = "vision"
SERVICE_VERSION = "1.0.0"

@app.get("/health")
def health():
    return {"service": SERVICE_NAME, "status": "healthy", "version": SERVICE_VERSION}

@app.post("/api/v1/vision")
def predict(request: dict):
    """
    视觉处理接口
    实际项目中这里会调用 YOLO / CLIP / OCR 等模型
    """
    task = request.get("task", "detect")
    image_url = request.get("image_url", "")

    # === 这里放真实的模型推理代码 ===
    # from ultralytics import YOLO
    # model = YOLO("yolov8n.pt")
    # results = model(image_url)

    # 示例返回（开发阶段用 mock）
    if task == "detect":
        return {
            "task": "detect",
            "objects": [
                {"label": "person", "confidence": 0.92, "bbox": [100, 50, 300, 400]},
                {"label": "car", "confidence": 0.87, "bbox": [400, 200, 600, 350]},
            ],
            "text": "",
            "labels": [],
        }
    elif task == "ocr":
        return {
            "task": "ocr",
            "objects": [],
            "text": "识别出的文字内容...",
            "labels": [],
        }
    else:
        return {"task": task, "objects": [], "text": "", "labels": ["cat", "outdoor"]}
```

### 4.2 语音服务（services/voice/）

**services/voice/requirements.txt**
```
fastapi==0.115.0
uvicorn==0.30.0
# openai-whisper==20240930
# edge-tts==6.1.12
```

**services/voice/Dockerfile**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# ffmpeg 用于音频处理
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**services/voice/app.py**
```python
from fastapi import FastAPI

app = FastAPI(title="Voice Service", version="1.0.0")

SERVICE_NAME = "voice"
SERVICE_VERSION = "1.0.0"

@app.get("/health")
def health():
    return {"service": SERVICE_NAME, "status": "healthy", "version": SERVICE_VERSION}

@app.post("/api/v1/voice")
def process(request: dict):
    """
    语音处理接口
    实际项目中调用 Whisper / edge-tts 等
    """
    task = request.get("task", "asr")

    if task == "asr":
        # whisper 语音转文字
        return {
            "task": "asr",
            "text": "你好，请帮我查一下今天的天气",
            "audio_url": "",
            "duration": 3.5,
        }
    elif task == "tts":
        # edge-tts 文字转语音
        return {
            "task": "tts",
            "text": request.get("text", ""),
            "audio_url": "http://voice:8000/static/output.mp3",
            "duration": 2.1,
        }
    else:
        return {"task": task, "text": "", "audio_url": "", "duration": 0.0}
```

### 4.3 NLP 服务（services/nlp/）

**services/nlp/requirements.txt**
```
fastapi==0.115.0
uvicorn==0.30.0
# langchain==0.3.0
# transformers==4.44.0
# faiss-cpu==1.8.0
```

**services/nlp/Dockerfile**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**services/nlp/app.py**
```python
from fastapi import FastAPI

app = FastAPI(title="NLP Service", version="1.0.0")

SERVICE_NAME = "nlp"
SERVICE_VERSION = "1.0.0"

@app.get("/health")
def health():
    return {"service": SERVICE_NAME, "status": "healthy", "version": SERVICE_VERSION}

@app.post("/api/v1/nlp")
def process(request: dict):
    """
    NLP 处理接口
    实际项目中调用 LLM / RAG / Embedding 等
    """
    task = request.get("task", "chat")
    query = request.get("query", "")

    if task == "chat":
        return {
            "task": "chat",
            "answer": f"这是对'{query}'的AI回复（实际接入LLM）",
            "embedding": [],
            "sources": [],
        }
    elif task == "embedding":
        return {
            "task": "embedding",
            "answer": "",
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],  # mock 向量
            "sources": [],
        }
    elif task == "rag":
        return {
            "task": "rag",
            "answer": f"根据知识库回答：{query}...",
            "embedding": [],
            "sources": ["doc1.pdf", "doc2.pdf"],
        }
    else:
        return {"task": task, "answer": "", "embedding": [], "sources": []}
```

### 4.4 编排服务（services/orchestrator/）

**services/orchestrator/requirements.txt**
```
fastapi==0.115.0
uvicorn==0.30.0
httpx==0.27.0
```

**services/orchestrator/Dockerfile**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**services/orchestrator/app.py**
```python
"""
编排服务：调用各个 AI 模块服务，组合成完整流程
这是对外的统一入口，不直接 import 任何 AI 模型依赖
"""
from fastapi import FastAPI, HTTPException
import httpx
import os

app = FastAPI(title="AI Orchestrator", version="1.0.0")

# 服务地址（Docker Compose 中用服务名访问）
VISION_URL = os.getenv("VISION_URL", "http://vision:8000")
VOICE_URL = os.getenv("VOICE_URL", "http://voice:8000")
NLP_URL = os.getenv("NLP_URL", "http://nlp:8000")

# HTTP 客户端
client = httpx.AsyncClient(timeout=30.0)


# ==================== 健康检查 ====================
@app.get("/health")
async def health():
    """检查所有下游服务的健康状态"""
    services = {
        "vision": VISION_URL,
        "voice": VOICE_URL,
        "nlp": NLP_URL,
    }
    status = {}
    for name, url in services.items():
        try:
            resp = await client.get(f"{url}/health")
            status[name] = resp.json()
        except Exception as e:
            status[name] = {"service": name, "status": "unhealthy", "error": str(e)}

    all_healthy = all(s.get("status") == "healthy" for s in status.values())
    return {
        "service": "orchestrator",
        "status": "healthy" if all_healthy else "degraded",
        "version": "1.0.0",
        "downstream": status,
    }


# ==================== 调用单个服务 ====================
async def call_service(base_url: str, endpoint: str, data: dict) -> dict:
    """统一的服务调用方法，带错误处理"""
    try:
        resp = await client.post(f"{base_url}{endpoint}", json=data)
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"服务不可用: {base_url}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 业务接口 ====================
@app.post("/api/v1/chat")
async def chat(request: dict):
    """纯文本对话 → 调用 NLP 服务"""
    result = await call_service(NLP_URL, "/api/v1/nlp", {
        "query": request.get("query", ""),
        "task": "chat",
    })
    return {"type": "chat", "result": result}


@app.post("/api/v1/voice-chat")
async def voice_chat(request: dict):
    """
    语音对话完整流程：
    1. 语音 → 文字（ASR）
    2. 文字 → AI回复（NLP）
    3. AI回复 → 语音（TTS）
    """
    # Step 1: ASR
    asr_result = await call_service(VOICE_URL, "/api/v1/voice", {
        "audio_url": request.get("audio_url", ""),
        "task": "asr",
    })
    user_text = asr_result.get("text", "")

    # Step 2: NLP
    nlp_result = await call_service(NLP_URL, "/api/v1/nlp", {
        "query": user_text,
        "task": "chat",
    })
    ai_reply = nlp_result.get("answer", "")

    # Step 3: TTS
    tts_result = await call_service(VOICE_URL, "/api/v1/voice", {
        "text": ai_reply,
        "task": "tts",
    })

    return {
        "type": "voice_chat",
        "pipeline": {
            "asr": {"input_audio": request.get("audio_url"), "output_text": user_text},
            "nlp": {"input_text": user_text, "output_text": ai_reply},
            "tts": {"input_text": ai_reply, "output_audio": tts_result.get("audio_url")},
        },
    }


@app.post("/api/v1/image-analyze")
async def image_analyze(request: dict):
    """
    图片分析流程：
    1. 图片 → 目标检测（Vision）
    2. 检测结果 → 自然语言描述（NLP）
    """
    # Step 1: Vision
    vision_result = await call_service(VISION_URL, "/api/v1/vision", {
        "image_url": request.get("image_url", ""),
        "task": request.get("task", "detect"),
    })

    # Step 2: NLP 生成描述
    objects = vision_result.get("objects", [])
    description_query = f"请用自然语言描述这张图片中的内容：{objects}"
    nlp_result = await call_service(NLP_URL, "/api/v1/nlp", {
        "query": description_query,
        "task": "chat",
    })

    return {
        "type": "image_analyze",
        "vision": vision_result,
        "description": nlp_result.get("answer", ""),
    }
```

---

## 5. Docker Compose 编排

### docker-compose.yml（核心文件）

```yaml
services:
  # ==================== AI 模型服务 ====================
  vision:
    build: ./services/vision
    ports:
      - "8001:8000"
    environment:
      - MODEL_PATH=/app/models
    volumes:
      - vision_models:/app/models        # 模型文件持久化
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s                  # AI模型加载需要时间
    restart: unless-stopped
    # GPU 支持（有GPU的机器取消注释）
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  voice:
    build: ./services/voice
    ports:
      - "8002:8000"
    volumes:
      - voice_models:/app/models
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 20s
    restart: unless-stopped

  nlp:
    build: ./services/nlp
    ports:
      - "8003:8000"
    environment:
      - OLLAMA_URL=http://host.docker.internal:11434   # 访问宿主机的 Ollama
    volumes:
      - nlp_models:/app/models
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 20s
    restart: unless-stopped

  # ==================== 编排层 ====================
  orchestrator:
    build: ./services/orchestrator
    ports:
      - "8000:8000"
    environment:
      - VISION_URL=http://vision:8000
      - VOICE_URL=http://voice:8000
      - NLP_URL=http://nlp:8000
    depends_on:
      vision:
        condition: service_healthy
      voice:
        condition: service_healthy
      nlp:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

volumes:
  vision_models:
  voice_models:
  nlp_models:
```

### docker-compose.dev.yml（开发环境覆盖）

开发时挂载代码目录，实现代码热重载：

```yaml
# docker compose -f docker-compose.yml -f docker-compose.dev.yml up
services:
  vision:
    volumes:
      - ./services/vision:/app         # 挂载代码（热重载）
      - vision_models:/app/models
    command: uvicorn app:app --host 0.0.0.0 --port 8000 --reload

  voice:
    volumes:
      - ./services/voice:/app
      - voice_models:/app/models
    command: uvicorn app:app --host 0.0.0.0 --port 8000 --reload

  nlp:
    volumes:
      - ./services/nlp:/app
      - nlp_models:/app/models
    command: uvicorn app:app --host 0.0.0.0 --port 8000 --reload

  orchestrator:
    volumes:
      - ./services/orchestrator:/app
    command: uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

---

## 6. 开发工作流

### 6.1 日常开发（只跑自己的服务）

```bash
# 团队A（视觉组）：只启动自己的服务
docker compose up vision -d

# 访问自己的 API
curl http://localhost:8001/health
curl -X POST http://localhost:8001/api/v1/vision \
  -H "Content-Type: application/json" \
  -d '{"image_url": "test.jpg", "task": "detect"}'
```

### 6.2 联调测试（拉起所有服务）

```bash
# 一键启动全部服务
docker compose up -d

# 查看所有服务状态
docker compose ps

# 测试编排接口
curl http://localhost:8000/health                    # 查看所有服务健康状态
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "你好"}'

# 测试完整流水线
curl -X POST http://localhost:8000/api/v1/voice-chat \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "test.wav"}'
```

### 6.3 只重启自己改的服务

```bash
# 视觉组改了代码，只重建 vision 服务
docker compose up -d --build vision

# 其他服务不受影响
docker compose ps
```

### 6.4 查看日志排查问题

```bash
# 查看某个服务的日志
docker compose logs -f vision

# 查看所有服务日志
docker compose logs -f

# 查看最近 50 行
docker compose logs --tail 50 orchestrator
```

---

## 7. Makefile 快捷命令

用 Makefile 简化日常操作：

```makefile
# Makefile

.PHONY: up down dev build logs ps test clean

# 生产模式启动
up:
	docker compose up -d

# 开发模式启动（代码热重载）
dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 停止所有服务
down:
	docker compose down

# 重新构建所有镜像
build:
	docker compose build --no-cache

# 只构建某个服务（用法：make build-one SVC=vision）
build-one:
	docker compose build --no-cache $(SVC)

# 只启动某个服务（用法：make run SVC=vision）
run:
	docker compose up -d $(SVC)

# 查看日志
logs:
	docker compose logs -f

# 查看某个服务日志（用法：make log SVC=vision）
log:
	docker compose logs -f $(SVC)

# 查看服务状态
ps:
	docker compose ps

# 运行测试
test:
	curl -s http://localhost:8000/health | python -m json.tool

# 测试所有接口
test-all:
	@echo "=== Health Check ==="
	curl -s http://localhost:8000/health | python -m json.tool
	@echo "\n=== Chat ==="
	curl -s -X POST http://localhost:8000/api/v1/chat \
		-H "Content-Type: application/json" \
		-d '{"query": "hello"}' | python -m json.tool
	@echo "\n=== Voice Chat ==="
	curl -s -X POST http://localhost:8000/api/v1/voice-chat \
		-H "Content-Type: application/json" \
		-d '{"audio_url": "test.wav"}' | python -m json.tool
	@echo "\n=== Image Analyze ==="
	curl -s -X POST http://localhost:8000/api/v1/image-analyze \
		-H "Content-Type: application/json" \
		-d '{"image_url": "test.jpg"}' | python -m json.tool

# 清理所有容器、镜像、卷
clean:
	docker compose down -v --rmi all
	docker system prune -f
```

### 使用方式

```bash
make dev          # 开发模式启动（热重载）
make up           # 生产模式启动
make down         # 停止
make logs         # 查看所有日志
make log SVC=vision   # 只看视觉服务日志
make build-one SVC=nlp  # 只重建 NLP 服务
make test         # 快速健康检查
make test-all     # 测试所有接口
make clean        # 全部清理
```

---

## 8. GPU 支持

### 8.1 安装 NVIDIA Container Toolkit

```bash
# Ubuntu
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# 验证
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### 8.2 Docker Compose GPU 配置

```yaml
services:
  vision:
    build: ./services/vision
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1                  # 用1块GPU
              capabilities: [gpu]

  # 多GPU分配
  nlp:
    build: ./services/nlp
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ["1"]         # 指定第2块GPU
              capabilities: [gpu]
```

### 8.3 GPU 镜像选择

```
# PyTorch 官方镜像（推荐）
pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime    # 小（~5GB）
pytorch/pytorch:2.4.0-cuda12.1-cudnn9-devel       # 大（~8GB，含编译工具）

# NVIDIA 基础镜像
nvidia/cuda:12.1.0-runtime-ubuntu22.04            # 只含 CUDA 运行时
nvidia/cuda:12.1.0-devel-ubuntu22.04              # 含开发工具

# CPU 版（不需要GPU的服务）
python:3.12-slim                                   # ~150MB
```

---

## 9. 进阶技巧

### 9.1 服务发现与负载均衡

Docker Compose 默认创建同一网络，容器之间用服务名访问：

```python
# 在编排服务中，直接用服务名
# "vision" 自动解析为 vision 容器的 IP
requests.get("http://vision:8000/health")
```

### 9.2 模型文件管理

模型文件通常很大，不应放在 Docker 镜像中：

```yaml
services:
  vision:
    volumes:
      # 方式1：宿主机目录挂载（开发推荐）
      - ./models/vision:/app/models

      # 方式2：命名卷（生产推荐）
      - vision_models:/app/models

# 首次需要手动下载模型到 ./models/vision/ 目录
# 或者在容器启动脚本中自动下载
```

**模型下载脚本示例：**
```bash
#!/bin/bash
# scripts/download_models.sh

echo "下载视觉模型..."
mkdir -p models/vision
# wget -O models/vision/yolov8n.pt https://xxx

echo "下载语音模型..."
mkdir -p models/voice
# wget -O models/voice/whisper-base.pt https://xxx

echo "模型下载完成！"
```

### 9.3 访问宿主机的 Ollama

很多团队在宿主机上跑 Ollama，容器内需要访问它：

```yaml
services:
  nlp:
    environment:
      # Docker Desktop (Windows/Mac)
      - OLLAMA_URL=http://host.docker.internal:11434

      # Linux 需要额外配置
    extra_hosts:
      - "host.docker.internal:host-gateway"   # Linux 需要这行
```

```python
# 在 NLP 服务中
import os, httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

async def call_ollama(prompt: str):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{OLLAMA_URL}/api/generate", json={
            "model": "qwen2.5",
            "prompt": prompt,
            "stream": False,
        })
        return resp.json()["response"]
```

### 9.4 Mock 模式（无GPU开发者）

有些开发者没有 GPU，可以用环境变量切换 mock 模式：

```yaml
# docker-compose.dev.yml
services:
  vision:
    environment:
      - MOCK_MODE=true              # 开启 mock
```

```python
# services/vision/app.py
import os

MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

@app.post("/api/v1/vision")
def predict(request: dict):
    if MOCK_MODE:
        # 返回假数据，不需要真实模型
        return {"task": "detect", "objects": [{"label": "mock_cat", "confidence": 0.99}]}

    # 真实模型推理
    model = load_model()
    return model.predict(request)
```

---

## 10. 团队协作规范

### Git 分支策略

```
main                        ← 稳定版本
├── develop                 ← 开发主线
│   ├── feature/vision-yolo   ← 视觉组: 接入YOLO
│   ├── feature/voice-tts     ← 语音组: 接入TTS
│   ├── feature/nlp-rag       ← NLP组: 接入RAG
│   └── feature/orch-pipeline ← 编排组: 新流水线
│
└── release/v1.0            ← 发布版本
```

### .gitignore 模板

```gitignore
# 模型文件（太大不入仓库）
models/
*.pt
*.bin
*.onnx
*.safetensors

# 环境变量
.env
!.env.example

# Python
__pycache__/
*.pyc
.venv/

# Docker
docker-compose.override.yml
```

### 新人入职 README

```markdown
## 快速开始（5分钟跑通）

1. 安装 Docker Desktop
2. git clone 本项目
3. cp .env.example .env
4. make dev
5. 打开 http://localhost:8000/health 验证

不需要安装 Python、PyTorch、或任何 AI 依赖！
```

---

## 11. 动手练习

```bash
# 1. 创建项目目录结构
mkdir -p ai-platform/services/{vision,voice,nlp,orchestrator}
mkdir -p ai-platform/shared

# 2. 按照本课内容，创建各服务的 app.py / requirements.txt / Dockerfile

# 3. 创建 docker-compose.yml

# 4. 启动所有服务
cd ai-platform
docker compose up -d --build

# 5. 测试健康检查
curl http://localhost:8000/health

# 6. 测试业务接口
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "你好"}'

# 7. 只重建某个服务
docker compose up -d --build vision

# 8. 查看日志
docker compose logs -f orchestrator

# 9. 停止并清理
docker compose down -v
```

---

## 12. 小结

| 问题 | Docker 解决方案 |
|------|----------------|
| **依赖冲突** | 每个服务独立容器，各自安装各自的依赖 |
| **环境不一致** | Dockerfile 定义完整环境，所有人一致 |
| **集成测试难** | `docker compose up` 一键拉起全部 |
| **新人配环境慢** | 装好 Docker 就行，不需要装 AI 依赖 |
| **GPU 分配** | Docker GPU 支持，按服务分配显卡 |
| **模块间通信** | HTTP API，用服务名访问（如 `http://vision:8000`） |
| **热重载开发** | 挂载代码目录 + `--reload` |
| **无GPU开发** | Mock 模式，返回假数据 |

### 架构对比

```
❌ 以前：所有模块在一个 Python 项目中
   → 依赖冲突、环境配置难、一个模块挂全挂

✅ 现在：每个模块一个 Docker 服务
   → 依赖隔离、独立部署、一键启动、故障隔离
```

---

**learn-docker 课程完成！** 🎉

回到总目录：[learn-tools README](../../../05-公共资源/课程说明.md)
