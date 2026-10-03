# Lesson 7 练习：网络操作

## 练习说明

本练习覆盖 Lesson 7 的所有核心概念。建议先通读 Lesson 7 教程，再完成以下练习。

---

## 练习 7.1：网络配置查看

**目标**：掌握网络配置信息的查看方法。

### 任务 A：ipconfig 命令

```powershell
# 查看 IP 配置
ipconfig

# 查看详细信息
ipconfig /all

# 刷新 DNS
# ipconfig /flushdns

# 显示 DNS 缓存
# ipconfig /displaydns
```

### 任务 B：PowerShell 网络命令

```powershell
# 查看网络适配器
Get-NetAdapter

# 查看网络适配器详情
Get-NetAdapter | Select-Object Name, Status, MacAddress, LinkSpeed

# 查看 IP 地址
Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias, IPAddress

# 查看 DHCP 配置
Get-NetIPInterface -AddressFamily IPv4 | Where-Object { $_.Dhcp -eq "Enabled" }
```

---

## 练习 7.2：网络连接测试

**目标**：掌握网络连通性测试方法。

### 任务 A：Test-Connection

```powershell
# 基本 ping
Test-Connection baidu.com

# ping 4 次
Test-Connection baidu.com -Count 4

# 快速 ping
Test-Connection baidu.com -Count 4 -Quick

# 获取本地网关
$gateway = (Get-NetRoute -DestinationPrefix "0.0.0.0/0").NextHop
Write-Output "网关: $gateway"

# ping 网关
Test-Connection $gateway -Count 2
```

### 任务 B：Test-NetConnection

```powershell
# 综合测试
Test-NetConnection baidu.com

# 测试特定端口
Test-NetConnection baidu.com -Port 443

# 测试常用端口
foreach ($port in @(80, 443, 22, 3389)) {
    $result = Test-NetConnection baidu.com -Port $port -WarningAction SilentlyContinue -InformationLevel Quiet
    Write-Output "端口 $port : $(if ($result) { '开放' } else { '关闭' })"
}
```

---

## 练习 7.3：端口与连接

**目标**：掌握端口和连接状态的查看方法。

### 任务 A：netstat 命令

```powershell
# 查看所有连接
netstat

# 显示进程 ID
netstat -ano

# 查看 TCP 连接
netstat -tcp -ano

# 查看监听端口
netstat -ano | Where-Object { $_ -match "LISTENING" }

# 查看连接统计
netstat -s
```

### 任务 B：PowerShell 查看连接

```powershell
# 查看活动的 TCP 连接
Get-NetTCPConnection -State Established |
    Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess |
    Select-Object -First 10

# 查看监听端口
Get-NetTCPConnection -State Listen |
    Select-Object LocalAddress, LocalPort, OwningProcess |
    Select-Object -First 10
```

### 任务 C：查找端口占用

```powershell
# 查找占用特定端口的进程
function Find-PortOwner {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($conn) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        Write-Output "端口 $Port 被进程: $($proc.Name) (PID: $($proc.Id))"
    } else {
        Write-Output "端口 $Port 未被占用"
    }
}

# 测试
Find-PortOwner -Port 80
Find-PortOwner -Port 443
```

---

## 练习 7.4：DNS 查询

**目标**：掌握 DNS 查询方法。

### 任务 A：nslookup

```powershell
# 基本查询
nslookup baidu.com

# 查询特定 DNS 服务器
nslookup baidu.com 8.8.8.8

# 反向查询
nslookup 8.8.8.8
```

### 任务 B：PowerShell DNS 命令

```powershell
# 解析域名
Resolve-DnsName baidu.com

# 查询 A 记录
Resolve-DnsName baidu.com -Type A

# 查询 MX 记录
Resolve-DnsName baidu.com -Type MX

# 查询 TXT 记录
Resolve-DnsName baidu.com -Type TXT

# 指定 DNS 服务器
Resolve-DnsName baidu.com -Server 8.8.8.8

# 反向查询
Resolve-DnsName 8.8.8.8 -Type PTR
```

