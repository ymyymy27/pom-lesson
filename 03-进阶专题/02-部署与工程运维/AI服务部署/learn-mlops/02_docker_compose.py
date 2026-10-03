import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：Docker Compose 多服务编排
==============================================================================

AI 服务通常包含多个组件：API、模型、数据库、缓存、代理
Docker Compose 用一个 YAML 文件管理所有服务。

本课内容：
1. Docker Compose 概述
2. AI 服务编排
3. 网络与服务发现
4. 数据持久化
5. Nginx 反向代理
6. 环境配置管理
==============================================================================
"""

import json

print("=" * 60)
print("第2课：Docker Compose 多服务编排")
print("=" * 60)

# ============================================================================
# 1. 概述
# ============================================================================
print("\n--- 1. 概述 ---")
print("""
Docker Compose = 用 YAML 定义和管理多容器应用

单个 docker run 命令：
  docker run -p 8000:8000 -e KEY=val -v ./data:/data myapp

Docker Compose（声明式）：
```yaml
services:
  myapp:
    build: .
    ports: ["8000:8000"]
    environment: {KEY: val}
    volumes: ["./data:/data"]
```

命令：
  docker-compose up -d          启动所有服务（后台）
  docker-compose down           停止并删除
  docker-compose logs -f api    查看日志
  docker-compose ps             查看状态
  docker-compose restart api    重启某个服务
  docker-compose up -d --build  重新构建并启动
""")

# ============================================================================
# 2. AI 服务编排
# ============================================================================
print("\n--- 2. AI 编排 ---")

compose_yaml = """
version: "3.8"

services:
  # ========== API 服务 ==========
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - REDIS_URL=redis://redis:6379/0
      - CHROMA_HOST=chromadb
    volumes:
      - ./logs:/app/logs
    depends_on:
      - redis
      - ollama
      - chromadb
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ========== 模型服务 ==========
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    # GPU 支持：取消注释
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  # ========== 向量数据库 ==========
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8500:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - ANONYMIZED_TELEMETRY=FALSE

  # ========== 缓存 ==========
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

  # ========== 反向代理 ==========
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - api

volumes:
  ollama_data:
  chroma_data:
  redis_data:
""".strip()

print("docker-compose.yml:")
for i, line in enumerate(compose_yaml.split("\n"), 1):
    if i <= 30:
        print(f"  {i:>2} | {line}")
print(f"  ... (共{len(compose_yaml.split(chr(10)))}行)")

# ============================================================================
# 3. 网络与服务发现
# ============================================================================
print("\n--- 3. 网络 ---")
print("""
Docker Compose 自动创建网络，服务名 = 主机名：

  API 容器中访问 Ollama:
    http://ollama:11434/api/chat     ✓（服务名自动解析）
    http://localhost:11434/api/chat   ✗（localhost是容器自己）

  API 容器中访问 Redis:
    redis://redis:6379/0             ✓

  API 容器中访问 ChromaDB:
    http://chromadb:8000             ✓

网络配置：
```yaml
services:
  api:
    networks:
      - frontend    # 对外网络
      - backend     # 内部网络

  ollama:
    networks:
      - backend     # 只在内部网络（更安全）

networks:
  frontend:
  backend:
    internal: true  # 不暴露到宿主机
```
""")

# ============================================================================
# 4. 数据持久化
# ============================================================================
print("\n--- 4. 持久化 ---")
print("""
容器删除后数据会丢失！需要 Volume 持久化：

三种挂载方式：
┌──────────────┬──────────────────────────────────────────┐
│  命名卷      │  volumes:                                │
│  (推荐)      │    - ollama_data:/root/.ollama           │
│              │  由 Docker 管理，跨平台                  │
├──────────────┼──────────────────────────────────────────┤
│  绑定挂载    │  volumes:                                │
│              │    - ./data:/app/data                    │
│              │  直接映射宿主机目录                      │
├──────────────┼──────────────────────────────────────────┤
│  tmpfs       │  tmpfs:                                  │
│              │    - /app/tmp                            │
│              │  内存临时存储，容器停止即丢失            │
└──────────────┴──────────────────────────────────────────┘

