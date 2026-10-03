> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 04 节：生产环境 Docker 部署

## 一、生产环境架构

```
                    ┌─────────┐
                    │  Nginx  │ ← 反向代理 + 静态文件 + SSL
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼───┐ ┌───▼────┐ ┌──▼───┐
         │ React  │ │ Django │ │ Media│
         │ (静态) │ │ (API)  │ │ 文件 │
         └────────┘ └───┬────┘ └──────┘
                        │
              ┌─────────┼─────────┐
              │         │         │
         ┌────▼───┐ ┌──▼───┐ ┌──▼──────────┐
         │Postgres│ │Redis │ │Celery Worker│
         └────────┘ └──────┘ │Celery Beat  │
                             └─────────────┘
```

---

## 二、生产环境 docker-compose.prod.yml

```yaml
# docker-compose.prod.yml
version: '3.9'

services:
  # ==================== 数据库 ====================
  db:
    image: postgres:16
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    # 不暴露端口到主机（只在内部网络访问）

  # ==================== Redis ====================
  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ==================== 后端 API ====================
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - DATABASE_URL=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}
    volumes:
      - backend-media:/app/media
      - backend-static:/app/staticfiles
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  # ==================== Celery Worker ====================
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    command: celery -A config worker --loglevel=warning --concurrency=4
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  # ==================== Celery Beat ====================
  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    command: celery -A config beat --loglevel=warning
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  # ==================== Nginx ====================
  nginx:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - backend-media:/app/media:ro
      - backend-static:/app/staticfiles:ro
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certbot/conf:/etc/letsencrypt:ro
    depends_on:
      - backend

volumes:
  pgdata:
  redisdata:
  backend-media:
  backend-static:
```

---

## 三、生产环境 Nginx 配置

```nginx
# nginx/nginx.conf
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml application/xml+rss text/javascript
               image/svg+xml;
    gzip_min_length 1024;

    # 上传大小限制
    client_max_body_size 20M;

    # 上游服务
    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # Let's Encrypt 验证
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        # HTTP 重定向到 HTTPS（生产环境启用）
        # location / {
        #     return 301 https://$host$request_uri;
        # }

        # === 以下为 HTTP 直接服务（或 HTTPS server 块中使用）===

        # 前端静态文件
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;

            # 静态资源缓存
            location /assets/ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # API 代理
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 120s;
        }

        # Django Admin
        location /admin/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # Django 静态文件
        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
            add_header Cache-Control "public";
        }

        # 媒体文件
        location /media/ {
            alias /app/media/;
            expires 7d;
            add_header Cache-Control "public";
        }

        # WebSocket
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_read_timeout 86400;
        }

        # 安全头
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    }
}
```

---

## 四、生产环境 .env

```bash
# .env.prod
POSTGRES_DB=taskflow
POSTGRES_USER=taskflow
POSTGRES_PASSWORD=<生成强密码>
REDIS_PASSWORD=<生成强密码>

SECRET_KEY=<生成 Django Secret Key>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com
```

```bash
# 生成密码/密钥
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
openssl rand -base64 32  # 生成随机密码
```

---

## 五、部署命令

```bash
# 使用生产配置启动
docker compose -f docker-compose.prod.yml up -d --build

# 运行迁移
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# 创建超级用户
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# 收集静态文件
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 重新部署（代码更新后）
docker compose -f docker-compose.prod.yml up -d --build backend celery-worker celery-beat nginx
```

---

## 六、生产安全检查清单

```
✅ 安全
  □ DEBUG = False
  □ SECRET_KEY 使用强随机值
  □ 数据库密码使用强随机值
  □ Redis 设置密码
  □ ALLOWED_HOSTS 限制域名
  □ CORS 只允许你的前端域名
  □ 使用非 root 用户运行容器
  □ 数据库不暴露端口到主机

✅ 性能
  □ Gunicorn workers = 2 × CPU + 1
  □ 开启 Gzip 压缩
  □ 静态文件设置长期缓存
  □ PostgreSQL 连接池
  □ Redis 持久化

✅ 可靠性
  □ restart: always 自动重启
  □ healthcheck 健康检查
  □ 数据卷持久化
  □ 日志收集
  □ 定期数据库备份
```

---

## 七、练习

1. 编写生产环境 `docker-compose.prod.yml`
2. 编写生产 Nginx 配置（静态文件 + API 代理 + WebSocket）
3. 配置生产环境变量（强密码、正确的域名）
4. 使用生产配置启动所有服务
5. 验证：前端页面、API 接口、静态文件、媒体文件、WebSocket
6. 对照安全检查清单逐项检查

## 阶段总结

至此，第 12 阶段全部完成。你已经掌握：

- ✅ Docker 核心概念（镜像、容器、卷、网络）
- ✅ 编写 Dockerfile（多阶段构建）
- ✅ Docker Compose 多容器编排
- ✅ 生产环境部署（Nginx + Gunicorn + SSL）

**下一阶段** → 第 13 阶段：CI/CD & 云部署
