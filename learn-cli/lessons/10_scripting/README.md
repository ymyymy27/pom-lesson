# Lesson 10: 脚本编程与自动化

> 用脚本自动化重复工作，让电脑为你打工——这是命令行技能的终极形态

---

## 10.1 脚本基础

### 什么是脚本？

脚本是一系列命令的集合，保存为文件后可以反复执行，节省重复输入的时间。

```
手动执行（重复劳动）：
  每次都要输入：
  cd project
  pip install -r requirements.txt
  python manage.py runserver

脚本执行（一劳永逸）：
  ./start-dev.ps1
  → 自动执行以上所有步骤
```

### PowerShell 脚本文件

```powershell
# PowerShell 脚本文件扩展名：.ps1

# 示例：hello-world.ps1
Write-Output "你好，世界！"

# 执行脚本
.\hello-world.ps1
.\path\to\script.ps1
C:\Scripts\script.ps1
```

### 执行策略

PowerShell 有脚本执行策略，防止恶意脚本运行：

```powershell
# 查看当前策略
Get-ExecutionPolicy

# 执行策略类型
# Restricted: 不允许任何脚本（默认）
# AllSigned: 需签名
# RemoteSigned: 本地脚本可运行，远程脚本需签名
# Unrestricted: 允许所有脚本（不安全）

# 设置当前用户可执行脚本
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 绕过执行策略（临时）
PowerShell -ExecutionPolicy Bypass -File script.ps1

# 临时提升权限
Start-Process powershell.exe -Verb RunAs
```

### 脚本最佳实践

```powershell
# 1. 指定脚本编码
# -*- coding: utf-8 -*-
Set-StrictMode -Version Latest  # 严格模式

# 2. 错误处理
$ErrorActionPreference = "Stop"  # 遇错停止

# 3. 添加参数
param(
    [string]$Name = "World"
)
```

---

## 10.2 参数传递

### 基本参数

```powershell
# script.ps1
param(
    [string]$Name,        # 必需参数
    [int]$Age = 18,       # 带默认值的参数
    [switch]$Verbose      # 开关参数
)

Write-Output "你好，$Name！你 $Age 岁了。"

if ($Verbose) {
    Write-Output "详细模式已启用"
}

# 执行
.\script.ps1 -Name "张三" -Age 25 -Verbose
.\script.ps1 "张三" 25  # 位置参数
```

### 参数属性

```powershell
param(
    [Parameter(Mandatory=$true, Position=0, HelpMessage="输入你的名字")]
    [string]$Name,

    [Parameter(Position=1)]
    [ValidateRange(0, 150)]
    [int]$Age = 18,

    [Parameter()]
    [ValidateSet("male", "female", "other")]
    [string]$Gender = "other",

    [Parameter()]
    [AllowNull()]
    [AllowEmptyString()]
    [string]$Email
)
```

### 高级参数

```powershell
# 参数验证
param(
    # 必选参数
    [Parameter(Mandatory=$true)]
    [string]$RequiredParam,

    # 有效值集合
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment = "dev",

    # 正则验证
    [ValidatePattern("^[a-zA-Z]+$")]
    [string]$Name,

    # 范围验证
    [ValidateRange(1, 100)]
    [int]$Count,

    # 非空验证
    [ValidateNotNullOrEmpty()]
    [string]$Input
)

# 参数别名
param(
    [Alias("n")]
    [string]$Name,

    [Alias("v")]
    [switch]$Verbose
)

# 参数管道绑定
param(
    [Parameter(ValueFromPipeline=$true)]
    [string]$InputObject
)
```

---

## 10.3 错误处理

### 常见错误类型

```
终止错误（Terminating Error）：
  - 脚本立即停止执行
  - 严重错误，如文件不存在、权限不足
  - 可用 try/catch 捕获

非终止错误（Non-terminating Error）：
  - 继续执行，只记录错误
  - 如某些文件删除失败
  - 可用 -ErrorAction 控制
```

### try / catch / finally

```powershell
try {
    # 尝试执行的代码
    $result = 10 / 0
    Write-Output "结果: $result"
}
catch {
    # 捕获错误
    Write-Output "发生错误: $_"
    Write-Output "错误类型: $($_.Exception.GetType().Name)"
}
finally {
    # 无论是否出错都执行
    Write-Output "清理资源..."
}
```

