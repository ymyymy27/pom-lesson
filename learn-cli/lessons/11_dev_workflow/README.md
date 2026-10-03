# Lesson 11: 开发工作流实战

> 用命令行串联开发全流程，从项目初始化到一键部署

---

## 11.1 Python 开发环境管理

### Python 版本与虚拟环境

```powershell
# 检查 Python 环境
python --version
py --list

# 创建虚拟环境
cd my-project
python -m venv .venv

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 在虚拟环境中安装依赖
pip install langchain langchain-openai
pip install -r requirements.txt

# 生成 requirements.txt
pip freeze > requirements.txt

# 快速初始化新项目
mkdir new-project
cd new-project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
```

### pipx（CLI 工具管理）

```powershell
# 安装 pipx（全局 CLI 工具管理）
pip install pipx
pipx ensurepath

# 全局安装 CLI 工具
pipx install httpie      # HTTP 客户端
pipx install black       # 代码格式化
pipx install mypy        # 类型检查
pipx install pre-commit  # Git hooks

# 运行 CLI 工具
http GET https://api.github.com
black .
mypy src/

# 升级 CLI 工具
pipx upgrade black
pipx upgrade-all
```

### Python 脚本工作流

```powershell
# 创建项目结构
mkdir my-python-project
cd my-python-project
mkdir src tests

# 创建虚拟环境
python -m venv .venv

# 激活并安装基础包
.\.venv\Scripts\Activate.ps1
pip install pytest

# 创建 requirements.txt
pip freeze > requirements.txt

# 创建 pyproject.toml（现代方式）
@"
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-package"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []

[tool.black]
line-length = 100
"@ | Out-File -FilePath pyproject.toml -Encoding UTF8

# 安装为开发包
pip install -e .
```

---

## 11.2 Node.js 开发环境

### nvm-windows（Node 版本管理）

```powershell
# 安装 nvm-windows
# 下载: https://github.com/coreybutler/nvm-windows/releases

# 常用命令
nvm list available          # 查看可用版本
nvm install lts             # 安装最新 LTS
nvm install 20             # 安装特定版本
nvm list                    # 查看已安装
nvm use 20                  # 切换版本
nvm uninstall 18            # 卸载版本
```

### npm 常用命令

```powershell
# 初始化项目
npm init
npm init -y                 # 快速初始化

# 安装依赖
npm install                 # 从 package.json 安装
npm install express         # 安装包
npm install -D prettier     # 安装开发依赖
npm install -g typescript   # 全局安装
npm install @types/node    # 安装类型定义

# package.json 脚本
# "scripts": {
#     "start": "node index.js",
#     "dev": "nodemon index.js",
#     "test": "jest",
#     "build": "tsc",
#     "lint": "eslint ."
# }

# 运行脚本
npm run dev
npm test

# 更新依赖
npm outdated               # 查看可更新的包
npm update                 # 更新所有
npm update express         # 更新特定包
npm install express@latest # 升级到最新

# 清理
npm ci                     # 清理安装（从 package-lock.json）
npm cache clean --force    # 清理缓存
```

---

## 11.3 项目脚手架

### 快速创建项目脚本

```powershell
# new-project.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectName,

    [Parameter()]
    [ValidateSet("python", "nodejs", "dotnet")]
    [string]$Type = "python"
)

$projectPath = Join-Path $PWD $ProjectName

Write-Output "创建项目: $ProjectName (类型: $Type)"
Write-Output "路径: $projectPath"

# 创建目录
New-Item -ItemType Directory -Path $projectPath -Force | Out-Null
Set-Location $projectPath

switch ($Type) {
    "python" {
        # Python 项目初始化
        python -m venv .venv
        @"
# 项目: $ProjectName

## 快速开始
\`\`\`powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
\`\`\`
"@ | Out-File -FilePath README.md -Encoding UTF8
        "pytest>=7.0" | Out-File -FilePath requirements-dev.txt -Encoding UTF8
        Write-Output "Python 项目创建完成"
    }

    "nodejs" {
        # Node.js 项目初始化
        npm init -y
        @"
# $ProjectName

\`\`\`bash
npm install
npm run dev
\`\`\`
"@ | Out-File -FilePath README.md -Encoding UTF8
        Write-Output "Node.js 项目创建完成"
    }

    "dotnet" {
        dotnet new console -n $ProjectName
        Write-Output ".NET 项目创建完成"
    }
}

# 创建通用文件
".gitignore" | Out-File -FilePath .gitignore -Encoding UTF8
".vscode/settings.json" | New-Item -ItemType Directory -Force | Out-Null
@"
{
    ""python.defaultInterpreterPath"": ""`${workspaceFolder}/.venv/Scripts/python.exe""
}
"@ | Out-File -FilePath .vscode/settings.json -Encoding UTF8

