> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Lesson 12 练习：远程操作与 SSH

## 练习说明

本练习覆盖 Lesson 12 的所有核心概念。建议先通读 Lesson 12 教程，再完成以下练习。

> **注意**：以下练习中涉及远程服务器的练习需要你有可用的 SSH 服务器。如果没有，可以跳过需要连接的练习，重点练习本地 SSH 配置和密钥管理。

---

## 练习 12.1：SSH 环境验证

**目标**：检查 SSH 安装和版本。

### 任务 A：检查 SSH 版本

```powershell
# 检查 OpenSSH 版本
ssh -V

# 检查 SSH 客户端可用性
Get-Command ssh -ErrorAction SilentlyContinue
```

### 任务 B：SSH 配置文件位置

```powershell
# 查看 SSH 配置目录
$ sshDir = "$env:USERPROFILE\.ssh"
Test-Path $sshDir

# 查看目录内容
if (Test-Path $sshDir) {
    Get-ChildItem $sshDir
}
```

---

## 练习 12.2：SSH 密钥管理

**目标**：掌握 SSH 密钥的生成和管理。

### 任务 A：生成 SSH 密钥

```powershell
# 生成 ED25519 密钥（推荐）
$email = Read-Host "请输入邮箱地址（用于密钥注释）"
ssh-keygen -t ed25519 -C $email

# 查看生成的密钥
Get-ChildItem "$env:USERPROFILE\.ssh" -Filter "id_*"
```

### 任务 B：查看和管理密钥

```powershell
# 查看公钥内容
$pubKeyPath = "$env:USERPROFILE\.ssh\id_ed25519.pub"
if (Test-Path $pubKeyPath) {
    Get-Content $pubKeyPath
    # 复制到剪贴板
    Get-Content $pubKeyPath | Set-Clipboard
    Write-Output "公钥已复制到剪贴板"
}

# 查看密钥指纹
ssh-keygen -l -f "$env:USERPROFILE\.ssh\id_ed25519.pub"

# 修改密钥密码
# ssh-keygen -p -f "$env:USERPROFILE\.ssh\id_ed25519"
```

---

## 练习 12.3：SSH 配置

**目标**：掌握 SSH 客户端配置。

### 任务 A：创建 SSH 配置

```powershell
# 创建 SSH 配置目录
$sshDir = "$env:USERPROFILE\.ssh"
if (-not (Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force
}

# 创建 SSH config 文件
$configPath = Join-Path $sshDir "config"

@"
# 全局配置
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3

# 示例：开发服务器
# Host dev
#     HostName 192.168.1.100
#     User developer
#     Port 22
#     IdentityFile ~/.ssh/id_ed25519

# 示例：GitHub
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519

# 示例：生产服务器
# Host prod
#     HostName production.example.com
#     User admin
#     Port 2222
#     IdentityFile ~/.ssh/id_ed25519_prod
"@ | Out-File -FilePath $configPath -Encoding UTF8

Write-Output "SSH 配置文件已创建: $configPath"
```

### 任务 B：设置配置文件权限

```powershell
# Windows 下确保配置文件权限正确
$configPath = "$env:USERPROFILE\.ssh\config"

# 查看当前权限
Get-Acl $configPath | Select-Object Owner, Group

# 建议：移除其他用户的读取权限（Windows 特殊处理）
icacls $configPath /inheritance:r
icacls $configPath /grant:r "$env:USERNAME:R"
```

---

## 练习 12.4：SCP 文件传输

**目标**：掌握本地文件传输操作。

### 任务 A：SCP 基本操作（本地模拟）

```powershell
# 创建测试文件
$testDir = "$env:TEMP\scp-test"
New-Item -ItemType Directory -Path "$testDir\source" -Force | Out-Null
New-Item -ItemType Directory -Path "$testDir\dest" -Force | Out-Null

# 创建测试文件
"Test content 1" | Out-File -FilePath "$testDir\source\file1.txt" -Encoding UTF8
"Test content 2" | Out-File -FilePath "$testDir\source\file2.txt" -Encoding UTF8

Write-Output "测试文件已创建"
ls "$testDir\source"

# 本地复制（使用 PowerShell 等效命令）
Copy-Item -Path "$testDir\source\*" -Destination "$testDir\dest\" -Force
Write-Output ""
Write-Output "文件已复制到目标目录"
ls "$testDir\dest"

# 清理
Remove-Item -Path $testDir -Recurse -Force
Write-Output ""
Write-Output "测试目录已清理"
```

