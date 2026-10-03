# 第2课：管道与重定向

## 1. 重定向是什么？

### 一句话解释
**重定向就是改变命令输出的去向** —— 本来输出到屏幕，重定向后输出到文件。

### 三个标准流

```
输入（stdin）  ──→  命令  ──→  输出（stdout）
      0                          1
                          ──→  错误（stderr）
                                 2
```

| 流 | 编号 | 默认去向 | 说明 |
|----|------|---------|------|
| stdin | 0 | 键盘 | 命令读取输入的地方 |
| stdout | 1 | 屏幕 | 命令正常输出 |
| stderr | 2 | 屏幕 | 错误信息 |

---

## 2. 输出重定向

### 2.1 覆盖写入（>）

```bash
echo "hello" > output.txt        # 把 hello 写入文件（覆盖）
ls -la > filelist.txt            # 把文件列表写入文件
cat app.py > backup.py           # 相当于复制文件
```

> ⚠️ `>` 会**覆盖**文件原有内容！

### 2.2 追加写入（>>）

```bash
echo "第一行" > log.txt          # 创建文件，写入第一行
echo "第二行" >> log.txt         # 追加第二行
echo "第三行" >> log.txt         # 追加第三行
date >> log.txt                  # 追加当前日期
```

### 2.3 错误重定向

```bash
# 正常输出到文件，错误仍然显示在屏幕
ls existing_dir/ > out.txt

# 错误输出到文件
ls nonexistent/ 2> error.txt

# 正常和错误都输出到同一个文件
ls -la > all.txt 2>&1

# 丢弃错误信息（不想看到错误时）
ls nonexistent/ 2>/dev/null

# 丢弃所有输出
command > /dev/null 2>&1
```

### /dev/null 是什么？

`/dev/null` 是"黑洞"—— 写入它的数据全部消失。常用来丢弃不想看到的输出。

---

## 3. 输入重定向

```bash
# 从文件读取输入（代替键盘输入）
wc -l < app.py                  # 统计 app.py 行数

# Here Document（多行输入）
cat << EOF > config.py
DATABASE = "sqlite:///app.db"
DEBUG = True
PORT = 8000
EOF
# 把这三行写入 config.py
```

---

## 4. 管道（Pipe）

### 一句话解释
**管道就是把一个命令的输出，当作另一个命令的输入** —— 命令接力赛。

```
命令A 的输出 ──→ | ──→ 命令B 的输入 ──→ | ──→ 命令C 的输入
```

### 基本用法

```bash
# ls 的输出 → grep 过滤
ls -la | grep ".py"              # 列出所有 .py 文件

# cat 的输出 → wc 统计
cat app.py | wc -l               # 统计行数

# 多级管道
cat access.log | grep "ERROR" | wc -l
# 读取日志 → 过滤错误行 → 统计数量

# 查看进程并搜索
ps aux | grep python             # 查找 Python 进程

# 排序并去重
cat names.txt | sort | uniq      # 排序后去除重复行

# 查看最大的文件
du -sh * | sort -rh | head -5    # 按大小排序，取前5
```

### 管道 vs 重定向

```bash
# 管道：命令 → 命令
ls | grep ".py"                  # ls 的输出传给 grep

# 重定向：命令 → 文件
ls > files.txt                   # ls 的输出写入文件
grep ".py" < files.txt           # 从文件读取输入给 grep
```

---

## 5. 常用管道组合

### 5.1 过滤（grep）

```bash
# 在文件中搜索关键词
grep "error" log.txt             # 搜索包含 error 的行
grep -i "error" log.txt          # 忽略大小写
grep -n "error" log.txt          # 显示行号
grep -r "TODO" .                 # 递归搜索当前目录所有文件
grep -c "error" log.txt          # 统计匹配行数
grep -v "debug" log.txt          # 反向匹配（排除 debug 的行）

# 管道中使用
ps aux | grep python
history | grep "git push"        # 搜索历史命令
pip list | grep numpy            # 查找已安装的包
```

