# Lesson 11 练习：开发工作流实战

## 练习说明

本练习覆盖 Lesson 11 的所有核心概念。建议先通读 Lesson 11 教程，再完成以下练习。

---

## 练习 11.1：Python 环境管理

**目标**：掌握 Python 虚拟环境和包管理。

### 任务 A：检查 Python 环境

```powershell
# 检查 Python 版本
python --version
py --list

# 检查 pip
pip --version
```

### 任务 B：创建和使用虚拟环境

```powershell
# 创建练习目录
$venvDir = "$env:TEMP\python-practice"
New-Item -ItemType Directory -Path $venvDir -Force | Out-Null
Set-Location $venvDir

# 创建虚拟环境
python -m venv .venv

# 查看虚拟环境
ls .venv

# 激活虚拟环境
# & "$venvDir\.venv\Scripts\Activate.ps1"
```

### 任务 C：安装和管理包

```powershell
# （在已激活的虚拟环境中）
# pip install requests
# pip install --upgrade pip
# pip freeze > requirements.txt
# pip install -r requirements.txt
```

---

## 练习 11.2：Node.js 环境管理

**目标**：掌握 Node.js 和 npm 的基本使用。

### 任务 A：检查 Node.js 环境

```powershell
# 检查 Node.js 版本
node --version

# 检查 npm 版本
npm --version

# 检查 npx
npx --version
```

### 任务 B：初始化项目

```powershell
# 创建练习目录
$nodeDir = "$env:TEMP\nodejs-practice"
New-Item -ItemType Directory -Path $nodeDir -Force | Out-Null
Set-Location $nodeDir

# 初始化项目
npm init -y

# 查看 package.json
Get-Content package.json
```

### 任务 C：安装和使用包

```powershell
# 安装依赖
# npm install express

# 安装开发依赖
# npm install -D jest

# 全局安装工具
# npm install -g typescript

# 查看已安装的包
# npm list
# npm list --depth=0
```

---

## 练习 11.3：项目脚手架脚本

**目标**：创建自动化项目初始化脚本。

### 任务 A：创建 Python 项目脚手架

```powershell
# 创建 Python 项目脚手架脚本
@"
param(
    [Parameter(Mandatory=`$true)]
    [string]`$ProjectName
)

`$projectPath = Join-Path `$PWD `$ProjectName

