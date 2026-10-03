# 第3课：SSH 隧道与端口转发 —— 打通内网服务

## 1. 为什么 SSH 是协作的基础工具

SSH 不只是"远程登录服务器"，它自带三条加密通道能力：

1. **本地转发（-L）**：把本地端口的数据，经 SSH 送到远程可达的目标；
2. **远程转发（-R）**：让远端访问到"你本地的服务"；
3. **动态转发（-D）**：在本地开一个 SOCKS 代理，所有流量走 SSH 出口。

只要**有一台双方都能访问的服务器**（跳板机/云服务器），就能把原本
隔离的两个网络"缝"起来。这是跨网段协作最轻量的方案，**不需要任何额外软件**。

> 前提：你有一台 SSH 可达的机器。云服务器、公司跳板机都可以。

---

## 2. SSH 密钥认证（先做好这一步）

密码登录容易被爆破，隧道长期使用必须用密钥。

```bash
# 生成密钥（一路回车即可）
ssh-keygen -t ed25519 -C "你的邮箱或备注"

# 查看公钥
cat ~/.ssh/id_ed25519.pub
```

把公钥内容追加到服务器的 `~/.ssh/authorized_keys`：

```bash
ssh-copy-id user@server-ip
# 没有 ssh-copy-id 时手动追加：
# ssh user@server-ip "mkdir -p ~/.ssh && echo '你的公钥' >> ~/.ssh/authorized_keys"
```

测试：

```bash
ssh user@server-ip
```

---

## 3. 本地转发 -L：访问远程内网的服务

### 3.1 典型场景

数据库只允许内网访问（`db.internal:5432`），你在本地无法直连，
但可以 SSH 到内网的一台跳板机 `jump.example.com`。

### 3.2 命令

```bash
ssh -L 5432:db.internal:5432 user@jump.example.com
```

含义：

```text
本机 5432 ──SSH 加密──> 跳板机 ──> db.internal:5432
```

之后，**在本机用 `127.0.0.1:5432` 连接数据库即可**：

```powershell
# 例如 PostgreSQL
psql -h 127.0.0.1 -p 5432 -U your_user
```

### 3.3 通用语法

```bash
ssh -L 本地端口:目标地址:目标端口 用户@跳板机
```

目标地址是**从跳板机视角解析的地址**，可以是内网 IP、内网域名，
甚至另一台机器的 `localhost`。

---

## 4. 远程转发 -R：把本地服务暴露给远端

### 4.1 典型场景

你本地起了 `http://localhost:3000`，想临时让云服务器（或同事）访问。

### 4.2 命令

```bash
ssh -R 8080:localhost:3000 user@server-ip
```

含义：

```text
server-ip:8080 ──SSH 加密──> 本机 localhost:3000
```

之后在服务器上访问 `http://localhost:8080` 就能看到你的本地页面。

### 4.3 让"别人"也能访问

默认远程转发只监听服务器本机。要让外部机器也能访问，需要：

1. 服务器 sshd 开启转发，并允许绑定到所有接口：

```ini
# /etc/ssh/sshd_config
AllowTcpForwarding yes
GatewayPorts yes
```

2. 重启 sshd 后用 `-R` 加绑定时注意 SSH 参数写法，常见做法是
   `ssh -R 0.0.0.0:8080:localhost:3000 user@server-ip`。

> ⚠️ 把服务暴露给所有人访问有风险！只用于**临时联调**，用完立刻断开；
> 长期对外服务请用第 6 课的工具 + HTTPS + 鉴权。

---

## 5. 动态转发 -D：把跳板机当"出口代理"

### 5.1 场景

你想访问公司内网的多个地址（`git.internal`、`wiki.internal`、`db.internal`），
不想为每个都建一条隧道。

### 5.2 命令

```bash
ssh -D 1080 user@jump.example.com
```

在本地开一个 SOCKS5 代理 `127.0.0.1:1080`，之后：

- 浏览器/代理插件设置 SOCKS5 `127.0.0.1:1080`；
- 命令行工具：`curl --socks5-hostname 127.0.0.1:1080 http://wiki.internal`
- Git：`git config --global http.proxy socks5h://127.0.0.1:1080`

这样，DNS 解析和流量都走跳板机，内网域名也能正常解析。

---

## 6. 多级跳板：ProxyJump

有的网络要"跳两次"才能到达目标：

```text
本机 ──> 公网跳板机 ──> 内网跳板机 ──> 目标服务
```

```bash
ssh -J user@public-jump -L 5432:db.internal:5432 user@inner-jump
```

`-J` 支持链式：`-J a,b,c`。

---

## 7. 用 ssh config 简化日常

把常用主机写进 `~/.ssh/config`，以后只需 `ssh dev`、`ssh bastion`。

```ini
# ~/.ssh/config

Host bastion
    HostName jump.example.com
    User dev
    IdentityFile ~/.ssh/id_ed25519

Host dev
    HostName 10.20.30.50
    User dev
    ProxyJump bastion          # 经过跳板机

Host db-tunnel
    HostName jump.example.com
    User dev
    LocalForward 5432 db.internal:5432   # 登录即自动建隧道
    ServerAliveInterval 60                # 保活，防止隧道断开
```

使用：

```bash
ssh db-tunnel      # 自动连跳板机并建立 5432 隧道
ssh dev            # 经跳板机登录内网开发机
```

> 隧道断开是常见问题，加 `ServerAliveInterval 30` 可显著减少掉线。

---

## 8. 安全注意事项

| 事项 | 要求 |
|------|------|
| 认证 | 只用密钥登录，关闭密码登录 |
| 暴露面 | 远程转发（-R）用后即断，避免长期开放 |
| 最小权限 | 不为所有用户开启 `GatewayPorts` |
| 审计 | 服务器上保留 SSH 登录日志（第 8 课） |
| 保活 | 配置 `ServerAliveInterval`，避免空闲断线 |

---

## 9. 动手练习

准备：一台云服务器（或同事的机器），一台本地电脑。

1. 生成本机 SSH 密钥，把公钥装到服务器，验证 `ssh` 免密登录。
2. 在服务器上启动一个测试服务（如 `python3 -m http.server 8080 --bind 127.0.0.1`），
   本地用 `ssh -L 8080:127.0.0.1:8080 user@server` 后访问
   `http://127.0.0.1:8080`。
3. 在你本地启动 `python -m http.server 3000`，用 `-R` 让服务器能访问
   `http://127.0.0.1:8080`，体会"反向暴露"。
4. 用 `-D 1080` 开启 SOCKS 代理，让浏览器走代理访问一个网页。
5. 把三台常用主机写进 `~/.ssh/config`，用别名登录。

---

## 10. 小结

| 方式 | 命令 | 场景 |
|------|------|------|
| 本地转发 | `ssh -L 端口:目标:端口 跳板机` | 访问远程内网服务 |
| 远程转发 | `ssh -R 端口:本地:端口 服务器` | 把本地服务暴露给远端 |
| 动态转发 | `ssh -D 1080 跳板机` | 代理访问整个内网 |
| 多级跳板 | `ssh -J 跳板1 目标` | 层层深入内网 |
| 自动隧道 | ssh config 的 `LocalForward` | 日常固定隧道 |

**SSH 隧道能解决"有跳板机"的场景；没有跳板机时，请看下一课的 Mesh VPN。**

---

**下一课：** `04_vpn_and_mesh.md` - VPN 与网状组网：WireGuard、Tailscale
