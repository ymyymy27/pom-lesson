# Lesson 4 练习：文本处理与管道

## 练习说明

本练习覆盖 Lesson 4 的所有核心概念。建议先通读 Lesson 4 教程，再完成以下练习。

---

## 练习 4.1：管道基础

**目标**：理解管道的工作原理。

### 任务 A：管道链式操作

```powershell
# 逐步构建管道
# 步骤 1: 获取数据
Get-Process

# 步骤 2: 添加筛选
Get-Process | Where-Object { $_.CPU -gt 0 }

# 步骤 3: 添加排序
Get-Process | Where-Object { $_.CPU -gt 0 } | Sort-Object CPU -Descending

# 步骤 4: 取前几个
Get-Process | Where-Object { $_.CPU -gt 0 } | Sort-Object CPU -Descending | Select-Object -First 5

# 步骤 5: 格式化输出
Get-Process | Where-Object { $_.CPU -gt 0 } | Sort-Object CPU -Descending | Select-Object -First 5 Name, CPU
```

### 任务 B：管道调试

```powershell
# 逐步检查管道中间结果
Get-Process | Tee-Object -Variable allProcesses | Measure-Object

Write-Output "总进程数: $($allProcesses.Count)"

$filtered = $allProcesses | Where-Object { $_.WorkingSet -gt 50MB }
Write-Output "大于50MB的进程数: $($filtered.Count)"
```

---

## 练习 4.2：Select-Object 选择

**目标**：掌握对象属性的选择和计算。

### 任务 A：基本选择

```powershell
# 选择单个属性
Get-Process | Select-Object Name | Select-Object -First 5

# 选择多个属性
Get-Process | Select-Object Name, CPU, WorkingSet | Select-Object -First 5

# 创建计算属性
Get-Process | Select-Object Name,
    @{Name="MemoryMB";Expression={[math]::Round($_.WorkingSet/1MB, 2)}},
    @{Name="Started";Expression={$_.StartTime.ToString("yyyy-MM-dd")}}
```

### 任务 B：切片操作

```powershell
# 取前 N 个
Get-Process | Select-Object -First 10

# 取后 N 个
Get-Process | Select-Object -Last 5

# 跳过前 N 个
Get-Process | Select-Object -Skip 10

# 索引选择
Get-Process | Select-Object -Index 1, 3, 5, 7, 9
```

### 任务 C：去重

```powershell
# 查找重复的进程名
Get-Process | Select-Object Name | Sort-Object Name | Select-Object -Unique
```

---

## 练习 4.3：Where-Object 筛选

**目标**：掌握各种筛选条件。

### 任务 A：基本筛选

```powershell
# 相等判断
Get-Process | Where-Object Name -eq "python"

# 数值比较
Get-Process | Where-Object CPU -gt 10
Get-Process | Where-Object WorkingSet -lt 50MB

# 字符串匹配
Get-Process | Where-Object Name -like "*python*"
Get-Process | Where-Object Name -match "^c.*"
```

### 任务 B：复合条件

```powershell
# 逻辑与
Get-Process | Where-Object { $_.CPU -gt 5 -and $_.WorkingSet -gt 100MB }

# 逻辑或
Get-Process | Where-Object { $_.Name -eq "python" -or $_.Name -eq "node" }

# 逻辑非
Get-Process | Where-Object { $_.Name -notlike "*python*" }
```

### 任务 C：范围和集合

```powershell
# 范围筛选
Get-Process | Where-Object { $_.CPU -gt 0 -and $_.CPU -le 10 }

# 集合包含
Get-Process | Where-Object { $_.Name -in @("python", "node", "code") }

# 排除空值
Get-Process | Where-Object { $null -ne $_.StartTime -and $_.CPU -gt 0 }
```

---

## 练习 4.4：ForEach-Object 遍历

**目标**：掌握对象的遍历处理。

### 任务 A：基本遍历

```powershell
# 简单遍历
1..5 | ForEach-Object { $_ * 2 }

# 带处理的遍历
Get-Process | ForEach-Object {
    $name = $_.Name
    $memMB = [math]::Round($_.WorkingSet / 1MB, 2)
    Write-Output "$name 使用 $memMB MB 内存"
}
```

### 任务 B：聚合计算

```powershell
# 使用 Begin/Process/End
1..100 | ForEach-Object -Begin {
    $sum = 0
    $count = 0
} -Process {
    $sum += $_
    $count++
} -End {
    Write-Output "总和: $sum"
    Write-Output "平均值: $($sum / $count)"
}
```

### 任务 C：对象转换

```powershell
# 转换为自定义对象
Get-Process | Select-Object -First 5 | ForEach-Object {
    [PSCustomObject]@{
        ProcessName = $_.Name
        PID = $_.Id
        MemoryMB = [math]::Round($_.WorkingSet / 1MB, 2)
        CPU_sec = $_.CPU
    }
}
```

---

## 练习 4.5：Sort-Object 排序

**目标**：掌握各种排序方式。

```powershell
# 升序排序
Get-Process | Sort-Object CPU | Select-Object -First 5 Name, CPU

# 降序排序
Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name, CPU

# 多列排序
Get-Process | Sort-Object CPU, WorkingSet -Descending

# 按计算属性排序
Get-ChildItem | Sort-Object { $_.Length } -Descending

# 去重后排序
Get-Process | Sort-Object Name -Unique
```

