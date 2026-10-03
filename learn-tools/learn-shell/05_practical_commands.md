# 第5课：实用命令集锦

## 1. 进程管理

### 查看进程

```bash
ps                             # 当前终端的进程
ps aux                         # 所有进程（最常用）
ps aux | grep python           # 查找 Python 进程

# 实时监控
top                            # 实时进程监控（q 退出）
htop                           # 更好用的版本（需安装）
```

### `ps aux` 输出解读

```
USER     PID  %CPU %MEM    VSZ   RSS  STAT COMMAND
root       1   0.0  0.1  16956  4832  Ss   /sbin/init
user    1234  15.0  2.3 123456 89012  Sl   python app.py
```

| 列 | 含义 |
|----|------|
| PID | 进程ID |
| %CPU | CPU 占用率 |
| %MEM | 内存占用率 |
| STAT | 状态（S=睡眠, R=运行, Z=僵尸） |
| COMMAND | 执行的命令 |

### 杀死进程

```bash
kill 1234                      # 优雅终止（SIGTERM）
kill -9 1234                   # 强制杀死（SIGKILL）
killall python                 # 杀死所有 python 进程

# 查找并杀死
ps aux | grep "python app.py" | awk '{print $2}' | xargs kill
# 或
pkill -f "python app.py"
```

### 后台运行

```bash
# 后台运行
python app.py &                # & 放到后台
nohup python app.py &          # 关闭终端后也继续运行
nohup python app.py > log.txt 2>&1 &   # 输出到日志

# 查看后台任务
jobs                           # 当前终端的后台任务
bg                             # 把暂停的任务放到后台
fg                             # 把后台任务拉到前台
```

---

## 2. 网络命令

### 网络检测

```bash
# 测试连通性
ping google.com                # Ctrl+C 停止
ping -c 4 google.com           # 只 ping 4次

# DNS 查询
nslookup google.com
dig google.com                 # 更详细

# 路由跟踪
traceroute google.com          # Linux/Mac
tracert google.com             # Windows
```

### 端口与连接

```bash
# 查看端口占用
lsof -i :8000                  # Mac/Linux：谁在用 8000 端口
netstat -tlnp                  # Linux：所有监听端口
ss -tlnp                       # Linux 新版（替代 netstat）

# Windows PowerShell
# netstat -ano | findstr :8000

# 测试端口是否开放
nc -zv localhost 8000          # netcat
curl -I http://localhost:8000  # HTTP 测试
```

### HTTP 请求（curl）

```bash
# GET 请求
curl http://localhost:8000/api/health
curl -s http://api.com/data | python -m json.tool    # 格式化 JSON

# POST 请求
curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "hello"}'

# 带认证
curl -H "Authorization: Bearer sk-xxx" http://api.com/data

# 下载文件
curl -O https://example.com/file.zip
curl -o myfile.zip https://example.com/file.zip

# 常用选项
curl -s       # 静默模式（不显示进度条）
curl -v       # 显示详细信息（调试用）
curl -L       # 跟随重定向
curl -i       # 显示响应头
```

### 文件传输

```bash
# SCP（基于 SSH 的文件复制）
scp file.txt user@server:/path/       # 上传
scp user@server:/path/file.txt .      # 下载
scp -r folder/ user@server:/path/     # 上传目录

# SSH 连接远程服务器
ssh user@server
ssh -p 2222 user@server               # 指定端口
ssh -i key.pem user@server            # 使用密钥
```

---

## 3. 压缩与解压

```bash
# tar（打包 + 压缩）
tar -czf archive.tar.gz folder/       # 打包压缩
tar -xzf archive.tar.gz               # 解压
tar -xzf archive.tar.gz -C /target/   # 解压到指定目录
tar -tzf archive.tar.gz               # 查看内容（不解压）

# 参数含义
# -c  创建（create）
# -x  解压（extract）
# -z  gzip 压缩
# -f  指定文件名
# -v  显示过程
# -t  列出内容

# zip
zip -r archive.zip folder/            # 压缩
unzip archive.zip                     # 解压
unzip -l archive.zip                  # 查看内容
unzip archive.zip -d /target/         # 解压到指定目录
```

---

## 4. 磁盘与空间

```bash
# 磁盘使用率
df -h                          # 各分区使用情况（-h 可读格式）

# 目录大小
du -sh *                       # 当前目录各项的大小
du -sh .                       # 当前目录总大小
du -sh * | sort -rh | head -10 # Top 10 大文件/目录

# 查找大文件
find . -type f -size +100M     # 查找大于 100MB 的文件
find . -type f -size +100M -exec ls -lh {} +
```

---

## 5. 环境变量

