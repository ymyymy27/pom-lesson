> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 03 节：Docker Compose 编排

## 一、什么是 Docker Compose？

Docker Compose 用于定义和运行 **多容器应用**。通过一个 `docker-compose.yml` 文件，一条命令启动所有服务。

```
TaskFlow 需要的服务：
┌────────────────────────────────────────┐
│  PostgreSQL  │  Redis  │  Django (API)  │
│  Celery Worker  │  Celery Beat  │  Nginx  │
│  React (构建后由 Nginx 提供)              │
└────────────────────────────────────────┘
```

---

## 二、开发环境 docker-compose.yml

```yaml
# docker-compose.yml（开发环境）
version: '3.9'

services:
  # ==================== 数据库 ====================
  db:
    image: postgres:16
    container_name: taskflow-db
    environment:
      POSTGRES_DB: taskflow
      POSTGRES_USER: taskflow
      POSTGRES_PASSWORD: taskflow123
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U taskflow"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ==================== 缓存/消息队列 ====================
  redis:
    image: redis:7-alpine
    container_name: taskflow-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ==================== 后端 API ====================
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: taskflow-backend
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app          # 代码热重载
      - backend-media:/app/media
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
      - DATABASE_URL=postgres://taskflow:taskflow123@db:5432/taskflow
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  # ==================== Celery Worker ====================
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: taskflow-celery-worker
    command: celery -A config worker --loglevel=info --pool=solo
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgres://taskflow:taskflow123@db:5432/taskflow
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  # ==================== Celery Beat ====================
  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: taskflow-celery-beat
    command: celery -A config beat --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgres://taskflow:taskflow123@db:5432/taskflow
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  # ==================== 前端（开发模式）====================
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: taskflow-frontend
    command: npm run dev -- --host 0.0.0.0
    volumes:
      - ./frontend:/app
      - /app/node_modules   # 排除 node_modules
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api/v1

volumes:
  pgdata:
  backend-media:
```

### 2.1 前端开发 Dockerfile

```dockerfile
# frontend/Dockerfile.dev
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

---

## 三、Docker Compose 常用命令

```bash
# 启动所有服务（后台运行）
docker compose up -d

# 启动并重新构建
docker compose up -d --build

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs              # 所有服务
docker compose logs backend      # 指定服务
docker compose logs -f backend   # 实时跟踪

# 停止所有服务
docker compose down

# 停止并删除数据卷
docker compose down -v

# 重启某个服务
docker compose restart backend

# 执行命令
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py shell
docker compose exec db psql -U taskflow -d taskflow

# 只启动部分服务
docker compose up -d db redis
docker compose up -d backend
```

---

## 四、初始化脚本

```bash
#!/bin/bash
# scripts/init.sh — 首次启动时运行

echo "等待数据库就绪..."
docker compose up -d db redis
sleep 5

echo "启动后端..."
docker compose up -d backend

echo "运行数据库迁移..."
docker compose exec backend python manage.py migrate

echo "创建超级用户..."
docker compose exec backend python manage.py createsuperuser --noinput \
  --username admin --email admin@taskflow.com 2>/dev/null || true

echo "启动所有服务..."
docker compose up -d

echo "✅ TaskFlow 已启动"
echo "   前端: http://localhost:3000"
echo "   后端: http://localhost:8000"
echo "   Admin: http://localhost:8000/admin/"
```

---

## 五、环境变量管理

```bash
# .env（Docker Compose 自动读取同目录的 .env 文件）
POSTGRES_DB=taskflow
POSTGRES_USER=taskflow
POSTGRES_PASSWORD=taskflow123
SECRET_KEY=your-secret-key-for-dev
DEBUG=True
```

```yaml
# docker-compose.yml 中引用
services:
  db:
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  
  backend:
    env_file:
      - .env              # 从 .env 文件加载
    environment:
      - DATABASE_URL=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
```

---

## 六、数据管理

```bash
# 导出数据库
docker compose exec db pg_dump -U taskflow taskflow > backup.sql

# 导入数据库
docker compose exec -T db psql -U taskflow taskflow < backup.sql

# 查看卷
docker volume ls | grep taskflow

# 备份卷数据
docker run --rm -v taskflow_pgdata:/data -v $(pwd):/backup \
  alpine tar czf /backup/pgdata-backup.tar.gz -C /data .
```

---

## 七、练习

1. 编写完整的 `docker-compose.yml`，包含 db、redis、backend、celery-worker、celery-beat、frontend
2. 使用 `docker compose up -d` 一键启动所有服务
3. 使用 `docker compose exec` 运行数据库迁移和创建超级用户
4. 查看各服务日志，确认都正常运行
5. 编写 `init.sh` 初始化脚本
6. 测试 `docker compose down` 后数据是否通过卷持久化