---

## 练习 7.5：Web 请求与下载

**目标**：掌握 Web 请求和文件下载方法。

### 任务 A：Invoke-WebRequest

```powershell
# 获取网页
$response = Invoke-WebRequest -Uri "https://api.github.com"
$response.StatusCode
$response.Headers

# 下载文件
# Invoke-WebRequest -Uri "https://example.com/file.zip" -OutFile "$env:TEMP\file.zip"

# 带认证请求
# Invoke-WebRequest -Uri "https://api.example.com" -Headers @{"Authorization"="Bearer token"}
```

### 任务 B：Invoke-RestMethod

```powershell
# 调用 REST API
$response = Invoke-RestMethod -Uri "https://jsonplaceholder.typicode.com/posts/1"
$response | Format-List

# 获取 GitHub 数据（示例）
# $headers = @{"Accept" = "application/vnd.github.v3+json"}
# Invoke-RestMethod -Uri "https://api.github.com/repos/PowerShell/PowerShell" -Headers $headers
```

### 任务 C：下载测试

```powershell
# 简单下载测试
$testUrl = "https://httpbin.org/get"
try {
    $result = Invoke-WebRequest -Uri $testUrl -TimeoutSec 10
    Write-Output "下载成功！状态码: $($result.StatusCode)"
} catch {
    Write-Output "下载失败: $($_.Exception.Message)"
}
```

---

## 练习 7.6：网络诊断脚本

**目标**：综合运用网络命令进行诊断。

### 任务 A：批量端口扫描

```powershell
# 端口扫描函数
function Test-PortRange {
    param(
        [string]$Target = "localhost",
        [int]$StartPort = 80,
        [int]$EndPort = 100
    )

    Write-Output "扫描 $Target 的端口 $StartPort-$EndPort ..."
    Write-Output ""

    $results = @()
    for ($port = $StartPort; $port -le $EndPort; $port++) {
        $result = Test-NetConnection -ComputerName $Target -Port $port -WarningAction SilentlyContinue -InformationLevel Quiet
        if ($result) {
            $results += $port
            Write-Host "端口 $port : " -NoNewline
            Write-Host "开放" -ForegroundColor Green
        }
    }

    Write-Output ""
    Write-Output "扫描完成，发现 $($results.Count) 个开放端口"
    return $results
}

# 使用
Test-PortRange -Target "localhost" -StartPort 80 -EndPort 90
```

### 任务 B：网络速度测试

```powershell
# 简单的网络速度测试
function Test-DownloadSpeed {
    param(
        [string]$Url = "https://speed.cloudflare.com/__down?bytes=10000000",
        [int]$SizeMB = 10
    )

    Write-Output "测试下载速度（$SizeMB MB）..."

    $start = Get-Date
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing
        $end = Get-Date

        $duration = ($end - $start).TotalSeconds
        $sizeMB = $response.Content.Length / 1MB
        $speedMBps = $sizeMB / $duration

        Write-Output "下载大小: $([math]::Round($sizeMB, 2)) MB"
        Write-Output "下载时间: $([math]::Round($duration, 2)) 秒"
        Write-Output "下载速度: $([math]::Round($speedMBps, 2)) MB/s"
    } catch {
        Write-Output "测试失败: $($_.Exception.Message)"
    }
}

# 使用
Test-DownloadSpeed
```

### 任务 C：网络配置报告