### 错误变量

```powershell
try {
    Get-Content "nonexistent.txt" -ErrorAction Stop
}
catch {
    # $_ = 当前的错误对象
    $_.Exception.Message           # 错误消息
    $_.Exception.GetType().Name    # 异常类型
    $_.ScriptStackTrace            # 错误堆栈
    $_.InvocationInfo              # 错误位置
}
```

### 错误处理策略

```powershell
# 全局错误行为
$ErrorActionPreference = "Stop"  # Stop, Continue, SilentlyContinue, Inquire

# 命令级错误行为
Get-Content "file.txt" -ErrorAction Stop
Get-Content "file.txt" -ErrorAction SilentlyContinue  # 静默忽略
Get-Content "file.txt" -ErrorAction Inquire          # 询问

# $? 检查上一个命令是否成功
Get-Content "file.txt"
if ($?) {
    Write-Output "命令成功"
} else {
    Write-Output "命令失败"
}

# $LASTEXITCODE（外部命令）
$program = "python"
& $program script.py
if ($LASTEXITCODE -ne 0) {
    Write-Output "程序退出码: $LASTEXITCODE"
}
```

### 自定义错误

```powershell
# 抛出错误
throw "这是一个错误"

# 抛出特定类型的错误
throw [System.DivideByZeroException]::new("除数不能为零")

# 写入错误日志
$Error | Out-File -FilePath "errors.log" -Append
```

---

## 10.4 函数进阶

### 函数参数

```powershell
function Get-FileInfo {
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
        [string]$Path,

        [Parameter()]
        [switch]$Detailed
    )

    process {
        if (Test-Path $Path) {
            $file = Get-Item $Path
            if ($Detailed) {
                $file | Select-Object FullName, Length, CreationTime, LastWriteTime, Attributes
            } else {
                $file | Select-Object Name, Length
            }
        }
    }
}

# 使用
Get-FileInfo -Path "C:\test.txt" -Detailed
Get-ChildItem | Get-FileInfo
```

### 返回值

```powershell
function Add-Numbers {
    param([int]$A, [int]$B)
    return $A + $B  # 返回值
}

$result = Add-Numbers -A 5 -B 3
Write-Output $result  # 输出: 8

# 返回多个值
function Get-Stats {
    $numbers = 1..10
    return @{
        Sum = ($numbers | Measure-Object -Sum).Sum
        Avg = ($numbers | Measure-Object -Average).Average
        Max = ($numbers | Measure-Object -Maximum).Maximum
    }
}

$stats = Get-Stats
$stats.Sum
$stats.Avg
```

### 高级函数

```powershell
function Send-Notification {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$To,

        [Parameter()]
        [string]$Subject = "通知",

        [Parameter()]
        [string]$Body,

        [Parameter()]
        [switch]$Urgent
    )

    Write-Output "发送通知到: $To"
    Write-Output "主题: $Subject"

    if ($Urgent) {
        Write-Warning "这是紧急通知！"
    }

    # 使用 Write-Verbose 等支持详细模式
    Write-Verbose "连接到邮件服务器..."
    Write-Verbose "发送邮件..."

    # 使用 Write-Progress 显示进度
    for ($i = 1; $i -le 100; $i++) {
        Write-Progress -Activity "处理中" -Status "$i%" -PercentComplete $i
        Start-Sleep -Milliseconds 20
    }
}

# 调用
Send-Notification -To "user@example.com" -Subject "测试" -Urgent -Verbose
```

---

## 10.5 循环与数组

### 数组操作

```powershell
# 创建数组
$arr = 1, 2, 3, 4, 5
$arr = @(1, 2, 3)

# 数组方法
$arr.Count        # 元素数量
$arr[0]           # 第一个元素
$arr[-1]          # 最后一个元素
$arr[0..2]        # 切片

# 添加元素
$arr += 6

# 过滤
$arr | Where-Object { $_ -gt 3 }

# 映射
$arr | ForEach-Object { $_ * 2 }

# 聚合
($arr | Measure-Object -Sum).Sum
($arr | Measure-Object -Average).Average
```

### 循环实战

