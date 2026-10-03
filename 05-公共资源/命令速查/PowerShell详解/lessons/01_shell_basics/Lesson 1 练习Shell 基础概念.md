> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Lesson 1 练习：Shell 基础概念

## 练习说明

本练习覆盖 Lesson 1 的所有核心概念。建议先通读 Lesson 1 教程，再完成以下练习。

---

## 练习 1.1：环境探索

**目标**：熟悉 PowerShell 环境，查看系统信息。

```powershell
# 1. 查看 PowerShell 版本信息
$PSVersionTable

# 2. 查看当前会话的详细信息
Get-Host

# 3. 查看当前用户
$env:USERNAME

# 4. 查看当前工作目录
Get-Location
```

**你的任务**：运行以上命令，记录输出，截图或复制关键信息。

---

## 练习 1.2：cmdlets 基础

**目标**：理解 cmdlets 命名规范，区分不同命令。

### 任务 A：查看系统信息

```powershell
# 查看当前日期和时间
Get-Date

# 查看日历
Get-Calendar  # 如果可用

# 查看帮助信息（最常用的 cmdlet）
Get-Help Get-Process
```

### 任务 B：探索命令命名规律

```powershell
# 1. 查找所有以 "Get-" 开头的命令
Get-Command -Verb Get | Measure-Object

# 2. 查找所有以 "-Item" 结尾的命令
Get-Command -Noun Item | Select-Object -First 10

# 3. 查找所有与 "Process" 相关的命令
Get-Command -Noun Process
```

---

## 练习 1.3：别名使用

**目标**：理解别名机制，熟练使用常用别名。

### 任务 A：查看别名

```powershell
# 查看所有别名
Get-Alias

# 查找特定别名的来源
Get-Alias -Definition Get-ChildItem

# 查找别名对应的原命令
Get-Alias -Name ls
Get-Alias -Name dir
Get-Alias -Name cd
Get-Alias -Name pwd
```

### 任务 B：使用不同方式执行同一操作

```powershell
# 使用完整命令
Get-ChildItem C:\Windows

# 使用 CMD 别名
dir C:\Windows

# 使用 Bash 别名（如果可用）
ls C:\Windows

# 使用 PowerShell 别名
gci C:\Windows
```

---

## 练习 1.4：帮助系统

**目标**：掌握获取帮助的技巧。

### 任务 A：使用 Get-Help

```powershell
# 查看命令基本帮助
Get-Help Get-Process

# 查看详细帮助
Get-Help Get-Process -Detailed

# 查看完整帮助（包含所有参数说明）
Get-Help Get-Process -Full

# 只查看示例
Get-Help Get-Process -Examples

# 在线查看最新文档
Get-Help Get-Process -Online
```

### 任务 B：更新本地帮助

```powershell
# 检查是否需要更新帮助（可能需要管理员权限）
Update-Help -WhatIf

# 如果想更新（谨慎使用，可能耗时较长）
# Update-Help -Module * -Force
```

---

## 练习 1.5：输出与格式化

**目标**：掌握不同的输出方式。

### 任务 A：基本输出

```powershell
# Write-Output（通过管道输出）
Write-Output "Hello, World!"

# Write-Host（直接显示，不经过管道）
Write-Host "Direct output" -ForegroundColor Green

# 使用变量
$name = "PowerShell"
Write-Output "Learning $name"
```

### 任务 B：格式化输出

```powershell
# 格式化表格
Get-Process | Select-Object Name, CPU, WorkingSet | Format-Table -AutoSize

# 格式化列表
Get-Process | Select-Object -First 1 | Format-List *

# 格式化宽表
Get-Process | Format-Wide Name -Column 3
```

---

## 练习 1.6：输入与交互

**目标**：学会在脚本中使用用户输入。

### 任务 A：读取用户输入

```powershell
# 简单输入
$name = Read-Host "请输入你的名字"
Write-Output "你好，$name！"

# 带默认值的输入
$answer = Read-Host "确认删除？(Y/N)"
```

### 任务 B：显示确认对话框

```powershell
# 确认对话框
$confirm = [System.Windows.Forms.MessageBox]::Show(
    "确定要继续吗？",
    "确认",
    [System.Windows.Forms.MessageBoxButtons]::YesNo,
    [System.Windows.Forms.MessageBoxIcon]::Question
)
```

