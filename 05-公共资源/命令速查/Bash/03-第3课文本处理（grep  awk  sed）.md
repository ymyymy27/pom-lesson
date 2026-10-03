> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第3课：文本处理（grep / awk / sed）

## 1. 为什么要学文本处理？

日常开发中大量操作都是处理文本：
- 分析日志文件
- 处理 CSV / JSON 数据
- 批量修改配置文件
- 提取关键信息

三大文本处理工具：
| 工具 | 擅长 | 类比 |
|------|------|------|
| **grep** | 搜索/过滤行 | "找到包含XX的行" |
| **sed** | 替换/编辑 | "把A换成B" |
| **awk** | 按列处理 | "取第3列求和" |

---

## 2. grep 深入

### 基本用法（第2课已学）

```bash
grep "pattern" file.txt          # 搜索包含 pattern 的行
grep -i "error" log.txt          # 忽略大小写
grep -n "TODO" app.py            # 显示行号
grep -r "import" .               # 递归搜索目录
grep -c "error" log.txt          # 统计匹配行数
grep -v "debug" log.txt          # 反向（排除）
grep -l "TODO" *.py              # 只显示文件名
```

### 进阶用法

```bash
# 正则表达式搜索（-E 或 egrep）
grep -E "error|warning" log.txt  # 匹配 error 或 warning
grep -E "^import" app.py         # 以 import 开头的行
grep -E "\.py$" files.txt        # 以 .py 结尾的行
grep -E "[0-9]{3}" data.txt      # 包含3位数字的行

# 上下文
grep -A 3 "error" log.txt       # 匹配行 + 后3行（After）
grep -B 2 "error" log.txt       # 匹配行 + 前2行（Before）
grep -C 2 "error" log.txt       # 匹配行 + 前后各2行（Context）

# 实用组合
grep -rn "TODO\|FIXME\|HACK" --include="*.py" .
# 递归搜索所有 .py 文件中的 TODO/FIXME/HACK，显示行号
```

---

## 3. sed - 流编辑器

### 一句话解释
**sed 就是"查找替换"的命令行版** —— 批量修改文本内容。

### 3.1 替换（最常用）

```bash
# 基本替换：s/旧/新/
sed 's/old/new/' file.txt         # 每行替换第一个匹配
sed 's/old/new/g' file.txt        # 全局替换（g = global）
sed 's/old/new/gi' file.txt       # 全局+忽略大小写

# 示例
echo "hello world" | sed 's/world/Python/'
# hello Python

echo "aaa bbb aaa" | sed 's/aaa/xxx/g'
# xxx bbb xxx
```

### 3.2 直接修改文件

```bash
# -i 直接修改原文件（⚠️ 不可逆！）
sed -i 's/old/new/g' file.txt

# -i.bak 修改前备份（推荐）
sed -i.bak 's/old/new/g' file.txt
# 生成 file.txt.bak 作为备份

# Mac 上 -i 需要空参数
sed -i '' 's/old/new/g' file.txt
```

### 3.3 删除行

```bash
sed '3d' file.txt                 # 删除第3行
sed '2,5d' file.txt               # 删除第2-5行
sed '/pattern/d' file.txt         # 删除匹配 pattern 的行
sed '/^$/d' file.txt              # 删除空行
sed '/^#/d' config.txt            # 删除注释行（以#开头）
```

### 3.4 插入/追加

```bash
sed '2i\新的一行' file.txt         # 在第2行前插入（i = insert）
sed '2a\新的一行' file.txt         # 在第2行后追加（a = append）
sed '$a\最后一行' file.txt         # 在文件末尾追加
```

### 3.5 打印指定行

```bash
sed -n '5p' file.txt              # 只打印第5行
sed -n '3,7p' file.txt            # 打印第3-7行
sed -n '/error/p' file.txt        # 打印匹配行（类似 grep）
```

### 3.6 实用示例

```bash
# 批量修改 API 地址
sed -i 's|http://localhost:8000|https://api.example.com|g' *.py

# 删除文件中的空行和注释
sed '/^$/d; /^#/d' config.txt

# 在每行末尾添加逗号
sed 's/$/,/' file.txt

# 在每行开头添加前缀
sed 's/^/    /' file.txt          # 添加4个空格缩进

# 提取两个标记之间的内容
sed -n '/START/,/END/p' file.txt
```

---

## 4. awk - 列处理工具

### 一句话解释
**awk 把每行按列分割，你指定要哪列、怎么处理** —— 文本版的 Excel。

### 4.1 基本语法

```bash
awk '{动作}' file.txt
awk '/模式/ {动作}' file.txt
awk -F'分隔符' '{动作}' file.txt
```

