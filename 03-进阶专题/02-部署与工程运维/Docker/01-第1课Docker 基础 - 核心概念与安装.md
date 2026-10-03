> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第1课：Docker 基础 - 核心概念与安装

## 1. Docker 是什么？

### 一句话解释
**Docker 就是"应用打包机"** —— 把你的代码、依赖、环境全部打包成一个盒子，在任何电脑上都能一样运行。

### 类比理解
| 日常概念 | Docker 概念 |
|---------|------------|
| 快递箱（标准化包装） | **容器**（Container） |
| 货物清单 | **Dockerfile**（构建说明） |
| 快递模板（可以复制多份） | **镜像**（Image） |
| 快递仓库 | **仓库**（Registry / Docker Hub） |

### 解决了什么问题？

```
没有 Docker：
  开发者：在我电脑上能跑啊！
  运维：服务器上跑不了...
  原因：Python 版本不同、依赖没装、系统配置不一样...

有了 Docker：
  开发者：打包成 Docker 镜像
  运维：docker run 一条命令搞定
  结果：在哪都一样运行
```

### Docker vs 虚拟机

```
虚拟机：                        Docker：
┌───────────┐                  ┌───────────┐
│   App A   │                  │   App A   │
├───────────┤                  ├───────────┤
│  Guest OS │ ← 每个都要装系统  │  依赖库    │ ← 共享主机内核
├───────────┤                  └─────┬─────┘
│ Hypervisor│                        │
├───────────┤                  ┌─────┴─────┐
│  Host OS  │                  │ Docker引擎 │
└───────────┘                  ├───────────┤
                               │  Host OS  │
启动：分钟级                    └───────────┘
大小：GB 级                     启动：秒级
                               大小：MB 级
```

| 对比 | 虚拟机 | Docker |
|------|--------|--------|
| 启动速度 | 分钟 | 秒 |
| 占用空间 | GB | MB |
| 性能 | 有损耗 | 接近原生 |
| 隔离性 | 强（完整OS） | 较强（共享内核） |
| 适用场景 | 完全隔离 | 应用部署 |

---

## 2. 安装 Docker

### Windows

```
1. 确保开启 WSL2：
   - 设置 → 应用 → 可选功能 → 更多Windows功能
   - 勾选"适用于Linux的Windows子系统"和"虚拟机平台"
   - 重启

2. 下载 Docker Desktop：
   https://www.docker.com/products/docker-desktop

3. 安装并重启

4. 验证：
   docker --version
   docker run hello-world
```

### Mac

```bash
# 下载 Docker Desktop
# https://www.docker.com/products/docker-desktop

# 或用 Homebrew
brew install --cask docker

# 验证
docker --version
docker run hello-world
```

### Linux (Ubuntu)

```bash
# 安装
sudo apt update
sudo apt install docker.io docker-compose -y

# 启动
sudo systemctl start docker
sudo systemctl enable docker

# 免 sudo 使用（可选）
sudo usermod -aG docker $USER
# 重新登录生效

# 验证
docker --version
docker run hello-world
```

---

## 3. 核心概念

### 三大核心

```
┌──────────────────────────────────────────────────┐
│                 Docker Hub (仓库)                  │
│     存放公开镜像：python, nginx, postgres...      │
│                    ↕ push/pull                    │
├──────────────────────────────────────────────────┤
│              镜像（Image）                         │
│     只读模板，包含代码+依赖+配置                   │
│     类似"安装光盘"                                │
│                    ↓ docker run                   │
├──────────────────────────────────────────────────┤
│              容器（Container）                     │
│     镜像的运行实例，可以有多个                     │
│     类似"安装后运行的软件"                        │
└──────────────────────────────────────────────────┘
```

**镜像 vs 容器：**
- **镜像**：类（Class） → 定义（只读）
- **容器**：实例（Instance） → 运行中的进程

一个镜像可以创建多个容器，就像一个类可以创建多个对象。

