# Lesson 7: 网络操作

> 网络诊断、文件下载、端口测试——用命令行掌握网络的一切

---

## 7.1 网络配置查看

### IP 配置（ipconfig）

```powershell
# 查看 IP 配置
ipconfig

# 查看详细信息
ipconfig /all

# 刷新 DNS
ipconfig /flushdns

# 显示 DNS 缓存
ipconfig /displaydns

# 释放 IP 地址（DHCP）
ipconfig /release

# 重新获取 IP 地址
ipconfig /renew

# 查看所有适配器
ipconfig /allcompartments /full
```

### PowerShell 网络命令

```powershell
# 查看网络适配器
Get-NetAdapter

# 查看网络适配器详细信息
Get-NetAdapter | Select-Object Name, Status, MacAddress, LinkSpeed

# 查看 IP 地址
Get-NetIPAddress

# 查看特定接口的 IP
Get-NetIPAddress -InterfaceAlias "以太网"

# 查看 IPv4 地址
Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias, IPAddress

# 查看 DHCP 配置
Get-NetIPInterface -AddressFamily IPv4 | Where-Object { $_.Dhcp -eq "Enabled" }
```

### 网络适配器信息

```powershell
# 查看网络适配器统计
Get-NetAdapterStatistics

# 查看适配器详细信息
Get-NetAdapter | Where-Object { $_.Status -eq "Up" } |
    Select-Object Name, MacAddress, LinkSpeed,
        @{Name="RxSpeed";Expression={$_.ReceiveLinkSpeed}},
        @{Name="TxSpeed";Expression={$_.TransmitLinkSpeed}}
```

---

## 7.2 网络连接测试

### Test-Connection（ping）

```powershell
# 基本 ping
Test-Connection baidu.com

# ping 指定次数
Test-Connection baidu.com -Count 4

# ping 本地网关
$gateway = (Get-NetRoute -DestinationPrefix "0.0.0.0/0").NextHop
Test-Connection $gateway -Count 2

# 快速 ping（不等待）
Test-Connection baidu.com -Count 4 -Quick

# 带详细信息的 ping
Test-Connection baidu.com -Count 4 | Format-Table *
```

### Test-NetConnection（综合测试）

```powershell
# 测试连接（类似 ping + traceroute）
Test-NetConnection baidu.com

# 测试端口
Test-NetConnection baidu.com -Port 443

# 测试端口（批量）
443, 80, 22, 3389 | ForEach-Object {
    $result = Test-NetConnection -ComputerName baidu.com -Port $_ -WarningAction SilentlyContinue
    [PSCustomObject]@{
        Port = $_
        Result = $result.TcpTestSucceeded
    }
}

# 指定源地址
Test-NetConnection -RemoteAddress baidu.com -SourceAddress 192.168.1.100
```

### 传统 ping 命令

```powershell
# Windows ping
ping baidu.com

# ping 4 次
ping -n 4 baidu.com

# 持续 ping（Ctrl+C 停止）
ping -t baidu.com

# 指定数据包大小
ping -l 1000 baidu.com
```

---

## 7.3 端口与连接

### netstat（查看网络连接）

```powershell
# 查看所有连接
netstat

# 显示进程 ID
netstat -ano

# 只显示 TCP 连接
netstat -tcp -ano

# 只显示 UDP 连接
netstat -udp -ano

# 显示监听端口
netstat -ano | Where-Object { $_ -match "LISTENING" }

# 显示路由表
netstat -r

# 显示以太网统计
netstat -e

# 显示 TCP 连接数统计
netstat -s -p tcp
```

### PowerShell 查看连接

```powershell
# 查看活动的 TCP 连接
Get-NetTCPConnection |
    Where-Object { $_.State -eq "Established" } |
    Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess

# 查看监听端口
Get-NetTCPConnection |
    Where-Object { $_.State -eq "Listen" } |
    Select-Object LocalAddress, LocalPort, OwningProcess

# 查看特定进程的连接
Get-NetTCPConnection -OwningProcess (Get-Process -Name python).Id

# 查看 UDP 端点
Get-NetUDPEndpoint
```

### 查找端口占用

```powershell
# 查找占用特定端口的进程
$port = 8080
$connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($connection) {
    $process = Get-Process -Id $connection.OwningProcess
    Write-Output "端口 $port 被进程: $($process.Name) (PID: $($process.Id)) 占用"
} else {
    Write-Output "端口 $port 未被占用"
}

# 列出所有端口占用
Get-NetTCPConnection -State Listen |
    ForEach-Object {
        $process = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        [PSCustomObject]@{
            Port = $_.LocalPort
            Process = $process.Name
            PID = $_.OwningProcess
        }
    } | Sort-Object Port | Format-Table -AutoSize
```