AI 服务需要持久化的数据：
  ✅ 模型文件（ollama_data）   → 命名卷
  ✅ 向量数据库（chroma_data） → 命名卷
  ✅ 缓存数据（redis_data）    → 命名卷
  ✅ 日志文件                  → 绑定挂载
  ✅ 上传文档                  → 绑定挂载
  ❌ 临时文件                  → tmpfs

备份：
```bash
# 导出卷数据
docker run --rm -v chroma_data:/data -v $(pwd):/backup \\
    alpine tar czf /backup/chroma_backup.tar.gz /data

# 恢复
docker run --rm -v chroma_data:/data -v $(pwd):/backup \\
    alpine tar xzf /backup/chroma_backup.tar.gz -C /
```
""")

# ============================================================================
# 5. Nginx 反向代理
# ============================================================================
print("\n--- 5. Nginx ---")

nginx_conf = """
server {
    listen 80;
    server_name _;

    # API 代理
    location /api/ {
        proxy_pass http://api:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # SSE 流式输出支持（关键！）
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_read_timeout 300s;
    }

    # 静态文件（前端）
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
""".strip()

print("nginx.conf:")
for i, line in enumerate(nginx_conf.split("\n"), 1):
    print(f"  {i:>2} | {line}")

print("""
Nginx 关键配置：
  proxy_buffering off    → 流式输出必须关闭缓冲
  proxy_read_timeout     → LLM 生成可能很慢
  proxy_http_version 1.1 → SSE 需要 HTTP/1.1
""")

# ============================================================================
# 6. 环境配置
# ============================================================================
print("\n--- 6. 环境配置 ---")

env_example = """
# .env
OPENAI_API_KEY=sk-xxx
DEEPSEEK_API_KEY=xxx
OLLAMA_BASE_URL=http://ollama:11434
REDIS_URL=redis://redis:6379/0
CHROMA_HOST=chromadb
CHROMA_PORT=8000
LOG_LEVEL=INFO
MAX_WORKERS=4
""".strip()

print(".env 文件:")
for line in env_example.split("\n"):
    print(f"  {line}")

print("""
环境配置最佳实践：
  ✅ .env 文件不提交到 Git（.gitignore）
  ✅ 提供 .env.example 作为模板
  ✅ Docker Compose 用 env_file 加载
  ✅ 敏感信息用 Docker Secrets
  ✅ 不同环境（dev/staging/prod）用不同 .env

启动流程：
```bash
# 1. 复制配置
cp .env.example .env
# 编辑 .env 填入实际值

# 2. 启动服务
docker-compose up -d --build

# 3. 下载模型
docker exec ollama ollama pull qwen2.5:7b

# 4. 验证
curl http://localhost/api/health
curl http://localhost:11434/api/tags
```
""")

# 模拟 Compose 配置生成
class ComposeGenerator:
    """Docker Compose 配置生成器"""

    def generate(self, services: list) -> dict:
        compose = {"version": "3.8", "services": {}, "volumes": {}}
        for svc in services:
            name = svc["name"]
            config = {}
            if "build" in svc:
                config["build"] = svc["build"]
            if "image" in svc:
                config["image"] = svc["image"]
            if "ports" in svc:
                config["ports"] = svc["ports"]
            if "volumes" in svc:
                config["volumes"] = svc["volumes"]
                for v in svc["volumes"]:
                    if ":" in v and not v.startswith("."):
                        vol_name = v.split(":")[0]
                        compose["volumes"][vol_name] = None
            if "depends_on" in svc:
                config["depends_on"] = svc["depends_on"]
            config["restart"] = "unless-stopped"
            compose["services"][name] = config
        return compose

gen = ComposeGenerator()
result = gen.generate([
    {"name": "api", "build": ".", "ports": ["8000:8000"], "depends_on": ["redis"]},
    {"name": "redis", "image": "redis:7-alpine", "ports": ["6379:6379"], "volumes": ["redis_data:/data"]},
])
print(f"生成的 Compose 配置:")
print(f"  服务: {list(result['services'].keys())}")
print(f"  卷: {list(result['volumes'].keys())}")

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] Docker Compose 声明式编排")
print("  [v] AI 服务多容器架构")
print("  [v] 容器网络与服务发现")
print("  [v] Volume 数据持久化")
print("  [v] Nginx 反向代理（支持SSE）")
print("  [v] 环境配置管理")
print("=" * 60)
print("\n下一课：03_model_serving.py - 模型服务")
