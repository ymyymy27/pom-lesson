> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Docker 语法结构参考

> 本文档系统梳理 Docker 的三层语法：**CLI 命令行**、**Dockerfile**、**Compose YAML**。建议配合 `01-第1课Docker 基础 - 核心概念与安装.md` 一起阅读。

---

## 1. 整体架构：三层语法的关系

```
┌─────────────────────────────────────────────────────────┐
│  1. Dockerfile          →  定义「如何构建镜像」           │
│     FROM / RUN / COPY / CMD ...                         │
├─────────────────────────────────────────────────────────┤
│  2. docker CLI 命令      →  操作「镜像 + 容器」           │
│     docker build / run / ps / exec ...                  │
├─────────────────────────────────────────────────────────┤
│  3. docker-compose.yml  →  编排「多个容器 + 网络 + 卷」   │
│     services / volumes / networks ...                   │
└─────────────────────────────────────────────────────────┘
```

**流水线：**

```
Dockerfile → docker build → 镜像 → docker run → 容器
```

多容器场景下，Compose 把多个 `docker run` 写进一个 YAML 文件，用 `docker compose up` 一次性启动。

---

## 2. CLI 命令行语法结构

### 2.1 通用格式

```bash
docker [全局选项] <子命令> [子命令选项] [参数...]
```

**示例拆解：**

```bash
docker run -d -p 8080:80 --name my-nginx nginx
│      │   │  │  │           │              │
│      │   │  │  │           │              └── 参数：镜像名
│      │   │  │  │           └── 长选项：容器名
│      │   │  │  └── 短选项：端口映射
│      │   │  └── 短选项：后台运行
│      │   └── 子命令：创建并运行容器
│      └── 主程序
└── docker 客户端
```

### 2.2 子命令分类

| 类别 | 常见子命令 | 作用 |
|------|-----------|------|
| **容器生命周期** | `run`, `start`, `stop`, `restart`, `rm`, `pause` | 创建、启停、删除容器 |
| **容器信息** | `ps`, `logs`, `inspect`, `stats`, `top` | 查看状态、日志、详情 |
| **容器交互** | `exec`, `attach`, `cp` | 进入容器、复制文件 |
| **镜像管理** | `images`, `pull`, `push`, `build`, `rmi`, `tag` | 拉取、构建、推送、删除镜像 |
| **系统管理** | `system prune`, `system df`, `info`, `version` | 清理、磁盘占用、环境信息 |
| **Compose（v2）** | `compose up`, `compose down`, `compose ps` | 多容器编排 |

### 2.3 选项的两种写法

```bash
# 短选项（单字母，可合并）
docker run -dit nginx
# 等价于
docker run -d -i -t nginx

# 长选项（双横线，语义更清晰）
docker run --detach --interactive --tty nginx
```

### 2.4 镜像命名语法

```
[registry/][namespace/]repository[:tag][@digest]
```

| 部分 | 含义 | 示例 |
|------|------|------|
| `registry` | 仓库地址 | `docker.io`（默认，可省略） |
| `namespace` | 命名空间/用户名 | `library`（官方镜像默认） |
| `repository` | 镜像名 | `python`, `nginx` |
| `tag` | 版本标签 | `3.12-slim`, `latest` |
| `digest` | 内容哈希（精确锁定） | `@sha256:abc123...` |

**常见写法：**

```bash
python:3.12-slim          # 仓库:标签
nginx                     # 省略标签 → 默认 latest
myregistry.com/myapp:v1   # 私有仓库
```

**命令拆解示例：**

```bash
docker run -it python:3.12-slim python
#        ↑   ↑        ↑              ↑
#     子命令 交互   镜像:标签        覆盖 CMD 的命令

docker run -d -p 8080:80 --name my-nginx nginx
#              ↑  主机:容器  ↑ 命名      ↑ 镜像
```

### 2.5 常用参数语法详解

| 参数 | 语法 | 含义 |
|------|------|------|
| `-p` | `-p 主机端口:容器端口` | 端口映射，如 `-p 8080:80` |
| `-v` | `-v 主机路径:容器路径[:权限]` | 目录挂载，如 `-v ./data:/app/data` |
| `-e` | `-e KEY=VALUE` 或 `-e KEY` | 环境变量 |
| `--name` | `--name 容器名` | 给容器起名 |
| `-d` | 无值 | detach，后台运行 |
| `-it` | `-i` + `-t` | 交互 + 分配终端 |
| `--rm` | 无值 | 容器退出后自动删除 |
| `--restart` | `--restart always` | 重启策略 |

**端口映射记忆：** `主机端口:容器端口` —— 左边是你电脑访问的，右边是容器内部监听的。

### 2.6 读命令的万能公式

遇到任何 Docker 命令，按四步拆解：