### 5.2 排序（sort）

```bash
sort names.txt                   # 按字母排序
sort -r names.txt                # 逆序
sort -n numbers.txt              # 按数字排序
sort -k2 data.txt                # 按第2列排序
sort -t, -k3 -n data.csv        # 用逗号分隔，按第3列数字排序

# 管道
du -sh * | sort -rh              # 按文件大小排序
```

### 5.3 去重（uniq）

```bash
# uniq 只去除相邻的重复行，所以通常配合 sort 使用
sort names.txt | uniq            # 排序后去重
sort names.txt | uniq -c         # 去重并统计出现次数
sort names.txt | uniq -d         # 只显示重复的行
```

### 5.4 截取列（cut）

```bash
# 按分隔符截取
echo "name,age,city" | cut -d, -f2         # 取第2列：age
cat /etc/passwd | cut -d: -f1              # 取用户名

# 按字符位置截取
echo "hello world" | cut -c1-5             # hello
```

### 5.5 替换（tr）

```bash
echo "HELLO" | tr 'A-Z' 'a-z'             # 大写转小写
echo "hello" | tr 'a-z' 'A-Z'             # 小写转大写
echo "a:b:c" | tr ':' '\n'                # 冒号替换为换行
cat file.txt | tr -d '\r'                  # 删除 Windows 换行符
```

### 5.6 统计（wc）

```bash
wc file.txt                      # 行数 单词数 字节数
wc -l file.txt                   # 只看行数
wc -w file.txt                   # 只看单词数
wc -c file.txt                   # 只看字节数

# 管道
find . -name "*.py" | wc -l      # 统计 .py 文件个数
cat app.py | wc -l               # 统计代码行数
```

---

## 6. 实用管道实例

```bash
# 1. 统计代码行数
find . -name "*.py" -exec cat {} + | wc -l

# 2. 查找最近修改的文件
find . -type f -mtime -1 | head -10

# 3. 查看磁盘空间占用 Top 10
du -sh */ | sort -rh | head -10

# 4. 在日志中统计各 HTTP 状态码出现次数
cat access.log | awk '{print $9}' | sort | uniq -c | sort -rn

# 5. 查看端口占用
# Linux/Mac
lsof -i :8000
# 或
netstat -tlnp | grep 8000

# 6. 查找并删除所有 .pyc 文件
find . -name "*.pyc" -delete

# 7. 统计当前目录每种文件类型的数量
find . -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn

# 8. 导出环境变量到文件
env | sort > env_dump.txt
```

---

## 7. 动手练习

```bash
# 1. 创建测试文件
echo -e "apple\nbanana\napple\ncherry\nbanana\napple" > fruits.txt

# 2. 统计每种水果出现几次
sort fruits.txt | uniq -c | sort -rn

# 3. 查找当前目录所有 .md 文件并统计数量
find . -name "*.md" | wc -l

# 4. 把 ls 的结果保存到文件
ls -la > listing.txt

# 5. 查看历史命令中用过的 git 命令
history | grep git

# 6. 统计某个 .py 文件的行数
wc -l < some_file.py
```

---

## 8. 小结

| 符号 | 作用 | 示例 |
|------|------|------|
| `>` | 输出覆盖写入文件 | `echo "hi" > file.txt` |
| `>>` | 输出追加到文件 | `echo "hi" >> file.txt` |
| `<` | 从文件读取输入 | `wc -l < file.txt` |
| `2>` | 错误输出到文件 | `cmd 2> error.txt` |
| `\|` | 管道，命令接力 | `ls \| grep ".py"` |
| `/dev/null` | 丢弃输出 | `cmd > /dev/null 2>&1` |

**核心思想：** 小命令通过管道组合，解决复杂问题。Unix 哲学：每个工具做好一件事。

---

**下一课：** `03_text_processing.md` - 文本处理（awk/sed）
