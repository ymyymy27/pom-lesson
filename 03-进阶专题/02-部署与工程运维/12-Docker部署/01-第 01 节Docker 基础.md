> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 01 节：Docker 基础

## 一、什么是 Docker？

Docker 是一个 **容器化平台**，将应用及其所有依赖打包到一个标准化的单元（容器）中，实现"一次构建，到处运行"。

```
传统部署的问题：
"我的电脑上能跑啊" — Python 版本不同、依赖缺失、系统差异

Docker 解决：
将应用 + 运行时 + 依赖 + 配置 全部打包到容器中
开发环境 = 测试环境 = 生产环境
```

### 1.1 核心概念

| 概念 | 说明 | 类比 |
|------|------|------|
| **镜像（Image）** | 只读模板，包含运行应用所需的一切 | 安装光盘 |
| **容器（Container）** | 镜像的运行实例 | 安装好的系统 |
| **Dockerfile** | 构建镜像的脚本 | 安装步骤 |
| **Registry** | 镜像仓库（Docker Hub） | 应用商店 |
| **Volume** | 持久化数据存储 | 外接硬盘 |
| **Network** | 容器间通信 | 局域网 |

```
Dockerfile → (构建) → Image → (运行) → Container
                         ↕
                    Docker Hub（推送/拉取）
```

---

## 二、安装 Docker

### Windows
1. 下载 Docker Desktop：https://www.docker.com/products/docker-desktop
2. 安装并启动
3. 确保 WSL 2 已启用

```bash
# 验证安装
docker --version          # Docker version 24.x
docker compose version    # Docker Compose version v2.x
```

---

## 三、镜像操作

```bash
# 拉取镜像
docker pull python:3.12-slim
docker pull postgres:16
docker pull redis:7-alpine
docker pull node:20-alpine
docker pull nginx:alpine

# 查看本地镜像
docker images

# 删除镜像
docker rmi python:3.12-slim

# 搜索镜像
docker search python
```

### 3.1 镜像标签

```
镜像名:标签

python:3.12          完整版（较大）
python:3.12-slim     精简版（推荐后端）
python:3.12-alpine   极简版（最小，但可能缺少编译工具）
node:20-alpine       Node.js Alpine 版（推荐前端构建）
postgres:16          PostgreSQL 16
redis:7-alpine       Redis 7 Alpine 版
nginx:alpine         Nginx Alpine 版
```

---

## 四、容器操作

```bash
# 运行容器
docker run -d --name my-redis -p 6379:6379 redis:7-alpine
#   -d          后台运行
#   --name      容器名称
#   -p 6379:6379  端口映射（主机:容器）

# 查看运行中的容器
docker ps

# 查看所有容器（包括已停止的）
docker ps -a

# 停止/启动/重启容器
docker stop my-redis
docker start my-redis
docker restart my-redis

# 删除容器
docker rm my-redis
docker rm -f my-redis    # 强制删除（包括运行中的）

# 查看容器日志
docker logs my-redis
docker logs -f my-redis  # 实时跟踪

# 进入容器内部
docker exec -it my-redis sh
docker exec -it my-postgres psql -U postgres

# 查看容器资源使用
docker stats
```

### 4.1 运行 PostgreSQL 容器

```bash
docker run -d \
  --name taskflow-db \
  -e POSTGRES_DB=taskflow \
  -e POSTGRES_USER=taskflow \
  -e POSTGRES_PASSWORD=taskflow123 \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16

# 连接数据库
docker exec -it taskflow-db psql -U taskflow -d taskflow
```

### 4.2 运行 Redis 容器

```bash
docker run -d \
  --name taskflow-redis \
  -p 6379:6379 \
  redis:7-alpine

# 连接 Redis
docker exec -it taskflow-redis redis-cli
```

---

## 五、数据卷（Volume）

容器销毁后数据会丢失，Volume 用于 **持久化数据**。

```bash
# 创建卷
docker volume create pgdata

# 查看卷
docker volume ls
docker volume inspect pgdata

# 使用卷（-v 参数）
docker run -d -v pgdata:/var/lib/postgresql/data postgres:16

# 绑定挂载（将主机目录映射到容器）
docker run -d -v ./src:/app/src python:3.12-slim

# 删除卷
docker volume rm pgdata

# 清理未使用的卷
docker volume prune
```

---

## 六、Docker 网络

```bash
# 创建网络
docker network create taskflow-net

# 容器加入网络
docker run -d --name db --network taskflow-net postgres:16
docker run -d --name redis --network taskflow-net redis:7-alpine
docker run -d --name web --network taskflow-net my-django-app

# 同一网络中的容器可以通过容器名互相访问
# web 容器内：postgres://db:5432/taskflow
# web 容器内：redis://redis:6379/0

# 查看网络
docker network ls
docker network inspect taskflow-net
```

---

## 七、常用清理命令

```bash
# 删除所有已停止的容器
docker container prune

# 删除未使用的镜像
docker image prune

# 全面清理（容器 + 镜像 + 网络 + 卷）
docker system prune -a --volumes

# 查看磁盘占用
docker system df
```

---

## 八、练习

1. 安装 Docker Desktop，验证 `docker --version`
2. 拉取 `postgres:16`、`redis:7-alpine` 镜像
3. 运行 PostgreSQL 容器，创建 `taskflow` 数据库
4. 运行 Redis 容器，用 `redis-cli` 测试连接
5. 使用 Volume 持久化 PostgreSQL 数据
6. 创建 Docker 网络，让 PostgreSQL 和 Redis 容器互通
7. 练习容器的启停、日志查看、进入容器