```bash
# 查看所有环境变量
env
env | grep PATH

# 查看某个变量
echo $PATH
echo $HOME
echo $USER

# 临时设置（只对当前终端有效）
export MY_VAR="hello"
export API_KEY="sk-xxx"

# 永久设置（写入配置文件）
echo 'export MY_VAR="hello"' >> ~/.bashrc
source ~/.bashrc               # 立即生效

# .bashrc vs .bash_profile
# .bashrc       → 每次打开终端都执行
# .bash_profile → 只在登录时执行
# Mac 上用 .zshrc（如果用 zsh）

# PATH 变量（系统查找命令的目录列表）
echo $PATH
# /usr/local/bin:/usr/bin:/bin

# 添加目录到 PATH
export PATH="$PATH:/my/custom/bin"
```

### .env 文件管理

```bash
# .env 文件格式
# DATABASE_URL=postgres://localhost/mydb
# API_KEY=sk-xxx
# DEBUG=true

# 加载 .env（Shell 脚本中）
set -a
source .env
set +a

# 或逐行加载
export $(grep -v '^#' .env | xargs)
```

---

## 6. 定时任务（cron）

```bash
# 编辑定时任务
crontab -e

# 查看当前定时任务
crontab -l

# cron 时间格式
# 分 时 日 月 周  命令
# *  *  *  *  *   command
# │  │  │  │  │
# │  │  │  │  └── 周几（0-7，0和7都是周日）
# │  │  │  └──── 月份（1-12）
# │  │  └────── 日期（1-31）
# │  └──────── 小时（0-23）
# └────────── 分钟（0-59）

# 示例
*/5 * * * *     /path/script.sh    # 每5分钟
0 */2 * * *     /path/script.sh    # 每2小时
0 9 * * 1-5     /path/script.sh    # 工作日每天9点
0 0 * * *       /path/backup.sh    # 每天午夜
0 0 1 * *       /path/monthly.sh   # 每月1号

# 输出日志
0 9 * * * /path/script.sh >> /var/log/cron.log 2>&1
```

---

## 7. 其他实用命令

```bash
# 历史命令
history                        # 查看所有历史
history | tail -20             # 最近20条
!123                          # 重新执行第123条
!!                            # 重新执行上一条
!grep                         # 执行最近的 grep 命令

# 别名
alias ll="ls -la"
alias gs="git status"
alias py="python3"
# 永久别名写入 ~/.bashrc

# 计算
echo $((3 + 5))               # 算术运算
echo "scale=2; 10/3" | bc     # 浮点运算

# 日期
date                           # 当前日期时间
date +%Y-%m-%d                 # 格式化：2024-01-15
date +%Y%m%d_%H%M%S           # 时间戳：20240115_143025

# 查看命令帮助
man ls                         # 完整手册
ls --help                      # 简要帮助
tldr ls                        # 社区简明示例（需安装 tldr）

# 命令位置
which python                   # 查找命令路径
type ls                        # 查看命令类型
```

---

## 8. 速查表

### 最常用命令 Top 20

| # | 命令 | 用途 |
|---|------|------|
| 1 | `ls -la` | 列出文件 |
| 2 | `cd` | 切换目录 |
| 3 | `cat / less` | 查看文件 |
| 4 | `grep -rn` | 搜索内容 |
| 5 | `find . -name` | 查找文件 |
| 6 | `cp -r` | 复制 |
| 7 | `mv` | 移动/重命名 |
| 8 | `rm -rf` | 删除 |
| 9 | `mkdir -p` | 创建目录 |
| 10 | `chmod +x` | 添加执行权限 |
| 11 | `ps aux \| grep` | 查找进程 |
| 12 | `kill` | 杀进程 |
| 13 | `curl` | HTTP 请求 |
| 14 | `ssh` | 远程连接 |
| 15 | `scp` | 远程传文件 |
| 16 | `tar -czf / -xzf` | 压缩/解压 |
| 17 | `df -h / du -sh` | 磁盘空间 |
| 18 | `tail -f` | 实时看日志 |
| 19 | `history` | 历史命令 |
| 20 | `export` | 设置环境变量 |

---

## 9. 动手练习

1. 用 `ps aux | grep` 查找你的 Python 进程
2. 用 `curl` 请求一个 API 并格式化 JSON 输出
3. 把当前目录打包成 `backup_日期.tar.gz`
4. 用 `du -sh * | sort -rh` 查看哪些文件最大
5. 设置一个环境变量并在脚本中使用它
6. 写一个别名 `alias ll="ls -la"`，添加到 `~/.bashrc`

---

**learn-shell 课程完成！** 🎉

回到总目录：[learn-tools README](../README.md)
