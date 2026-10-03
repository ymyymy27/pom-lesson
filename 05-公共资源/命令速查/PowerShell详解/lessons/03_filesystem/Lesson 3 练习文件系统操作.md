> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Lesson 3 练习：文件系统操作

## 练习说明

本练习覆盖 Lesson 3 的所有核心概念。建议先通读 Lesson 3 教程，再完成以下练习。

---

## 练习 3.1：路径操作

**目标**：掌握绝对路径、相对路径和路径切换。

### 任务 A：路径基础

```powershell
# 查看当前目录
Get-Location
pwd

# 查看用户主目录
$HOME
$env:USERPROFILE

# 切换到用户主目录
Set-Location $HOME
cd ~
```

### 任务 B：Push-Location / Pop-Location

```powershell
# 使用栈式导航
Push-Location C:\Windows
Write-Output "当前位置: $(Get-Location)"

Push-Location C:\Windows\System32
Write-Output "当前位置: $(Get-Location)"

# 返回上一个目录
Pop-Location
Write-Output "返回后: $(Get-Location)"

Pop-Location
Write-Output "再返回: $(Get-Location)"
```

---

## 练习 3.2：查看目录内容

**目标**：掌握 Get-ChildItem 的各种用法。

### 任务 A：基本查看

```powershell
# 查看当前目录
Get-ChildItem

# 查看指定目录
Get-ChildItem C:\Windows

# 使用别名
ls C:\Windows
dir C:\Windows
```

### 任务 B：过滤器参数

```powershell
# -Filter 参数（快速，单一模式）
Get-ChildItem -Path C:\Windows -Filter *.exe

# -Include 参数（支持多个模式）
Get-ChildItem -Path C:\Windows\System32 -Include *.dll,*.sys

# -Exclude 参数（排除）
Get-ChildItem -Path C:\Windows\System32 -Include *.dll -Exclude *32*
```

### 任务 C：递归查看

```powershell
# 递归查看（谨慎使用，可能很慢）
Get-ChildItem -Path C:\Windows -Recurse -Depth 1 -ErrorAction SilentlyContinue | Measure-Object

# 只看文件
Get-ChildItem -Path C:\Windows\System32 -File | Measure-Object

# 只看目录
Get-ChildItem -Path C:\Windows\System32 -Directory

# 包含隐藏文件
Get-ChildItem -Path C:\ -Force
```

---

## 练习 3.3：创建文件与目录

**目标**：掌握文件和目录的创建方法。

### 任务 A：创建目录

```powershell
# 创建单个目录
New-Item -ItemType Directory -Path C:\Temp\TestFolder

# 使用别名
mkdir C:\Temp\TestFolder2

# 创建多级目录
New-Item -ItemType Directory -Path C:\Temp\Parent\Child\GrandChild -Force
```

### 任务 B：创建文件

```powershell
# 创建空文件
New-Item -ItemType File -Path C:\Temp\test.txt

# 创建并写入内容
New-Item -ItemType File -Path C:\Temp\test2.txt -Value "Hello, PowerShell!"

# 使用 Set-Content
Set-Content -Path C:\Temp\test3.txt -Value "第二行`n第三行"

# 使用 Out-File
"Hello from Out-File" | Out-File -FilePath C:\Temp\test4.txt

# 追加内容
Add-Content -Path C:\Temp\test.txt -Value "追加的内容"
```

### 任务 C：批量创建

```powershell
# 批量创建目录
1..5 | ForEach-Object {
    New-Item -ItemType Directory -Path "C:\Temp\Folder_$_"
}

# 批量创建文件
1..5 | ForEach-Object {
    New-Item -ItemType File -Path "C:\Temp\file_$_.txt" -Value "File $_"
}
```

---

## 练习 3.4：查看文件内容

**目标**：掌握不同方式读取文件内容。

### 任务 A：基本读取

```powershell
# 读取整个文件
Get-Content C:\Temp\test.txt

# 使用别名
cat C:\Temp\test.txt
type C:\Temp\test.txt
```

### 任务 B：部分读取

```powershell
# 读取前 N 行
Get-Content C:\Temp\test.txt -TotalCount 10

