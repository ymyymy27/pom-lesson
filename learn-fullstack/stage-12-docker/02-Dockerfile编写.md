# 第 02 节：Dockerfile 编写

## 一、Dockerfile 基础

Dockerfile 是构建镜像的 **指令文件**，每条指令生成一层镜像层。

### 1.1 常用指令

| 指令 | 说明 | 示例 |
|------|------|------|
| `FROM` | 基础镜像 | `FROM python:3.12-slim` |
| `WORKDIR` | 工作目录 | `WORKDIR /app` |
| `COPY` | 复制文件 | `COPY . /app` |
| `RUN` | 执行命令 | `RUN pip install -r requirements.txt` |
| `ENV` | 设置环境变量 | `ENV PYTHONDONTWRITEBYTECODE=1` |
| `EXPOSE` | 声明端口 | `EXPOSE 8000` |
| `CMD` | 启动命令 | `CMD ["python", "manage.py", "runserver"]` |
| `ENTRYPOINT` | 入口点 | `ENTRYPOINT ["gunicorn"]` |
| `ARG` | 构建参数 | `ARG ENVIRONMENT=production` |
| `VOLUME` | 声明挂载点 | `VOLUME /app/media` |

---

## 二、后端 Dockerfile（Django）

### 2.1 开发环境

```dockerfile
# backend/Dockerfile.dev
FROM python:3.12-slim

# 环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制依赖文件（利用缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### 2.2 生产环境（多阶段构建）

```dockerfile
# backend/Dockerfile
# ==================== 阶段1：构建 ====================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ==================== 阶段2：运行 ====================
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 只安装运行时依赖（不需要 gcc）
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制已安装的包
COPY --from=builder /install /usr/local

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY . .

# 收集静态文件
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# 创建媒体目录
RUN mkdir -p /app/media && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# 使用 Gunicorn 运行
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

### 2.3 requirements.txt

```
Django==5.0
djangorestframework==3.14
djangorestframework-simplejwt==5.3
django-cors-headers==4.3
django-filter==23.5
django-redis==5.4
drf-spectacular==0.27
psycopg2-binary==2.9
celery==5.3
django-celery-beat==2.5
django-celery-results==2.5
redis==5.0
gunicorn==21.2
channels==4.0
channels-redis==4.1
daphne==4.0
Pillow==10.2
python-dotenv==1.0
factory-boy==3.3
```

---

## 三、前端 Dockerfile（React）

### 3.1 多阶段构建

```dockerfile
# frontend/Dockerfile
# ==================== 阶段1：构建 ====================
FROM node:20-alpine AS builder

WORKDIR /app

# 先复制依赖文件（利用缓存）
COPY package.json package-lock.json ./
RUN npm ci

# 复制源代码并构建
COPY . .
RUN npm run build

# ==================== 阶段2：Nginx 提供服务 ====================
FROM nginx:alpine AS runtime

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 3.2 前端 Nginx 配置

```nginx
# frontend/nginx.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # SPA 路由：所有路径都返回 index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理（转发到后端）
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 媒体文件代理
    location /media/ {
        proxy_pass http://backend:8000;
    }

    # 静态文件缓存
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 1024;
}
```

---

## 四、.dockerignore

```
# backend/.dockerignore
__pycache__
*.pyc
*.pyo
.env
.env.local
.git
.gitignore
.vscode
media/*
!media/.gitkeep
*.sqlite3
htmlcov
.coverage
.pytest_cache
node_modules

# frontend/.dockerignore
node_modules
dist
.git
.gitignore
.env
.env.local
.vscode
coverage
```

---

## 五、构建与运行

```bash
# 构建后端镜像
cd backend
docker build -t taskflow-backend:latest .
docker build -f Dockerfile.dev -t taskflow-backend:dev .

# 构建前端镜像
cd frontend
docker build -t taskflow-frontend:latest .

# 运行容器
docker run -d --name backend -p 8000:8000 taskflow-backend:latest
docker run -d --name frontend -p 80:80 taskflow-frontend:latest

# 查看镜像大小
docker images | grep taskflow
```

---

## 六、Dockerfile 最佳实践

```
1. 使用多阶段构建 — 减小镜像体积
2. 先复制依赖文件再复制代码 — 利用 Docker 构建缓存
3. 使用 slim/alpine 基础镜像 — 减小体积
4. 不以 root 用户运行 — 安全
5. 使用 .dockerignore — 排除不必要的文件
6. 合并 RUN 命令 — 减少镜像层数
7. 清理缓存 — rm -rf /var/lib/apt/lists/*
```

---

## 七、练习

1. 编写 Django 后端 Dockerfile（开发版和生产版）
2. 编写 React 前端 Dockerfile（多阶段构建 + Nginx）
3. 编写 `.dockerignore` 文件
4. 构建镜像，对比开发版和生产版的大小
5. 运行后端容器，测试 API 是否正常
6. 运行前端容器，测试页面是否正常
