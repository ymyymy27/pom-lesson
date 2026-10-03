> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第3课：Docker Compose 多容器编排

## 1. 为什么需要 Compose？

### 问题
一个真实应用通常需要多个服务：

```
Web 应用 + 数据库 + Redis缓存 + Nginx反代

没有 Compose：
docker run -d --name db -e POSTGRES_PASSWORD=xxx postgres
docker run -d --name redis redis
docker run -d --name app --link db --link redis myapp
docker run -d --name nginx -p 80:80 --link app nginx
# 每次要敲4条命令，容易忘、容易错

有了 Compose：
docker-compose up -d
# 一条命令全部启动！
```

### 一句话解释
**Docker Compose 就是"批量管理容器的配置文件"** —— 用一个 YAML 文件定义所有服务，一条命令全部启停。

---

## 2. 安装

```bash
# Docker Desktop 自带 Compose（v2）
docker compose version
# Docker Compose version v2.24.0

# Linux 单独安装
sudo apt install docker-compose-plugin
# 或
pip install docker-compose
```

**注意：** 新版用 `docker compose`（空格），旧版用 `docker-compose`（连字符）。

---

## 3. docker-compose.yml 基本结构

```yaml
# docker-compose.yml

services:
  # 服务1：Web 应用
  web:
    build: .                     # 用当前目录的 Dockerfile 构建
    ports:
      - "8000:8000"             # 端口映射
    environment:
      - DATABASE_URL=postgres://db:5432/mydb
    depends_on:
      - db                      # 依赖 db 服务
    restart: always

  # 服务2：数据库
  db:
    image: postgres:16           # 使用现成镜像
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - db_data:/var/lib/postgresql/data   # 数据持久化
    ports:
      - "5432:5432"

  # 服务3：Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

# 声明数据卷
volumes:
  db_data:
```

---

## 4. 常用配置项

### 4.1 build（构建镜像）

```yaml
services:
  app:
    # 简写
    build: .

    # 详细写法
    build:
      context: .                 # 构建上下文目录
      dockerfile: Dockerfile.prod   # 指定 Dockerfile
      args:                      # 构建参数
        - VERSION=1.0
```

### 4.2 image（使用镜像）

```yaml
services:
  db:
    image: postgres:16
  redis:
    image: redis:7-alpine
  nginx:
    image: nginx:1.25
```

### 4.3 ports（端口映射）

```yaml
ports:
  - "8000:8000"         # 主机端口:容器端口
  - "127.0.0.1:5432:5432"  # 只绑定 localhost
  - "8080-8090:8080-8090"  # 端口范围
```

### 4.4 volumes（数据卷）

```yaml
volumes:
  # 命名卷（Docker 管理）
  - db_data:/var/lib/postgresql/data

  # 绑定挂载（主机目录）
  - ./config:/app/config:ro       # :ro = 只读
  - ./logs:/app/logs

  # 匿名卷
  - /app/node_modules
```

### 4.5 environment（环境变量）

```yaml
environment:
  # 列表格式
  - DB_HOST=db
  - DB_PORT=5432
  - SECRET_KEY=mysecret

# 或字典格式
environment:
  DB_HOST: db
  DB_PORT: 5432

# 从文件加载
env_file:
  - .env
  - .env.local
```

### 4.6 depends_on（依赖关系）

```yaml
services:
  web:
    depends_on:
      - db
      - redis
    # web 会在 db 和 redis 之后启动

  # 带健康检查的依赖（推荐）
  web:
    depends_on:
      db:
        condition: service_healthy

  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 5s
      timeout: 5s
      retries: 5
```

### 4.7 restart（重启策略）

```yaml
restart: "no"              # 不自动重启（默认）
restart: always            # 总是重启
restart: on-failure        # 失败时重启
restart: unless-stopped    # 除非手动停止
```

### 4.8 networks（自定义网络）

```yaml
services:
  web:
    networks:
      - frontend
      - backend
  db:
    networks:
      - backend           # db 只在 backend 网络，web 无法直接访问

networks:
  frontend:
  backend:
```

---

## 5. 常用命令

### 启停管理

```bash
# 启动所有服务（后台）
docker compose up -d

# 启动并重新构建
docker compose up -d --build

# 停止所有服务
docker compose down

# 停止并删除数据卷（⚠️ 数据会丢失）
docker compose down -v

# 重启某个服务
docker compose restart web

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs              # 所有服务
docker compose logs -f web       # 实时跟踪 web 服务
docker compose logs --tail 50    # 最后50行
```

### 扩缩容

```bash
# 启动3个 web 实例
docker compose up -d --scale web=3

# 查看
docker compose ps
```

### 执行命令

```bash
# 在运行中的容器执行命令
docker compose exec web bash
docker compose exec db psql -U user mydb

# 运行一次性命令（创建新容器）
docker compose run web python manage.py migrate
docker compose run web pytest
```

---

## 6. 实战示例：Python + PostgreSQL + Redis

### 项目结构

```
my-project/
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
└── .dockerignore
```

### docker-compose.yml

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - .:/app          # 开发时挂载代码（热重载）
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 操作流程

```bash
# 1. 启动所有服务
docker compose up -d

# 2. 查看状态
docker compose ps

# 3. 查看日志
docker compose logs -f web

# 4. 进入数据库
docker compose exec db psql -U user mydb

# 5. 停止
docker compose down
```

---

## 7. 多环境配置

### 开发环境 vs 生产环境

```yaml
# docker-compose.yml（基础配置）
services:
  web:
    build: .
    depends_on:
      - db

# docker-compose.dev.yml（开发覆盖）
services:
  web:
    volumes:
      - .:/app           # 挂载代码
    environment:
      - DEBUG=true
    ports:
      - "8000:8000"

# docker-compose.prod.yml（生产覆盖）
services:
  web:
    restart: always
    environment:
      - DEBUG=false
    deploy:
      replicas: 3
```

```bash
# 开发环境
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 生产环境
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 8. 动手练习

1. 写一个 `docker-compose.yml`，包含 Nginx + Python Web App
2. 加入 PostgreSQL 数据库服务
3. 用 `docker compose up -d` 启动所有服务
4. 用 `docker compose logs -f` 查看日志
5. 用 `docker compose exec` 进入数据库容器
6. 用 `docker compose down -v` 清理所有

---

## 9. 小结

| 命令 | 作用 |
|------|------|
| `docker compose up -d` | 后台启动所有服务 |
| `docker compose down` | 停止并删除所有服务 |
| `docker compose ps` | 查看服务状态 |
| `docker compose logs -f` | 实时查看日志 |
| `docker compose exec 服务 命令` | 在容器中执行命令 |
| `docker compose build` | 重新构建镜像 |

**核心文件：** `docker-compose.yml` 定义所有服务、网络、卷。

---

**下一课：** `04-第4课网络与数据持久化.md` - 网络与数据持久化