# 读取后 N 行
Get-Content C:\Temp\test.txt -Tail 10

# 按范围读取
(Get-Content C:\Temp\test.txt)[0..9]
```

### 任务 C：动态监控

```powershell
# 实时监控文件变化（类似 tail -f）
# Get-Content C:\Temp\test.txt -Wait -Tail 10
```

---

## 练习 3.5：复制文件与目录

**目标**：掌握文件和目录的复制操作。

### 任务 A：复制文件

```powershell
# 复制单个文件
Copy-Item -Path C:\Temp\test.txt -Destination C:\Temp\Backup\test.txt

# 使用别名
cp C:\Temp\test.txt C:\Temp\Backup\

# 复制并保留属性
Copy-Item -Path C:\Temp\test.txt -Destination C:\Temp\Backup\test2.txt -Preserve
```

### 任务 B：复制目录

```powershell
# 复制整个目录
Copy-Item -Path C:\Temp\Folder_1 -Destination C:\Temp\Backup\Folder_1 -Recurse

# 批量复制
Copy-Item -Path C:\Temp\*.txt -Destination C:\Temp\Backup\
```

### 任务 C：高级复制

```powershell
# 复制并重命名
Copy-Item -Path C:\Temp\test.txt -Destination C:\Temp\test_copy.txt

# 强制覆盖
Copy-Item -Path C:\Temp\test.txt -Destination C:\Temp\test_copy.txt -Force

# 模拟复制（预览）
Copy-Item -Path C:\Temp\* -Destination C:\Temp\Backup\ -WhatIf
```

---

## 练习 3.6：移动与重命名

**目标**：掌握文件和目录的移动和重命名操作。

### 任务 A：移动文件

```powershell
# 移动文件
Move-Item -Path C:\Temp\test.txt -Destination C:\Temp\Archive\test.txt

# 使用别名
mv C:\Temp\test2.txt C:\Temp\Archive\
```

### 任务 B：重命名

```powershell
# 重命名文件
Rename-Item -Path C:\Temp\test.txt -NewName new_test.txt

# 批量重命名（将 .txt 改为 .md）
Get-ChildItem -Path C:\Temp -Filter *.txt | ForEach-Object {
    $newName = $_.Name -replace '\.txt$', '.md'
    Rename-Item -Path $_.FullName -NewName $newName
}
```

---

## 练习 3.7：删除文件与目录

**目标**：掌握安全删除操作。

### 任务 A：删除文件

```powershell
# 删除单个文件
Remove-Item -Path C:\Temp\test.txt

# 使用别名
rm C:\Temp\test2.txt
del C:\Temp\test3.txt

# 删除前确认
Remove-Item -Path C:\Temp\test.txt -Confirm

# 强制删除（即使只读）
Remove-Item -Path C:\Temp\test.txt -Force
```

### 任务 B：删除目录

```powershell
# 删除目录及其内容
Remove-Item -Path C:\Temp\TestFolder -Recurse

# 删除所有 txt 文件
Remove-Item -Path C:\Temp\*.txt
```

### 任务 C：安全删除

```powershell
# 模拟删除（预览）
Remove-Item -Path C:\Temp\* -WhatIf

# 先检查再删除
if (Test-Path C:\Temp\test.txt) {
    Remove-Item -Path C:\Temp\test.txt
    Write-Output "文件已删除"
} else {
    Write-Output "文件不存在"
}
```

---

## 练习 3.8：Test-Path 路径测试

**目标**：掌握路径测试的各种场景。

```powershell
# 测试文件是否存在
Test-Path C:\Windows\notepad.exe

# 测试目录是否存在
Test-Path C:\Windows

# 测试特定类型
Test-Path C:\Windows\notepad.exe -PathType Leaf
Test-Path C:\Windows -PathType Container

# 在条件中使用
if (Test-Path C:\Temp\test.txt) {
    Write-Output "文件存在"
    Get-Content C:\Temp\test.txt
} else {
    Write-Output "文件不存在"
    New-Item -ItemType File -Path C:\Temp\test.txt
}
```

---

## 练习 3.9：获取文件信息

**目标**：掌握文件属性的查看方法。

```powershell
# 获取文件对象
$file = Get-Item C:\Windows\notepad.exe

