# Lesson 10 练习：脚本编程与自动化

## 练习说明

本练习覆盖 Lesson 10 的所有核心概念。建议先通读 Lesson 10 教程，再完成以下练习。

---

## 练习 10.1：脚本基础

**目标**：掌握脚本文件的创建和执行。

### 任务 A：创建第一个脚本

```powershell
# 创建脚本文件
@"
# 我的第一个 PowerShell 脚本
Write-Output "Hello, PowerShell!"
Write-Output "当前时间: $(Get-Date)"
"@ | Out-File -FilePath "$env:TEMP\hello.ps1" -Encoding UTF8

# 执行脚本
& "$env:TEMP\hello.ps1"

# 使用点号执行（在同一作用域）
. "$env:TEMP\hello.ps1"
```

### 任务 B：检查执行策略

```powershell
# 查看当前执行策略
Get-ExecutionPolicy

# 查看详细策略信息
Get-ExecutionPolicy -List

# 设置为 RemoteSigned（允许本地脚本）
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 临时绕过策略执行
# PowerShell -ExecutionPolicy Bypass -File script.ps1
```

---

## 练习 10.2：参数传递

**目标**：掌握脚本参数的使用方法。

### 任务 A：基础参数

```powershell
# 创建带参数的脚本 param-script.ps1
@"
param(
    [string]`$Name = "World",
    [int]`$Age = 18
)

Write-Output "你好，`$Name！"
Write-Output "你的年龄是 `$Age 岁。"
"@ | Out-File -FilePath "$env:TEMP\param-script.ps1" -Encoding UTF8

# 执行
& "$env:TEMP\param-script.ps1" -Name "张三" -Age 25
& "$env:TEMP\param-script.ps1"
```

### 任务 B：强制参数和验证

```powershell
# 创建带参数验证的脚本
@"
param(
    [Parameter(Mandatory=`$true)]
    [string]`$Username,

    [Parameter(Mandatory=`$true)]
    [ValidateRange(0, 150)]
    [int]`$Age,

    [ValidateSet("male", "female", "other")]
    [string]`$Gender = "other"
)

Write-Output "用户: `$Username"
Write-Output "年龄: `$Age"
Write-Output "性别: `$Gender"
"@ | Out-File -FilePath "$env:TEMP\validate-script.ps1" -Encoding UTF8

# 测试
& "$env:TEMP\validate-script.ps1" -Username "张三" -Age 25 -Gender male
```

---

## 练习 10.3：错误处理

**目标**：掌握 try/catch 的使用。

### 任务 A：基本错误处理

```powershell
# 创建带错误处理的脚本
@"
`$ErrorActionPreference = "Stop"

try {
    Write-Output "尝试执行可能失败的代码..."

    # 模拟可能失败的代码
    `$result = 10 / 0
    Write-Output "这行不会执行"

} catch {
    Write-Output "捕获到错误: `$($_.Exception.Message)"

} finally {
    Write-Output "清理代码（无论成功或失败都会执行）"
}
"@ | Out-File -FilePath "$env:TEMP\error-handling.ps1" -Encoding UTF8

& "$env:TEMP\error-handling.ps1"
```

### 任务 B：错误处理策略

```powershell
# 创建测试错误处理的脚本
@"
# 测试不同的错误处理策略

# 1. 忽略错误继续执行
Write-Output "=== 测试 SilentlyContinue ==="
`$result = Get-Content "nonexistent.txt" -ErrorAction SilentlyContinue
Write-Output "继续执行..."

# 2. 停止执行
Write-Output ""
Write-Output "=== 测试 Stop ==="
try {
    Get-Content "nonexistent.txt" -ErrorAction Stop
} catch {
    Write-Output "捕获错误: `$($_.Exception.Message)"
}

# 3. 检查命令结果
Write-Output ""
Write-Output "=== 测试 $? ==="
Get-Content "nonexistent.txt"
if (`$?) {
    Write-Output "命令成功"
} else {
    Write-Output "命令失败，退出码: `$LASTEXITCODE"
}
"@ | Out-File -FilePath "$env:TEMP\error-test.ps1" -Encoding UTF8

& "$env:TEMP\error-test.ps1"
```

---

## 练习 10.4：函数进阶

**目标**：掌握函数的参数和返回值。

### 任务 A：管道函数

```powershell
# 创建管道函数
@"
function Get-Square {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline=`$true)]
        [int]`$Number
    )

    process {
        `$Number * `$Number
    }
}

function Get-Cube {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline=`$true)]
        [int]`$Number
    )

    process {
        `$Number * `$Number * `$Number
    }
}

# 测试
Write-Output "1..5 的平方："
1..5 | Get-Square

Write-Output ""
Write-Output "1..5 的立方："
1..5 | Get-Cube
"@ | Out-File -FilePath "$env:TEMP\pipeline-function.ps1" -Encoding UTF8

& "$env:TEMP\pipeline-function.ps1"
```

### 任务 B：返回多个值

```powershell
# 创建返回哈希表的函数
@"
function Get-ProcessStats {
    param([string]`$ProcessName = "powershell")

    `$procs = Get-Process -Name `$ProcessName -ErrorAction SilentlyContinue

    if (`$procs) {
        return @{
            Count = `$procs.Count
            TotalMemory = (`$procs | Measure-Object WorkingSet -Sum).Sum
            MaxCPU = (`$procs | Measure-Object CPU -Maximum).Maximum
        }
    } else {
        return @{
            Count = 0
            TotalMemory = 0
            MaxCPU = 0
        }
    }
}

