# 命令行（CLI）完全指南

> 从零开始，系统掌握命令行工具，成为真正的效率大师

---

## 课程概述

本课程面向希望深度掌握命令行的开发者，系统讲解从 **Shell 基础概念** 到 **远程操作与自动化** 的完整知识体系。命令行是开发者的"第二双手"，掌握它能让你在日常工作中效率倍增。

### 前置知识

- 会使用电脑（鼠标、键盘、文件资源管理器）
- 有基本的英文阅读能力（命令多为英文）

### 学习目标

- 理解 Shell 的工作原理和设计哲学
- 熟练使用 PowerShell 进行日常操作
- 掌握文件系统的高效操作技巧
- 学会使用管道组合命令处理复杂任务
- 掌握 Git 和 Docker 命令行操作
- 能够编写自动化脚本提升工作效率

### 当前环境

```
Shell 类型: PowerShell
PowerShell 版本: 5.1
系统: Windows 10/11 (win32 10.0.26200)
可用命令数: 1721+
```

---

## 知识体系全景图

```
命令行知识体系
│
├── 1. Shell 基础层
│   ├── Shell 是什么？
│   ├── 命令行 vs 图形界面
│   ├── Shell 的工作原理
│   └── PowerShell / CMD / Bash 区别
│
├── 2. PowerShell 核心语法
│   ├── cmdlets（命令命名规范）
│   ├── 对象 vs 文本
│   ├── 变量与数据类型
│   ├── 运算符与表达式
│   └── 帮助系统（Get-Help）
│
├── 3. 文件系统操作
│   ├── 目录导航（cd, pwd, pushd/popd）
│   ├── 文件查看（ls, Get-ChildItem）
│   ├── 文件创建、复制、移动、删除
│   ├── 路径处理（相对路径、绝对路径）
│   └── 通配符与过滤器
│
├── 4. 文本处理与管道
│   ├── 管道（|）的工作原理
│   ├── Select-Object / Where-Object / ForEach-Object
│   ├── 文本搜索（Select-String / grep）
│   ├── 格式化输出（Format-Table, Format-List）
│   └── 常用文本工具（sort, uniq, head, tail）
│
├── 5. 环境变量与配置
│   ├── 环境变量概念
│   ├── PATH 的作用与管理
│   ├── PowerShell 配置文件
│   ├── profile 脚本
│   └── 永久配置 vs 会话配置
│
├── 6. 进程与服务管理
│   ├── 查看进程（Get-Process）
│   ├── 启动/停止/重启进程
│   ├── 后台任务与任务计划
│   └── Windows 服务管理（services.msc）
│
├── 7. 网络操作
│   ├── 测试连接（Test-Connection / ping）
│   ├── 查看网络配置（ipconfig）
│   ├── 端口与连接（netstat）
│   ├── DNS 查询（nslookup）
│   └── 下载文件（Invoke-WebRequest）
│
├── 8. Git 命令行
│   ├── Git 基础概念（仓库、提交、分支）
│   ├── 日常工作流（add, commit, push, pull）
│   ├── 分支管理（branch, checkout, merge）
│   ├── 查看历史（log, diff）
│   └── 远程操作（remote, fetch, pull request）
│
├── 9. Docker 命令行
│   ├── 容器 vs 镜像 vs Dockerfile
│   ├── 镜像操作（pull, images, rmi）
│   ├── 容器操作（run, ps, exec, logs）
│   ├── Docker Compose
│   └── 构建自己的镜像
│
├── 10. 脚本编程与自动化
│   ├── 脚本文件（.ps1）
│   ├── 条件语句（if, switch）
│   ├── 循环语句（for, foreach, while）
│   ├── 函数定义
│   ├── 错误处理
│   └── 计划任务（Task Scheduler）
│
├── 11. 开发工作流实战
│   ├── Python 环境管理（cli 版）
│   ├── Node.js 环境管理
│   ├── 项目初始化脚手架
│   └── 一键部署脚本
│
└── 12. 远程操作与 SSH
    ├── SSH 基础
    ├── SCP 文件传输
    ├── 远程命令执行
    └── SSH 密钥管理
```

---

## 课程目录

### [Lesson 0: PowerShell 语法结构（进阶/可选前置）](./lessons/00_syntax_structure/README.md)
> 900+ 行完整语法参考，适合需要系统复习 PowerShell 语法的学习者

### [Lesson 1: Shell 基础概念](./lessons/01_shell_basics/README.md)
> 理解 Shell 是什么，它如何工作，以及为什么命令行如此强大

- Shell 的定义与作用
- 命令行与图形界面的对比
- Windows 上的 Shell 选项（CMD, PowerShell, Windows Terminal）
- Shell 的工作流程解析

### [Lesson 2: PowerShell 核心语法](./lessons/02_powershell_core/README.md)
> 掌握 PowerShell 的独特语法，理解其"面向对象"的命令行哲学