# 查看常用属性
$file.FullName
$file.Name
$file.BaseName
$file.Extension
$file.Length
$file.LastWriteTime
$file.CreationTime

# 获取文件哈希
Get-FileHash C:\Windows\notepad.exe -Algorithm SHA256

# 获取文件大小（格式化）
$size = (Get-Item C:\Windows\notepad.exe).Length
"$([math]::Round($size / 1KB, 2)) KB"
```

---

## 综合练习：文件管理器

**目标**：创建一个交互式文件管理器。

### 任务 1：创建目录结构

```powershell
# 在 study/ 目录下创建以下结构：
# project/
# ├── src/
# │   ├── modules/
# │   └── utils/
# ├── tests/
# ├── docs/
# └── config/

$basePath = "C:\Temp\study\project"

New-Item -ItemType Directory -Path "$basePath\src\modules" -Force
New-Item -ItemType Directory -Path "$basePath\src\utils" -Force
New-Item -ItemType Directory -Path "$basePath\tests" -Force
New-Item -ItemType Directory -Path "$basePath\docs" -Force
New-Item -ItemType Directory -Path "$basePath\config" -Force

# 在各目录创建 README 文件
Get-ChildItem $basePath -Recurse -Directory | ForEach-Object {
    $readmePath = Join-Path $_.FullName "README.txt"
    "目录: $($_.Name)" | Out-File -FilePath $readmePath
}
```

### 任务 2：备份脚本

```powershell
# 编写备份脚本
function Backup-Folder {
    param(
        [string]$SourcePath,
        [string]$BackupPath
    )

    if (-not (Test-Path $SourcePath)) {
        Write-Error "源目录不存在: $SourcePath"
        return
    }

    if (-not (Test-Path $BackupPath)) {
        New-Item -ItemType Directory -Path $BackupPath -Force
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $dest = Join-Path $BackupPath "backup_$timestamp"

    Write-Output "开始备份..."
    Write-Output "源: $SourcePath"
    Write-Output "目标: $dest"

    Copy-Item -Path $SourcePath -Destination $dest -Recurse

    Write-Output "备份完成！"
}

# 测试备份
Backup-Folder -SourcePath C:\Temp\study -BackupPath C:\Temp\backups
```

### 任务 3：清理脚本

```powershell
# 清理临时文件脚本
function Clean-TempFiles {
    param(
        [string]$Path,
        [int]$DaysOld = 7
    )

    $cutoffDate = (Get-Date).AddDays(-$DaysOld)

    Write-Output "清理路径: $Path"
    Write-Output "清理 $DaysOld 天前的文件"

    $files = Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $cutoffDate }

    Write-Output "找到 $($files.Count) 个文件需要清理"

    foreach ($file in $files) {
        Remove-Item -Path $file.FullName -Force
        Write-Output "已删除: $($file.Name)"
    }

    Write-Output "清理完成！"
}
```

---

## 扩展挑战

### 挑战 1：递归查找大文件

```powershell
# 找出指定目录下大于 100MB 的文件
function Find-LargeFiles {
    param(
        [string]$Path,
        [int]$MinSizeMB = 100
    )

    Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Length -gt ($MinSizeMB * 1MB) } |
        Sort-Object Length -Descending |
        Select-Object FullName,
            @{Name="SizeMB";Expression={[math]::Round($_.Length/1MB, 2)}},
            LastWriteTime |
        Format-Table -AutoSize
}

# 使用
Find-LargeFiles -Path C:\Windows -MinSizeMB 50
```

### 挑战 2：批量重命名

```powershell
# 按日期批量重命名文件
function Rename-ByDate {
    param([string]$Path)

    Get-ChildItem -Path $Path -File | ForEach-Object {
        $date = $_.LastWriteTime.ToString("yyyyMMdd")
        $newName = "${date}_$($_.Name)"
        Rename-Item -Path $_.FullName -NewName $newName
        Write-Output "重命名: $($_.Name) -> $newName"
    }
}
```

---

## 下一步

完成以上练习后，继续学习 [Lesson 4: 文本处理与管道](../04_text_processing/课程说明.md)
