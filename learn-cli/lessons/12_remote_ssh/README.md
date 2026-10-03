# Lesson 12: 远程操作与 SSH

> 掌握远程服务器管理、安全的文件传输、SSH 密钥管理

---

## 12.1 SSH 基础概念

### 什么是 SSH？

SSH（Secure Shell）是一种加密的网络协议，用于安全地远程登录到其他计算机。

```
SSH vs Telnet：

Telnet（不安全）：
  用户名、密码、命令都以明文传输
  任何人都能截获

SSH（安全）：
  所有通信都经过加密
  身份验证后建立安全通道
```

### SSH 连接原理

```
SSH 密钥认证流程：

1. 客户端发起连接请求
        ↓
2. 服务器发送自己的公钥（首次连接需要确认）
        ↓
3. 客户端验证服务器身份
        ↓
4. 双方协商会话密钥
        ↓
5. 建立加密通道
        ↓
6. 客户端使用私钥证明身份
        ↓
7. 连接建立
```

### Windows 上的 SSH

Windows 10/11 内置了 OpenSSH 客户端：

```powershell
# 检查 SSH 版本
ssh -V

# 测试 SSH 连接
ssh user@hostname

# SSH 命令格式
ssh [user@]hostname [command]
```

---

## 12.2 基本 SSH 操作

### 远程登录

```powershell
# 基本连接
ssh user@192.168.1.100

# 指定端口（默认 22）
ssh -p 2222 user@hostname

# 使用特定密钥
ssh -i ~/.ssh/mykey.pem user@hostname

# 指定用户
ssh hostname  # 使用当前用户名
ssh otheruser@hostname  # 指定用户

# 执行单个命令后退出
ssh user@hostname "ls -la"
ssh user@hostname "systemctl status nginx"
```

### SSH 配置

编辑 `~/.ssh/config` 文件：

```ssh-config
# 全局配置
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3

# 开发服务器
Host dev
    HostName 192.168.1.100
    User developer
    Port 22
    IdentityFile ~/.ssh/id_ed25519_dev

# 生产服务器
Host prod
    HostName production.example.com
    User admin
    Port 2222
    IdentityFile ~/.ssh/id_ed25519_prod

# GitHub
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github

# 简化连接
Host server1
    HostName server1.example.com
    User root
    IdentityFile ~/.ssh/server1_key
```

使用配置后简化连接：

```powershell
ssh dev        # 等于: ssh developer@192.168.1.100
ssh prod       # 等于: ssh admin@production.example.com -p 2222
```

---

## 12.3 SSH 密钥管理

### 生成 SSH 密钥

```powershell
# 生成 ED25519 密钥（推荐）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 生成 RSA 密钥（旧方式）
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 生成时指定保存位置和密码
ssh-keygen -t ed25519 -C "work" -f ~/.ssh/id_ed25519_work

# 交互式生成（默认位置）
ssh-keygen -t ed25519
```

### 密钥类型选择

| 类型 | 长度 | 安全性 | 兼容性 | 推荐度 |
|-----|------|--------|--------|-------|
| ED25519 | 256 位 | 很高 | 好（现代系统） | ⭐⭐⭐⭐⭐ |
| RSA | 4096 位 | 高 | 最好 | ⭐⭐⭐⭐ |
| RSA | 2048 位 | 中 | 最好 | ⭐⭐ |

### 密钥管理命令

```powershell
# 查看已生成的密钥
Get-ChildItem ~/.ssh

# 查看公钥内容
cat ~/.ssh/id_ed25519.pub
Get-Content ~/.ssh/id_ed25519.pub

# 复制公钥到服务器
ssh-copy-id user@hostname
# 或手动复制
cat ~/.ssh/id_ed25519.pub
# 登录服务器后粘贴到 ~/.ssh/authorized_keys

# 修改密钥密码
ssh-keygen -p -f ~/.ssh/id_ed25519

# 查看指纹
ssh-keygen -l -f ~/.ssh/id_ed25519.pub
```

