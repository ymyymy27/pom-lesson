> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Lesson 6 练习：进程与服务管理

## 练习说明

本练习覆盖 Lesson 6 的所有核心概念。建议先通读 Lesson 6 教程，再完成以下练习。

---

## 练习 6.1：进程基础

**目标**：掌握进程的查看和信息获取。

### 任务 A：基本进程查看

```powershell
# 查看所有进程
Get-Process

# 查看特定进程
Get-Process -Name python
Get-Process -Name python, code

# 按 PID 查看
Get-Process -Id 0
```

### 任务 B：进程属性

```powershell
# 查看进程详细信息
Get-Process -Name notepad | Select-Object *

# 查看常用属性
Get-Process | Select-Object Name, Id, CPU, WorkingSet, StartTime | Select-Object -First 10

# 格式化显示
Get-Process | Select-Object Name, Id, CPU,
    @{Name="MemoryMB";Expression={[math]::Round($_.WorkingSet/1MB,2)}} |
    Format-Table -AutoSize
```

---

## 练习 6.2：进程筛选与排序

**目标**：掌握进程的筛选和排序技巧。

### 任务 A：筛选进程

```powershell
# 筛选特定进程
Get-Process | Where-Object Name -eq "python"

# 筛选 CPU 占用高的
Get-Process | Where-Object CPU -gt 10 | Sort-Object CPU -Descending

# 筛选内存占用高的
Get-Process | Where-Object { $_.WorkingSet -gt 100MB }

# 筛选不响应的进程
Get-Process | Where-Object { $_.Responding -eq $false }
```

### 任务 B：排序与 Top N

```powershell
# CPU 最高的 5 个进程
Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name, CPU

# 内存最高的 5 个进程
Get-Process | Sort-Object WorkingSet -Descending |
    Select-Object -First 5 Name,
        @{Name="MemoryMB";Expression={[math]::Round($_.WorkingSet/1MB,2)}}

# 综合排序
Get-Process | Sort-Object CPU, WorkingSet -Descending | Select-Object -First 10
```

---

## 练习 6.3：启动进程

**目标**：掌握进程的启动方法。

### 任务 A：Start-Process 基本用法

```powershell
# 启动记事本
Start-Process notepad.exe

# 启动并指定文件
Start-Process notepad.exe -ArgumentList "C:\Windows\System32\drivers\etc\hosts"

# 启动新 PowerShell 窗口
Start-Process powershell.exe

# 启动最大化窗口
Start-Process notepad.exe -WindowStyle Maximized
```

### 任务 B：高级启动

```powershell
# 以管理员身份运行
# Start-Process notepad.exe -Verb RunAs

# 启动隐藏窗口
Start-Process python.exe -ArgumentList "script.py" -WindowStyle Hidden

# 获取启动后的进程对象
$process = Start-Process notepad.exe -PassThru
$process.Id

# 启动并等待
Start-Process python.exe -ArgumentList "script.py" -Wait
```

---

## 练习 6.4：停止进程

**目标**：掌握进程的停止方法。

### 任务 A：Stop-Process 基本用法

```powershell
# 按名称停止
Stop-Process -Name notepad

# 按 PID 停止
# Stop-Process -Id 1234

# 强制停止
Stop-Process -Name python -Force

# 停止前确认
# Stop-Process -Name python -Confirm
```

### 任务 B：进程控制

```powershell
# 启动并停止流程
$proc = Start-Process notepad.exe -PassThru
Start-Sleep -Seconds 2
Stop-Process -Id $proc.Id
Write-Output "进程已停止"

# 等待进程结束
$proc = Start-Process python -ArgumentList "-c 'import time; time.sleep(3)'" -PassThru
Wait-Process -Id $proc.Id
Write-Output "进程执行完成"
```

---

## 练习 6.5：后台任务

**目标**：掌握后台任务的管理。

### 任务 A：Start-Job

```powershell
# 启动后台任务
$job = Start-Job -ScriptBlock {
    Get-Process | Sort-Object WorkingSet -Descending |
        Select-Object -First 5
}

# 查看任务状态
Get-Job

# 获取任务结果
Receive-Job -Job $job

# 清理任务
Remove-Job -Job $job
```

### 任务 B：任务管理