### 任务 B：SCP 命令参考

```powershell
# 以下是 SCP 命令参考，实际使用需要远程服务器

# 上传本地文件到服务器
# scp localfile.txt user@hostname:/remote/path/

# 下载服务器文件到本地
# scp user@hostname:/remote/path/remotefile.txt local/path/

# 上传目录
# scp -r localdir/ user@hostname:/remote/path/

# 下载目录
# scp -r user@hostname:/remote/path/remotedir/ local/path/

# 使用特定密钥
# scp -i ~/.ssh/mykey.pem localfile.txt user@hostname:/remote/path/
```

---

## 练习 12.5：SFTP 操作

**目标**：掌握 SFTP 的基本操作。

### 任务 A：SFTP 命令参考

```powershell
# SFTP 基本命令参考

# 连接
# sftp user@hostname
# sftp -i ~/.ssh/mykey.pem user@hostname

# SFTP 交互命令
@"
常用 SFTP 命令：
==================
ls                    # 列出远程目录
lls                   # 列出本地目录
cd /path              # 切换远程目录
lcd local/path        # 切换本地目录
get remote.txt        # 下载文件
put local.txt         # 上传文件
get -r remote_dir/    # 下载目录
put -r local_dir/     # 上传目录
pwd                   # 当前远程目录
lpwd                  # 当前本地目录
exit                  # 退出
help                  # 显示帮助
"@
```

### 任务 B：SFTP 批处理

```powershell
# 创建 SFTP 批处理脚本
$sftpScript = @"
cd /remote/path
put localfile.txt
get remotefile.txt
bye
"@

Write-Output "SFTP 批处理脚本示例："
Write-Output $sftpScript
Write-Output ""
Write-Output "使用方式：sftp -b script.txt user@hostname"
```

---

## 练习 12.6：rsync 同步

**目标**：了解 rsync 的使用场景。

### 任务 A：rsync 命令参考

```powershell
# rsync 基本命令参考

@"
rsync 常用命令：
==================

# 基本同步（本地）
rsync -av source/ destination/

# 通过 SSH 同步
rsync -avz -e ssh source/ user@hostname:/remote/path/

# 参数说明：
# -a: 归档模式（保留权限、时间、链接等）
# -v: 详细输出
# -z: 压缩传输
# -n: 模拟运行（预览）
# --delete: 删除目标中源没有的文件
# --exclude: 排除文件

# 示例：
rsync -avz --exclude='node_modules' --exclude='.git' ./ user@hostname:/var/www/
rsync -avzn ./ user@hostname:/var/www/  # 预览

注意：Windows 需要 WSL 或 Git Bash 来运行 rsync
"@
```

---

## 练习 12.7：远程命令执行

**目标**：掌握远程命令执行方法。

### 任务 A：SSH 命令执行参考

```powershell
# SSH 执行远程命令

@"
SSH 远程命令执行：
==================

# 执行单个命令
ssh user@hostname "uptime"
ssh user@hostname "df -h"
ssh user@hostname "free -m"

# 执行多条命令
ssh user@hostname "cd /app && ls -la && ./deploy.sh"

# 在 PowerShell 中执行
Invoke-Expression "ssh user@hostname 'ls -la'"
"@
```

### 任务 B：PowerShell SSH 会话（PowerShell 7+）

```powershell
# PowerShell SSH 会话参考

@"
PowerShell SSH 会话（PowerShell 7+）：
=====================================

# 创建 SSH 会话
`$session = New-PSSession -HostName hostname -UserName user -KeyFilePath ~/.ssh/id_ed25519

# 在远程执行命令
Invoke-Command -Session `$session -ScriptBlock { Get-Process }

# 复制文件到远程
Copy-Item -ToSession `$session -Path local.txt -Destination /remote/path/