```powershell
# 生成网络配置报告
function Get-NetworkReport {
    $report = @"
===== 网络配置报告 =====
生成时间: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

--- IP 配置 ---
$($host.UI.RawUI.WindowTitle)

--- 网络适配器 ---
"@

    $report += Get-NetAdapter | Select-Object Name, Status, MacAddress, LinkSpeed |
        Format-Table -AutoSize | Out-String

    $report += @"

--- IP 地址 ---
"@

    $report += Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias, IPAddress |
        Format-Table -AutoSize | Out-String

    $report += @"

--- DNS 服务器 ---
$((Get-DnsClientServerAddress -AddressFamily IPv4).ServerAddresses | Out-String)

--- 网络连接统计 ---
TCP 连接数: $((Get-NetTCPConnection).Count)
建立连接: $((Get-NetTCPConnection -State Established).Count)
监听端口: $((Get-NetTCPConnection -State Listen).Count)

--- 默认网关 ---
$((Get-NetRoute -DestinationPrefix "0.0.0.0/0").NextHop | Out-String)

============================
"@

    Write-Output $report
}

Get-NetworkReport
```

---

## 综合练习：网络监控工具

### 任务 1：连接监控

```powershell
# 监控网络连接变化
function Watch-NetworkConnections {
    $lastCount = (Get-NetTCPConnection -State Established).Count

    Write-Output "监控网络连接变化（按 Ctrl+C 停止）"
    Write-Output ""

    while ($true) {
        Start-Sleep -Seconds 5

        $currentCount = (Get-NetTCPConnection -State Established).Count
        $diff = $currentCount - $lastCount

        $time = Get-Date -Format "HH:mm:ss"
        $arrow = if ($diff -gt 0) { "↑" } elseif ($diff -lt 0) { "↓" } else { "=" }

        Write-Host "[$time] 连接数: $currentCount ($arrow $diff)"

        $lastCount = $currentCount
    }
}

# 使用（取消注释运行）：
# Watch-NetworkConnections
```

### 任务 2：DNS 缓存管理

```powershell
# DNS 缓存管理工具
function Manage-DnsCache {
    Write-Output "===== DNS 缓存管理 ====="
    Write-Output ""

    # 查看缓存大小
    $cache = Get-DnsClientCache -ErrorAction SilentlyContinue
    Write-Output "缓存条目数: $($cache.Count)"

    # 按类型分组
    $cache | Group-Object Type | Select-Object Name, Count |
        Sort-Object Count -Descending | Select-Object -First 10

    # 查看最近的查询
    Write-Output ""
    Write-Output "最近的 DNS 查询（按类型分组）："
    $cache | Select-Object Entry, RecordType, TimeToLive |
        Sort-Object TimeToLive |
        Select-Object -First 10
}

# 刷新 DNS 缓存（需要管理员）
# Clear-DnsClientCache
# Write-Output "DNS 缓存已清除"

Manage-DnsCache
```

---

## 扩展挑战

### 挑战：网站可用性监控

```powershell
# 监控网站可用性
function Test-WebsiteAvailability {
    param(
        [string[]]$Urls = @(
            "https://www.baidu.com",
            "https://www.google.com",
            "https://www.github.com"
        ),
        [int]$TimeoutSec = 10
    )

    Write-Output "===== 网站可用性监控 ====="
    Write-Output "监控时间: $(Get-Date)"
    Write-Output ""

    foreach ($url in $Urls) {
        $domain = $url -replace 'https?://', '' -replace '/.*', ''

        try {
            $start = Get-Date
            $response = Invoke-WebRequest -Uri $url -TimeoutSec $TimeoutSec -UseBasicParsing
            $duration = ((Get-Date) - $start).TotalMilliseconds

            Write-Host "$domain : " -NoNewline
            Write-Host "可用" -ForegroundColor Green
            Write-Host "  状态码: $($response.StatusCode) | 响应时间: $([math]::Round($duration, 0))ms"
        } catch {
            Write-Host "$domain : " -NoNewline
            Write-Host "不可用" -ForegroundColor Red
            Write-Host "  错误: $($_.Exception.Message)"
        }
    }
}

Test-WebsiteAvailability
```

---

## 下一步

完成以上练习后，继续学习 [Lesson 8: Git 命令行](../08_git_cli/README.md)