```powershell
# 启动命名任务
$job = Start-Job -Name "MyTask" -ScriptBlock {
    Start-Sleep -Seconds 5
    "任务完成！时间: $(Get-Date)"
}

# 查看所有任务
Get-Job

# 等待任务完成
Wait-Job -Name "MyTask"

# 获取结果（保留数据）
Receive-Job -Job $job -Keep

# 停止任务
Stop-Job -Name "MyTask"

# 删除任务
Remove-Job -Name "MyTask"
```

---

## 练习 6.6：服务管理

**目标**：掌握 Windows 服务的查看和管理。

### 任务 A：查看服务

```powershell
# 查看所有服务
Get-Service

# 查看特定服务
Get-Service -Name wuauserv

# 按状态筛选
Get-Service | Where-Object Status -eq "Running" | Measure-Object
Get-Service | Where-Object Status -eq "Stopped" | Measure-Object

# 查看自动启动的服务
Get-Service | Where-Object { $_.StartType -eq "Automatic" }
```

### 任务 B：服务控制

```powershell
# 启动服务
# Start-Service -Name wuauserv

# 停止服务
# Stop-Service -Name Spooler

# 重启服务
# Restart-Service -Name Spooler

# 设置启动类型
# Set-Service -Name wuauserv -StartupType Automatic
```

---

## 练习 6.7：计划任务

**目标**：掌握计划任务的创建和管理。

### 任务 A：查看计划任务

```powershell
# 查看所有计划任务
Get-ScheduledTask

# 查看特定任务
Get-ScheduledTask -TaskName "Daily Backup"

# 查看任务状态
Get-ScheduledTask -TaskName "Daily Backup" | Get-ScheduledTaskInfo
```

### 任务 B：创建计划任务

```powershell
# 创建简单的每日任务
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-Command 'Write-Output Hello'"
$trigger = New-ScheduledTaskTrigger -Daily -At "09:00"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries

# 注册任务
# Register-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -TaskName "MyDailyTask"

# 手动启动任务
# Start-ScheduledTask -TaskName "MyDailyTask"

# 删除任务
# Unregister-ScheduledTask -TaskName "MyDailyTask" -Confirm:$false
```

---

## 练习 6.8：系统监控

**目标**：掌握系统资源的监控方法。

### 任务 A：CPU 监控

```powershell
# 查看 CPU 使用率
Get-WmiObject -Class Win32_Processor | Select-Object Name, LoadPercentage

# 查看 CPU 占用最高的进程
Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name, CPU
```

### 任务 B：内存监控

```powershell
# 查看内存使用情况
Get-WmiObject -Class Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,
    @{Name="TotalGB";Expression={[math]::Round($_.TotalVisibleMemorySize/1MB,2)}},
    @{Name="FreeGB";Expression={[math]::Round($_.FreePhysicalMemory/1MB,2)}}

# 计算使用率
$mem = Get-WmiObject -Class Win32_OperatingSystem
$used = [math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / $mem.TotalVisibleMemorySize * 100, 1)
Write-Output "内存使用率: $used%"
```

### 任务 C：磁盘监控

```powershell
# 查看磁盘空间
Get-WmiObject -Class Win32_LogicalDisk -Filter "DriveType=3" |
    Select-Object DeviceID,
        @{Name="TotalGB";Expression={[math]::Round($_.Size/1GB,2)}},
        @{Name="FreeGB";Expression={[math]::Round($_.FreeSpace/1GB,2)}},
        @{Name="UsedPercent";Expression={[math]::Round(($_.Size - $_.FreeSpace) / $_.Size * 100, 1)}}
```

---

## 综合练习：系统监控脚本

### 任务 1：实时进程监控器

```powershell
# 创建实时进程监控函数
function Watch-Process {
    param(
        [string]$ProcessName,
        [int]$Interval = 2
    )

    Write-Output "监控进程: $ProcessName (按 Ctrl+C 停止)"
    Write-Output ""

    while ($true) {
        $proc = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue

        if ($proc) {
            $time = Get-Date -Format "HH:mm:ss"
            Write-Host "[$time] " -NoNewline
            Write-Host "运行中 | " -NoNewline -ForegroundColor Green
            Write-Host "CPU: $($proc.CPU) | " -NoNewline
            Write-Host "内存: $([math]::Round($proc.WorkingSet/1MB, 2)) MB"
        } else {
            $time = Get-Date -Format "HH:mm:ss"
            Write-Host "[$time] " -NoNewline
            Write-Host "未运行" -ForegroundColor Red
        }

        Start-Sleep -Seconds $Interval
    }
}

# 使用示例（取消注释运行）：
# Watch-Process -ProcessName "notepad" -Interval 3
```