---

## 练习 4.6：Group-Object 分组

**目标**：掌握对象分组和统计。

```powershell
# 按属性分组
Get-Process | Group-Object Name | Select-Object -First 10

# 按扩展名分组
Get-ChildItem C:\Windows\System32 -Filter *.dll -ErrorAction SilentlyContinue |
    Group-Object Extension

# 分组后统计
Get-Process | Group-Object Name |
    Select-Object Name, Count |
    Sort-Object Count -Descending |
    Select-Object -First 10
```

---

## 练习 4.7：Measure-Object 统计

**目标**：掌握数值统计方法。

```powershell
# 计数
Get-Process | Measure-Object

# 求和
Get-Process | Measure-Object WorkingSet -Sum

# 平均值
Get-Process | Measure-Object WorkingSet -Average

# 最大/最小值
Get-Process | Measure-Object CPU -Maximum -Minimum -Average

# 综合统计
Get-Process | Measure-Object -Property WorkingSet -Sum -Average -Maximum -Minimum
```

---

## 练习 4.8：Select-String 搜索

**目标**：掌握文本内容搜索。

### 任务 A：基本搜索

```powershell
# 在文件中搜索
# Select-String -Path "*.txt" -Pattern "关键词"

# 搜索多个模式
# Select-String -Path *.log -Pattern "ERROR|WARN|CRITICAL"
```

### 任务 B：正则表达式

```powershell
# 匹配邮箱格式
# Select-String -Path emails.txt -Pattern "\w+@\w+\.\w+"

# 匹配 IP 地址
# Select-String -Path log.txt -Pattern "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"

# 匹配日期
# Select-String -Path log.txt -Pattern "\d{4}-\d{2}-\d{2}"
```

### 任务 C：高级搜索

```powershell
# 区分大小写
# Select-String -Path *.py -Pattern "import" -CaseSensitive

# 显示行号
# Select-String -Path test.txt -Pattern "error" -NumericRanges

# 只返回文件名
# Select-String -Path *.py -Pattern "TODO" -Recurse | Select-Object -ExpandProperty Filename -Unique
```

---

## 综合练习：数据处理管道

### 任务 1：进程分析

```powershell
# 分析进程数据，创建综合报告
Get-Process |
    Where-Object { $_.WorkingSet -gt 10MB } |
    Select-Object Name, Id,
        @{Name="MemoryMB";Expression={[math]::Round($_.WorkingSet/1MB, 2)}},
        @{Name="CPU_sec";Expression={[math]::Round($_.CPU, 2)}},
        @{Name="Threads";Expression={$_.Threads.Count}} |
    Sort-Object MemoryMB -Descending |
    Select-Object -First 15 |
    Format-Table -AutoSize
```

### 任务 2：文件统计

```powershell
# 统计指定目录的文件情况
function Get-FileStats {
    param([string]$Path)

    Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue |
        Group-Object Extension |
        Select-Object Name,
            @{Name="Count";Expression={$_.Count}},
            @{Name="TotalSizeMB";Expression={[math]::Round(($_.Group | Measure-Object -Property Length -Sum).Sum / 1MB, 2)}} |
        Sort-Object TotalSizeMB -Descending |
        Format-Table -AutoSize
}

Get-FileStats -Path C:\Windows\System32
```

### 任务 3：日志分析

```powershell
# 模拟日志分析
$sampleLog = @"
2024-01-01 10:00:00 INFO User login
2024-01-01 10:01:00 ERROR Database connection failed
2024-01-01 10:02:00 WARN Cache miss
2024-01-01 10:03:00 ERROR Timeout error
2024-01-01 10:04:00 INFO User logout
2024-01-01 10:05:00 ERROR Authentication failed
"@

$sampleLog -split "`n" | ForEach-Object {
    $_ -match "(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) (.+)"
    [PSCustomObject]@{
        Time = $Matches[1]
        Level = $Matches[2]
        Message = $Matches[3]
    }
} | Group-Object Level | Select-Object Name,
    @{Name="Count";Expression={$_.Count}},
    @{Name="Messages";Expression={$_.Group.Message -join ", "}}
```

---

## 扩展挑战

### 挑战 1：Tee-Object 进阶使用

```powershell
# 使用 Tee-Object 实现多步骤处理和保存
Get-Process |
    Where-Object { $_.WorkingSet -gt 50MB } |
    Tee-Object -Variable topProcesses |
    Sort-Object WorkingSet -Descending |
    Select-Object -First 10 |
    Format-Table Name, WorkingSet -AutoSize

# 对已保存的数据进行其他分析
$topProcesses |
    Group-Object Name |
    Sort-Object Count -Descending |
    Select-Object -First 5
```

### 挑战 2：性能对比

```powershell
# 比较不同写法的性能
$iterations = 1000

# 方法 1: Where-Object
Measure-Command {
    1..$iterations | Where-Object { $_ -gt 500 }
} | Select-Object TotalMilliseconds

# 方法 2: ForEach-Object
Measure-Command {
    $result = @()
    1..$iterations | ForEach-Object {
        if ($_ -gt 500) { $result += $_ }
    }
} | Select-Object TotalMilliseconds
```

---

## 下一步

完成以上练习后，继续学习 [Lesson 5: 环境变量与配置](../05_env_config/README.md)