---

## 12.4 SCP 文件传输

### 基本 SCP 命令

```powershell
# 上传本地文件到服务器
scp localfile.txt user@hostname:/remote/path/

# 下载服务器文件到本地
scp user@hostname:/remote/path/remotefile.txt local/path/

# 上传目录
scp -r localdir/ user@hostname:/remote/path/

# 下载目录
scp -r user@hostname:/remote/path/remotedir/ local/path/

# 指定端口
scp -P 2222 localfile.txt user@hostname:/remote/path/

# 使用密钥文件
scp -i ~/.ssh/mykey.pem localfile.txt user@hostname:/remote/path/
```

### SCP 常用参数

```powershell
scp [参数] 源 目标

# 常用参数：
-p  # 保留文件属性（修改时间、访问时间、权限）
-r  # 递归复制整个目录
-v  # 显示详细输出（调试用）
-C  # 启用压缩
-q  # 静默模式，不显示传输进度
-P  # 指定服务器端口（大写 P）
-i  # 指定私钥文件
```

### 批量传输

```powershell
# 传输多个文件
scp file1.txt file2.txt user@hostname:/remote/path/

# 使用通配符
scp *.txt user@hostname:/remote/path/

# 从远程到远程
scp user1@host1:/path/file.txt user2@host2:/path/
```

---

## 12.5 SFTP 交互式传输

### SFTP 基本操作

```powershell
# 启动 SFTP 连接
sftp user@hostname
sftp -i ~/.ssh/mykey.pem user@hostname

# SFTP 命令（本地命令前加 l）
sftp> help

# 文件操作
sftp> ls                    # 列出远程目录
sftp> lls                   # 列出本地目录
sftp> cd /remote/path       # 切换远程目录
sftp> lcd local/path        # 切换本地目录
sftp> get remote.txt        # 下载文件
sftp> put local.txt         # 上传文件
sftp> get -r remote_dir/    # 下载目录
sftp> put -r local_dir/     # 上传目录

# 权限和属性
sftp> chmod 755 file.txt    # 修改远程文件权限
sftp> lchmod 755 local.txt  # 修改本地文件权限

# 其他
sftp> pwd                   # 当前远程目录
sftp> lpwd                  # 当前本地目录
sftp> exit                  # 退出
```

### SFTP 批处理模式

```powershell
# 使用 -b 参数执行批处理文件
# batch.txt 内容：
#   cd /remote/path
#   put localfile.txt
#   get remotefile.txt
#   bye

sftp -b batch.txt user@hostname
```

---

## 12.6 rsync 同步

rsync 是比 scp 更智能的文件同步工具，只传输差异部分。

### 基本 rsync

```powershell
# 安装 rsync（Windows 需要 WSL 或 Git Bash）
# 在 WSL 中:
# sudo apt install rsync

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
```

### 常用 rsync 示例

```powershell
# 同步目录
rsync -avz ./my-project user@hostname:/var/www/

# 排除文件和目录
rsync -avz --exclude='node_modules' --exclude='.git' ./ user@hostname:/var/www/

# 模拟同步（预览）
rsync -avzn ./ user@hostname:/var/www/

# 删除目标中多余的文件
rsync -avz --delete ./ user@hostname:/var/www/

# 限制带宽
rsync -avz --bwlimit=1000 ./ user@hostname:/var/www/

# 同步时显示进度
rsync -avzP ./ user@hostname:/var/www/
```

---

## 12.7 远程命令执行

### 单命令执行

```powershell
# 执行简单命令
ssh user@hostname "uptime"
ssh user@hostname "df -h"
ssh user@hostname "free -m"

# 执行多条命令
ssh user@hostname "cd /app && ls -la && ./deploy.sh"

# 使用引号
ssh user@hostname 'for i in {1..5}; do echo $i; done'
```

### 远程脚本执行

