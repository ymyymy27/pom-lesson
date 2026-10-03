> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第6课：内网穿透工具 —— frp、ngrok、Cloudflare Tunnel

## 1. 什么是内网穿透

**内网穿透（反向隧道/反向代理）**：让公网上的人访问你本地/内网的服务。

```text
公网用户 ──> 公网服务器/隧道入口 ──加密转发──> 你的本地服务 localhost:3000
```

与第 4 课 Mesh VPN 的区别：

| 维度 | Mesh VPN | 内网穿透 |
|------|----------|----------|
| 使用者 | 加入网络的成员 | 任何拿到 URL 的人 |
| 形态 | 虚拟内网 IP | 公网域名/端口 |
| 典型场景 | 团队成员日常互访 | 临时暴露、回调、演示 |
| 典型工具 | Tailscale | frp / ngrok / Cloudflare Tunnel |

---

## 2. 典型场景

1. **Webhook 调试**：微信/钉钉/支付回调必须访问公网 HTTPS URL，
   而你的服务在 `localhost`；
2. **手机真机调试**：手机访问电脑上的本地页面；
3. **给同事演示**：把本地原型临时发给同事看；
4. **内网服务上云**：把家里 NAS、开发数据库临时发布；
5. **无公网 IP 的服务器**：自建服务对外提供访问。

---

## 3. frp：自建、可控、功能全

frp 由 **frps（服务端）** 和 **frpc（客户端）** 组成，需要一台公网服务器。

### 3.1 服务端配置（公网服务器）

新版 frp 使用 TOML 配置：

```toml
# frps.toml
bindPort = 7000

# 建议加一个连接令牌，防止别人蹭你的 frps
auth.method = "token"
auth.token = "换成一段随机长字符串"
```

启动：

```bash
./frps -c frps.toml
```

### 3.2 客户端配置（你的电脑）

```toml
# frpc.toml
serverAddr = "1.2.3.4"      # frps 服务器公网 IP
serverPort = 7000
auth.method = "token"
auth.token = "换成一段随机长字符串"

[[proxies]]
name = "local-web"
type = "tcp"
localIP = "127.0.0.1"
localPort = 3000
remotePort = 8080            # 服务器上对外开放的端口
```

启动：

```bash
./frpc -c frpc.toml
```

之后任何人都能访问 `http://1.2.3.4:8080`，流量经服务器转发到你本机 3000。

### 3.3 常用代理类型

| type | 用途 | 示例 |
|------|------|------|
| `tcp` | 任意 TCP 服务 | HTTP、SSH、数据库 |
| `http` / `https` | Web 服务 + 域名 | 按域名/路径分发 |
| `udp` | UDP 服务 | 部分游戏/语音 |
| `stcp` | 加密点对点（需要双方都装 frpc） | 安全访问内网 SSH |

### 3.4 注意

- 服务器安全组/防火墙要放行 `7000`（frps 端口）和 `8080`（对外端口）；
- frp 默认不做 HTTPS，自用建议套 Caddy/Nginx + 证书；
- `stcp` 比直接暴露 TCP 更安全，适合团队内部使用。

---

## 4. ngrok：一分钟临时隧道

### 4.1 使用

```bash
# 安装后登录获取 authtoken（免费注册）
ngrok config add-authtoken 你的令牌

# 把本地 3000 端口暴露出去
ngrok http 3000
```

输出：

```text
Forwarding  https://abcd-12-34-56-78.ngrok-free.app -> http://localhost:3000
```

把 `https://...ngrok-free.app` 发给同事，即可访问你的本地服务。

### 4.2 常用参数

```bash
ngrok http 3000 --host-header=rewrite   # 解决 Host 校验问题
ngrok tcp 22                             # 暴露 TCP（SSH）
ngrok http 3000 --basic-auth 用户名:密码 # 加访问密码
```

### 4.3 优缺点

