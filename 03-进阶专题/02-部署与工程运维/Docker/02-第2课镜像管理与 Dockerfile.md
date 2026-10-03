> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第2课：镜像管理与 Dockerfile

## 1. 镜像基础

### 查看与搜索

```bash
# 查看本地镜像
docker images
# REPOSITORY    TAG       IMAGE ID       SIZE
# python        3.12      abc123def456   1.01GB
# nginx         latest    789ghi012jkl   187MB

# 搜索 Docker Hub
docker search python
docker search nginx --filter stars=100    # 只看星标>100的

# 拉取镜像
docker pull python:3.12-slim             # 指定标签
docker pull nginx:latest                 # latest 是默认标签
docker pull python                       # 等同于 python:latest
```

### 镜像标签（Tag）

```
格式：仓库名:标签
  python:3.12          Python 3.12
  python:3.12-slim     精简版（推荐）
  python:3.12-alpine   Alpine 版（最小）
  nginx:1.25           指定版本
  nginx:latest         最新版

大小对比：
  python:3.12          ~1.0GB
  python:3.12-slim     ~150MB    ← 推荐
  python:3.12-alpine   ~50MB     ← 最小但可能有兼容问题
```

**最佳实践：** 生产环境永远用具体版本号，不要用 `latest`。

### 镜像清理

```bash
docker rmi python:3.12              # 删除指定镜像
docker image prune                  # 删除无用镜像（dangling）
docker image prune -a               # 删除所有未使用的镜像
docker system prune                 # 清理所有（镜像+容器+网络+缓存）
docker system prune -a              # 彻底清理（释放空间）
docker system df                    # 查看 Docker 磁盘占用
```

---

## 2. Dockerfile 编写

### 2.1 基本结构

```dockerfile
# 基础镜像
FROM python:3.12-slim

# 维护者信息
LABEL maintainer="yourname@example.com"

# 设置工作目录
WORKDIR /app

# 复制依赖文件（利用缓存，依赖不变就不重装）
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.2 常用指令

| 指令 | 作用 | 示例 |
|------|------|------|
| `FROM` | 基础镜像 | `FROM python:3.12-slim` |
| `WORKDIR` | 工作目录 | `WORKDIR /app` |
| `COPY` | 复制文件 | `COPY . .` |
| `ADD` | 复制文件（支持URL和解压） | `ADD archive.tar.gz /app/` |
| `RUN` | 构建时执行命令 | `RUN pip install flask` |
| `CMD` | 容器启动命令 | `CMD ["python", "app.py"]` |
| `ENTRYPOINT` | 容器入口点 | `ENTRYPOINT ["python"]` |
| `ENV` | 环境变量 | `ENV PORT=8000` |
| `EXPOSE` | 声明端口 | `EXPOSE 8000` |
| `VOLUME` | 声明数据卷 | `VOLUME /data` |
| `ARG` | 构建参数 | `ARG VERSION=1.0` |

### CMD vs ENTRYPOINT

```dockerfile
# CMD：可以被 docker run 参数覆盖
CMD ["python", "app.py"]
# docker run myapp              → python app.py
# docker run myapp python -V    → python -V（覆盖了 CMD）

# ENTRYPOINT：不会被覆盖，参数会追加
ENTRYPOINT ["python"]
CMD ["app.py"]
# docker run myapp              → python app.py
# docker run myapp test.py      → python test.py（CMD 被替换）
```

### 2.3 .dockerignore

类似 `.gitignore`，排除不需要复制到镜像的文件。

```
# .dockerignore
.git
.venv
__pycache__
*.pyc
.env
node_modules
*.md
.dockerignore
Dockerfile
```

---

## 3. 构建镜像

```bash
# 基本构建
docker build -t myapp:1.0 .
# -t 指定名称和标签
# .  表示 Dockerfile 在当前目录

# 指定 Dockerfile 路径
docker build -f Dockerfile.prod -t myapp:prod .

# 构建参数
docker build --build-arg VERSION=2.0 -t myapp:2.0 .

