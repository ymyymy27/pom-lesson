> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Lesson 5 练习：环境变量与配置

## 练习说明

本练习覆盖 Lesson 5 的所有核心概念。建议先通读 Lesson 5 教程，再完成以下练习。

---

## 练习 5.1：环境变量基础

**目标**：掌握环境变量的查看和访问方法。

### 任务 A：查看所有环境变量

```powershell
# 查看所有环境变量
Get-ChildItem Env:

# 统计数量
(Get-ChildItem Env:).Count

# 格式化显示
Get-ChildItem Env: | Format-Table Name, Value -AutoSize
```

### 任务 B：访问单个变量

```powershell
# 使用 $env: 前缀
$env:PATH
$env:USERPROFILE
$env:TEMP
$env:USERNAME
$env:COMPUTERNAME

# 访问不存在的变量
$env:NONEXISTENT  # 返回空字符串

# 测试变量是否存在
Test-Path Env:\PATH
```

### 任务 C：常见环境变量

```powershell
# 系统相关
$env:OS                    # 操作系统
$env:PROCESSOR_ARCHITECTURE  # CPU架构
$env:NUMBER_OF_PROCESSORS   # CPU核心数

# 路径相关
$env:USERPROFILE  # 用户目录
$env:HOMEDRIVE    # 主驱动器
$env:HOMEPATH     # 主路径
$env:TEMP         # 临时目录
$env:LOCALAPPDATA # 本地应用数据

# PowerShell 相关
$HOME             # 主目录（跨平台）
$PWD              # 当前目录
$PSVersionTable   # 版本信息
```

---

## 练习 5.2：PATH 环境变量

**目标**：掌握 PATH 变量的查看和修改。

### 任务 A：查看 PATH

```powershell
# 查看 PATH（原始）
$env:PATH

# 分行显示
$env:PATH -split ";"

# 格式化显示
$env:PATH -split ";" | ForEach-Object {
    Write-Output "  $_"
}

# 统计路径数量
($env:PATH -split ";").Count
```

### 任务 B：查找命令位置

```powershell
# 查找命令位置
Get-Command notepad | Select-Object Source
Get-Command python | Select-Object Source
Get-Command git | Select-Object Source

# 查找所有 python
Get-Command python* | Select-Object Name, Source
```

### 任务 C：添加临时路径

```powershell
# 临时添加到 PATH（当前会话）
$env:PATH += ";C:\MyTools\bin"

# 验证添加成功
$env:PATH -split ";" | Select-String "MyTools"

# 注意：关闭 PowerShell 后会失效
```

---

## 练习 5.3：环境变量作用域

**目标**：理解不同作用域的环境变量。

### 任务 A：查看不同作用域

```powershell
# 查看进程级变量
[Environment]::GetEnvironmentVariables("Process")

# 查看用户级变量
[Environment]::GetEnvironmentVariables("User")

# 查看系统级变量
[Environment]::GetEnvironmentVariables("Machine")
```

### 任务 B：设置不同作用域

```powershell
# 设置进程级（临时）
$env:TEST_VAR = "process-level"

# 设置用户级（永久）
[Environment]::SetEnvironmentVariable("TEST_VAR", "user-level", "User")

# 设置系统级（永久，需要管理员）
# [Environment]::SetEnvironmentVariable("TEST_VAR", "machine-level", "Machine")

# 读取验证
[Environment]::GetEnvironmentVariable("TEST_VAR", "User")
```

### 任务 C：刷新环境变量

```powershell
# 修改后刷新 PATH
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
             [Environment]::GetEnvironmentVariable("PATH", "User")

# 重新加载 profile
. $PROFILE
```

---

## 练习 5.4：PowerShell Profile

**目标**：掌握 Profile 的创建和配置。

### 任务 A：查看 Profile 信息

```powershell
# 查看 Profile 信息
$PROFILE

# 查看所有 Profile 类型
$PROFILE | Get-Member -MemberType NoteProperty

# 检查 Profile 是否存在
Test-Path $PROFILE

# 查看 Profile 目录
Split-Path -Parent $PROFILE
```