# 从远程复制文件
Copy-Item -FromSession `$session -Path /remote/path/file.txt -Destination local/

# 关闭会话
Remove-PSSession `$session

注意：需要 PowerShell 7+ 和 OpenSSH
"@
```

---

## 综合练习：SSH 工具脚本

### 任务 1：SSH 配置生成器

```powershell
# 创建 SSH 配置生成器
@"
param(
    [Parameter(Mandatory=`$true)]
    [string]`$HostName,

    [Parameter()]
    [string]`$User = "root",

    [Parameter()]
    [int]`$Port = 22,

    [Parameter()]
    [string]`$KeyPath = "`$(`$env:USERPROFILE)\.ssh\id_ed25519",

    [Parameter()]
    [string]`$Alias
)

`$sshDir = "`$(`$env:USERPROFILE)\.ssh"
if (-not (Test-Path `$sshDir)) {
    New-Item -ItemType Directory -Path `$sshDir -Force | Out-Null
}

`$configPath = Join-Path `$sshDir "config"
`$aliasName = if (`$Alias) { `$Alias } else { `$HostName -replace '\..*$', '' }

`$entry = @"

Host `$aliasName
    HostName `$HostName
    User `$User
    Port `$Port
    IdentityFile `$(`$KeyPath -replace '\\', '/')
"@

# 检查是否已存在
if (Test-Path `$configPath) {
    `$existing = Get-Content `$configPath -Raw
    if (`$existing -match "`$(`$aliasName)`$") {
        Write-Warning "主机别名 `$aliasName 已存在"
        `$confirm = Read-Host "是否覆盖？(y/n)"
        if (`$confirm -ne "y") {
            Write-Output "已取消"
            exit 0
        }
    }
}

# 添加配置
`$entry | Out-File -FilePath `$configPath -Append -Encoding UTF8

Write-Output "SSH 配置已添加："
Write-Output `$entry
Write-Output ""
Write-Output "现在可以使用: ssh `$aliasName"
"@ | Out-File -FilePath "$env:TEMP\ssh-config-add.ps1" -Encoding UTF8

# 测试添加配置
& "$env:TEMP\ssh-config-add.ps1" -HostName "example.com" -User "developer" -Alias "example"

# 查看配置文件
Write-Output ""
Write-Output "当前 SSH 配置："
Get-Content "$env:USERPROFILE\.ssh\config"
```

### 任务 2：SSH 连接测试

```powershell
# 创建 SSH 连接测试脚本
@"
param(
    [Parameter()]
    [string]`$Host = "github.com"
)

`$ErrorActionPreference = "Stop"

Write-Output "===== SSH 连接测试 ====="
Write-Output "测试主机: `$(`$Host)"
Write-Output ""

# 解析主机名
`$resolved = Resolve-DnsName `$Host -ErrorAction SilentlyContinue
if (`$resolved) {
    Write-Output "DNS 解析: " -NoNewline
    Write-Host "成功" -ForegroundColor Green
    Write-Output "  IP: `$(`$resolved.IPAddress)"
} else {
    Write-Output "DNS 解析: " -NoNewline
    Write-Host "失败" -ForegroundColor Red
}

# 测试端口
`$portOpen = Test-NetConnection -ComputerName `$Host -Port 22 -WarningAction SilentlyContinue -InformationLevel Quiet
Write-Output "SSH 端口 (22): " -NoNewline
if (`$portOpen) {
    Write-Host "开放" -ForegroundColor Green
} else {
    Write-Host "关闭或被阻止" -ForegroundColor Red
}

# 测试 HTTPS 端口（GitHub 需要）
`$httpsOpen = Test-NetConnection -ComputerName `$Host -Port 443 -WarningAction SilentlyContinue -InformationLevel Quiet
Write-Output "HTTPS 端口 (443): " -NoNewline
if (`$httpsOpen) {
    Write-Host "开放" -ForegroundColor Green
} else {
    Write-Host "关闭或被阻止" -ForegroundColor Red
}

Write-Output ""
Write-Output "测试完成"
"@ | Out-File -FilePath "$env:TEMP\ssh-test.ps1" -Encoding UTF8

# 测试
& "$env:TEMP\ssh-test.ps1" -Host "github.com"
```

### 任务 3：批量远程命令

```powershell
# 创建批量远程命令脚本
@"
param(
    [Parameter(Mandatory=`$true)]
    [string[]]`$Hosts,

    [Parameter(Mandatory=`$true)]
    [string]`$Command,

    [Parameter()]
    [string]`$User = "root",

    [Parameter()]
    [string]`$KeyPath
)

`$ErrorActionPreference = "Continue"

