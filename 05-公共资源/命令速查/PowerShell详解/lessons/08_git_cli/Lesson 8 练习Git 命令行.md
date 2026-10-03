> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Lesson 8 练习：Git 命令行

## 练习说明

本练习覆盖 Lesson 8 的所有核心概念。建议先通读 Lesson 8 教程，再完成以下练习。

> **注意**：以下练习需要 Git 已安装。如果还没有安装，请先安装 Git。

---

## 练习 8.1：Git 首次配置

**目标**：完成 Git 的初始配置。

### 任务 A：配置用户信息

```powershell
# 设置用户名（全局）
git config --global user.name "你的名字"

# 设置邮箱（全局）
git config --global user.email "your.email@example.com"

# 验证配置
git config --list
git config user.name
git config user.email
```

### 任务 B：设置别名

```powershell
# 设置常用别名
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.lg "log --oneline --graph --all"

# 查看别名
git config --get-regexp alias
```

---

## 练习 8.2：创建仓库

**目标**：掌握 Git 仓库的创建和初始化。

### 任务 A：初始化新仓库

```powershell
# 创建练习目录
New-Item -ItemType Directory -Path "$env:TEMP\git-practice" -Force
Set-Location "$env:TEMP\git-practice"

# 初始化 Git 仓库
git init

# 查看仓库状态
git status
```

### 任务 B：创建初始文件

```powershell
# 创建 README
"# 我的第一个 Git 项目" | Out-File -FilePath README.md

# 创建 .gitignore
@"
# 临时文件
*.tmp
*.log

# 系统文件
.DS_Store
Thumbs.db
"@ | Out-File -FilePath .gitignore

# 查看状态
git status
```

---

## 练习 8.3：基本操作

**目标**：掌握 add、commit 的基本用法。

### 任务 A：添加和提交

```powershell
# 添加文件到暂存区
git add README.md
git status

# 提交
git commit -m "feat: 添加 README 文件"

# 查看日志
git log

# 使用别名（如果已设置）
git st
```

### 任务 B：修改和提交

```powershell
# 修改 README
"$(Get-Content README.md)`n`n这是我的第一个 Git 项目。" | Out-File README.md

# 查看变更
git status
git diff

# 添加变更并提交
git add .
git commit -m "docs: 更新 README 内容"
```

### 任务 C：快捷提交

```powershell
# 对于已跟踪的文件，可以直接提交（跳过 git add）
"$(Get-Content README.md)`n`n更新于: $(Get-Date)" | Out-File README.md
git commit -am "docs: 快速更新 README"
```

---

## 练习 8.4：查看历史

**目标**：掌握日志和差异查看。

### 任务 A：git log

```powershell
# 查看完整日志
git log

# 单行格式
git log --oneline

# 图形化分支
git log --oneline --graph --all

# 查看最近 N 条
git log -5

# 按作者筛选
git log --author="你的名字"

# 按日期筛选
git log --since="2024-01-01"
```

### 任务 B：git diff

```powershell
# 查看工作区与暂存区的差异
git diff

# 查看暂存区与上次提交的差异
git diff --staged
git diff --cached

# 查看工作区与特定提交的差异
git diff HEAD~1

# 比较两个提交
# git diff abc123..def456

# 只显示文件名
git diff --name-only
```

---

## 练习 8.5：分支管理

**目标**：掌握分支的创建、切换和管理。

### 任务 A：创建和切换分支

```powershell
# 列出所有分支
git branch

# 创建新分支
git branch feature-login

# 切换分支
git checkout feature-login
# 或（新版）
git switch feature-login

# 创建并切换
git checkout -b feature-dashboard
# 或
git switch -c feature-dashboard
```

### 任务 B：在分支上工作

```powershell
# 在当前分支创建新文件
"功能: 登录页面" | Out-File feature_login.txt
git add feature_login.txt
git commit -m "feat: 添加登录功能"

# 查看当前分支
git branch

# 切换回主分支
git checkout main
# 或
git switch main

# 查看分支内容
ls
```

### 任务 C：删除分支

```powershell
# 删除已合并的分支
git branch -d feature-login

# 强制删除分支
# git branch -D feature-old

# 查看所有分支（包括远程）
git branch -a
```

---

## 练习 8.6：合并分支

**目标**：掌握分支合并的方法。

### 任务 A：基本合并

```powershell
# 切换到主分支
git checkout main

# 合并功能分支
git merge feature-dashboard

# 查看日志
git log --oneline --graph --all
```

### 任务 B：解决冲突

```powershell
# 模拟冲突场景
# 1. 创建新分支
git checkout -b conflict-test

# 2. 修改同一文件
"版本1" | Out-File conflict.txt
git add conflict.txt
git commit -m "conflict-test: 版本1"

# 3. 切回主分支
git checkout main

# 4. 修改同一文件
"版本2" | Out-File conflict.txt
git add conflict.txt
git commit -m "main: 版本2"

# 5. 尝试合并（会产生冲突）
# git merge conflict-test

# 6. 解决冲突后
# git add conflict.txt
# git commit
```

