# 第4课：VPN 与网状组网 —— WireGuard、Tailscale

## 1. VPN 是什么

**VPN（Virtual Private Network，虚拟专用网络）** 把多个物理网络
通过加密隧道"缝合"成一个虚拟内网。

```text
上海办公室 ─┐
           ├─ 加密隧道 ── 云端中心 ── 加密隧道 ── 深圳办公室
北京家宽   ─┘
```

加入 VPN 后，每台设备都获得一个虚拟内网 IP，彼此访问就像在同一个局域网。

## 2. 传统 VPN vs 现代 Mesh VPN

| 维度 | 传统 VPN（OpenVPN/WireGuard 中心化） | Mesh VPN（Tailscale/ZeroTier） |
|------|--------------------------------------|--------------------------------|
| 拓扑 | 星型：所有流量经中心服务器 | 网状：设备之间尽量直连 |
| 配置 | 需要手写配置、管理证书/密钥 | 登录账号，自动下发配置 |
| 公网 IP | 中心节点需要公网 IP | 任意节点都不需要公网 IP |
| NAT 穿透 | 需额外配置 | 自动打洞 + 中继兜底 |
| 适用 | 固定网络、企业合规场景 | 分布式团队、个人设备组网 |

**推荐组合**：团队小、想快速上手用 Tailscale；追求可控和极简用 WireGuard。

---

## 3. WireGuard：极简但需要手动配置

### 3.1 核心概念

| 概念 | 说明 |
|------|------|
| Interface | 本机的虚拟网卡配置（私钥、虚拟 IP） |
| Peer | 对端设备（公钥、Endpoint、AllowedIPs） |
| Endpoint | 对端的**公网地址:端口** |
| AllowedIPs | 允许通过隧道访问的网段（同时充当路由规则） |

### 3.2 生成密钥

```bash
# Linux 上安装后生成
wg genkey | tee privatekey | wg pubkey > publickey

# Windows 客户端（如 WireGuard 官方客户端）也有生成按钮
```

### 3.3 服务器配置

```ini
# /etc/wireguard/wg0.conf（服务器）
[Interface]
PrivateKey = <服务器私钥>
Address = 10.66.66.1/24
ListenPort = 51820
SaveConfig = true

# 每个客户端一个 Peer
[Peer]
PublicKey = <客户端1公钥>
AllowedIPs = 10.66.66.2/32

[Peer]
PublicKey = <客户端2公钥>
AllowedIPs = 10.66.66.3/32
```

启动并设置开机自启：

```bash
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
```

服务器还需要开启 IP 转发（如果客户端之间要互访）：

```bash
echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-wg.conf
sudo sysctl -p
```

### 3.4 客户端配置

```ini
# 客户端 /etc/wireguard/wg0.conf 或 Windows 客户端导入
[Interface]
PrivateKey = <客户端私钥>
Address = 10.66.66.2/24

[Peer]
PublicKey = <服务器公钥>
Endpoint = 1.2.3.4:51820
AllowedIPs = 10.66.66.0/24
PersistentKeepalive = 25
```

说明：

- `Endpoint` 填服务器的**公网 IP 或域名**；
- `AllowedIPs = 10.66.66.0/24` 表示只把虚拟网段路由进隧道；
- `PersistentKeepalive = 25` 用于 NAT 后保持映射（客户端必须加）。

客户端连接：

```bash
sudo wg-quick up wg0
sudo wg show        # 查看握手状态
```

成功后 `ping 10.66.66.1` 应能通，服务器也能访问 `10.66.66.2`。

### 3.5 常见坑

| 问题 | 原因 | 解决 |
|------|------|------|
| 只有一端能通 | AllowedIPs/防火墙不对称 | 两端都要正确配置 |
| 握手超时 | Endpoint 不可达或端口没放行 | 检查云安全组 UDP 51820 |
| 通了但 ping 不通 | 服务器没开 IP 转发 | 开启 `net.ipv4.ip_forward` |
| 重启后失效 | 配置没保存/服务没启用 | `systemctl enable` + `SaveConfig` |

---

## 4. Tailscale：十分钟组好一个"团队内网"