```powershell
# 方法 1: 本地脚本远程执行
Get-Content local-script.ps1 | ssh user@hostname "powershell -"

# 方法 2: 复制脚本后执行
scp local-script.ps1 user@hostname:/tmp/
ssh user@hostname "powershell /tmp/local-script.ps1"

# 方法 3: 使用 here-string
ssh user@hostname @"
cd /app
git pull
docker-compose up -d --build
"@
```

### PowerShell SSH 会话

PowerShell 7+ 支持 SSH 会话：

```powershell
# 创建 SSH 会话
$session = New-PSSession -HostName hostname -UserName user -KeyFilePath ~/.ssh/id_ed25519

# 复制文件到远程
Copy-Item -ToSession $session -Path local.txt -Destination /remote/path/

# 从远程复制文件
Copy-Item -FromSession $session -Path /remote/path/file.txt -Destination local/

# 在远程执行命令
Invoke-Command -Session $session -ScriptBlock { ls -la /app }

# 关闭会话
Remove-PSSession $session
```

---

## 12.8 SSH 安全最佳实践

### 保护 SSH 密钥

```powershell
# 密钥文件权限（Linux/macOS）
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub

# Windows: 右键属性 → 安全 → 禁用继承，移除多余用户
```

### 服务器端 SSH 配置

编辑 `/etc/ssh/sshd_config`：

```sshd-config
# 禁用密码登录（强制密钥认证）
PasswordAuthentication no

# 禁用 root 登录
PermitRootLogin no

# 限制允许的用户
AllowUsers user1 user2

# 更改默认端口
Port 2222

# 禁用空密码
PermitEmptyPasswords no

# 设置空闲超时
ClientAliveInterval 300
ClientAliveCountMax 2

# 最大认证尝试次数
MaxAuthTries 3

# 使用强加密算法
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
```

### fail2ban 防暴力破解

```bash
# 安装 fail2ban
sudo apt install fail2ban

# 配置
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local

# 启用 SSH 保护
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
```

---

## 12.9 隧道与代理

### 本地端口转发

```powershell
# 将远程服务器的 3306（MySQL）映射到本地 3307
ssh -L 3307:localhost:3306 user@hostname

# 常用场景：
# 访问远程数据库
ssh -L 3306:localhost:3306 user@remote-db-server

# 访问内网服务
ssh -L 8080:localhost:80 user@gateway-server

# 多个端口转发
ssh -L 3306:localhost:3306 -L 5432:localhost:5432 user@hostname
```

### 动态端口转发（SOCKS 代理）

```powershell
# 创建 SOCKS 代理（本地 1080 端口）
ssh -D 1080 user@hostname

# 配置浏览器或系统使用 localhost:1080 作为代理
# 所有流量通过 SSH 隧道加密传输
```

### 反向隧道

```powershell
# 从远程服务器创建反向隧道到本地
# 在本地机器上执行：
ssh -R 8080:localhost:80 user@remote-server

# 现在可以通过 remote-server:8080 访问本地 80 端口
```

---

## 12.10 实用脚本

### 批量 SSH 命令

```powershell
# batch-ssh.ps1
param(
    [Parameter(Mandatory=$true)]
    [string[]]$Hosts,

    [Parameter(Mandatory=$true)]
    [string]$Command,

    [Parameter()]
    [string]$User = "root"
)

foreach ($host in $Hosts) {
    Write-Output "===== $host =====" -ForegroundColor Cyan
    ssh $User@$host $Command
    Write-Output ""
}
```

### 远程部署脚本