# 调用函数
`$stats = Get-ProcessStats -ProcessName "notepad"
Write-Output "进程数: `$(`$stats.Count)"
Write-Output "总内存: `$(`$stats.TotalMemory / 1MB) MB"
Write-Output "最大CPU: `$(`$stats.MaxCPU)"
"@ | Out-File -FilePath "$env:TEMP\function-return.ps1" -Encoding UTF8

& "$env:TEMP\function-return.ps1"
```

---

## 练习 10.5：模块化脚本

**目标**：掌握脚本模块的创建和使用。

### 任务 A：创建模块

```powershell
# 创建模块目录
$moduleDir = "$env:TEMP\MyMathModule"
New-Item -ItemType Directory -Path $moduleDir -Force | Out-Null

# 创建模块文件 MyMathModule.psm1
@"
function Get-Square {
    param([int]`$Number)
    return `$Number * `$Number
}

function Get-Cube {
    param([int]`$Number)
    return `$Number * `$Number * `$Number
}

function Get-Factorial {
    param([int]`$Number)
    if (`$Number -le 1) { return 1 }
    return `$Number * (Get-Factorial -Number (`$Number - 1))
}

function Get-Fibonacci {
    param([int]`$Number)
    `$sequence = 0, 1
    for (`$i = 2; `$i -lt `$Number; `$i++) {
        `$sequence += ,(`$sequence[-1] + `$sequence[-2])
    }
    return `$sequence[0..(`$Number-1)]
}

# 导出函数
Export-ModuleMember -Function Get-Square, Get-Cube, Get-Factorial, Get-Fibonacci
"@ | Out-File -FilePath "$moduleDir\MyMathModule.psm1" -Encoding UTF8

# 使用模块
Import-Module "$moduleDir\MyMathModule.psm1"

# 测试函数
Get-Square -Number 5
Get-Cube -Number 3
Get-Factorial -Number 5
Get-Fibonacci -Number 10

# 查看模块信息
Get-Module MyMathModule
Get-Command -Module MyMathModule
```

---

## 综合练习：实用脚本

### 任务 1：文件备份脚本

```powershell
# 创建备份脚本 backup.ps1
@"
param(
    [Parameter(Mandatory=`$true)]
    [string]`$SourcePath,

    [Parameter(Mandatory=`$true)]
    [string]`$BackupPath,

    [int]`$DaysToKeep = 30
)

