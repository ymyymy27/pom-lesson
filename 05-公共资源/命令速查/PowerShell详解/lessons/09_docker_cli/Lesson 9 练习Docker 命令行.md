> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Lesson 9 练习：Docker 命令行

## 练习说明

本练习覆盖 Lesson 9 的所有核心概念。建议先通读 Lesson 9 教程，再完成以下练习。

> **注意**：以下练习需要 Docker Desktop 已安装并运行。如果没有安装，请先安装 Docker Desktop。

---

## 练习 9.1：Docker 环境验证

**目标**：验证 Docker 安装和运行状态。

### 任务 A：检查 Docker 版本

```powershell
# 检查 Docker 版本
docker --version

# 查看 Docker 信息
docker info

# 验证 Docker 运行
docker ps
```

### 任务 B：运行测试镜像

```powershell
# 运行 hello-world 镜像测试
docker run hello-world
```

---

## 练习 9.2：镜像操作

**目标**：掌握镜像的查看、拉取和管理。

### 任务 A：查看镜像

```powershell
# 查看本地镜像
docker images
docker image ls

# 查看镜像详细信息
docker image inspect nginx:latest

# 查看镜像大小
docker images --format "{{.Repository}}:{{.Tag}} - {{.Size}}"
```

### 任务 B：拉取镜像

```powershell
# 拉取镜像
docker pull nginx:latest

# 拉取特定版本
docker pull nginx:1.25-alpine

# 拉取 Ubuntu
docker pull ubuntu:latest
```

### 任务 C：删除镜像

```powershell
# 删除镜像
docker rmi nginx:latest

# 强制删除
# docker rmi -f nginx:latest

# 清理未使用的镜像
docker image prune

# 清理所有未使用的镜像
# docker image prune -a
```

---

## 练习 9.3：容器生命周期

**目标**：掌握容器的创建、启动、停止操作。

### 任务 A：创建容器

```powershell
# 创建但不启动
docker create --name my-nginx nginx

# 查看容器状态
docker ps -a
```

### 任务 B：启动和停止

```powershell
# 启动容器
docker start my-nginx

# 停止容器
docker stop my-nginx

# 重启容器
docker restart my-nginx

# 强制停止
# docker kill my-nginx
```

### 任务 C：运行新容器

```powershell
# 运行交互式容器
docker run -it ubuntu /bin/bash

# 运行后台容器
docker run -d --name my-nginx nginx

# 运行临时容器（退出后删除）
docker run --rm -it ubuntu /bin/bash
```

---

## 练习 9.4：进入容器

**目标**：掌握进入运行中容器的方法。

### 任务 A：使用 docker exec

```powershell
# 启动一个测试容器
docker run -d --name test-container ubuntu sleep 3600

# 进入容器
docker exec -it test-container /bin/bash

# 在容器中执行命令
docker exec test-container ls /

# 以 root 用户进入
docker exec -it -u root test-container /bin/bash

# 清理
docker stop test-container
docker rm test-container
```

---

## 练习 9.5：容器管理

**目标**：掌握容器的查看、日志和检查。

### 任务 A：查看容器

```powershell
# 查看运行中的容器
docker ps

# 查看所有容器（包括已停止）
docker ps -a

# 查看容器 ID 列表
docker ps -aq

# 格式化输出
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### 任务 B：查看日志

```powershell
# 启动一个生成日志的容器
docker run -d --name log-test nginx

# 查看日志
docker logs log-test

# 实时跟踪日志
# docker logs -f log-test

# 查看最近 N 行
docker logs --tail 20 log-test

# 查看特定时间的日志
docker logs --since "2024-01-01" log-test

# 清理
docker stop log-test
docker rm log-test
```

### 任务 C：检查容器

```powershell
# 查看容器进程
docker top container_name

# 查看端口映射
docker port container_name

# 查看文件系统变更
docker diff container_name

# 查看详细信息
docker inspect container_name
```

---

## 练习 9.6：网络管理

**目标**：掌握 Docker 网络的创建和管理。

### 任务 A：查看网络

```powershell
# 查看网络列表
docker network ls