```powershell
# remote-deploy.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$Host,

    [Parameter(Mandatory=$true)]
    [string]$User,

    [Parameter()]
    [string]$KeyPath = "$env:USERPROFILE\.ssh\id_ed25519",

    [Parameter()]
    [string]$AppPath = "/var/www/myapp",

    [Parameter()]
    [string]$Branch = "main"
)

Write-Output "===== 开始部署到 $Host ====="

# 1. 拉取最新代码
Write-Output "拉取最新代码..."
ssh -i $KeyPath $User@$Host "cd $AppPath && git pull origin $Branch"

# 2. 安装依赖
Write-Output "安装依赖..."
ssh -i $KeyPath $User@$Host "cd $AppPath && pip install -r requirements.txt"

# 3. 运行测试
Write-Output "运行测试..."
$testResult = ssh -i $KeyPath $User@$Host "cd $AppPath && pytest tests/"
if ($testResult -match "FAILED") {
    Write-Error "测试失败，部署中止"
    exit 1
}

# 4. 重启服务
Write-Output "重启服务..."
ssh -i $KeyPath $User@$Host "cd $AppPath && systemctl restart myapp"

# 5. 检查状态
Write-Output "检查服务状态..."
ssh -i $KeyPath $User@$Host "systemctl status myapp --no-pager"

Write-Output "===== 部署完成 ====="
```

### 远程监控脚本

```powershell
# remote-monitor.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$Host,

    [Parameter()]
    [string]$User = "root",

    [Parameter()]
    [int]$Interval = 5
)

Write-Output "===== 远程监控: $Host ====="
Write-Output "按 Ctrl+C 停止"
Write-Output ""

while ($true) {
    $timestamp = Get-Date -Format "HH:mm:ss"

    # 获取远程服务器信息
    $uptime = ssh $User@$Host "uptime -p" 2>$null
    $cpu = ssh $User@$Host "top -bn1 | grep 'Cpu(s)' | awk '{print \$2}'" 2>$null
    $mem = ssh $User@$Host "free -m | grep Mem | awk '{print \$3\"MB / \"\$2\"MB\"}'" 2>$null
    $disk = ssh $User@$Host "df -h / | tail -1 | awk '{print \$5}'" 2>$null

    Write-Host "[$timestamp]" -ForegroundColor Cyan -NoNewline
    Write-Host " Uptime: $uptime | CPU: $cpu | MEM: $mem | Disk: $disk"

    Start-Sleep -Seconds $Interval
}
```

---

## 12.11 SSH 配置示例

### GitHub 配置

```powershell
# 1. 生成密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. 添加到 SSH agent
Start-Service ssh-agent
ssh-add ~/.ssh/id_ed25519

# 3. 复制公钥
Get-Content ~/.ssh/id_ed25519.pub | clip

# 4. 在 GitHub → Settings → SSH and GPG keys → New SSH key 粘贴
```

### GitLab 配置

同上，生成的公钥添加到 GitLab 的 SSH Keys 设置。

### 服务器配置

```powershell
# ~/.ssh/config 示例

# 阿里云服务器
Host aliyun-dev
    HostName 123.45.67.89
    User developer
    Port 22
    IdentityFile ~/.ssh/id_ed25519_aliyun

# AWS 服务器
Host aws-prod
    HostName ec2-12-345-67-890.compute-1.amazonaws.com
    User ec2-user
    Port 22
    IdentityFile ~/.ssh/id_ed25519_aws
    RequestTTY force

# 内网跳板机
Host bastion
    HostName bastion.internal.example.com
    User admin
    Port 2222
    IdentityFile ~/.ssh/id_ed25519_bastion

# 通过跳板机访问内网服务器
Host internal-server
    HostName 192.168.1.100
    User appuser
    ProxyJump bastion
    IdentityFile ~/.ssh/id_ed25519_internal
```

---

## 课后练习

1. 检查你的系统是否已安装 SSH：`ssh -V`
2. 生成一个 SSH 密钥对
3. 创建一个包含多个主机配置的 `~/.ssh/config` 文件
4. 练习使用 SCP 在本地和远程之间传输文件
5. 如果有远程服务器，尝试 SSH 连接并执行命令
6. 创建一个批量执行远程命令的脚本

---

## 课程总结

现在你已经掌握了完整的命令行技能体系：

```
学习路线回顾：
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

**建议**：每天在终端中练习一个命令，坚持一周后你会发现效率大幅提升。