---

## 练习 8.7：撤销操作

**目标**：掌握各种撤销场景的处理方法。

### 任务 A：撤销工作区修改

```powershell
# 修改文件
"新的内容" | Out-File README.md

# 撤销工作区的修改（恢复到暂存区/HEAD）
git checkout -- README.md
# 或
git restore README.md

# 验证
Get-Content README.md
```

### 任务 B：取消暂存

```powershell
# 添加文件到暂存区
git add README.md
git status

# 取消暂存
git reset HEAD README.md
# 或
git restore --staged README.md

git status
```

### 任务 C：回退提交

```powershell
# 查看提交历史
git log --oneline

# 回退到上一个提交（保留修改）
git reset HEAD~1

# 回退到上一个提交（不保留修改）
git reset --hard HEAD~1

# 回退到特定提交
# git reset --hard abc123
```

---

## 练习 8.8：储藏（Stash）

**目标**：掌握工作进度的保存和恢复。

### 任务 A：基本储藏

```powershell
# 修改文件
"临时修改" | Out-File README.md

# 保存当前进度
git stash

# 查看储藏列表
git stash list

# 恢复进度
git stash pop
```

### 任务 B：带消息的储藏

```powershell
# 保存并添加消息
git stash push -m "修复登录bug到一半"

# 查看储藏详情
git stash show
git stash show -p stash@{0}

# 应用特定储藏
git stash apply stash@{0}

# 删除储藏
git stash drop stash@{0}

# 清空所有储藏
git stash clear
```

---

## 练习 8.9：标签管理

**目标**：掌握版本标签的创建和管理。

### 任务 A：创建标签

```powershell
# 创建轻量标签
git tag v1.0.0

# 创建附注标签
git tag -a v1.1.0 -m "版本 1.1.0 发布"

# 为特定提交打标签
# git tag -a v0.9.0 abc123 -m "版本 0.9.0"

# 查看所有标签
git tag

# 查看标签详情
git show v1.0.0
```

### 任务 B：管理标签

```powershell
# 删除本地标签
git tag -d v0.9.0

# 推送标签到远程
# git push origin v1.0.0

# 推送所有标签
# git push --tags

# 删除远程标签
# git push origin --delete v1.0.0
```

---

## 综合练习：Git 工作流

### 任务 1：完整工作流程

```powershell
# 场景：开发新功能

# 1. 从 main 创建功能分支
git checkout main
git pull
git checkout -b feature-new-feature

# 2. 开发...
"新功能说明" | Out-File feature_new.txt
git add feature_new.txt
git commit -m "feat: 添加新功能"

# 3. 定期同步 main
git fetch origin
git rebase origin/main

# 4. 功能完成，合并到 main
git checkout main
git merge feature-new-feature

# 5. 删除功能分支
git branch -d feature-new-feature

# 6. 推送到远程
# git push origin main
```

### 任务 2：批量查看仓库状态

```powershell
# 查看多个仓库状态的脚本
function Get-GitStatus {
    param([string]$BasePath = $PWD)

    Write-Output "===== Git 仓库状态检查 ====="
    Write-Output "检查目录: $BasePath"
    Write-Output ""

    Get-ChildItem -Directory -Path $BasePath | ForEach-Object {
        $gitDir = Join-Path $_.FullName ".git"
        if (Test-Path $gitDir) {
            Push-Location $_.FullName

            Write-Host "仓库: " -NoNewline
            Write-Host $_.Name -ForegroundColor Cyan

            # 获取分支
            $branch = git branch --show-current
            if (-not $branch) { $branch = "(无分支)" }
            Write-Host "  分支: $branch"

            # 获取状态
            $status = git status --short
            if ($status) {
                Write-Host "  状态: 有未提交的更改" -ForegroundColor Yellow
                $status | Select-Object -First 3 | ForEach-Object {
                    Write-Host "    $_"
                }
            } else {
                Write-Host "  状态: 干净" -ForegroundColor Green
            }

            Write-Output ""

            Pop-Location
        }
    }

    Write-Output "检查完成"
}

# 使用
# Get-GitStatus -BasePath "C:\Projects"
```

---

## 扩展挑战

### 挑战：Git 搜索

```powershell
# 在提交历史中搜索
# git log -S "搜索的字符串"

# 在文件中搜索
# git grep "搜索的字符串"

# 查找特定日期的提交
# git log --after="2024-01-01" --before="2024-01-31"

# 查找修改了特定文件的提交
# git log --oneline -- filename.txt
```

---

## 清理练习环境

```powershell
# 练习结束后清理
Set-Location $env:TEMP
# Remove-Item -Path "$env:TEMP\git-practice" -Recurse -Force
Write-Output "练习环境已清理"
```

---

## 下一步

完成以上练习后，继续学习 [Lesson 9: Docker 命令行](../09_docker_cli/课程说明.md)