# 不使用缓存（强制重新构建）
docker build --no-cache -t myapp:1.0 .

# 查看构建历史
docker history myapp:1.0
```

---

## 4. 缓存优化

### 理解 Docker 层缓存

Dockerfile 每条指令创建一层。如果某层没变，Docker 会使用缓存。

```dockerfile
# ✗ 坏的写法：改一行代码就要重新装依赖
COPY . .
RUN pip install -r requirements.txt

# ✓ 好的写法：依赖不变就用缓存
COPY requirements.txt .               # 第1层：只复制依赖文件
RUN pip install -r requirements.txt   # 第2层：安装依赖（依赖没变就用缓存）
COPY . .                              # 第3层：复制代码（代码变了只重建这层）
```

### 合并 RUN 命令

```dockerfile
# ✗ 坏的：每条 RUN 创建一层，镜像更大
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y vim

# ✓ 好的：合并为一层，并清理缓存
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl vim && \
    rm -rf /var/lib/apt/lists/*
```

---

## 5. 多阶段构建

用多个 `FROM` 分阶段构建，最终镜像只保留需要的文件。

```dockerfile
# === 阶段1：构建 ===
FROM python:3.12 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# === 阶段2：运行（精简镜像）===
FROM python:3.12-slim
WORKDIR /app

# 只复制安装好的依赖
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]
```

**效果：** 构建工具不会进入最终镜像，镜像大小显著减小。

---

## 6. 容器操作进阶

### 生命周期

```
docker create → docker start → docker stop → docker rm
  创建            启动            停止           删除
                    ↕
                docker pause / unpause
                  暂停      恢复
```

### 容器与主机交互

```bash
# 复制文件
docker cp myapp:/app/data.json ./      # 容器 → 主机
docker cp ./config.py myapp:/app/      # 主机 → 容器

# 查看容器日志
docker logs myapp                       # 全部日志
docker logs -f myapp                    # 实时跟踪
docker logs --tail 100 myapp            # 最后100行
docker logs --since 2024-01-15 myapp    # 指定时间之后

# 查看资源使用
docker stats                            # 实时监控所有容器
docker stats myapp                      # 监控特定容器

# 查看容器进程
docker top myapp
```

### 镜像导入导出

```bash
# 导出镜像为文件（备份/迁移）
docker save -o myapp.tar myapp:1.0

# 导入镜像
docker load -i myapp.tar

# 从容器创建镜像（快照）
docker commit myapp myapp:snapshot
```

---

## 7. 实战：打包 Python Web 应用

### 项目结构

```
my-web-app/
├── app.py
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

### app.py

```python
from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def hello():
    return jsonify({"message": "Hello Docker!", "status": "running"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### requirements.txt

```
flask==3.0.0
```

### Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

### 构建和运行

```bash
# 构建
docker build -t my-web-app:1.0 .

# 运行
docker run -d -p 5000:5000 --name web my-web-app:1.0

# 测试
curl http://localhost:5000/
# {"message": "Hello Docker!", "status": "running"}

curl http://localhost:5000/health
# {"status": "healthy"}

# 查看日志
docker logs web

# 清理
docker stop web && docker rm web
```

---

## 8. 动手练习

1. 拉取 `python:3.12-slim` 镜像，查看大小
2. 写一个 Dockerfile，打包一个简单的 Python 脚本
3. 构建镜像并运行
4. 进入容器内部查看文件
5. 练习 `.dockerignore`，排除 `.git` 和 `__pycache__`
6. 用多阶段构建优化镜像大小

---

## 9. 小结

| 概念 | 要点 |
|------|------|
| 镜像标签 | 用具体版本号，不要用 latest |
| Dockerfile | FROM → WORKDIR → COPY deps → RUN install → COPY code → CMD |
| 缓存优化 | 先复制依赖文件，再复制代码 |
| 多阶段构建 | 构建和运行分开，减小镜像体积 |
| .dockerignore | 排除不需要的文件 |

---

**下一课：** `03-第3课Docker Compose 多容器编排.md` - Docker Compose 多容器编排