---

## 练习 1.7：重定向与管道

**目标**：掌握输出重定向和管道连接。

### 任务 A：输出重定向

```powershell
# 重定向标准输出到文件
Write-Output "Test line 1" > test_output.txt
Write-Output "Test line 2" >> test_output.txt

# 查看文件内容
Get-Content test_output.txt

# 重定向错误输出
# 命令 2> error.txt

# 同时重定向输出和错误
# 命令 > output.txt 2>&1
```

### 任务 B：管道连接

```powershell
# 管道示例：筛选进程
Get-Process | Where-Object { $_.CPU -gt 0 } | Select-Object -First 5

# 管道示例：排序和筛选
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 5 Name, WorkingSet
```

---

## 练习 1.8：通配符与特殊字符

**目标**：掌握通配符匹配。

### 任务 A：使用通配符

```powershell
# * 匹配任意字符
Get-ChildItem C:\Windows\*.exe

# ? 匹配单个字符
Get-ChildItem C:\Windows\???.exe

# [] 匹配括号内字符
Get-ChildItem C:\Windows\[abc]*.dll
```

### 任务 B：特殊变量

```powershell
# 当前管道对象
1..5 | ForEach-Object { $_ * 2 }

# 脚本根目录
$PSScriptRoot

# 当前工作目录
$PWD

# 用户主目录
$HOME

# 环境变量
$env:PATH -split ";"
```

---

## 练习 1.9：常用快捷键

**目标**：熟练使用快捷键提升效率。

### 任务 A：练习以下快捷键

| 快捷键 | 功能 | 练习次数 |
|--------|------|----------|
| Tab | 自动补全命令 | 10 次 |
| ↑ / ↓ | 浏览历史命令 | 10 次 |
| Ctrl+C | 取消当前命令 | 2 次 |
| Ctrl+L | 清屏 | 2 次 |
| Ctrl+A / Ctrl+E | 光标跳到行首/行尾 | 10 次 |
| Ctrl+U / Ctrl+K | 删除光标前/后内容 | 5 次 |
| Ctrl+R | 搜索历史 | 3 次 |

### 任务 B：查看历史命令

```powershell
# 查看所有历史
Get-History

# 查看最近 10 条
Get-History | Select-Object -Last 10

# 搜索包含特定命令的历史
Get-History | Where-Object { $_.CommandLine -match "git" }
```

---

## 综合练习：环境信息报告

**目标**：综合运用本课所学知识，生成一份环境信息报告。

### 任务：编写 PowerShell 脚本

```powershell
# 生成环境信息报告
@"
========================================
PowerShell 环境信息报告
生成时间: $(Get-Date)
========================================

1. PowerShell 版本
------------------
PSVersion: $($PSVersionTable.PSVersion)
Edition: $($PSVersionTable.PSEdition)

2. 当前用户信息
--------------
用户名: $env:USERNAME
用户目录: $HOME

3. 系统信息
-----------
计算机名: $env:COMPUTERNAME
操作系统: $($PSVersionTable.Platform)

4. 可用命令统计
---------------
"@

$cmdCount = (Get-Command | Measure-Object).Count
$cmdCount | Out-String

@"

5. 常用别名
-----------
Get-Alias | Select-Object -First 10 | Format-Table Name, Definition -AutoSize

========================================
报告结束
========================================
"@
```

### 扩展任务

1. 将以上脚本保存为 `env-report.ps1`
2. 执行脚本并将输出保存到文件：`.\env-report.ps1 > report.txt`
3. 修改脚本，添加更多系统信息（如内存、磁盘空间等）

---

## 答案参考

### 练习 1.1 参考输出格式

```
PSVersion      PSEdition      Platform       OS
-----------    ---------      --------       --
5.1.26100     Desktop        Win32NT        10.0.26100
```

### 练习 1.3 参考

| 别名 | 原命令 |
|------|--------|
| ls | Get-ChildItem |
| dir | Get-ChildItem |
| cd | Set-Location |
| pwd | Get-Location |
| cp | Copy-Item |
| rm | Remove-Item |

---

## 下一步

完成以上练习后，继续学习 [Lesson 2: PowerShell 核心语法](../02_powershell_core/课程说明.md)
