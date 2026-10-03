import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第1课：Docker 容器化 AI 服务
==============================================================================

Docker = 把应用和环境打包成容器，一次构建到处运行。
AI 服务尤其需要 Docker：依赖复杂、环境难复现。

本课内容：
1. 为什么 AI 服务需要 Docker
2. Docker 核心概念
3. Dockerfile 编写
4. AI 服务 Dockerfile
5. 多阶段构建
6. GPU Docker 配置
==============================================================================
"""

import json

print("=" * 60)
print("第1课：Docker 容器化 AI 服务")
print("=" * 60)

# ============================================================================
# 1. 为什么需要 Docker
# ============================================================================
print("\n--- 1. 为什么 Docker ---")
print("""
AI 服务部署的痛点：

  ❌ "在我电脑上能跑"综合症
  ❌ Python 版本不一致
  ❌ CUDA / cuDNN 版本冲突
  ❌ pip 依赖地狱（chromadb vs numpy vs torch）
  ❌ 模型文件管理混乱

Docker 解决：

  ✅ 环境一致性（开发 = 测试 = 生产）
  ✅ 依赖隔离（每个服务独立容器）
  ✅ 快速部署（秒级启动）
  ✅ 水平扩展（多副本+负载均衡）
  ✅ 版本管理（镜像标签）

AI 服务典型架构：
  ┌─────────┐  ┌─────────┐  ┌─────────┐
  │ API 容器 │  │ 模型容器 │  │ DB 容器  │
  │ FastAPI  │  │ Ollama   │  │ ChromaDB │
  │ :8000    │  │ :11434   │  │ :8500    │
  └─────────┘  └─────────┘  └─────────┘
       ↑             ↑            ↑
       └──────── Docker Network ──┘
""")

# ============================================================================
# 2. 核心概念
# ============================================================================
print("\n--- 2. 核心概念 ---")
print("""
┌──────────────────┬──────────────────────────────────────┐
│  概念             │  说明                                 │
├──────────────────┼──────────────────────────────────────┤
│  镜像 (Image)    │  只读模板，包含应用+环境             │
│                  │  类比：类/蓝图                        │
├──────────────────┼──────────────────────────────────────┤
│  容器 (Container)│  镜像的运行实例                       │
│                  │  类比：对象/实例                      │
├──────────────────┼──────────────────────────────────────┤
│  Dockerfile      │  构建镜像的脚本                       │
│                  │  FROM → RUN → COPY → CMD             │
├──────────────────┼──────────────────────────────────────┤
│  Registry        │  镜像仓库（Docker Hub / 阿里云）     │
├──────────────────┼──────────────────────────────────────┤
│  Volume          │  持久化存储（数据不随容器删除丢失）  │
├──────────────────┼──────────────────────────────────────┤
│  Network         │  容器间通信网络                       │
└──────────────────┴──────────────────────────────────────┘

常用命令：
  docker build -t myapp .         构建镜像
  docker run -p 8000:8000 myapp   运行容器
  docker ps                       查看运行中容器
  docker logs <container>         查看日志
  docker exec -it <container> sh  进入容器
  docker stop <container>         停止容器
""")

# ============================================================================
# 3. Dockerfile 编写
# ============================================================================
print("\n--- 3. Dockerfile ---")

dockerfile_basic = """
# 基础镜像
FROM python:3.11-slim

# 工作目录
WORKDIR /app

# 系统依赖（AI 服务常需要编译工具）
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Python 依赖（先 COPY requirements.txt 利用缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码
COPY . .

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
""".strip()

print("基础 Dockerfile:")
for i, line in enumerate(dockerfile_basic.split("\n"), 1):
    print(f"  {i:>2} | {line}")

print("""
Dockerfile 最佳实践：
  ✅ 使用 slim 基础镜像（减小体积）
  ✅ 先 COPY requirements.txt 再 COPY .（利用层缓存）
  ✅ --no-cache-dir（减小镜像大小）
  ✅ PYTHONUNBUFFERED=1（实时输出日志）
  ✅ 非 root 用户运行（安全）
  ❌ 不要 COPY 整个 .git 目录
  ❌ 不要在镜像中存 API Key
""")

# ============================================================================
# 4. AI 服务 Dockerfile
# ============================================================================
print("\n--- 4. AI 服务 Dockerfile ---")

ai_dockerfile = """
FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential curl \\
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/logs