Tailscale 基于 WireGuard，自动完成 NAT 穿透、密钥管理和中继，**不需要公网 IP**。

### 4.1 安装并登录

Windows：

```powershell
# 下载安装包或 winget
winget install Tailscale.Tailscale
```

Linux：

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

macOS 可以直接从 App Store 安装。

### 4.2 加入网络

```bash
tailscale up
# 浏览器会打开登录页，用团队账号（Google/Microsoft/GitHub/邮箱）登录
```

查看网络里的设备：

```bash
tailscale status
```

```text
100.101.1.1  alice-laptop   alice@example.com  linux
100.101.1.2  office-server  bob@example.com    linux
100.101.1.3  shenzhen-pc    carol@example.com  windows
```

现在 `ping 100.101.1.2` 或直接访问服务即可，**像在同一内网**。

### 4.3 使用设备名（MagicDNS）

Tailscale 默认提供 MagicDNS，可以不用记 IP：

```bash
ssh alice@alice-laptop
curl http://office-server:8000
```

### 4.4 子网路由（让整段内网都可达）

如果想让 Tailscale 网络里的成员访问办公室的整段 `10.20.0.0/16`，
需要在一台能访问该网段的机器上做子网路由：

```bash
sudo tailscale up --advertise-routes=10.20.0.0/16
```

然后在 Tailscale 管理后台（Access Controls）里 **批准该路由**，
其他成员才能使用：

```text
admin console → Machines → 对应机器 → Edit route settings → Approve
```

### 4.5 访问控制（ACL）

默认所有成员可以互访。想限制时，在管理后台编辑策略：

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["autogroup:member"],
      "dst": ["100.101.0.0/10:*"]
    },
    {
      "action": "accept",
      "src": ["alice@example.com"],
      "dst": ["10.20.0.0/16:22,3306,5432"]
    }
  ]
}
```

> 第一条是默认全通；第二条表示只允许 alice 访问办公室子网的部分端口。
> ACL 是 JSON 策略，改完立即生效。

### 4.6 分享给临时协作者

不用让对方加入团队，可以分享单台机器或服务：

```bash
# 分享一台机器
tailscale share 机器名
```

---

## 5. 其他 Mesh 方案

| 工具 | 特点 | 适合 |
|------|------|------|
| ZeroTier | 自建控制器能力强，可离线部署 | 想自托管、深度定制 |
| NetBird | 轻量、支持私有部署 | 对数据主权敏感的团队 |
| Headscale | Tailscale 协议的开源控制端 | 想自托管 Tailscale 生态 |

---

## 6. 选型建议

| 团队情况 | 推荐 |
|----------|------|
| 5~20 人，想 10 分钟跑通 | Tailscale（免费额度足够） |
| 有固定云服务器，想要完全可控 | WireGuard |
| 公司合规要求数据不出境 | 自建 Headscale / ZeroTier / WireGuard |
| 临时给外部协作者开访问 | Tailscale share 或第 6 课的内网穿透 |

---

## 7. 动手练习

1. 注册 Tailscale，在**两台不同网络**的设备（本机 + 手机/同事电脑/云服务器）
   上安装并登录，确认 `tailscale status` 能看到双方。
2. 在设备 A 启动 `python -m http.server 8000`，从设备 B 通过 Tailscale IP
   访问，验证"虚拟内网"已打通。
3. 打开 Tailscale 管理后台，查看设备列表和 MagicDNS 名称。
4. （进阶）用一台云服务器部署 WireGuard，配置一个客户端，验证虚拟 IP 互通。
5. （进阶）给团队配置一条 ACL：只允许成员访问开发服务器的 22/8000 端口。

---

## 8. 小结

- VPN 把分散的网络缝合成虚拟内网；
- WireGuard 极简、可控，适合有公网服务器的场景；
- Tailscale 自动打洞、免配置，适合快速组建团队内网；
- 子网路由 + ACL 让"部分网段、部分端口"按需开放；
- **Mesh VPN 是最接近"在不同地区像在同一个办公室"的协作方案。**

为什么没有公网 IP 也能直连？答案在第 5 课：NAT 穿透。

---

**下一课：** `05_nat_traversal.md` - NAT 穿透原理：打洞、STUN、TURN 中继
