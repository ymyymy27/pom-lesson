# Docker 部署 AI 服务

## 学习目标

- 用 Docker 容器化 AI 应用
- 掌握 GPU 容器配置
- 实现多服务编排（模型服务 + API + 向量数据库）

## 1. AI 服务 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码
COPY . .

# 环境变量
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```txt
# requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
openai==1.50.0
langchain==0.3.0
langchain-openai==0.2.0
langchain-chroma==0.1.0
chromadb==0.5.0
python-multipart==0.0.9
```

## 2. Docker Compose 多服务编排

```yaml
# docker-compose.yml
version: "3.8"

services:
  # AI API 服务
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./chroma_data:/app/chroma_data
      - ./docs:/app/docs
    depends_on:
      - redis
    restart: unless-stopped

  # Redis（缓存 + 会话存储）
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Ollama（本地模型服务）
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    # GPU 支持（需要 nvidia-docker）
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - api

volumes:
  redis_data:
  ollama_data:
```

```nginx
# nginx.conf
server {
    listen 80;
    
    location /api/ {
        proxy_pass http://api:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # SSE 流式输出支持
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

## 3. 构建与运行

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看日志
docker-compose logs -f api

# 下载 Ollama 模型
docker exec -it ollama ollama pull qwen2.5:7b

# 健康检查
curl http://localhost/api/health
curl http://localhost:11434/api/tags
```

## 4. GPU Docker 配置

```bash
# 安装 NVIDIA Container Toolkit
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

# 运行 GPU 容器
docker run --gpus all nvidia/cuda:12.0-base nvidia-smi

# Ollama GPU 模式
docker run -d --gpus all -p 11434:11434 \
    -v ollama:/root/.ollama \
    ollama/ollama
```

## 5. 环境配置

```bash
# .env
OPENAI_API_KEY=sk-xxx
DEEPSEEK_API_KEY=xxx
OLLAMA_BASE_URL=http://ollama:11434
REDIS_URL=redis://redis:6379/0
CHROMA_PERSIST_DIR=/app/chroma_data
LOG_LEVEL=INFO
```

## 6. 多阶段构建（优化镜像大小）

```dockerfile
# 构建阶段
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# 运行阶段
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 练习

1. 将你的 RAG 服务容器化，编写 Dockerfile 和 docker-compose.yml
2. 配置 Nginx 反向代理，支持流式输出
3. 集成 Ollama 容器，实现本地模型服务
4. 优化 Docker 镜像大小（多阶段构建）

## 下一节

→ [02-模型服务与推理优化](02-模型服务与推理优化.md)