# 查看网络详细信息
docker network inspect bridge
```

### 任务 B：创建和使用网络

```powershell
# 创建网络
docker network create my-network

# 将容器连接到网络
docker run -d --name web --network my-network nginx
docker run -d --name db --network my-network redis

# 测试容器间通信
docker exec web ping db

# 断开容器与网络的连接
docker network disconnect my-network web

# 删除网络
# docker network rm my-network
```

---

## 练习 9.7：卷（Volume）管理

**目标**：掌握数据卷的使用和数据持久化。

### 任务 A：查看卷

```powershell
# 查看卷列表
docker volume ls

# 查看卷详细信息
# docker volume inspect my-volume

# 创建卷
docker volume create my-data

# 删除未使用的卷
docker volume prune
```

### 任务 B：使用卷

```powershell
# 使用命名卷
docker run -d --name data-container -v my-data:/app/data nginx

# 使用绑定挂载（当前目录）
docker run -d --name web -v "$(Get-Location):/usr/share/nginx/html" nginx

# 查看容器中的卷内容
docker exec data-container ls /app/data
```

---

## 练习 9.8：Docker Compose

**目标**：掌握 Docker Compose 的使用。

### 任务 A：创建 compose 文件

```powershell
# 创建项目目录
$composeDir = "$env:TEMP\compose-test"
New-Item -ItemType Directory -Path $composeDir -Force | Out-Null
Set-Location $composeDir

# 创建 docker-compose.yml
@"
version: '3.8'

services:
  web:
    image: nginx
    ports:
      - '8080:80'
    volumes:
      - ./html:/usr/share/nginx/html:ro

  redis:
    image: redis:alpine
    ports:
      - '6379:6379'
"@ | Out-File -FilePath docker-compose.yml -Encoding UTF8

# 创建 HTML 文件
New-Item -ItemType Directory -Path html -Force | Out-Null
"<h1>Hello from Docker Compose!</h1>" | Out-File -FilePath html\index.html -Encoding UTF8
```

### 任务 B：启动服务

```powershell
# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs
docker-compose logs web

# 停止服务
docker-compose down

# 清理
Set-Location $env:TEMP
Remove-Item -Path $composeDir -Recurse -Force
```

---

## 综合练习：Docker 实战

### 任务 1：搭建开发环境

```powershell
# 使用 Docker 搭建开发环境

# 1. 搭建 MySQL 数据库
docker run -d `
    --name mysql-dev `
    -e MYSQL_ROOT_PASSWORD=root123 `
    -e MYSQL_DATABASE=myapp `
    -p 3306:3306 `
    -v mysql-data:/var/lib/mysql `
    mysql:8

# 2. 查看容器状态
docker ps

# 3. 连接到数据库
# docker exec -it mysql-dev mysql -uroot -proot123

# 4. 清理
# docker stop mysql-dev
# docker rm mysql-dev
# docker volume rm mysql-data
```

### 任务 2：搭建 Node.js 开发环境

```powershell
# 创建 Node.js 开发容器
docker run -d `
    --name node-dev `
    -p 3000:3000 `
    -v "$(Get-Location):/app" `
    -w /app `
    node:18-alpine `
    sh -c "npm install && npm run dev"

# 查看日志
docker logs -f node-dev

# 进入容器
docker exec -it node-dev sh

# 清理
# docker stop node-dev
# docker rm node-dev
```

### 任务 3：容器监控

```powershell
# 查看资源使用
docker stats

# 查看所有容器统计
docker stats --all --no-stream

# 格式化显示
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

## 清理练习环境

```powershell
# 停止并删除所有测试容器
docker ps -a --filter "name=test" -q | ForEach-Object {
    docker stop $_ 2>$null
    docker rm $_ 2>$null
}

# 清理未使用的资源
docker system prune

Write-Output "Docker 练习环境已清理"
```

---

## 下一步

完成以上练习后，继续学习 [Lesson 10: 脚本编程与自动化](../10_scripting/课程说明.md)
