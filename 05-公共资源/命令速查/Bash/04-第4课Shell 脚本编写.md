> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第4课：Shell 脚本编写

## 1. Shell 脚本是什么？

### 一句话解释
**Shell 脚本就是把多条命令写到一个文件里，一次执行** —— 自动化你的重复操作。

### 为什么要写脚本？

| 手动操作 | 脚本自动化 |
|---------|-----------|
| 每次部署敲10条命令 | 一个 `deploy.sh` 搞定 |
| 忘记某一步 | 脚本不会忘 |
| 教别人怎么操作 | 给他脚本就行 |
| 定时任务 | cron + 脚本 |

---

## 2. 第一个脚本

### 创建并运行

```bash
# 1. 创建脚本文件
cat << 'EOF' > hello.sh
#!/bin/bash
# 这是我的第一个脚本

echo "Hello, Shell!"
echo "当前时间: $(date)"
echo "当前目录: $(pwd)"
echo "当前用户: $(whoami)"
EOF

# 2. 赋予执行权限
chmod +x hello.sh

# 3. 运行
./hello.sh
# 或
bash hello.sh
```

### Shebang（#!）

```bash
#!/bin/bash         # 用 Bash 执行
#!/bin/sh           # 用 sh 执行（更通用）
#!/usr/bin/env bash # 自动查找 bash 路径（最推荐）
```

第一行 `#!` 告诉系统用什么解释器运行这个脚本。

---

## 3. 变量

### 3.1 定义和使用

```bash
# 定义（= 两边不能有空格！）
name="小明"
age=25
file_path="/home/user/app.py"

# 使用（$变量名 或 ${变量名}）
echo "我叫 $name，今年 $age 岁"
echo "文件路径: ${file_path}"

# 用大括号避免歧义
prefix="app"
echo "${prefix}_config.py"    # app_config.py
echo "$prefix_config.py"      # 错！会找 $prefix_config 变量
```

### 3.2 命令替换

```bash
# 把命令的输出赋值给变量
current_date=$(date +%Y-%m-%d)
file_count=$(ls *.py | wc -l)
my_ip=$(hostname -I | awk '{print $1}')

echo "今天是 $current_date"
echo "有 $file_count 个 Python 文件"
```

### 3.3 特殊变量

```bash
$0      脚本文件名
$1      第1个参数
$2      第2个参数
$#      参数个数
$@      所有参数（每个独立）
$*      所有参数（作为一个字符串）
$?      上一条命令的退出码（0=成功）
$$      当前脚本的进程ID
```

示例：
```bash
#!/bin/bash
echo "脚本名: $0"
echo "参数1: $1"
echo "参数2: $2"
echo "参数个数: $#"
echo "所有参数: $@"

# 运行: ./script.sh hello world
# 输出:
# 脚本名: ./script.sh
# 参数1: hello
# 参数2: world
# 参数个数: 2
# 所有参数: hello world
```

### 3.4 读取用户输入

```bash
#!/bin/bash
read -p "请输入你的名字: " name
echo "你好, $name!"

read -sp "请输入密码: " password    # -s 不显示输入
echo
echo "密码长度: ${#password}"
```

---

## 4. 条件判断

### 4.1 if 语句

```bash
#!/bin/bash

age=18

if [ $age -ge 18 ]; then
    echo "成年人"
elif [ $age -ge 12 ]; then
    echo "青少年"
else
    echo "儿童"
fi
```

### 4.2 数字比较

| 运算符 | 含义 | 示例 |
|--------|------|------|
| `-eq` | 等于 | `[ $a -eq $b ]` |
| `-ne` | 不等于 | `[ $a -ne $b ]` |
| `-gt` | 大于 | `[ $a -gt $b ]` |
| `-ge` | 大于等于 | `[ $a -ge $b ]` |
| `-lt` | 小于 | `[ $a -lt $b ]` |
| `-le` | 小于等于 | `[ $a -le $b ]` |

### 4.3 字符串比较

```bash
[ "$str1" = "$str2" ]      # 相等
[ "$str1" != "$str2" ]     # 不相等
[ -z "$str" ]              # 为空
[ -n "$str" ]              # 不为空
```

### 4.4 文件判断

```bash
[ -f "file.txt" ]          # 文件存在
[ -d "dir/" ]              # 目录存在
[ -e "path" ]              # 路径存在（文件或目录）
[ -r "file.txt" ]          # 可读
[ -w "file.txt" ]          # 可写
[ -x "script.sh" ]        # 可执行
[ -s "file.txt" ]          # 文件非空
```

### 4.5 逻辑组合

```bash
# && 且
[ -f "app.py" ] && [ -r "app.py" ] && echo "文件存在且可读"

# || 或
[ -f "app.py" ] || echo "文件不存在"

# [[ ]] 中可以用 && 和 ||
if [[ $age -ge 18 && $age -le 65 ]]; then
    echo "工作年龄"
fi
```

### 实用示例

```bash
#!/bin/bash
# 检查文件是否存在

file=$1

if [ -z "$file" ]; then
    echo "用法: $0 <文件名>"
    exit 1
fi

if [ -f "$file" ]; then
    echo "文件存在, $(wc -l < "$file") 行"
elif [ -d "$file" ]; then
    echo "这是一个目录"
else
    echo "文件不存在: $file"
    exit 1
fi
```

