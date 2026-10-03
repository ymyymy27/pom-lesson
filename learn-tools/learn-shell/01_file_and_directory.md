# 第1课：文件与目录操作

## 1. 命令行是什么？

### 一句话解释
**命令行就是用文字和电脑对话** —— 你打字告诉它做什么，它用文字回复结果。

### 为什么要学命令行？

| 场景 | 图形界面 | 命令行 |
|------|---------|--------|
| 重命名 100 个文件 | 一个一个点... | 一条命令搞定 |
| 查找包含某关键词的文件 | 不好找 | `grep -r "关键词" .` |
| 远程管理服务器 | 没有图形界面 | SSH 连上去用命令行 |
| 自动化任务 | 做不到 | 写个脚本定时运行 |
| Git / Docker / pip | 本来就是命令行工具 | 必须会 |

### Shell 是什么？

```
你（用户）
    ↓ 输入命令
Shell（命令解释器）      ← Bash / Zsh / PowerShell
    ↓ 翻译成系统调用
操作系统（内核）
    ↓ 执行
硬件（CPU/磁盘/网络）
```

常见 Shell：
- **Bash**：Linux/Mac 默认，最通用（本课使用）
- **Zsh**：Mac 新版默认，兼容 Bash
- **PowerShell**：Windows 默认（语法不同）
- **Git Bash**：Windows 上的 Bash 环境（推荐 Windows 用户使用）

---

## 2. 目录导航

### 2.1 查看当前位置

```bash
pwd                    # Print Working Directory
# /home/user/projects
```

### 2.2 列出文件（ls）

```bash
ls                     # 列出当前目录的文件和文件夹
ls -l                  # 详细列表（权限、大小、日期）
ls -la                 # 包括隐藏文件（以.开头的）
ls -lh                 # 文件大小用人类可读格式（KB/MB）
ls -lt                 # 按修改时间排序（最新的在前）
ls -lS                 # 按文件大小排序
ls *.py                # 只列出 .py 文件
ls -R                  # 递归列出子目录
```

`ls -la` 输出解读：
```
drwxr-xr-x  5 user group 4096 Jan 10 14:30 projects
-rw-r--r--  1 user group 2048 Jan 10 14:25 app.py
│└───┬───┘    └─┬─┘ └─┬─┘ └─┬─┘ └────┬────┘ └─ 文件名
│    │         │     │     │        │
│    权限      所有者  组    大小    修改时间
│
d=目录, -=文件, l=链接
```

### 2.3 切换目录（cd）

```bash
cd projects            # 进入 projects 目录
cd ..                  # 返回上一级
cd ../..               # 返回上两级
cd ~                   # 回到用户主目录
cd -                   # 回到上次所在的目录（来回切换很方便）
cd /                   # 到根目录
```

### 路径

```
绝对路径（从根目录开始）：
  /home/user/projects/app.py

相对路径（从当前位置开始）：
  ./app.py          当前目录的 app.py
  ../config.py      上一级目录的 config.py
  projects/app.py   子目录的 app.py

特殊符号：
  .     当前目录
  ..    上一级目录
  ~     用户主目录（/home/用户名）
  /     根目录
```

---

## 3. 文件操作

### 3.1 创建

```bash
# 创建空文件
touch app.py
touch file1.txt file2.txt     # 创建多个

# 创建目录
mkdir projects
mkdir -p a/b/c                 # 递归创建（自动创建中间目录）

# 用 echo 创建带内容的文件
echo "print('hello')" > app.py
```

### 3.2 查看文件内容

```bash
cat app.py                     # 输出全部内容
cat -n app.py                  # 带行号

head app.py                    # 查看前10行
head -n 20 app.py              # 查看前20行

tail app.py                    # 查看最后10行
tail -n 20 app.py              # 查看最后20行
tail -f log.txt                # 实时追踪文件末尾（看日志超有用）

less app.py                    # 分页查看（按 q 退出，空格翻页）

wc app.py                      # 统计行数、单词数、字节数
wc -l app.py                   # 只看行数
```