### 任务 2：服务健康检查

```powershell
# 创建服务健康检查脚本
function Get-ServiceHealth {
    param(
        [string[]]$ServiceNames = @("wuauserv", "Spooler", "WSearch")
    )

    Write-Output "===== Windows 服务健康检查 ====="
    Write-Output "检查时间: $(Get-Date)"
    Write-Output ""

    foreach ($name in $ServiceNames) {
        $svc = Get-Service -Name $name -ErrorAction SilentlyContinue

        if ($svc) {
            $status = if ($svc.Status -eq "Running") { "正常" } else { "异常" }
            $color = if ($svc.Status -eq "Running") { "Green" } else { "Red" }

            Write-Host "$name : " -NoNewline
            Write-Host $svc.Status -ForegroundColor $color
            Write-Host "  启动类型: $($svc.StartType)"
            Write-Host "  显示名称: $($svc.DisplayName)"
            Write-Output ""
        } else {
            Write-Host "$name : " -NoNewline
            Write-Host "未找到" -ForegroundColor Yellow
            Write-Output ""
        }
    }
}

Get-ServiceHealth -ServiceNames "wuauserv", "Spooler", "WSearch"
```

### 任务 3：系统报告生成

```powershell
# 创建系统报告函数
function Get-SystemReport {
    param([string]$OutputPath = "$env:TEMP\system_report.txt")

    $report = @"
========================================
Windows 系统报告
生成时间: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
========================================

--- 系统信息 ---
计算机名: $env:COMPUTERNAME
用户名: $env:USERNAME
操作系统: $env:OS

--- CPU 信息 ---
"@

    $cpu = Get-WmiObject -Class Win32_Processor
    $report += @"

处理器: $($cpu.Name)
核心数: $($cpu.NumberOfCores)
线程数: $($cpu.NumberOfLogicalProcessors)
使用率: $($cpu.LoadPercentage)%

--- 内存信息 ---
"@

    $mem = Get-WmiObject -Class Win32_OperatingSystem
    $report += @"

总内存: $([math]::Round($mem.TotalVisibleMemorySize/1MB, 2)) GB
可用内存: $([math]::Round($mem.FreePhysicalMemory/1MB, 2)) GB
使用率: $([math]::Round(($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / $mem.TotalVisibleMemorySize * 100, 1))%

--- 磁盘信息 ---
"@

    $disks = Get-WmiObject -Class Win32_LogicalDisk -Filter "DriveType=3"
    foreach ($disk in $disks) {
        $report += @"

驱动器: $($disk.DeviceID)
总容量: $([math]::Round($disk.Size/1GB, 2)) GB
可用空间: $([math]::Round($disk.FreeSpace/1GB, 2)) GB
使用率: $([math]::Round(($disk.Size - $disk.FreeSpace) / $disk.Size * 100, 1))%

"@
    }

    $report += @"

--- 进程统计 ---
总进程数: $((Get-Process).Count)
运行中: $((Get-Process | Where-Object { $_.Responding -eq $true }).Count)

--- 服务统计 ---
总服务数: $((Get-Service).Count)
运行中: $((Get-Service | Where-Object { $_.Status -eq "Running" }).Count)
已停止: $((Get-Service | Where-Object { $_.Status -eq "Stopped" }).Count)

========================================
报告结束
========================================
"@

    $report | Out-File -FilePath $OutputPath -Encoding UTF8
    Write-Output "报告已生成: $OutputPath"
}

Get-SystemReport
```

---

## 扩展挑战

### 挑战：创建定时清理脚本

```powershell
# 自动清理不响应的进程和临时文件
function Clear-SystemJunk {
    Write-Output "===== 系统清理 ====="

    # 1. 关闭不响应的进程
    $hung = Get-Process | Where-Object { $_.Responding -eq $false }
    Write-Output "发现 $($hung.Count) 个不响应的进程"

    # 2. 清理临时文件
    $tempFiles = Get-ChildItem -Path $env:TEMP -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) }

    Write-Output "发现 $($tempFiles.Count) 个超过7天的临时文件"

    # 确认后再清理
    # $tempFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    # Write-Output "清理完成！"
}
```

---

## 下一步

完成以上练习后，继续学习 [Lesson 7: 网络操作](../07_network_ops/课程说明.md)