```powershell
# 处理文件列表
Get-ChildItem *.txt | ForEach-Object {
    $content = Get-Content $_.FullName
    $lineCount = ($content | Measure-Object).Count
    [PSCustomObject]@{
        FileName = $_.Name
        LineCount = $lineCount
    }
}

# 批量处理
$files = Get-ChildItem -Path "C:\Logs" -Filter *.log
foreach ($file in $files) {
    if ($file.Length -gt 10MB) {
        Compress-Archive -Path $file.FullName -DestinationPath "$($file.FullName).zip" -Force
        Remove-Item $file.FullName
        Write-Output "已压缩并删除: $($file.Name)"
    }
}

# While 循环
$i = 0
while ($i -lt 5) {
    Write-Output $i
    $i++
}
```

---

## 10.6 模块化脚本

### 脚本模块

```powershell
# MyFunctions.psm1
function Get-Square {
    param([int]$Number)
    return $Number * $Number
}

function Get-Cube {
    param([int]$Number)
    return $Number * $Number * $Number
}

function Get-Factorial {
    param([int]$Number)
    if ($Number -le 1) { return 1 }
    return $Number * (Get-Factorial -Number ($Number - 1))
}

# 导出函数
Export-ModuleMember -Function Get-Square, Get-Cube
```

### 使用模块

```powershell
# 加载模块
Import-Module .\MyFunctions.psm1

# 使用函数
Get-Square -Number 5  # 25
Get-Cube -Number 3    # 27
Get-Factorial -Number 5  # 120

# 卸载模块
Remove-Module MyFunctions

# 查看已加载的模块
Get-Module
```

---

## 10.7 实际脚本示例

### 批量文件备份

```powershell
# backup.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$SourceDir,

    [Parameter(Mandatory=$true)]
    [string]$BackupDir,

    [Parameter()]
    [int]$DaysToKeep = 30
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = Join-Path $BackupDir "backup_$timestamp"

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force
}

Write-Output "开始备份..."
Write-Output "源目录: $SourceDir"
Write-Output "目标目录: $backupPath"

try {
    Copy-Item -Path $SourceDir -Destination $backupPath -Recurse -Force
    Write-Output "备份成功！"

    # 清理旧备份
    $oldBackups = Get-ChildItem -Path $BackupDir -Directory |
        Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-$DaysToKeep) }

    foreach ($old in $oldBackups) {
        Remove-Item -Path $old.FullName -Recurse -Force
        Write-Output "已删除旧备份: $($old.Name)"
    }
}
catch {
    Write-Error "备份失败: $_"
    exit 1
}

# 清理旧备份
$oldBackups = Get-ChildItem -Path $BackupDir -Directory |
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-$DaysToKeep) }

foreach ($old in $oldBackups) {
    Write-Output "删除旧备份: $($old.Name)"
    Remove-Item -Path $old.FullName -Recurse -Force
}
```

### 日志分析脚本

```powershell
# analyze-logs.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$LogPath,

    [Parameter()]
    [string]$OutputPath = ".\report.html"
)

$errors = @()
$warnings = @()

Write-Output "分析日志文件: $LogPath"

if (-not (Test-Path $LogPath)) {
    Write-Error "日志文件不存在: $LogPath"
    exit 1
}

$logs = Get-Content $LogPath

# 统计错误
$errors = $logs | Select-String -Pattern "ERROR" -AllMatches
$warnings = $logs | Select-String -Pattern "WARN" -AllMatches

# 生成报告
$report = @"
# 日志分析报告
生成时间: $(Get-Date)

## 统计
- 总行数: $($logs.Count)
- 错误数: $($errors.Count)
- 警告数: $($warnings.Count)

## 错误详情
$($errors | ForEach-Object { $_.Line } | Out-String)

## 警告详情
$($warnings | ForEach-Object { $_.Line } | Out-String)
"@

$report | Out-File -FilePath $OutputPath -Encoding UTF8
Write-Output "报告已生成: $OutputPath"
```

### 监控系统