---

## 7.4 DNS 查询

### nslookup

```powershell
# 基本查询
nslookup baidu.com

# 查询特定 DNS 服务器
nslookup baidu.com 8.8.8.8

# 反向查询（IP → 域名）
nslookup 8.8.8.8

# 查询 MX 记录
nslookup -type=MX baidu.com

# 查询 TXT 记录
nslookup -type=TXT baidu.com
```

### PowerShell DNS 命令

```powershell
# 解析域名
Resolve-DnsName baidu.com

# 查询 A 记录
Resolve-DnsName baidu.com -Type A

# 查询 MX 记录
Resolve-DnsName baidu.com -Type MX

# 查询 TXT 记录
Resolve-DnsName baidu.com -Type TXT

# 反向查询
Resolve-DnsName 8.8.8.8 -Type PTR

# 指定 DNS 服务器
Resolve-DnsName baidu.com -Server 8.8.8.8

# 列出域的 DNS 服务器
Resolve-DnsName baidu.com -Type NS
```

### hosts 文件

```powershell
# 查看 hosts 文件
Get-Content C:\Windows\System32\drivers\etc\hosts

# 添加 hosts 条目（需要管理员权限）
$entry = "127.0.0.1`tmysite.local"
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value $entry
```

---

## 7.5 Web 请求与下载

### Invoke-WebRequest

```powershell
# 获取网页内容
Invoke-WebRequest -Uri "https://api.github.com"

# 获取响应头
$response = Invoke-WebRequest -Uri "https://www.baidu.com" -Method Head

# 下载文件
Invoke-WebRequest -Uri "https://example.com/file.zip" -OutFile "C:\Downloads\file.zip"

# 带认证的请求
Invoke-WebRequest -Uri "https://api.example.com" -Headers @{"Authorization"="Bearer token123"}

# 发送 POST 请求
Invoke-WebRequest -Uri "https://api.example.com/data" -Method POST -Body '{"key":"value"}'

# 设置超时
Invoke-WebRequest -Uri "https://slow-site.com" -TimeoutSec 30
```

### Invoke-RestMethod（JSON/API 专用）

```powershell
# 调用 REST API（自动解析 JSON）
$response = Invoke-RestMethod -Uri "https://jsonplaceholder.typicode.com/posts/1"
$response.title

# 获取 GitHub API 数据
$headers = @{
    "Accept" = "application/vnd.github.v3+json"
}
Invoke-RestMethod -Uri "https://api.github.com/repos/PowerShell/PowerShell" -Headers $headers