### 任务 B：创建 Profile

```powershell
# 获取 Profile 目录
$profileDir = Split-Path -Parent $PROFILE

# 创建目录（如果不存在）
if (-not (Test-Path $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force
}

# 创建 Profile 文件
New-Item -ItemType File -Path $PROFILE -Force

# 查看创建的文件
Get-Item $PROFILE
```

### 任务 C：编辑 Profile

```powershell
# 使用记事本打开
notepad $PROFILE

# 或使用 VS Code
# code $PROFILE

# 查看当前 Profile 内容
if (Test-Path $PROFILE) {
    Get-Content $PROFILE
}
```

---

## 练习 5.5：Profile 常用配置

**目标**：为 Profile 添加实用配置。

### 任务 A：自定义提示符

```powershell
# 在 Profile 中添加（需要重启 PowerShell 生效）
function prompt {
    $location = Get-Location
    $user = $env:USERNAME
    $git = ""  # 可添加 git 分支信息
    "[$user] $location$git > "
}
```

### 任务 B：设置别名

```powershell
# 在 Profile 中添加别名
Set-Alias -Name ll -Value Get-ChildItem
Set-Alias -Name grep -Value Select-String
Set-Alias -Name which -Value Get-Command

# 查看自定义别名
Get-Alias | Where-Object { $_.Description }
```

### 任务 C：添加函数

```powershell
# 在 Profile 中添加实用函数
function which {
    param([string]$cmd)
    Get-Command $cmd -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Source
}

function cdp {
    Set-Location C:\code\Projects
}

function mkcd {
    param([string]$dir)
    New-Item -ItemType Directory -Path $dir -Force
    Set-Location $dir
}
```

### 任务 D：设置默认参数

```powershell
# 设置默认参数值
$PSDefaultParameterValues = @{
    "Get-Process:ComputerName" = "localhost"
    "Get-Service:ComputerName" = "localhost"
}
```

---

## 练习 5.6：PowerShell 模块

**目标**：掌握模块的查看和使用。

### 任务 A：查看模块

```powershell
# 查看已加载的模块
Get-Module

# 查看所有可用模块
Get-Module -ListAvailable

# 按名称筛选
Get-Module -ListAvailable -Name "*git*"
Get-Module -ListAvailable -Name "*docker*"
```

### 任务 B：导入模块

```powershell
# 导入模块
# Import-Module ModuleName

# 查看模块导出的命令
# (Get-Module ModuleName).ExportedCommands

# 卸载模块
# Remove-Module ModuleName
```

---

## 综合练习：配置个性化环境

### 任务 1：创建完整的 Profile

```powershell
# 以下是推荐的 Profile 配置，添加到 $PROFILE 文件中

@"

# ========== PowerShell Profile ==========

# 1. 设置提示符颜色
$host.PrivateData.ErrorForegroundColor = "Red"
$host.PrivateData.WarningForegroundColor = "Yellow"
$host.PrivateData.VerboseForegroundColor = "Cyan"

# 2. 设置别名
Set-Alias -Name ll -Value Get-ChildItem
Set-Alias -Name grep -Value Select-String
Set-Alias -Name which -Value Get-Command

# 3. 设置函数
function which {
    param([string]`$cmd)
    Get-Command `$cmd -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Source
}

function temp {
    Set-Location `$env:TEMP
}