### 4.2 列提取

默认以空格/Tab 分隔，`$1` 是第1列，`$2` 是第2列，`$0` 是整行。

```bash
# 示例数据 data.txt:
# Alice 90 85
# Bob 78 92
# Carol 95 88

awk '{print $1}' data.txt          # 打印第1列：Alice Bob Carol
awk '{print $1, $2}' data.txt      # 打印第1、2列
awk '{print $NF}' data.txt         # 打印最后一列（NF=列数）
awk '{print NR, $0}' data.txt      # 打印行号+整行
```

### 4.3 指定分隔符

```bash
# CSV 文件（逗号分隔）
echo "Alice,90,85" | awk -F',' '{print $2}'
# 90

# /etc/passwd（冒号分隔）
awk -F: '{print $1}' /etc/passwd   # 打印所有用户名

# 指定输出分隔符
awk -F',' '{OFS="\t"; print $1, $2}' data.csv
# 用 Tab 分隔输出
```

### 4.4 条件过滤

```bash
awk '$2 > 80 {print $1, $2}' data.txt
# 打印第2列大于80的行的第1、2列

awk '$1 == "Alice" {print}' data.txt
# 打印第1列是 Alice 的行

awk 'NR >= 2 && NR <= 5' file.txt
# 打印第2-5行

awk '/error/ {print}' log.txt
# 打印包含 error 的行（类似 grep）

awk 'length > 80' file.txt
# 打印长度超过80字符的行
```

### 4.5 计算

```bash
# 求和
awk '{sum += $2} END {print "总分:", sum}' data.txt

# 平均值
awk '{sum += $2; n++} END {print "平均:", sum/n}' data.txt

# 最大值
awk 'BEGIN {max=0} $2>max {max=$2} END {print "最高:", max}' data.txt

# 统计行数
awk 'END {print NR}' file.txt
```

### 4.6 格式化输出

```bash
# printf 格式化
awk '{printf "%-10s %5d %5d\n", $1, $2, $3}' data.txt
# Alice       90    85
# Bob         78    92

# 添加表头
awk 'BEGIN {print "姓名\t数学\t英语"} {print $1"\t"$2"\t"$3}' data.txt
```

### 4.7 实用示例

```bash
# 统计日志中各 IP 的访问次数
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10

# 计算 CSV 某列总和
awk -F',' '{sum += $3} END {print sum}' sales.csv

# 统计各 HTTP 状态码
awk '{print $9}' access.log | sort | uniq -c | sort -rn

# 提取 JSON 风格的键值（简单场景）
grep '"name"' data.json | awk -F'"' '{print $4}'

# 统计代码行数（排除空行和注释）
awk '!/^$/ && !/^#/' app.py | wc -l

# 交换两列
awk '{print $2, $1}' data.txt
```

---

## 5. 综合实战

```bash
# 场景1：分析 nginx 访问日志
# 格式：IP - - [时间] "方法 URL 协议" 状态码 大小

# 访问量 Top 10 IP
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10

# 统计 404 错误
awk '$9 == 404 {print $7}' access.log | sort | uniq -c | sort -rn

# 统计每小时请求数
awk -F'[/:]' '{print $4":"$5}' access.log | sort | uniq -c


# 场景2：批量处理配置文件
# 把所有 .env 文件中的 localhost 改成 production 地址
find . -name ".env" -exec sed -i 's/localhost/prod.example.com/g' {} +

# 场景3：代码库分析
# 统计每个文件类型的代码行数
find . -type f -name "*.py" -exec wc -l {} + | sort -n | tail -10
```

---

## 6. 动手练习

先创建测试数据：
```bash
# 创建成绩表
cat << EOF > scores.txt
Alice 90 85 92
Bob 78 92 88
Carol 95 88 91
David 82 79 85
Eve 88 94 90
EOF
```

练习：
1. 用 grep 找出分数中有 90 以上的行
2. 用 awk 打印姓名和第一门成绩
3. 用 awk 计算每人三门课的平均分
4. 用 sed 把 Alice 替换成 Amy
5. 用 awk 找出第一门成绩最高的人
6. 组合使用：找出平均分 > 88 的同学

---

## 7. 小结

| 工具 | 核心能力 | 最常用场景 |
|------|---------|-----------|
| `grep` | 搜索/过滤 | 在文件/日志中找内容 |
| `sed` | 替换/删除 | 批量修改文件内容 |
| `awk` | 按列处理 | 提取数据、统计计算 |

**记忆口诀：** grep 找、sed 改、awk 算

---

**下一课：** `04-第4课Shell 脚本编写.md` - Shell 脚本编写