- 优点：零配置、免费、自带 HTTPS；
- 缺点：免费版域名随机、地址每次变化（付费可固定）、依赖 ngrok 服务。

---

## 5. Cloudflare Tunnel：免费 + 自有域名

### 5.1 快速体验（临时隧道）

```bash
cloudflared tunnel --url http://localhost:3000
```

会得到一个 `https://xxxx.trycloudflare.com` 地址，无需账号即可用。

### 5.2 正式用法（命名隧道 + 自有域名）

```bash
# 1. 登录（浏览器授权）
cloudflared tunnel login

# 2. 创建隧道
cloudflared tunnel create my-tunnel

# 3. 绑定域名
cloudflared tunnel route dns my-tunnel dev.example.com

# 4. 编辑配置文件（见下方 config.yml 示例）
```

配置文件 `~/.cloudflared/config.yml`：

```yaml
tunnel: my-tunnel
credentials-file: /Users/you/.cloudflared/my-tunnel.json

ingress:
  - hostname: dev.example.com
    service: http://localhost:3000
  - service: http_status:404
```

启动：

```bash
cloudflared tunnel run my-tunnel
```

之后 `https://dev.example.com` 就指向你的本地服务，自带 HTTPS。

### 5.3 优点

- 免费、稳定、自带 HTTPS；
- 不出网关口（出站连接，不需要路由器开放端口）；
- 支持 Access 鉴权（配合 Cloudflare Access 限制谁能访问）。

---

## 6. 方案对比

| 方案 | 需要公网服务器 | 免费 | 固定地址 | HTTPS | 适合 |
|------|----------------|------|----------|-------|------|
| frp | 是 | 是（自己运维） | 是 | 需自配 | 长期、自建、数据可控 |
| ngrok | 否 | 是（域名随机） | 付费 | 自带 | 快速临时调试 |
| Cloudflare Tunnel | 否 | 是（有域名时） | 是 | 自带 | 个人/团队长期暴露 Web 服务 |
| Tailscale Funnel | 否 | 额度内 | 是 | 自带 | 已用 Tailscale 的团队 |

---

## 7. 安全清单

任何穿透方案都要做到：

| 事项 | 做法 |
|------|------|
| 令牌/密钥 | frp 加 token；ngrok 用 basic-auth；Cloudflare 加 Access |
| 最小暴露 | 只开需要的端口，用完即关 |
| 限访问 | 优先限定 IP 白名单/团队账号 |
| HTTPS | 公开访问一律 HTTPS |
| 日志 | 服务器记录访问日志，发现异常立即回收 |
| 数据库 | **永远不要**把数据库直接穿透到公网，用 SSH 隧道 |

---

## 8. 动手练习

1. 本地启动 `python -m http.server 3000`。
2. 依次体验三种方式（任选两种以上）：
   - `ngrok http 3000`；
   - `cloudflared tunnel --url http://localhost:3000`；
   - 自建 frps + frpc。
3. 用手机（关闭 Wi-Fi，用流量）访问生成的公网 URL，确认从外网可达。
4. 模拟 Webhook：在本地写一个接收 POST 的接口，把公网 URL 填到
   钉钉/企业微信自定义机器人或 GitHub webhook 里，验证回调到达。
5. 给穿透服务加一层访问控制（basic-auth / token），并验证无凭据访问被拒绝。

---

## 9. 小结

| 工具 | 一句话 |
|------|--------|
| frp | 自建穿透，功能最全，数据可控 |
| ngrok | 最快上手，临时调试神器 |
| Cloudflare Tunnel | 免费 + 自有域名 + HTTPS |
| Tailscale Funnel | 已有 Tailscale 时的顺路方案 |

**规则：临时调试用 ngrok/Cloudflare；长期服务用 frp 或 Cloudflare + Access；**
**数据库用 SSH 隧道而非穿透工具。**

---

**下一课：** `07-第7课远程开发协作实战 —— 多地点联调工作流.md` - 远程开发协作实战