Write-Output "===== 批量 SSH 命令执行 ====="
Write-Output "命令: `$(`$Command)"
Write-Output ""

foreach (`$host in `$Hosts) {
    Write-Host "`$(`$host)" -ForegroundColor Cyan
    Write-Host ("=" * 40)

    try {
        if (`$KeyPath) {
            `$result = ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i `$KeyPath "`$(`$User)@`$(`$host)" `$Command 2>&1
        } else {
            `$result = ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "`$(`$User)@`$(`$host)" `$Command 2>&1
        }

        if (`$LASTEXITCODE -eq 0) {
            Write-Output `$result
        } else {
            Write-Warning "命令执行失败"
            Write-Output `$result
        }
    } catch {
        Write-Error "连接失败: `$(`$_.Exception.Message)"
    }

    Write-Output ""
}

Write-Output "执行完成"
"@ | Out-File -FilePath "$env:TEMP\batch-ssh.ps1" -Encoding UTF8

Write-Output "批量 SSH 脚本已创建"
Write-Output ""
Write-Output "使用示例："
Write-Output "  .\`$(`$env:TEMP)\batch-ssh.ps1 -Hosts @('host1', 'host2') -Command 'uptime' -User admin"
```

---

## 练习 12.8：SSH 安全最佳实践

**目标**：了解 SSH 安全配置。

### 任务 A：密钥权限设置

```powershell
# SSH 安全最佳实践

@"
SSH 安全最佳实践：
==================

1. 密钥文件权限
----------------
Windows: 使用 icacls 设置权限
  icacls `$env:USERPROFILE\.ssh\id_ed25519 /inheritance:r
  icacls `$env:USERPROFILE\.ssh\id_ed25519 /grant:r `$env:USERNAME:R

2. 禁用密码登录（服务器端）
----------------
编辑 /etc/ssh/sshd_config:
  PasswordAuthentication no
  PubkeyAuthentication yes

3. 禁用 root 登录（服务器端）
----------------
编辑 /etc/ssh/sshd_config:
  PermitRootLogin no

4. 更改默认端口
----------------
编辑 /etc/ssh/sshd_config:
  Port 2222

5. 限制登录用户
----------------
编辑 /etc/ssh/sshd_config:
  AllowUsers user1 user2

6. 设置空闲超时
----------------
编辑 /etc/ssh/sshd_config:
  ClientAliveInterval 300
  ClientAliveCountMax 2
"@

# 查看当前密钥权限
$keyPath = "$env:USERPROFILE\.ssh\id_ed25519"
if (Test-Path $keyPath) {
    Write-Output ""
    Write-Output "当前密钥权限："
    icacls $keyPath
}
```

---

## 清理练习文件

```powershell
# 清理练习文件
Remove-Item "$env:TEMP\ssh-config-add.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\ssh-test.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\batch-ssh.ps1" -Force -ErrorAction SilentlyContinue

Write-Output "练习文件已清理"
```

---

## 下一步

完成以上练习后，你已经完成了 **learn-cli** 的全部 12 课的学习！

回顾课程总结：
```
✅ Lesson 1: Shell 基础概念
✅ Lesson 2: PowerShell 核心语法
✅ Lesson 3: 文件系统操作
✅ Lesson 4: 文本处理与管道
✅ Lesson 5: 环境变量与配置
✅ Lesson 6: 进程与服务管理
✅ Lesson 7: 网络操作
✅ Lesson 8: Git 命令行
✅ Lesson 9: Docker 命令行
✅ Lesson 10: 脚本编程与自动化
✅ Lesson 11: 开发工作流实战
✅ Lesson 12: 远程操作与 SSH
```

**建议**：每天练习一个命令，坚持一周后你会发现效率大幅提升！