# 非 root 用户
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_BASE_URL=http://ollama:11434

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
""".strip()

ai_requirements = """
fastapi==0.115.0
uvicorn[standard]==0.30.0
httpx==0.27.0
openai==1.50.0
chromadb==0.5.0
numpy==1.26.0
python-dotenv==1.0.0
python-multipart==0.0.9
""".strip()

print("AI 服务 Dockerfile:")
for i, line in enumerate(ai_dockerfile.split("\n"), 1):
    print(f"  {i:>2} | {line}")

print(f"\nrequirements.txt:")
for line in ai_requirements.split("\n"):
    print(f"  {line}")

# ============================================================================
# 5. 多阶段构建
# ============================================================================
print("\n--- 5. 多阶段构建 ---")

multistage = """
# 阶段1: 构建
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# 阶段2: 运行
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
""".strip()

print("多阶段构建:")
for i, line in enumerate(multistage.split("\n"), 1):
    print(f"  {i:>2} | {line}")

print("""
镜像大小对比：
  单阶段: ~1.2GB（包含编译工具）
  多阶段: ~600MB（只含运行时）
  + .dockerignore: 更小

.dockerignore 示例：
  .git
  .venv
  __pycache__
  *.pyc
  .env
  chroma_data/
  *.md
""")

# ============================================================================
# 6. GPU Docker
# ============================================================================
print("\n--- 6. GPU Docker ---")
print("""
GPU 容器 = NVIDIA Container Toolkit

安装：
```bash
# Ubuntu
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

使用：
```bash
# 测试 GPU
docker run --gpus all nvidia/cuda:12.0-base nvidia-smi

# Ollama GPU 模式
docker run -d --gpus all \\
    -p 11434:11434 \\
    -v ollama:/root/.ollama \\
    --name ollama \\
    ollama/ollama

# vLLM GPU 模式
docker run --gpus all \\
    -p 8000:8000 \\
    -v ./models:/models \\
    vllm/vllm-openai \\
    --model /models/Qwen2.5-7B-Instruct \\
    --dtype float16
```

GPU 资源配置：
```yaml
# docker-compose.yml
services:
  model:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1        # GPU 数量
              capabilities: [gpu]
```

无 GPU 方案：
  Ollama CPU 模式（慢但能用）
  GGUF 量化模型（CPU友好）
  云 GPU 实例（按需租用）
""")

# 模拟 Dockerfile 生成
print("\n--- Dockerfile 生成器 ---")

class DockerfileGenerator:
    """AI 服务 Dockerfile 生成器"""

    def generate(self, config: dict) -> str:
        lines = []
        base = config.get("base_image", "python:3.11-slim")
        lines.append(f"FROM {base}")
        lines.append("WORKDIR /app")
        lines.append("")

        if config.get("system_deps"):
            deps = " ".join(config["system_deps"])
            lines.append(f"RUN apt-get update && apt-get install -y --no-install-recommends \\")
            lines.append(f"    {deps} \\")
            lines.append(f"    && rm -rf /var/lib/apt/lists/*")
            lines.append("")

        lines.append("COPY requirements.txt .")
        lines.append("RUN pip install --no-cache-dir -r requirements.txt")
        lines.append("")
        lines.append("COPY . .")

        for env_key, env_val in config.get("env", {}).items():
            lines.append(f"ENV {env_key}={env_val}")

        port = config.get("port", 8000)
        lines.append(f"EXPOSE {port}")
        lines.append("")
        lines.append(f'CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "{port}"]')

        return "\n".join(lines)

gen = DockerfileGenerator()
result = gen.generate({
    "base_image": "python:3.11-slim",
    "system_deps": ["build-essential", "curl"],
    "env": {"PYTHONUNBUFFERED": "1", "LOG_LEVEL": "INFO"},
    "port": 8000,
})
print(f"生成的 Dockerfile ({len(result.split(chr(10)))} 行):")
for line in result.split("\n")[:8]:
    print(f"  {line}")
print(f"  ...")

print("\n" + "=" * 60)
print("[完成] 第1课完成！你已经学会了：")
print("  [v] AI 服务为什么需要 Docker")
print("  [v] Docker 核心概念（镜像/容器/卷/网络）")
print("  [v] Dockerfile 编写与最佳实践")
print("  [v] AI 服务专用 Dockerfile")
print("  [v] 多阶段构建优化镜像大小")
print("  [v] GPU Docker 配置")
print("=" * 60)
print("\n下一课：02_docker_compose.py - 多服务编排")