Write-Output "项目创建完成！"
Set-Location $projectPath
```

---

## 11.4 一键环境搭建

### 通用环境安装脚本

```powershell
# install-dev-env.ps1
param(
    [Parameter()]
    [switch]$Python,

    [Parameter()]
    [switch]$Node,

    [Parameter()]
    [switch]$Docker,

    [Parameter()]
    [switch]$All
)

Write-Output "===== 开发环境一键安装 ====="
Write-Output ""

# 安装 Chocolatey（包管理器）
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Output "安装 Chocolatey..."
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

if ($All -or $Python) {
    Write-Output "安装 Python 开发环境..."
    choco install python --version=3.11.9 -y
    Write-Output "Python 安装完成"
}

if ($All -or $Node) {
    Write-Output "安装 Node.js 开发环境..."
    choco install nodejs.install --version=20 -y
    Write-Output "Node.js 安装完成"
}

if ($All -or $Docker) {
    Write-Output "安装 Docker Desktop..."
    choco install docker-desktop -y
    Write-Output "Docker Desktop 安装完成，请重启电脑"
}

Write-Output ""
Write-Output "===== 安装完成 ====="

# 使用示例
@"
使用示例：
  .\install-dev-env.ps1 -Python -Node
  .\install-dev-env.ps1 -All
"@
```

### 项目依赖安装脚本

```powershell
# setup-project.ps1
param(
    [Parameter()]
    [string]$ProjectPath = "."
)

$projectPath = Resolve-Path $ProjectPath
Set-Location $projectPath

Write-Output "===== 项目环境初始化 ====="
Write-Output "项目路径: $projectPath"
Write-Output ""

# Python 项目
if (Test-Path "requirements.txt") {
    Write-Output "[Python] 检测到 requirements.txt"
    if (Test-Path ".venv") {
        Write-Output "[Python] .venv 已存在，跳过创建"
    } else {
        Write-Output "[Python] 创建虚拟环境..."
        python -m venv .venv
    }

    Write-Output "[Python] 激活虚拟环境..."
    & "$projectPath\.venv\Scripts\Activate.ps1"

    Write-Output "[Python] 安装依赖..."
    pip install --upgrade pip
    pip install -r requirements.txt

    if (Test-Path "requirements-dev.txt") {
        Write-Output "[Python] 安装开发依赖..."
        pip install -r requirements-dev.txt
    }
}

# Node.js 项目
if (Test-Path "package.json") {
    Write-Output "[Node.js] 检测到 package.json"
    Write-Output "[Node.js] 安装依赖..."
    npm install

    if (Test-Path "package-lock.json") {
        Write-Output "[Node.js] 使用锁定版本安装..."
        npm ci
    }
}

# Docker Compose
if (Test-Path "docker-compose.yml") {
    Write-Output "[Docker] 检测到 docker-compose.yml"
    Write-Output "[Docker] 启动服务..."
    docker-compose up -d
}