### 3.3 复制（cp）

```bash
cp app.py app_backup.py        # 复制文件
cp -r projects/ backup/        # 复制目录（-r = 递归）
cp *.py backup/                # 复制所有 .py 文件到 backup/
```

### 3.4 移动/重命名（mv）

```bash
mv app.py src/                 # 移动文件到 src/ 目录
mv old_name.py new_name.py     # 重命名
mv *.py src/                   # 移动所有 .py 文件
```

### 3.5 删除（rm）

```bash
rm file.txt                    # 删除文件
rm -r folder/                  # 删除目录及其内容
rm -rf folder/                 # 强制删除（不提示确认）⚠️ 危险！
rm *.pyc                       # 删除所有 .pyc 文件
```

> ⚠️ **rm 没有回收站！** 删了就是真的删了。操作前确认好。

### 3.6 查找文件（find）

```bash
find . -name "*.py"            # 查找当前目录下所有 .py 文件
find . -name "app*"            # 查找以 app 开头的文件
find . -type d -name "test"    # 查找名为 test 的目录
find . -size +1M               # 查找大于 1MB 的文件
find . -mtime -7               # 查找最近 7 天修改过的文件
```

---

## 4. 通配符

```bash
*           匹配任意字符（0个或多个）
?           匹配单个字符
[abc]       匹配 a、b 或 c
[0-9]       匹配数字
{a,b,c}     匹配 a、b 或 c（Bash 扩展）
```

示例：
```bash
ls *.py            # 所有 .py 文件
ls app.??          # app.后跟2个字符（app.py、app.js）
ls [abc]*.py       # a/b/c 开头的 .py 文件
cp {app,config}.py backup/   # 复制 app.py 和 config.py
```

---

## 5. 快捷键

| 快捷键 | 作用 |
|--------|------|
| `Tab` | 自动补全（最常用！） |
| `Tab Tab` | 显示所有补全选项 |
| `Ctrl + C` | 中断当前命令 |
| `Ctrl + L` | 清屏 |
| `Ctrl + A` | 光标到行首 |
| `Ctrl + E` | 光标到行尾 |
| `Ctrl + W` | 删除光标前一个单词 |
| `Ctrl + R` | 搜索历史命令 |
| `↑ / ↓` | 翻阅历史命令 |

---

## 6. 动手练习

```bash
# 1. 创建练习目录
mkdir -p ~/shell-demo/src ~/shell-demo/docs

# 2. 进入目录
cd ~/shell-demo

# 3. 创建文件
echo "print('hello')" > src/app.py
echo "# README" > docs/README.md
touch src/utils.py src/config.py

# 4. 查看结构
ls -la src/

# 5. 复制文件
cp src/app.py src/app_backup.py

# 6. 重命名
mv src/config.py src/settings.py

# 7. 查找
find . -name "*.py"

# 8. 查看文件
cat src/app.py

# 9. 统计
wc -l src/*.py

# 10. 清理
rm src/app_backup.py
```

---

## 7. 小结

| 命令 | 作用 | 常用选项 |
|------|------|---------|
| `pwd` | 当前位置 | |
| `ls` | 列出文件 | `-la`(详细+隐藏) `-lh`(可读大小) |
| `cd` | 切换目录 | `..`(上级) `~`(主目录) `-`(上次) |
| `mkdir` | 创建目录 | `-p`(递归创建) |
| `touch` | 创建空文件 | |
| `cat` | 查看内容 | `-n`(带行号) |
| `cp` | 复制 | `-r`(复制目录) |
| `mv` | 移动/重命名 | |
| `rm` | 删除 | `-r`(目录) `-f`(强制) |
| `find` | 查找文件 | `-name` `-type` `-size` |

---

**下一课：** `02_pipe_and_redirect.md` - 管道与重定向