# 发送 JSON 数据
$body = @{
    title = "Test Post"
    body = "This is a test"
    userId = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://jsonplaceholder.typicode.com/posts" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

### wget / curl 别名

```powershell
# PowerShell 5.1+ 有 curl 别名（实际调用 Invoke-WebRequest）
curl https://api.github.com

# PowerShell 7+ 的 curl 是真正的 curl
# 建议使用 Invoke-WebRequest 以保持一致
```

### 下载实用示例

```powershell
# 下载文件并显示进度
$url = "https://example.com/largefile.zip"
$output = "C:\Downloads\largefile.zip"
$webClient = New-Object System.Net.WebClient
$webClient.DownloadFile($url, $output)

# 带进度条的下载
$wc = New-Object System.Net.WebClient
$url = "https://example.com/file.zip"
$output = "C:\Downloads\file.zip"
$wc.DownloadFileAsync($url, $output)

# 检查下载速度
Measure-Command {
    Invoke-WebRequest -Uri "https://speed.cloudflare.com/__down?bytes=10000000" -OutFile $null
}
```

---

## 7.6 路由追踪

### tracert

```powershell
# 跟踪路由
tracert baidu.com

# 跟踪路由（最大跳数）
tracert -h 20 baidu.com

# 强制使用 IP 地址
tracert -d baidu.com  # 不解析域名

# 等待每次回复的超时
tracert -w 1000 baidu.com  # 1秒
```

### Test-NetConnection（带 traceroute）

```powershell
# 同时测试连接和追踪路由
Test-NetConnection baidu.com -TraceRoute
```

---

## 7.7 网络诊断脚本

### 批量端口扫描

```powershell
# 扫描本地常用端口
$ports = @(21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3306, 3389, 5432, 8080)
$target = "localhost"

foreach ($port in $ports) {
    $result = Test-NetConnection -ComputerName $target -Port $port -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($result) {
        Write-Host "端口 $port - 开放" -ForegroundColor Green
    } else {
        Write-Host "端口 $port - 关闭" -ForegroundColor Red
    }
}
```

### 网络速度测试

```powershell
# 测试下载速度（使用 Cloudflare）
$url = "https://speed.cloudflare.com/__down?bytes=25000000"
$start = Get-Date

try {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing
    $end = Get-Date
    $duration = ($end - $start).TotalSeconds
    $sizeMB = $response.Content.Length / 1MB
    $speedMBps = $sizeMB / $duration
    Write-Output "下载速度: $([math]::Round($speedMBps, 2)) MB/s"
} catch {
    Write-Error "测试失败: $_"
}
```

### 检查网络配置

```powershell
# 网络配置报告脚本
@"
===== 网络配置报告 =====
生成时间: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

--- IP 配置 ---
$($host.UI.RawUI.WindowTitle)
$(ipconfig /all | Out-String)

--- DNS 服务器 ---
$((Get-DnsClientServerAddress -AddressFamily IPv4).ServerAddresses | Out-String)

--- 网络连接 ---
TCP 连接数: $((Get-NetTCPConnection).Count)
建立连接: $((Get-NetTCPConnection -State Established).Count)
监听端口: $((Get-NetTCPConnection -State Listen).Count)

--- 默认网关 ---
$((Get-NetRoute -DestinationPrefix "0.0.0.0/0").NextHop | Out-String)
"@ | Out-File -FilePath C:\Logs\network-report.txt -Encoding UTF8
Write-Output "报告已保存到 C:\Logs\network-report.txt"
```

---

## 7.8 防火墙基础

### Windows 防火墙状态

```powershell
# 查看防火墙状态
Get-NetFirewallProfile

# 查看入站规则
Get-NetFirewallRule | Where-Object { $_.Enabled -eq $true -and $_.Direction -eq "Inbound" }

# 查看出站规则
Get-NetFirewallRule | Where-Object { $_.Enabled -eq $true -and $_.Direction -eq "Outbound" }

# 查找特定程序的规则
Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*Python*" }
```

### 防火墙开关

```powershell
# 关闭防火墙（需要管理员权限）
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False

# 开启防火墙
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

# 查看特定端口的防火墙规则
Get-NetFirewallPortFilter | Where-Object { $_.LocalPort -eq 8080 }
```

---

## 7.9 代理设置

```powershell
# 查看当前代理设置
Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"

# 设置系统代理
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" `
    -Name ProxyEnable -Value 1
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" `
    -Name ProxyServer -Value "proxy.example.com:8080"

# 关闭代理
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" `
    -Name ProxyEnable -Value 0

# 查看 PowerShell 会话的代理设置
[System.Net.WebRequest]::DefaultWebProxy
```

---

## 7.10 常见问题

### Q1: 无法连接到某个网站

**诊断步骤**：
```powershell
# 1. 测试 DNS 解析
Resolve-DnsName website.com

# 2. 测试网络连接
Test-NetConnection website.com -Port 443

# 3. 测试 ping
Test-Connection website.com -Count 3

# 4. 查看路由
Test-NetConnection website.com -TraceRoute
```

### Q2: 端口被占用

**解决方法**：
```powershell
# 1. 找到占用端口的进程
$port = 8080
$pid = (Get-NetTCPConnection -LocalPort $port).OwningProcess

# 2. 关闭进程
Stop-Process -Id $pid -Force
```

### Q3: DNS 解析失败

**解决方法**：
```powershell
# 1. 刷新 DNS 缓存
ipconfig /flushdns

# 2. 更换 DNS 服务器
Set-DnsClientServerAddress -InterfaceAlias "以太网" -ServerAddresses ("8.8.8.8", "8.8.4.4")

# 3. 使用公共 DNS
Resolve-DnsName website.com -Server 8.8.8.8
```

---

## 课后练习

1. 运行 `ipconfig /all` 查看你的网络配置
2. 使用 `Test-NetConnection` 测试 baidu.com 的 443 端口
3. 使用 `Get-NetTCPConnection` 查看当前所有 TCP 连接
4. 使用 `Resolve-DnsName` 查询几个域名的 IP 地址
5. 使用 `Invoke-WebRequest` 下载一个网页并查看内容
6. 编写一个端口扫描脚本，扫描本地端口 80-100

---

## 下一步

→ [Lesson 8: Git 命令行](../08_git_cli/README.md)