if (Test-Path `$projectPath) {
    Write-Error "项目目录已存在: `$(`$projectPath)"
    exit 1
}

Write-Output "===== 创建 Python 项目: `$(`$ProjectName) ====="

# 创建目录
New-Item -ItemType Directory -Path `$projectPath -Force | Out-Null
Set-Location `$projectPath

# 创建目录结构
New-Item -ItemType Directory -Path "src" -Force | Out-Null
New-Item -ItemType Directory -Path "tests" -Force | Out-Null
New-Item -ItemType Directory -Path "docs" -Force | Out-Null

# 创建虚拟环境
Write-Output "创建虚拟环境..."
python -m venv .venv

# 创建 README
@"
# `$(`$ProjectName)

## 快速开始

\`\`\`bash
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
\`\`\`

## 项目结构

- `src/` - 源代码
- `tests/` - 测试代码
- `docs/` - 文档
"@ | Out-File -FilePath README.md -Encoding UTF8

# 创建 requirements.txt
"pytest>=7.0.0" | Out-File -FilePath requirements.txt -Encoding UTF8

# 创建 .gitignore
@"
__pycache__/
*.py[cod]
*$py.class
.env
.venv/
*.egg-info/
dist/
build/
"@ | Out-File -FilePath .gitignore -Encoding UTF8

# 创建 __init__.py
"" | Out-File -FilePath "src\__init__.py" -Encoding UTF8

# 创建主模块
@"
def main():
    print("Hello from `$(`$ProjectName)!")

if __name__ == "__main__":
    main()
"@ | Out-File -FilePath "src\main.py" -Encoding UTF8

# 创建测试文件
@"
import pytest
from src.main import main

def test_main():
    main()  # 测试不报错即可
"@ | Out-File -FilePath "tests\test_main.py" -Encoding UTF8

Write-Output ""
Write-Output "项目创建完成！"
Write-Output "目录: `$(`$projectPath)"
Write-Output ""
Write-Output "下一步："
Write-Output "  cd `$(`$ProjectName)"
Write-Output "  .\.venv\Scripts\Activate.ps1"
Write-Output "  pip install -r requirements.txt"
"@ | Out-File -FilePath "$env:TEMP\python-scaffold.ps1" -Encoding UTF8

# 执行脚本创建项目
& "$env:TEMP\python-scaffold.ps1" -ProjectName "my_python_app"
```

### 任务 B：创建 Node.js 项目脚手架

```powershell
# 创建 Node.js 项目脚手架脚本
@"
param(
    [Parameter(Mandatory=`$true)]
    [string]`$ProjectName
)

`$projectPath = Join-Path `$PWD `$ProjectName

if (Test-Path `$projectPath) {
    Write-Error "项目目录已存在: `$(`$projectPath)"
    exit 1
}

Write-Output "===== 创建 Node.js 项目: `$(`$ProjectName) ====="

# 创建目录
New-Item -ItemType Directory -Path `$projectPath -Force | Out-Null
Set-Location `$projectPath

# 创建目录结构
New-Item -ItemType Directory -Path "src" -Force | Out-Null
New-Item -ItemType Directory -Path "tests" -Force | Out-Null
New-Item -ItemType Directory -Path "dist" -Force | Out-Null

# 初始化 npm
npm init -y

# 修改 package.json
`$package = Get-Content package.json | ConvertFrom-Json
`$package.name = `$ProjectName
`$package.version = "1.0.0"
`$package.description = "`$(`$ProjectName) - A new project"
`$package.main = "dist/index.js"
`$package.scripts = @{
    start = "node dist/index.js"
    dev = "node --watch dist/index.js"
    build = "tsc"
    test = "jest"
    lint = "eslint src/"
}
`$package | ConvertTo-Json | Out-File -FilePath package.json -Encoding UTF8

# 创建 README
@"
# `$(`$ProjectName)

## 安装

\`\`\`bash
npm install
\`\`\`

## 运行

\`\`\`bash
npm run dev
\`\`\`

## 构建

\`\`\`bash
npm run build
\`\`\`
"@ | Out-File -FilePath README.md -Encoding UTF8

# 创建 .gitignore
@"
node_modules/
dist/
.env
*.log
.DS_Store
coverage/
"@ | Out-File -FilePath .gitignore -Encoding UTF8

# 创建示例代码
@"
console.log("Hello from `$(`$ProjectName)!");

function greet(name) {
    return `\`Hello, \`\${name}!\`;
}

console.log(greet("World"));
"@ | Out-File -FilePath "src\index.js" -Encoding UTF8

Write-Output ""
Write-Output "项目创建完成！"
Write-Output "目录: `$(`$projectPath)"
Write-Output ""
Write-Output "下一步："
Write-Output "  cd `$(`$ProjectName)"
Write-Output "  npm install"
Write-Output "  npm run dev"
"@ | Out-File -FilePath "$env:TEMP\nodejs-scaffold.ps1" -Encoding UTF8

# 执行脚本创建项目
& "$env:TEMP\nodejs-scaffold.ps1" -ProjectName "my_node_app"
```

---

## 练习 11.4：Git 工作流自动化

**目标**：掌握 Git 钩子和自动化脚本。

### 任务 A：Git 状态检查脚本

```powershell
# 创建批量检查 Git 仓库的脚本
@"
param(
    [string]`$Path = `$PWD
)

`$ErrorActionPreference = "SilentlyContinue"

Write-Output "===== Git 仓库状态检查 ====="
Write-Output "检查目录: `$(`$Path)"
Write-Output ""

`$repos = @()

Get-ChildItem -Directory -Path `$Path | ForEach-Object {
    `$gitDir = Join-Path `$_.FullName ".git"
    if (Test-Path `$gitDir) {
        `$repos += `$_.FullName
    }
}

if (`$repos.Count -eq 0) {
    Write-Output "未找到 Git 仓库"
    exit 0
}

Write-Output "找到 `$(`$repos.Count) 个 Git 仓库"
Write-Output ""

foreach (`$repo in `$repos) {
    Push-Location `$repo

    Write-Host "仓库: " -NoNewline
    Write-Host `$repo -ForegroundColor Cyan

    `$branch = git branch --show-current
    if (-not `$branch) { `$branch = "(detached)" }
    Write-Output "  分支: `$(`$branch)"

    `$status = git status --short
    if (`$status) {
        Write-Output "  状态: 有未提交的更改" -ForegroundColor Yellow
        `$status | Select-Object -First 3 | ForEach-Object {
            Write-Output "    `$(`$_)"
        }
        if (`$status.Count -gt 3) {
            Write-Output "    ... 还有 `$(`$status.Count - 3) 个更改"
        }
    } else {
        Write-Output "  状态: 干净" -ForegroundColor Green
    }

    `$unpushed = git log --oneline origin/`$(`$branch)..HEAD 2>`$null
    if (`$unpushed) {
        Write-Output "  未推送: `$(`$unpushed.Count) 个提交" -ForegroundColor Yellow
    }

    Write-Output ""

    Pop-Location
}

Write-Output "检查完成"
"@ | Out-File -FilePath "$env:TEMP\git-status-all.ps1" -Encoding UTF8

# 执行
& "$env:TEMP\git-status-all.ps1" -Path "$env:TEMP"
```

### 任务 B：清理 Git 分支

```powershell
# 创建清理已合并分支的脚本
@"
`$ErrorActionPreference = "Stop"

Write-Output "===== 清理 Git 分支 ====="

# 获取当前分支
`$currentBranch = git branch --show-current
Write-Output "当前分支: `$(`$currentBranch)"
Write-Output ""

# 获取已合并到 main 的分支
`$mainBranches = "main", "master", "develop"
foreach (`$main in `$mainBranches) {
    `$merged = git branch --merged `$main 2>`$null | Where-Object { `$_ -notmatch `$main }
    if (`$merged) {
        Write-Output "已合并到 `$main 的分支:"
        `$merged | ForEach-Object {
            Write-Output "  - `$(`$_.Trim())"
        }
    }
}

Write-Output ""
`$confirm = Read-Host "是否删除这些分支？(y/n)"
if (`$confirm -eq "y") {
    `$merged | ForEach-Object {
        `$branch = `$_.Trim()
        git branch -d `$branch
        Write-Output "已删除: `$(`$branch)"
    }
} else {
    Write-Output "已取消"
}
"@ | Out-File -FilePath "$env:TEMP\git-clean-branches.ps1" -Encoding UTF8
```

---

## 练习 11.5：部署脚本

**目标**：创建自动化部署脚本。

### 任务 A：Git 部署脚本

```powershell
# 创建简单的 Git 部署脚本
@"
param(
    [Parameter()]
    [string]`$Branch = "main",

    [Parameter()]
    [switch]`$Force
)

`$ErrorActionPreference = "Stop"

Write-Output "===== Git 部署脚本 ====="
Write-Output "目标分支: `$(`$Branch)"
Write-Output ""

# 检查是否有未提交的更改
`$status = git status --porcelain
if (`$status) {
    Write-Warning "有未提交的更改："
    `$status | ForEach-Object { Write-Output "  `$(`$_)" }
    Write-Output ""

    if (-not `$Force) {
        `$confirm = Read-Host "是否继续？(y/n)"
        if (`$confirm -ne "y") {
            Write-Output "已取消"
            exit 0
        }
    }
}

# 获取当前分支
`$currentBranch = git branch --show-current
Write-Output "当前分支: `$(`$currentBranch)"

if (`$currentBranch -ne `$Branch) {
    Write-Output "切换到分支: `$(`$Branch)"
    git checkout `$Branch
}

# 拉取最新代码
Write-Output "拉取最新代码..."
if (`$Force) {
    git pull --rebase origin `$Branch --force
} else {
    git pull origin `$Branch
}

# 查看状态
`$status = git status --short
if (`$status) {
    Write-Output "更新后状态："
    `$status | ForEach-Object { Write-Output "  `$(`$_)" }
}

Write-Output ""
Write-Output "===== 部署完成 ====="
"@ | Out-File -FilePath "$env:TEMP\git-deploy.ps1" -Encoding UTF8
```

---

## 综合练习：开发环境工具包

### 任务：创建一站式开发环境脚本

```powershell
# 创建开发环境工具包
@"
param(
    [Parameter()]
    [ValidateSet("status", "init", "backup", "clean")]
    [string]`$Action = "status"
)

`$ErrorActionPreference = "SilentlyContinue"

switch (`$Action) {
    "status" {
        Write-Output "===== 开发环境状态 ====="
        Write-Output ""

        Write-Output "--- Git 状态 ---"
        `$gitStatus = git status --porcelain
        if (`$gitStatus) {
            Write-Output "有未提交的更改" -ForegroundColor Yellow
            `$gitStatus | Select-Object -First 5 | ForEach-Object { Write-Output "  `$(`$_)" }
        } else {
            Write-Output "工作区干净" -ForegroundColor Green
        }

        `$branch = git branch --show-current
        Write-Output "当前分支: `$(`$branch)"

        Write-Output ""
        Write-Output "--- Node.js ---"
        Write-Output "Node: $(node --version 2>`$null)"
        Write-Output "npm: $(npm --version 2>`$null)"

        Write-Output ""
        Write-Output "--- Python ---"
        Write-Output "Python: $(python --version 2>`$null)"

        Write-Output ""
        Write-Output "--- Docker ---"
        `$dockerStatus = docker ps 2>`$null
        if (`$dockerStatus) {
            `$containerCount = (`$dockerStatus | Measure-Object).Lines - 1
            Write-Output "运行中的容器: `$(`$containerCount)" -ForegroundColor Green
        } else {
            Write-Output "Docker 未运行" -ForegroundColor Yellow
        }
    }

    "init" {
        Write-Output "===== 初始化开发环境 ====="
        Write-Output ""

        Write-Output "检查 Python..."
        if (Get-Command python -ErrorAction SilentlyContinue) {
            Write-Output "  Python: $(python --version)"
        } else {
            Write-Output "  Python: 未安装" -ForegroundColor Red
        }

        Write-Output ""
        Write-Output "检查 Node.js..."
        if (Get-Command node -ErrorAction SilentlyContinue) {
            Write-Output "  Node.js: $(node --version)"
            Write-Output "  npm: $(npm --version)"
        } else {
            Write-Output "  Node.js: 未安装" -ForegroundColor Red
        }

        Write-Output ""
        Write-Output "检查 Docker..."
        if (Get-Command docker -ErrorAction SilentlyContinue) {
            Write-Output "  Docker: 已安装"
        } else {
            Write-Output "  Docker: 未安装" -ForegroundColor Yellow
        }

        Write-Output ""
        Write-Output "检查 Git..."
        if (Get-Command git -ErrorAction SilentlyContinue) {
            Write-Output "  Git: $(git --version)"
        } else {
            Write-Output "  Git: 未安装" -ForegroundColor Red
        }
    }

    "backup" {
        Write-Output "===== 备份开发配置 ====="
        Write-Output "此功能需要指定备份目标"
        Write-Output "示例：dev-tools.ps1 -Action backup -BackupPath C:\Backups"
    }

    "clean" {
        Write-Output "===== 清理开发环境 ====="
        Write-Output ""

        # 清理临时文件
        Write-Output "清理临时文件..."
        Get-ChildItem -Path `$env:TEMP -Filter "*.tmp" -Recurse -ErrorAction SilentlyContinue |
            Remove-Item -Force -ErrorAction SilentlyContinue

        # 清理 node_modules
        Write-Output "查找 node_modules 目录..."
        `$nodeModules = Get-ChildItem -Path . -Filter "node_modules" -Recurse -Directory -ErrorAction SilentlyContinue
        if (`$nodeModules) {
            Write-Output "  找到 `$(`$nodeModules.Count) 个 node_modules"
            `$confirm = Read-Host "是否删除？(y/n)"
            if (`$confirm -eq "y") {
                `$nodeModules | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
                Write-Output "已删除"
            }
        }

        Write-Output ""
        Write-Output "清理完成"
    }
}
"@ | Out-File -FilePath "$env:TEMP\dev-tools.ps1" -Encoding UTF8

# 测试
Write-Output "=== 测试 status ==="
& "$env:TEMP\dev-tools.ps1" -Action status

Write-Output ""
Write-Output "=== 测试 init ==="
& "$env:TEMP\dev-tools.ps1" -Action init
```

---

## 清理练习环境

```powershell
# 清理练习文件
Remove-Item "$env:TEMP\python-scaffold.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\nodejs-scaffold.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\git-*.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\dev-tools.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\python-practice" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\nodejs-practice" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\my_python_app" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\my_node_app" -Recurse -Force -ErrorAction SilentlyContinue

Write-Output "练习环境已清理"
```

---

## 下一步

完成以上练习后，继续学习 [Lesson 12: 远程操作与 SSH](../12_remote_ssh/README.md)