```powershell
# monitor.ps1
param(
    [Parameter()]
    [int]$Interval = 5,

    [Parameter()]
    [int]$Duration = 60
)

$startTime = Get-Date
$endTime = $startTime.AddSeconds($Duration)

Write-Output "开始监控，间隔: $Interval 秒，持续: $Duration 秒"
Write-Output "开始时间: $startTime"
Write-Output "按 Ctrl+C 停止"

while ((Get-Date) -lt $endTime) {
    Clear-Host
    $currentTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    $cpu = (Get-WmiObject -Class Win32_Processor).LoadPercentage
    $mem = [math]::Round((Get-WmiObject -Class Win32_OperatingSystem).TotalVisibleMemorySize / 1MB, 2)
    $memFree = [math]::Round((Get-WmiObject -Class Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)
    $memUsed = [math]::Round($mem - $memFree, 2)
    $memPercent = [math]::Round($memUsed / $mem * 100, 1)

    Write-Host "===== 系统监控 =====" -ForegroundColor Cyan
    Write-Host "时间: $currentTime" -ForegroundColor Yellow
    Write-Host "CPU: $cpu%" -ForegroundColor $(if ($cpu -gt 80) {"Red"} else {"Green"})
    Write-Host "内存: $memUsed GB / $mem GB ($memPercent%)" -ForegroundColor $(if ($memPercent -gt 80) {"Red"} else {"Green"})

    $topProcesses = Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name, CPU, @{Name="MemoryMB";Expression={[math]::Round($_.WorkingSet/1MB, 2)}}
    Write-Host "`nTop 5 进程:" -ForegroundColor Cyan
    $topProcesses | Format-Table -AutoSize

    $remaining = ($endTime - (Get-Date)).TotalSeconds
    Write-Host "剩余时间: $([math]::Round($remaining, 0)) 秒" -ForegroundColor Yellow

    Start-Sleep -Seconds $Interval
}

Write-Output "监控结束"
```

---

## 10.8 计划任务自动化

### 创建计划任务

```powershell
# 创建脚本计划任务
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"C:\Scripts\backup.ps1`" -SourceDir `"C:\Data`" -BackupDir `"D:\Backups`""

$trigger = New-ScheduledTaskTrigger -Daily -At "09:00"

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -TaskName "每日备份" `
    -Description "每日自动备份重要数据"
```

### 管理计划任务

```powershell
# 查看所有任务
Get-ScheduledTask

# 查看任务详情
Get-ScheduledTask -TaskName "每日备份"

# 启用/禁用任务
Enable-ScheduledTask -TaskName "每日备份"
Disable-ScheduledTask -TaskName "每日备份"

# 手动运行任务
Start-ScheduledTask -TaskName "每日备份"

# 停止任务
Stop-ScheduledTask -TaskName "每日备份"

# 删除任务
Unregister-ScheduledTask -TaskName "每日备份" -Confirm:$false

# 查看任务历史
Get-ScheduledTaskInfo -TaskName "每日备份"
```

---

## 10.9 脚本调试

### 调试方法

```powershell
# 1. Set-PSBreakpoint 断点
Set-PSBreakpoint -Script script.ps1 -Line 10

# 2. Write-Debug
$DebugPreference = "Continue"
Write-Debug "调试信息"

# 3. 详细输出
.\script.ps1 -Verbose

# 4. 模拟运行（WhatIf）
Get-Process | Remove-Process -WhatIf

# 5. -ErrorAction Stop 强制中断
Get-Content "nonexistent.txt" -ErrorAction Stop
```

### 常见脚本错误

```powershell
# 错误1: 路径问题
# 解决：使用绝对路径或 $PSScriptRoot
$scriptPath = $PSScriptRoot
$configFile = Join-Path $scriptPath "config.json"

# 错误2: 变量作用域
# 解决：使用 $script:var 或 $global:var
$script:counter = 0

# 错误3: 类型转换
# 解决：显式转换
[string]$num = 123
[int]$str = "456"

# 错误4: 空值处理
# 解决：使用 $null 检查
if ($null -ne $obj) { ... }
$obj?.Property?.SubProperty
```

---

## 课后练习

1. 创建一个脚本 `hello.ps1`，输出 "Hello, World!"
2. 创建一个带参数的脚本，实现两个数相除
3. 编写一个备份脚本，自动备份指定目录
4. 编写一个日志分析脚本，统计日志中的错误和警告数量
5. 创建一个函数库（.psm1），导出几个实用函数
6. 创建一个计划任务，每天自动执行

---

## 下一步

→ [Lesson 11: 开发工作流实战](../11_dev_workflow/README.md)