### Dockerfile

Dockerfile 是构建镜像的"说明书"。

```dockerfile
# 基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "app.py"]
```

---

## 4. 第一个容器

### 4.1 运行 hello-world

```bash
docker run hello-world
```

输出解释：
```
1. Docker 在本地找 hello-world 镜像
2. 没找到 → 从 Docker Hub 下载
3. 用镜像创建容器
4. 容器运行，输出消息
5. 容器退出
```

### 4.2 运行 Python

```bash
# 运行 Python 容器（交互模式）
docker run -it python:3.12-slim python
# 进入 Python 交互环境
# >>> print("Hello from Docker!")
# >>> exit()

# 运行单条命令
docker run python:3.12-slim python -c "print('Hello Docker!')"
```

### 4.3 运行 Nginx

```bash
# 后台运行 Nginx（-d = detach 后台）
docker run -d -p 8080:80 --name my-nginx nginx

# 浏览器打开 http://localhost:8080 看到 Nginx 欢迎页

# 停止并删除
docker stop my-nginx
docker rm my-nginx
```

### docker run 常用参数

| 参数 | 含义 | 示例 |
|------|------|------|
| `-d` | 后台运行 | `docker run -d nginx` |
| `-p` | 端口映射 | `-p 8080:80`（主机:容器） |
| `--name` | 容器命名 | `--name my-app` |
| `-it` | 交互模式 | `docker run -it ubuntu bash` |
| `-v` | 挂载目录 | `-v ./data:/app/data` |
| `-e` | 环境变量 | `-e DB_HOST=localhost` |
| `--rm` | 退出后自动删除 | `docker run --rm python` |
| `--restart` | 重启策略 | `--restart always` |

---

## 5. 基本管理命令

```bash
# === 容器操作 ===
docker ps                      # 查看运行中的容器
docker ps -a                   # 查看所有容器（含停止的）
docker start 容器名             # 启动
docker stop 容器名              # 停止
docker restart 容器名           # 重启
docker rm 容器名                # 删除
docker rm $(docker ps -aq)     # 删除所有停止的容器

# === 镜像操作 ===
docker images                  # 查看本地镜像
docker pull python:3.12        # 拉取镜像
docker rmi 镜像名               # 删除镜像
docker image prune             # 清理无用镜像

# === 查看信息 ===
docker logs 容器名              # 查看日志
docker logs -f 容器名           # 实时查看日志
docker inspect 容器名           # 查看详细信息
docker stats                   # 实时资源使用

# === 进入容器 ===
docker exec -it 容器名 bash    # 进入运行中的容器
docker exec -it 容器名 sh      # 如果没有 bash
```

---

## 6. 动手练习

```bash
# 1. 运行 hello-world
docker run hello-world

# 2. 运行 Python 容器，打印版本
docker run --rm python:3.12-slim python --version

# 3. 后台运行 Nginx，映射到 8080 端口
docker run -d -p 8080:80 --name test-nginx nginx
# 浏览器打开 http://localhost:8080

# 4. 查看运行中的容器
docker ps

# 5. 查看 Nginx 日志
docker logs test-nginx

# 6. 进入 Nginx 容器
docker exec -it test-nginx bash
# ls /usr/share/nginx/html/
# exit

# 7. 停止并删除
docker stop test-nginx
docker rm test-nginx

# 8. 查看本地镜像
docker images
```

---

## 7. 小结

| 概念 | 说明 |
|------|------|
| **镜像（Image）** | 只读模板，包含代码和依赖 |
| **容器（Container）** | 镜像的运行实例 |
| **Dockerfile** | 构建镜像的说明书 |
| **Docker Hub** | 公共镜像仓库 |
| `docker run` | 创建并运行容器 |
| `docker ps` | 查看容器 |
| `docker images` | 查看镜像 |

---

**下一课：** `02-第2课镜像管理与 Dockerfile.md` - 镜像管理与 Dockerfile