```
1. 操作对象是谁？   →  镜像 / 容器 / 网络 / 卷
2. 做什么动作？   →  run / build / ps / exec ...
3. 有哪些选项？   →  -d, -p, -v, -e, --name ...
4. 参数是什么？   →  镜像名、容器名、命令 ...
```

**举例：**

```bash
docker exec -it test-nginx bash
# 对象：容器 test-nginx
# 动作：exec（在运行中的容器里执行命令）
# 选项：-it（交互终端）
# 参数：bash（要执行的命令）

docker build -t myapp:1.0 .
# 对象：镜像（构建产物）
# 动作：build
# 选项：-t myapp:1.0（命名标签）
# 参数：.（构建上下文目录）
```

---

## 3. Dockerfile 语法结构

### 3.1 基本规则

1. **一行一条指令**，指令名大写（约定，非强制）
2. **从上到下顺序执行**，每一层生成一个镜像层（Layer）
3. **`#` 开头是注释**
4. 分为两类指令：
   - **构建时执行**：`FROM`, `RUN`, `COPY`, `ARG` …
   - **运行时生效**：`CMD`, `ENTRYPOINT`, `EXPOSE`, `ENV` …

### 3.2 标准结构模板

```dockerfile
# ── 1. 基础层 ──
FROM python:3.12-slim          # 必须：第一条有效指令（多阶段构建除外）
LABEL maintainer="xxx"         # 元数据（可选）

# ── 2. 环境配置 ──
WORKDIR /app                   # 后续命令的工作目录
ENV PYTHONDONTWRITEBYTECODE=1  # 环境变量
ARG VERSION=1.0                # 构建参数（仅 build 时有效）

# ── 3. 依赖安装（利用缓存，先 COPY 依赖文件）──
COPY requirements.txt .
RUN pip install -r requirements.txt

# ── 4. 应用代码 ──
COPY . .

# ── 5. 运行声明 ──
EXPOSE 8000                    # 声明端口（文档作用，不自动映射）
VOLUME /data                   # 声明数据卷挂载点
CMD ["python", "app.py"]       # 容器启动默认命令
```

### 3.3 核心指令对照

| 指令 | 执行时机 | 作用 |
|------|---------|------|
| `FROM` | 构建 | 指定基础镜像，通常是第一条 |
| `WORKDIR` | 构建 | 设置工作目录，类似 `cd` |
| `COPY` | 构建 | 从宿主机复制文件到镜像 |
| `ADD` | 构建 | 类似 COPY，还支持 URL 和解压 |
| `RUN` | 构建 | 执行 shell 命令（装依赖、改配置） |
| `ENV` | 构建+运行 | 设置环境变量，会写入镜像 |
| `ARG` | 仅构建 | 构建参数，不会留在最终运行时 |
| `EXPOSE` | 声明 | 告诉使用者容器监听哪个端口 |
| `CMD` | 运行 | 默认启动命令，可被 `docker run` 覆盖 |
| `ENTRYPOINT` | 运行 | 固定入口，参数会追加而不是替换 |

### 3.4 CMD 的两种写法

```dockerfile
# Exec 形式（推荐）：JSON 数组，不经过 shell
CMD ["python", "app.py"]

# Shell 形式：经过 /bin/sh -c
CMD python app.py
```

**区别：** Exec 形式不会处理环境变量展开，信号传递更干净；Shell 形式方便写简单命令，但多一层 shell 进程。

### 3.5 CMD vs ENTRYPOINT

```dockerfile
# 场景 A：CMD 单独使用 —— 可被完全覆盖
CMD ["python", "app.py"]
# docker run myapp python -V  →  执行 python -V

# 场景 B：ENTRYPOINT + CMD —— 入口固定，CMD 当默认参数
ENTRYPOINT ["python"]
CMD ["app.py"]
# docker run myapp           →  python app.py
# docker run myapp test.py   →  python test.py
```

### 3.6 构建命令语法

```bash
docker build [选项] <构建上下文路径>

# 常用选项
-t myapp:1.0              # 给镜像打 tag
-f Dockerfile.prod         # 指定 Dockerfile 文件名
--build-arg VERSION=2.0     # 传入 ARG 参数
--no-cache                # 禁用缓存，强制重建
.                         # 构建上下文：docker 能访问的文件范围
```