---

## 5. 循环

### 5.1 for 循环

```bash
# 遍历列表
for name in Alice Bob Carol; do
    echo "Hello, $name"
done

# 遍历文件
for file in *.py; do
    echo "处理: $file ($(wc -l < "$file") 行)"
done

# 数字范围
for i in {1..5}; do
    echo "第 $i 次"
done

# C 风格
for ((i=0; i<5; i++)); do
    echo "i = $i"
done

# 遍历命令输出
for user in $(cat users.txt); do
    echo "用户: $user"
done
```

### 5.2 while 循环

```bash
# 基本 while
count=1
while [ $count -le 5 ]; do
    echo "第 $count 次"
    count=$((count + 1))
done

# 逐行读取文件（推荐方式）
while IFS= read -r line; do
    echo "行: $line"
done < file.txt

# 无限循环（监控场景）
while true; do
    echo "$(date): 服务运行中..."
    sleep 5
done
```

### 5.3 实用循环示例

```bash
#!/bin/bash
# 批量重命名：给所有 .txt 文件加上日期前缀

date_prefix=$(date +%Y%m%d)
for file in *.txt; do
    if [ -f "$file" ]; then
        mv "$file" "${date_prefix}_${file}"
        echo "重命名: $file → ${date_prefix}_${file}"
    fi
done
```

```bash
#!/bin/bash
# 监控磁盘空间，超过 80% 报警

threshold=80
usage=$(df / | awk 'NR==2 {print $5}' | tr -d '%')

if [ $usage -gt $threshold ]; then
    echo "⚠️ 磁盘使用率 ${usage}%，超过 ${threshold}%！"
else
    echo "✓ 磁盘使用率 ${usage}%，正常"
fi
```

---

## 6. 函数

```bash
#!/bin/bash

# 定义函数
greet() {
    local name=$1    # local 局部变量
    echo "Hello, $name!"
}

# 带返回值的函数
is_file_exists() {
    if [ -f "$1" ]; then
        return 0     # 成功（true）
    else
        return 1     # 失败（false）
    fi
}

# 返回字符串的函数
get_timestamp() {
    echo $(date +%Y%m%d_%H%M%S)
}

# 调用
greet "小明"
greet "小红"

if is_file_exists "app.py"; then
    echo "app.py 存在"
fi

ts=$(get_timestamp)
echo "时间戳: $ts"
```

---

## 7. 实用脚本模板

### 项目初始化脚本

```bash
#!/bin/bash
# init_project.sh - 初始化 Python 项目

PROJECT_NAME=${1:-"my-project"}

echo "创建项目: $PROJECT_NAME"

mkdir -p "$PROJECT_NAME/src" "$PROJECT_NAME/tests" "$PROJECT_NAME/docs"
cd "$PROJECT_NAME"

# 创建文件
cat > README.md << EOF
# $PROJECT_NAME

## 安装
\`\`\`bash
pip install -r requirements.txt
\`\`\`
EOF

cat > requirements.txt << EOF
# 在这里添加依赖
EOF

cat > .gitignore << EOF
__pycache__/
*.pyc
.venv/
.env
EOF

cat > src/__init__.py << EOF
EOF

# 初始化 Git
git init
git add .
git commit -m "chore: 初始化项目"

echo "✓ 项目 $PROJECT_NAME 创建完成！"
```

### 简易部署脚本

```bash
#!/bin/bash
# deploy.sh - 简易部署脚本

set -e    # 出错立即停止

echo "========== 开始部署 =========="

echo "1. 拉取最新代码..."
git pull origin main

echo "2. 安装依赖..."
pip install -r requirements.txt

echo "3. 运行测试..."
python -m pytest tests/ -v

echo "4. 重启服务..."
# systemctl restart myapp
# 或
# docker-compose up -d --build

echo "========== 部署完成 =========="
```

---

## 8. 动手练习

1. 写一个脚本 `backup.sh`，把当前目录的 .py 文件复制到 backup/ 文件夹
2. 写一个脚本，接收文件名参数，输出文件行数和单词数
3. 写一个脚本，遍历当前目录所有 .py 文件，统计总行数
4. 写一个带函数的脚本，包含 `log_info` 和 `log_error` 两个日志函数
5. 写一个项目初始化脚本（参考上面的模板）

---

## 9. 小结

| 概念 | 语法 |
|------|------|
| 变量 | `name="value"` / `$name` |
| 命令替换 | `$(command)` |
| if | `if [ 条件 ]; then ... fi` |
| for | `for x in list; do ... done` |
| while | `while [ 条件 ]; do ... done` |
| 函数 | `func() { ... }` |
| 参数 | `$1` `$2` `$#` `$@` |
| 退出码 | `$?` (0=成功) |

**脚本编写要点：**
- 首行加 `#!/bin/bash`
- 加 `set -e` 让脚本出错时停止
- 用 `"$变量"` 加引号防止空格问题
- 多加注释，方便维护

---

**下一课：** `05-第5课实用命令集锦.md` - 实用命令集锦