`$ErrorActionPreference = "Stop"

Write-Output "===== 文件备份工具 ====="
Write-Output "源目录: `$(`$SourcePath)"
Write-Output "目标目录: `$(`$BackupPath)"
Write-Output "保留天数: `$(`$DaysToKeep)"
Write-Output ""

# 检查源目录
if (-not (Test-Path `$SourcePath)) {
    Write-Error "源目录不存在: `$(`$SourcePath)"
    exit 1
}

# 创建备份目录
if (-not (Test-Path `$BackupPath)) {
    New-Item -ItemType Directory -Path `$BackupPath -Force | Out-Null
    Write-Output "创建备份目录"
}

# 生成备份文件名
`$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
`$backupName = "backup_`$(`$timestamp)"
`$backupFullPath = Join-Path `$BackupPath `$backupName

Write-Output "开始备份..."

try {
    Copy-Item -Path `$SourcePath -Destination `$backupFullPath -Recurse -Force
    Write-Output "备份成功！"
    Write-Output "备份位置: `$(`$backupFullPath)"

    # 清理旧备份
    Write-Output ""
    Write-Output "清理旧备份..."

    `$cutoffDate = (Get-Date).AddDays(-`$(`$DaysToKeep))
    `$oldBackups = Get-ChildItem -Path `$BackupPath -Directory |
        Where-Object { `$_.CreationTime -lt `$cutoffDate }

    foreach (`$old in `$oldBackups) {
        Write-Output "  删除: `$(`$old.Name)"
        Remove-Item -Path `$old.FullName -Recurse -Force
    }

    Write-Output "清理完成！"

} catch {
    Write-Error "备份失败: `$(`$_.Exception.Message)"
    exit 1
}

Write-Output ""
Write-Output "===== 备份完成 ====="
"@ | Out-File -FilePath "$env:TEMP\backup.ps1" -Encoding UTF8

# 测试备份
& "$env:TEMP\backup.ps1" -SourcePath "$env:TEMP\test" -BackupPath "$env:TEMP\backups" -DaysToKeep 7
```

### 任务 2：日志分析脚本

```powershell
# 创建日志分析脚本
@"
param(
    [Parameter(Mandatory=`$true)]
    [string]`$LogPath
)

Write-Output "===== 日志分析工具 ====="
Write-Output "分析文件: `$(`$LogPath)"
Write-Output ""

# 检查文件是否存在
if (-not (Test-Path `$LogPath)) {
    Write-Error "日志文件不存在"
    exit 1
}

# 读取日志
`$logs = Get-Content `$LogPath
`$totalLines = `$logs.Count

Write-Output "总行数: `$(`$totalLines)"
Write-Output ""

# 统计 ERROR
`$errors = `$logs | Select-String -Pattern "ERROR" -AllMatches
Write-Output "ERROR 数量: `$(`$errors.Count)"

# 统计 WARN
`$warnings = `$logs | Select-String -Pattern "WARN" -AllMatches
Write-Output "WARN 数量: `$(`$warnings.Count)"

# 统计 INFO
`$info = `$logs | Select-String -Pattern "INFO" -AllMatches
Write-Output "INFO 数量: `$(`$info.Count)"

# 显示最近的错误
if (`$errors.Count -gt 0) {
    Write-Output ""
    Write-Output "最近的 ERROR（最多显示10条）："
    `$errors | Select-Object -Last 10 | ForEach-Object {
        Write-Output "  `$(`$_.Line)"
    }
}
"@ | Out-File -FilePath "$env:TEMP\analyze-log.ps1" -Encoding UTF8

# 创建测试日志文件
@"
2024-01-01 10:00:00 INFO Application started
2024-01-01 10:01:00 INFO User logged in
2024-01-01 10:02:00 ERROR Database connection failed
2024-01-01 10:03:00 WARN Retry attempt 1
2024-01-01 10:04:00 ERROR Timeout error
2024-01-01 10:05:00 INFO Connection restored
"@ | Out-File -FilePath "$env:TEMP\test.log" -Encoding UTF8

# 运行分析
& "$env:TEMP\analyze-log.ps1" -LogPath "$env:TEMP\test.log"
```

### 任务 3：计划任务管理

```powershell
# 创建计划任务管理脚本
@"
param(
    [Parameter(Mandatory=`$true)]
    [string]`$TaskName,

    [Parameter()]
    [ValidateSet("start", "stop", "status", "create", "delete")]
    [string]`$Action = "status"
)

switch (`$Action) {
    "status" {
        Write-Output "查看任务状态: `$(`$TaskName)"
        `$task = Get-ScheduledTask -TaskName `$TaskName -ErrorAction SilentlyContinue
        if (`$task) {
            `$info = Get-ScheduledTaskInfo -TaskName `$TaskName
            Write-Output "  状态: `$(`$task.State)"
            Write-Output "  上次运行: `$(`$info.LastRunTime)"
            Write-Output "  下次运行: `$(`$info.NextRunTime)"
            Write-Output "  上次结果: `$(`$info.LastTaskResult)"
        } else {
            Write-Output "任务不存在"
        }
    }

    "start" {
        Write-Output "启动任务: `$(`$TaskName)"
        Start-ScheduledTask -TaskName `$TaskName
        Write-Output "任务已启动"
    }

    "stop" {
        Write-Output "停止任务: `$(`$TaskName)"
        Stop-ScheduledTask -TaskName `$TaskName
        Write-Output "任务已停止"
    }

    "create" {
        Write-Output "创建任务: `$(`$TaskName)"
        # 注意：实际创建需要更多配置
        Write-Output "提示：使用 New-ScheduledTask* cmdlets 创建"
    }

    "delete" {
        Write-Output "删除任务: `$(`$TaskName)"
        # Unregister-ScheduledTask -TaskName `$TaskName -Confirm:`$false
        Write-Output "提示：取消注释实际执行"
    }
}
"@ | Out-File -FilePath "$env:TEMP\manage-task.ps1" -Encoding UTF8

# 查看所有计划任务
Get-ScheduledTask | Select-Object TaskName, State | Select-Object -First 10
```

---

## 扩展挑战

### 挑战：创建交互式菜单

```powershell
# 创建交互式菜单脚本
@"
function Show-Menu {
    param([hashtable]`$MenuItems)

    while (`$true) {
        Clear-Host
        Write-Output "===== 交互式菜单 ====="
        Write-Output ""
        `$i = 1
        foreach (`$key in `$MenuItems.Keys | Sort-Object) {
            Write-Output "`$i. `$(`$MenuItems[`$key])"
            `$i++
        }
        Write-Output "Q. 退出"
        Write-Output ""

        `$choice = Read-Host "请选择"

        if (`$choice -eq "Q" -or `$choice -eq "q") {
            Write-Output "再见！"
            break
        }

        if (`$choice -match '^\d+$') {
            `$keys = (`$MenuItems.Keys | Sort-Object)
            `$index = [int]`$choice - 1

            if (`$index -ge 0 -and `$index -lt `$keys.Count) {
                `$selected = `$keys[`$index]
                Write-Output "执行: `$(`$MenuItems[`$selected])"
                # 在这里执行对应的操作
                Write-Output "（模拟执行）"
                Read-Host "按 Enter 继续"
            }
        }
    }
}

# 定义菜单
`$menu = @{
    "1" = "查看进程"
    "2" = "查看服务"
    "3" = "查看磁盘空间"
    "4" = "查看网络连接"
    "5" = "系统信息"
}

Show-Menu -MenuItems `$menu
"@ | Out-File -FilePath "$env:TEMP\interactive-menu.ps1" -Encoding UTF8

# & "$env:TEMP\interactive-menu.ps1"
```

---

## 清理练习文件

```powershell
# 清理临时脚本
Remove-Item "$env:TEMP\*.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\MyMathModule" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\test.log" -Force -ErrorAction SilentlyContinue

Write-Output "练习文件已清理"
```

---

## 下一步

完成以上练习后，继续学习 [Lesson 11: 开发工作流实战](../11_dev_workflow/README.md)