function home {
    Set-Location `$HOME
}

# 4. 设置默认参数
`$PSDefaultParameterValues = @{
    "Get-Process:ErrorAction" = "SilentlyContinue"
    "Get-Service:ErrorAction" = "SilentlyContinue"
}

# 5. 欢迎信息
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PowerShell 已启动" -ForegroundColor Green
Write-Host "  当前目录: $(Get-Location)" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

"@ | Out-File -FilePath $PROFILE -Encoding UTF8 -Append
```

### 任务 2：创建模块

```powershell
# 创建实用函数库模块
$moduleDir = "$HOME\Documents\PowerShell\Modules\MyUtils"
New-Item -ItemType Directory -Path $moduleDir -Force

# 创建模块文件 MyUtils.psm1
@"

function Get-SystemInfo {
    `@"
计算机名: `$env:COMPUTERNAME
用户名: `$env:USERNAME
操作系统: `$env:OS
CPU架构: `$env:PROCESSOR_ARCHITECTURE
核心数: `$env:NUMBER_OF_PROCESSORS
当前目录: `$PWD
PowerShell版本: `$PSVersionTable.PSVersion
"@
}

function Get-DiskInfo {
    Get-WmiObject -Class Win32_LogicalDisk -Filter "DriveType=3" |
        Select-Object DeviceID,
            `@{Name="TotalGB";Expression={`$_.Size / 1GB -as [int]}},
            `@{Name="FreeGB";Expression={`$_.FreeSpace / 1GB -as [int}},
            `@{Name="UsedPercent";Expression={[math]::Round((`$_.Size - `$_.FreeSpace) / `$_.Size * 100, 1)}}
}

function Clear-Temp {
    `$files = Get-ChildItem -Path `$env:TEMP -Recurse -File -ErrorAction SilentlyContinue
    `$files | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Output "已清理 `$(`$files.Count) 个临时文件"
}

Export-ModuleMember -Function Get-SystemInfo, Get-DiskInfo, Clear-Temp

"@ | Out-File -FilePath "$moduleDir\MyUtils.psm1" -Encoding UTF8

# 创建模块清单
@"
@{
    ModuleVersion = '1.0.0'
    Description = 'My utility functions'
    Author = 'User'
}
"@ | Out-File -FilePath "$moduleDir\MyUtils.psd1" -Encoding UTF8

# 导入并测试
Import-Module $moduleDir\MyUtils.psm1
Get-SystemInfo
Get-DiskInfo
```

### 任务 3：环境备份脚本

```powershell
# 备份当前环境配置的脚本
function Backup-Environment {
    param(
        [string]$BackupPath = "$HOME\Documents\PowerShell_Backup"
    )

    if (-not (Test-Path $BackupPath)) {
        New-Item -ItemType Directory -Path $BackupPath -Force
    }

    # 备份 Profile
    if (Test-Path $PROFILE) {
        Copy-Item -Path $PROFILE -Destination "$BackupPath\profile_backup.ps1"
        Write-Output "已备份 Profile"
    }

    # 备份别名
    Get-Alias | Export-Clixml "$BackupPath\aliases.xml"
    Write-Output "已备份别名"

    # 导出环境变量列表
    Get-ChildItem Env: | Select-Object Name, Value |
        Export-Csv "$BackupPath\environment_variables.csv" -NoTypeInformation
    Write-Output "已备份环境变量"

    Write-Output "备份完成！位置: $BackupPath"
}

Backup-Environment
```

---

## 扩展挑战

### 挑战 1：多机器同步 Profile

```powershell
# 使用 OneDrive/Git 同步 Profile
$onedrivePath = "$env:USERPROFILE\OneDrive\Documents\PowerShell"
$localPath = Split-Path -Parent $PROFILE

# 创建符号链接
# New-Item -ItemType SymbolicLink -Path $PROFILE -Target "$onedrivePath\Microsoft.PowerShell_profile.ps1" -Force
```

### 挑战 2：动态 Profile

```powershell
# 根据时间显示不同欢迎语
function prompt {
    $hour = (Get-Date).Hour
    $greeting = switch ($hour) {
        { $_ -lt 6 }  { "夜深了，注意休息" }
        { $_ -lt 12 } { "早上好" }
        { $_ -lt 14 } { "中午好" }
        { $_ -lt 18 } { "下午好" }
        { $_ -lt 22 } { "晚上好" }
        default       { "夜深了" }
    }

    "$greeting $(Get-Location)> "
}
```

---

## 下一步

完成以上练习后，继续学习 [Lesson 6: 进程与服务管理](../06_process_management/课程说明.md)