- cmdlets 命名规范（Verb-Noun）
- PowerShell 的对象模型
- 变量与数据类型
- 运算符与表达式
- 帮助系统（Get-Help）

### [Lesson 3: 文件系统操作](./lessons/03_filesystem/README.md)
> 高效管理文件和目录，掌握路径处理的精髓

- 目录导航
- 文件查看与搜索
- 文件的增删改查
- 通配符与过滤器
- 路径解析

### [Lesson 4: 文本处理与管道](./lessons/04_text_processing/README.md)
> 理解管道的威力，掌握数据处理的组合技巧

- 管道的基础
- 核心 cmdlet（Select, Where, ForEach, Sort, Group）
- 文本搜索与正则表达式
- 格式化输出
- 实用文本工具组合

### [Lesson 5: 环境变量与配置](./lessons/05_env_config/README.md)
> 理解环境变量，学会配置你的 Shell 环境

- 环境变量的概念
- PATH 的作用与管理
- PowerShell profile 配置
- 永久配置与会话配置

### [Lesson 6: 进程与服务管理](./lessons/06_process_management/README.md)
> 监控系统资源，管理运行中的程序

- 进程查看与筛选
- 启动、停止、重启进程
- 后台任务管理
- Windows 服务管理

### [Lesson 7: 网络操作](./lessons/07_network_ops/README.md)
> 网络诊断、文件下载、端口测试

- 网络配置查看
- 连接测试
- 端口与网络连接
- Web 请求与下载
- DNS 查询

### [Lesson 8: Git 命令行](./lessons/08_git_cli/README.md)
> 从图形界面升级到纯命令行的 Git 操作

- Git 基础命令
- 分支管理
- 远程操作
- 高级技巧

### [Lesson 9: Docker 命令行](./lessons/09_docker_cli/README.md)
> 容器化时代必备技能

- 镜像管理
- 容器生命周期
- Docker Compose
- 日志与调试

### [Lesson 10: 脚本编程与自动化](./lessons/10_scripting/README.md)
> 用脚本自动化重复工作，让电脑为你打工

- 脚本基础
- 控制流语句
- 函数与模块化
- 错误处理
- 计划任务

### [Lesson 11: 开发工作流实战](./lessons/11_dev_workflow/README.md)
> 用命令行串联开发全流程

- Python CLI 工具链
- 项目脚手架
- 一键环境搭建
- CI/CD 集成

### [Lesson 12: 远程操作与 SSH](./lessons/12_remote_ssh/README.md)
> 远程服务器管理，安全的远程操作

- SSH 基础
- 密钥管理
- SCP / SFTP 文件传输
- 远程命令执行

---

## 推荐学习路径

```
入门路线（按顺序学习）:
Lesson 0（可选语法复习）→ Lesson 1 → Lesson 2 → Lesson 3 → Lesson 4 → Lesson 5
    ↓
按需深入:
  想用 Git  → Lesson 8
  想用 Docker → Lesson 9
  想自动化   → Lesson 10
  想远程连接 → Lesson 12
```

```
进阶路线:
Lesson 6（进程管理）→ Lesson 7（网络）→ Lesson 10（脚本）
→ Lesson 11（开发工作流）→ Lesson 12（远程）
```

---

## 常见命令速查卡

### 目录操作
```powershell
Get-Location          # 显示当前目录（pwd）
Set-Location 路径     # 切换目录（cd）
Get-ChildItem         # 列出文件（ls/dir）
Push-Location 路径   # 进入目录并记录位置（pushd）
Pop-Location          # 返回上一个位置（popd）
```

### 文件操作
```powershell
New-Item -ItemType File 文件名    # 创建文件
Copy-Item 源 目标                  # 复制（cp）
Move-Item 源 目标                  # 移动（mv）
Remove-Item 文件                   # 删除（rm/del）
Rename-Item 旧名 新名             # 重命名
```

### 查找与搜索
```powershell
Get-ChildItem -Recurse -Filter "*.py"    # 递归查找
Select-String -Pattern "关键词" 文件      # 搜索文件内容
Get-Process                                # 查看进程
Get-Service                                # 查看服务
```

### 管道组合
```powershell
Get-Process | Where-Object CPU -gt 10
Get-ChildItem | Where-Object Length -gt 1MB
Get-Service | Select-Object Name, Status
Get-ChildItem | Sort-Object Length -Descending | Select-Object -First 10
```

### 系统信息
```powershell
$PSVersionTable              # PowerShell 版本
Get-Host                     # 主机信息
Get-ComputerInfo             # 系统详细信息
Test-NetConnection 主机名    # 网络测试
```

---

## 你的当前环境信息

```
Shell: PowerShell
版本: 5.1.26100.7920
可用命令数: 1721+
工作目录: E:\code\Projects\learn
当前用户: 22271
操作系统: Windows 10 (win32 10.0.26200)
```