Write-Output ""
Write-Output "===== 初始化完成 ====="
```

---

## 11.5 Git 工作流自动化

### Git 钩子脚本

```powershell
# .git/hooks/pre-commit
@"
#!/usr/bin/env pwsh
`$ErrorActionPreference = "Stop"

Write-Output "运行预提交检查..."

# 运行测试
`$testResult = & pytest tests/ --tb=short 2>&1
if (`$LASTEXITCODE -ne 0) {
    Write-Error "测试失败，请修复后重试"
    exit 1
}

# 代码格式化检查
`$formatResult = & black --check src/
if (`$LASTEXITCODE -ne 0) {
    Write-Warning "代码格式不符合规范"
    Write-Output "运行 'black src/' 自动格式化"
}

Write-Output "预提交检查通过！"
"@ | Out-File -FilePath ".git/hooks/pre-commit" -Encoding UTF8
```

### 常用 Git 脚本

```powershell
# git-status-all.ps1 - 查看所有仓库状态
@"
`$ErrorActionPreference = "SilentlyContinue"

Write-Output "===== Git 仓库状态检查 ====="
Write-Output ""

Get-ChildItem -Directory | ForEach-Object {
    `$gitDir = Join-Path `$_.FullName ".git"
    if (Test-Path `$gitDir) {
        Set-Location `$_.FullName
        Write-Output "仓库: `$($_.Name)" -ForegroundColor Cyan
        git status --short
        `$unpushed = git log --oneline origin/main..HEAD 2>`$null
        if (`$unpushed) {
            Write-Output "  未推送的提交: `$(`$unpushed.Count)" -ForegroundColor Yellow
        }
        Write-Output ""
    }
}

Set-Location $originalPath
Write-Output "检查完成"
"@

# git-clean-branches.ps1 - 清理已合并的分支
@"
`$ErrorActionPreference = "Stop"

Write-Output "===== 清理已合并的 Git 分支 ====="

# 获取当前分支
`$currentBranch = git branch --show-current
Write-Output "当前分支: `$currentBranch"
Write-Output ""

# 获取已合并到 main 的分支
`$mergedBranches = git branch --merged main | Where-Object { `$_ -notmatch "main|master|develop" }

if (-not `$mergedBranches) {
    Write-Output "没有需要清理的分支"
    exit 0
}

Write-Output "以下分支将被删除:"
`$mergedBranches | ForEach-Object { Write-Output "  - `$_" }

`$confirm = Read-Host "确认删除？(y/n)"
if (`$confirm -eq "y") {
    `$mergedBranches | ForEach-Object {
        `$branch = `$_.Trim()
        Write-Output "删除: `$branch"
        git branch -d `$branch
    }
    Write-Output "清理完成"
} else {
    Write-Output "已取消"
}
"@
```

---

## 11.6 一键部署脚本

### Docker 部署脚本

```powershell
# deploy.ps1
param(
    [Parameter()]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment = "dev",

    [Parameter()]
    [switch]$Rebuild,

    [Parameter()]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Output "===== 开始部署 - $Environment ====="

# 读取环境变量
$envFile = ".env.$Environment"
if (Test-Path $envFile) {
    Write-Output "加载环境变量: $envFile"
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^(.+?)=(.*)$") {
            [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

# 拉取最新代码
Write-Output "拉取最新代码..."
git pull

# 构建镜像
if ($Rebuild) {
    Write-Output "重新构建镜像..."
    docker-compose build --force-rm
} else {
    Write-Output "构建镜像..."
    docker-compose build
}

# 停止旧容器
Write-Output "停止旧容器..."
docker-compose down

# 启动新容器
Write-Output "启动服务..."
docker-compose up -d

# 等待服务启动
Write-Output "等待服务启动..."
Start-Sleep -Seconds 5

# 检查状态
Write-Output "检查服务状态..."
docker-compose ps

# 查看日志
Write-Output "最近日志:"
docker-compose logs --tail 20

Write-Output ""
Write-Output "===== 部署完成 ====="
```

### 本地开发服务器脚本

```powershell
# dev-server.ps1
param(
    [Parameter()]
    [int]$Port = 8000,

    [Parameter()]
    [switch]$Reload,

    [Parameter()]
    [switch]$Debug
)

$ErrorActionPreference = "Stop"

Write-Output "===== 启动开发服务器 ====="
Write-Output "端口: $Port"
Write-Output ""

# 检查虚拟环境
if (-not (Test-Path ".venv")) {
    Write-Output "创建虚拟环境..."
    python -m venv .venv
}

Write-Output "激活虚拟环境..."
& "$PWD\.venv\Scripts\Activate.ps1"

# 安装依赖
Write-Output "安装依赖..."
pip install -r requirements.txt 2>$null
pip install -r requirements-dev.txt 2>$null

# 构建前端（如果有）
if (Test-Path "package.json") {
    Write-Output "安装前端依赖..."
    npm install
    Write-Output "构建前端..."
    npm run build
}

# 启动后端
Write-Output "启动开发服务器..."
if ($Reload) {
    $args = @("-m", "uvicorn", "main:app", "--reload", "--port", $Port)
} else {
    $args = @("-m", "uvicorn", "main:app", "--port", $Port)
}

if ($Debug) {
    $args += "--log-level", "debug"
}

Write-Output "命令: python $($args -join ' ')"
& python @args
```

---

## 11.7 CI/CD 概念

### GitHub Actions 工作流

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m venv .venv
          .venv/bin/pip install -r requirements.txt
          .venv/bin/pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          .venv/bin/pytest --cov=src tests/
      
      - name: Lint
        run: |
          .venv/bin/black --check src/
          .venv/bin/mypy src/

  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .
      
      - name: Push to registry
        run: |
          echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker push myapp:${{ github.sha }}
```

---

## 11.8 实用工作流脚本

### 批量操作

```powershell
# batch-process.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$Folder,

    [Parameter()]
    [int]$DaysOld = 7
)

$folder = Get-Item $Folder
$cutoffDate = (Get-Date).AddDays(-$DaysOld)

Write-Output "===== 批量处理任务 ====="
Write-Output "文件夹: $($folder.FullName)"
Write-Output "处理 $DaysOld 天前的文件"
Write-Output ""

# 查找文件
$files = Get-ChildItem -Path $folder -Recurse -File |
    Where-Object { $_.LastWriteTime -lt $cutoffDate }

Write-Output "找到 $($files.Count) 个文件需要处理"

$files | ForEach-Object -Parallel {
    $file = $_
    Write-Output "处理: $($file.Name)"

    # 示例处理：压缩旧文件
    $archiveName = "$($file.BaseName)_$(Get-Date -Format 'yyyyMMdd')$($file.Extension)"
    Compress-Archive -Path $file.FullName -DestinationPath "$($file.DirectoryName)\$archiveName" -Force
    Remove-Item $file.FullName -Force

    Write-Output "  已压缩并删除: $($file.Name)"
} -ThrottleLimit 4

Write-Output ""
Write-Output "批量处理完成"
```

### 项目报告生成

```powershell
# project-report.ps1
param(
    [Parameter()]
    [string]$OutputPath = "project-report.html"
)

$projectPath = $PWD

$report = @"
<!DOCTYPE html>
<html>
<head>
    <title>项目报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        .stat { display: inline-block; margin: 10px; padding: 20px; background: #f0f0f0; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>项目报告</h1>
    <p>生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</p>

    <h2>统计信息</h2>
    <div class="stat">
        <strong>文件总数</strong><br>
        $(@(Get-ChildItem -Path $projectPath -Recurse -File).Count)
    </div>
    <div class="stat">
        <strong>代码行数</strong><br>
        $((Get-ChildItem -Path $projectPath -Recurse -Include *.py,*.js,*.ts | Get-Content | Measure-Object -Line).Lines)
    </div>
    <div class="stat">
        <strong>目录数</strong><br>
        $(@(Get-ChildItem -Path $projectPath -Recurse -Directory).Count)
    </div>

    <h2>Git 状态</h2>
"@

# Git 信息
if (Test-Path ".git") {
    $branch = git branch --show-current
    $status = git status --short
    $commits = git log --oneline -5

    $report += @"
    <p><strong>当前分支:</strong> $branch</p>
    <p><strong>未提交的更改:</strong> $($status.Count)</p>
    <h3>最近提交</h3>
    <pre>$commits</pre>
"@
} else {
    $report += "<p>不是 Git 仓库</p>"
}

$report += @"
</body>
</html>
"@

$report | Out-File -FilePath $OutputPath -Encoding UTF8
Write-Output "报告已生成: $OutputPath"
Start-Process $OutputPath
```

---

## 课后练习

1. 在 `study/` 目录创建一个 Python 项目的初始化脚本
2. 创建一个一键安装所有开发工具的脚本
3. 创建一个 Git 仓库状态批量检查脚本
4. 创建一个 Docker Compose 项目的部署脚本
5. 创建一个项目报告生成脚本

---

## 下一步

→ [Lesson 12: 远程操作与 SSH](../12_remote_ssh/README.md)