### 3.7 .dockerignore

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
Dockerfile
```

---

## 4. Docker Compose 语法结构

### 4.1 文件格式

Compose 使用 **YAML**，顶层常见四个块：

```yaml
services:      # 必填：定义各个容器服务
volumes:       # 可选：命名数据卷
networks:      # 可选：自定义网络
configs/secrets:  # 可选：配置和密钥
```

### 4.2 最小可读结构

```yaml
services:
  web:                    # 服务名（也是 DNS 主机名）
    build: .              # 或 image: nginx
    ports:
      - "8000:8000"       # 注意 YAML 里字符串建议加引号
    environment:
      DATABASE_URL: postgres://db:5432/mydb
    depends_on:
      - db
    restart: always

  db:
    image: postgres:16
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:                # 声明命名卷
```

### 4.3 YAML 语法要点

```yaml
# 键值对
image: nginx

# 列表（短横线开头）
ports:
  - "8080:80"
  - "8443:443"

# 嵌套对象
build:
  context: .
  dockerfile: Dockerfile.prod
  args:
    VERSION: "1.0"

# 环境变量两种写法
environment:
  - KEY=VALUE          # 列表写法
  POSTGRES_DB: mydb     # 映射写法
```

### 4.4 常用配置项速查

| 配置项 | 作用 | 示例 |
|--------|------|------|
| `build` | 从 Dockerfile 构建 | `build: .` |
| `image` | 使用现成镜像 | `image: nginx:1.25` |
| `ports` | 端口映射 | `"8080:80"` |
| `volumes` | 数据挂载 | `./data:/app/data` |
| `environment` | 环境变量 | `DB_HOST=db` |
| `depends_on` | 启动依赖 | `- db` |
| `restart` | 重启策略 | `always` |
| `networks` | 指定网络 | `mynet` |
| `command` | 覆盖 CMD | `python app.py` |

### 4.5 Compose 命令语法

```bash
# v2（推荐，Docker Desktop 自带）
docker compose up -d          # 后台启动所有服务
docker compose down           # 停止并删除容器
docker compose ps             # 查看服务状态
docker compose logs -f web    # 实时查看 web 服务日志
docker compose build          # 重新构建镜像
docker compose restart web    # 重启单个服务

# v1（旧版，连字符）
docker-compose up -d
```

**注意：** 新版用 `docker compose`（空格），旧版用 `docker-compose`（连字符）。

---

## 5. 三层语法的对应关系

同一件事，三种写法往往等价：

| 意图 | CLI | Dockerfile | Compose |
|------|-----|-----------|---------|
| 用哪个镜像 | `docker run nginx` | `FROM nginx` | `image: nginx` |
| 端口映射 | `-p 8080:80` | `EXPOSE 80`（仅声明） | `ports: ["8080:80"]` |
| 环境变量 | `-e KEY=VAL` | `ENV KEY=VAL` | `environment: KEY=VAL` |
| 挂载目录 | `-v ./data:/app` | `VOLUME /app` | `volumes: ["./data:/app"]` |
| 启动命令 | `docker run ... cmd` | `CMD ["cmd"]` | `command: cmd` |
| 后台运行 | `-d` | — | 默认 detach（`up -d`） |
| 服务依赖 | 自定义网络 | — | `depends_on` |

**重要：** `EXPOSE` 只写在 Dockerfile 里是**声明**，真正映射端口要靠 `docker run -p` 或 Compose 的 `ports`。

---

## 6. 动手练习：语法拆解

```bash
# 练习 1：拆解这条命令
docker run -d -p 8080:80 --name my-nginx nginx
# 答案：后台运行 nginx 镜像，容器名 my-nginx，主机 8080 → 容器 80

# 练习 2：拆解这条命令
docker run -it python:3.12-slim python
# 答案：交互模式运行 python:3.12-slim，执行 python 命令

# 练习 3：这条 Dockerfile 指令什么时候执行？
# RUN pip install -r requirements.txt
# 答案：docker build 构建时执行，不是容器启动时

# 练习 4：Compose 中 web 服务如何访问 db？
# 答案：直接用服务名 db 作为主机名，如 postgres://db:5432/mydb
```

---

## 7. 小结

| 语法层 | 文件/命令 | 核心结构 |
|--------|----------|---------|
| **CLI** | 终端命令 | `docker <子命令> [选项] [参数]` |
| **Dockerfile** | 构建说明书 | `FROM → WORKDIR → COPY → RUN → CMD` |
| **Compose** | `docker-compose.yml` | `services → volumes → networks` |

**学习建议：**

1. 先熟练 CLI 结构 —— 尤其是 `docker run` 的参数组合
2. 再写 Dockerfile —— 理解 `FROM → COPY → RUN → CMD` 顺序和缓存
3. 最后用 Compose —— 把多个 `docker run` 合并成一个 YAML

---

**相关课程：**

- `01-第1课Docker 基础 - 核心概念与安装.md` —— Docker 核心概念与第一个容器
- `02-第2课镜像管理与 Dockerfile.md` —— Dockerfile 深入与镜像构建
- `03-第3课Docker Compose 多容器编排.md` —— Compose 多容器编排
