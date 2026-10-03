> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 01 节：CI/CD 概念与 GitHub Actions

## 一、什么是 CI/CD？

| 概念 | 全称 | 说明 |
|------|------|------|
| **CI** | Continuous Integration（持续集成） | 代码推送后自动运行测试，确保代码质量 |
| **CD** | Continuous Delivery（持续交付） | 测试通过后自动构建，随时可部署 |
| **CD** | Continuous Deployment（持续部署） | 测试通过后自动部署到生产环境 |

```
开发者 Push 代码
    ↓
CI：自动运行测试 + 代码检查
    ↓ 通过
CD：自动构建 Docker 镜像
    ↓
CD：自动部署到服务器
    ↓
用户访问最新版本
```

### 1.1 CI/CD 流水线

```
┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐
│ Push │ → │ Lint │ → │ Test │ → │Build │ → │Deploy│
│ 代码 │   │ 检查 │   │ 测试 │   │ 构建 │   │ 部署 │
└──────┘   └──────┘   └──────┘   └──────┘   └──────┘
```

---

## 二、GitHub Actions 入门

GitHub Actions 是 GitHub 内置的 CI/CD 平台，通过 YAML 文件定义工作流。

### 2.1 核心概念

| 概念 | 说明 |
|------|------|
| **Workflow** | 工作流，一个 YAML 文件定义一个工作流 |
| **Event** | 触发事件（push、pull_request、schedule） |
| **Job** | 工作，一个 Workflow 包含多个 Job |
| **Step** | 步骤，一个 Job 包含多个 Step |
| **Action** | 可复用的步骤（如 checkout、setup-python） |
| **Runner** | 执行环境（ubuntu-latest、windows-latest） |

### 2.2 文件位置

```
项目根目录/
└── .github/
    └── workflows/
        ├── ci.yml          # 持续集成（测试）
        ├── cd.yml          # 持续部署
        └── codeql.yml      # 代码安全扫描
```

---

## 三、第一个 Workflow

```yaml
# .github/workflows/ci.yml
name: CI

# 触发条件
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # ==================== 后端测试 ====================
  backend-test:
    name: Backend Tests
    runs-on: ubuntu-latest
    
    # 服务容器（测试用的数据库和 Redis）
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: testdb
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      # 1. 检出代码
      - name: Checkout code
        uses: actions/checkout@v4

      # 2. 设置 Python
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      # 3. 安装依赖
      - name: Install dependencies
        working-directory: ./backend
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      # 4. 代码检查
      - name: Lint with flake8
        working-directory: ./backend
        run: |
          pip install flake8
          flake8 apps/ --max-line-length=120 --exclude=migrations

      # 5. 运行测试
      - name: Run tests
        working-directory: ./backend
        env:
          DATABASE_URL: postgres://testuser:testpass@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key
          DEBUG: 'True'
        run: |
          pytest -v --cov=apps --cov-report=xml

      # 6. 上传覆盖率报告
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml

  # ==================== 前端测试 ====================
  frontend-test:
    name: Frontend Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Lint
        working-directory: ./frontend
        run: npm run lint

      - name: Type check
        working-directory: ./frontend
        run: npx tsc --noEmit

      - name: Run tests
        working-directory: ./frontend
        run: npm run test:run

      - name: Build
        working-directory: ./frontend
        run: npm run build
```

---

## 四、Workflow 触发条件

```yaml
on:
  # 推送到指定分支
  push:
    branches: [main, develop]
    paths:
      - 'backend/**'       # 只有后端代码变化时触发
      - '.github/workflows/ci.yml'

  # Pull Request
  pull_request:
    branches: [main]

  # 定时任务（每天凌晨 2 点）
  schedule:
    - cron: '0 2 * * *'

  # 手动触发
  workflow_dispatch:
    inputs:
      environment:
        description: '部署环境'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

  # 其他 Workflow 完成后
  workflow_run:
    workflows: ["CI"]
    types: [completed]
```

---

## 五、Secrets 管理

在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：

```
DOCKER_USERNAME        — Docker Hub 用户名
DOCKER_PASSWORD        — Docker Hub 密码
SERVER_HOST            — 服务器 IP
SERVER_USER            — SSH 用户名
SSH_PRIVATE_KEY        — SSH 私钥
DEPLOY_PATH            — 部署路径
SECRET_KEY             — Django SECRET_KEY
POSTGRES_PASSWORD      — 数据库密码
```

```yaml
# 在 Workflow 中使用
steps:
  - name: Login to Docker Hub
    uses: docker/login-action@v3
    with:
      username: ${{ secrets.DOCKER_USERNAME }}
      password: ${{ secrets.DOCKER_PASSWORD }}
```

---

## 六、状态徽章

在 README.md 中添加构建状态：

```markdown
![CI](https://github.com/<user>/<repo>/actions/workflows/ci.yml/badge.svg)
```

---

## 七、练习

1. 在项目中创建 `.github/workflows/ci.yml`
2. 配置后端测试 Job：安装依赖 → Lint → pytest
3. 配置前端测试 Job：安装依赖 → Lint → 类型检查 → 测试 → 构建
4. 推送代码到 GitHub，查看 Actions 执行结果
5. 在 GitHub Secrets 中配置敏感信息
6. 在 README 中添加 CI 状态徽章
