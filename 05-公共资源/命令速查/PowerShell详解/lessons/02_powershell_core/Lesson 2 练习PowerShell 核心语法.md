> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Lesson 2 练习：PowerShell 核心语法

## 练习说明

本练习覆盖 Lesson 2 的所有核心概念。建议先通读 Lesson 2 教程，再完成以下练习。

---

## 练习 2.1：cmdlets 命名规范

**目标**：理解 Verb-Noun 命名规范，能快速找到需要的命令。

### 任务 A：探索命令命名

```powershell
# 1. 列出所有 Get 动词命令的数量
(Get-Command -Verb Get).Count

# 2. 列出所有 Set 动词命令
Get-Command -Verb Set | Select-Object -First 10

# 3. 列出所有 Remove 动词命令
Get-Command -Verb Remove | Select-Object -First 10

# 4. 查找所有与 "Service" 相关的命令
Get-Command -Noun Service | Select-Object Name
```

### 任务 B：自定义练习

```powershell
# 找出满足以下条件的命令：
# 1. Verb 是 Start 或 Stop
# 2. Verb 是 New, Copy, Move, Remove 中的任意一个
# 3. Noun 包含 "File" 或 "Item"

Get-Command -Verb Start,Stop | Select-Object Name
Get-Command -Verb New,Copy,Move,Remove | Select-Object Name
Get-Command -Noun *File*,*Item* | Select-Object Name
```

---

## 练习 2.2：参数使用

**目标**：掌握不同类型参数的使用方法。

### 任务 A：位置参数 vs 命名参数

```powershell
# 两种写法效果相同，体会区别

# 位置参数（不写参数名）
Get-ChildItem C:\Windows

# 命名参数（写参数名）
Get-ChildItem -Path C:\Windows

# 多个参数
Get-ChildItem -Path C:\Windows -Filter *.dll -ErrorAction SilentlyContinue
```

### 任务 B：开关参数

```powershell
# 使用开关参数
Get-ChildItem -Path C:\Windows -Recurse -Depth 1 -ErrorAction SilentlyContinue | Measure-Object

# 使用 WhatIf（安全参数）
Remove-Item -Path test.txt -WhatIf

# 使用 Confirm（确认参数）
# Remove-Item -Path test.txt -Confirm
```

### 任务 C：参数组合练习

```powershell
# 查找大于 1MB 的文件
Get-ChildItem -Path C:\Windows\System32 -Filter *.dll -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -gt 1MB } |
    Select-Object Name, @{Name="SizeMB";Expression={$_.Length / 1MB}} |
    Sort-Object Length -Descending |
    Select-Object -First 10
```

---

## 练习 2.3：变量操作

**目标**：掌握变量的创建、使用和管理。

### 任务 A：基础变量操作

```powershell
# 创建各种类型的变量
$name = "张三"
$age = 25
$isStudent = $true
$price = 99.99
$today = Get-Date

# 输出变量
Write-Output "姓名: $name, 年龄: $age"

# 查看变量类型
$name.GetType()
$age.GetType()
```

### 任务 B：强类型变量

```powershell
# 强制类型
[string]$text = "123"
[int]$num = 456
[bool]$flag = "true"
[array]$arr = 1,2,3

# 类型转换
[int]"100" + 50
"hello".GetType()
```

### 任务 C：数组操作

```powershell
# 创建数组
$fruits = @("苹果", "香蕉", "橙子")
$numbers = 1..10

# 数组索引
$fruits[0]      # 第一个元素
$fruits[-1]     # 最后一个元素
$fruits[0..2]   # 前三个元素

# 数组方法
$fruits.Count
$fruits += "葡萄"  # 添加元素
$fruits | ForEach-Object { $_ }
```

### 任务 D：Hashtable 操作

```powershell
# 创建哈希表
$person = @{
    Name = "张三"
    Age = 25
    City = "北京"
}

# 访问值
$person.Name
$person["Name"]

# 添加/修改
$person["Job"] = "工程师"
$person.Age = 26

# 遍历
foreach ($key in $person.Keys) {
    Write-Output "$key = $($person[$key])"
}
```

---

## 练习 2.4：运算符

**目标**：掌握各类运算符的使用。

### 任务 A：算术运算符

```powershell
$a = 15
$b = 4

$a + $b   # 加法
$a - $b   # 减法
$a * $b   # 乘法
$a / $b   # 除法
$a % $b   # 取余

# 复合赋值
$i = 10
$i += 5   # $i = $i + 5
$i *= 2   # $i = $i * 2
```

### 任务 B：比较运算符

```powershell
# 数值比较
5 -eq 5    # 等于
5 -ne 3    # 不等于
5 -gt 3    # 大于
5 -lt 10   # 小于
5 -ge 5    # 大于等于
5 -le 5    # 小于等于

# 字符串比较
"hello" -eq "hello"
"hello" -like "*ll*"
"hello" -match "^h"

# 包含判断
"hello world" -contains "world"
@(1,2,3) -contains 2
```

### 任务 C：逻辑运算符

```powershell
$x = 10
$y = 20

($x -gt 5) -and ($y -lt 30)  # 逻辑与
($x -gt 15) -or ($y -lt 30)  # 逻辑或
-not ($x -eq 5)               # 逻辑非
```

### 任务 D：字符串操作

```powershell
# 拼接
"Hello " + "World"

# 重复
"=" * 30

# 方法
"hello".ToUpper()
"Hello".ToLower()
"  hello  ".Trim()
"hello".Length

# -f 格式化
"{0} + {1} = {2}" -f 1, 2, 3
"{0:N2}" -f 3.14159
"{0:P}" -f 0.25
```

---

## 练习 2.5：条件语句

**目标**：掌握 if/elseif/else 和 switch 语句。

### 任务 A：if 语句

```powershell
$score = 85

if ($score -ge 90) {
    Write-Output "优秀"
} elseif ($score -ge 70) {
    Write-Output "良好"
} elseif ($score -ge 60) {
    Write-Output "及格"
} else {
    Write-Output "不及格"
}
```

### 任务 B：switch 语句

```powershell
# 基础 switch
$grade = "B"

switch ($grade) {
    "A" { Write-Output "优秀"; break }
    "B" { Write-Output "良好"; break }
    "C" { Write-Output "及格"; break }
    default { Write-Output "未知等级" }
}

# 带通配符的 switch
$filename = "report2024.pdf"

switch -Wildcard ($filename) {
    "*.txt" { Write-Output "文本文件"; break }
    "*.pdf" { Write-Output "PDF文件"; break }
    "*.doc*" { Write-Output "Word文档"; break }
    default { Write-Output "未知类型" }
}
```

### 任务 C：三元运算符（PowerShell 7+）

```powershell
$age = 20
$result = $age -ge 18 ? "成年人" : "未成年人"
Write-Output $result
```

---

## 练习 2.6：循环语句

**目标**：掌握各种循环语句的使用。

### 任务 A：foreach-Object（管道中）

```powershell
# 基本用法
1..5 | ForEach-Object { $_ * 2 }

# 对数组处理
@(1,2,3,4,5) | ForEach-Object {
    $square = $_ * $_
    Write-Output "$_ 的平方是 $square"
}

# 带 Begin/Process/End
1..5 | ForEach-Object -Begin {
    $total = 0
    Write-Output "开始计算..."
} -Process {
    $total += $_
} -End {
    Write-Output "总和: $total"
}
```

### 任务 B：foreach 循环

```powershell
$fruits = @("苹果", "香蕉", "橙子", "葡萄")

foreach ($fruit in $fruits) {
    Write-Output "我喜欢吃 $fruit"
}
```

### 任务 C：for 循环

```powershell
# 传统 for 循环
for ($i = 0; $i -lt 5; $i++) {
    Write-Output $i
}

# 范围操作符
1..10 | ForEach-Object { $_ * 2 }
```

### 任务 D：while 循环

```powershell
$i = 0
while ($i -lt 5) {
    Write-Output $i
    $i++
}

# do-while（至少执行一次）
do {
    $response = Read-Host "继续？(y/n)"
} while ($response -eq "y")
```

### 任务 E：循环控制

```powershell
# break - 跳出循环
for ($i = 1; $i -le 10; $i++) {
    if ($i -eq 5) { break }
    Write-Output $i
}

# continue - 跳过当前迭代
for ($i = 1; $i -le 5; $i++) {
    if ($i -eq 3) { continue }
    Write-Output $i
}
```

---

## 练习 2.7：帮助系统

**目标**：熟练使用帮助系统。

### 任务 A：查看帮助

```powershell
# 基本帮助
Get-Help Get-Process

# 详细帮助
Get-Help Get-Process -Detailed

# 示例
Get-Help Get-Process -Examples
```

### 任务 B：探索对象

```powershell
# 查看进程对象的属性和方法
Get-Process | Get-Member | Select-Object -First 20

# 查看日期对象的属性
Get-Date | Get-Member

# 查看特定类型的成员
(Get-Date).GetType() | Get-Member
```

---

## 练习 2.8：函数基础

**目标**：学会创建和使用函数。

### 任务 A：基础函数

```powershell
function Get-Square {
    param([int]$Number)
    return $Number * $Number
}

# 调用函数
Get-Square -Number 5  # 输出: 25
```

### 任务 B：带默认参数的函数

```powershell
function Greet {
    param(
        [string]$Name = "访客",
        [int]$Age = 0
    )
    Write-Output "你好，$Name！你的年龄是 $Age 岁。"
}

Greet -Name "张三" -Age 25
Greet  # 使用默认值
```

### 任务 C：管道函数

```powershell
function Get-Perimeter {
    param(
        [Parameter(ValueFromPipeline=$true)]
        [int]$Length,
        [int]$Width = 1
    )
    process {
        2 * ($Length + $Width)
    }
}

# 使用管道
5 | Get-Perimeter -Width 3
1..5 | Get-Perimeter -Width 2
```

---

## 综合练习：计算器函数库

**目标**：综合运用本课知识，创建一个计算器函数库。

### 任务：编写计算器函数

```powershell
# 定义函数库

# 1. 加法
function Add-Numbers {
    param([int]$A, [int]$B)
    return $A + $B
}

# 2. 减法
function Subtract-Numbers {
    param([int]$A, [int]$B)
    return $A - $B
}

# 3. 乘法
function Multiply-Numbers {
    param([int]$A, [int]$B)
    return $A * $B
}

# 4. 除法（带错误处理）
function Divide-Numbers {
    param([int]$A, [int]$B)
    if ($B -eq 0) {
        Write-Error "除数不能为零"
        return $null
    }
    return $A / $B
}

# 5. 计算矩形面积
function Get-RectangleArea {
    param([int]$Length, [int]$Width)
    return $Length * $Width
}

# 6. 计算矩形周长
function Get-RectanglePerimeter {
    param([int]$Length, [int]$Width)
    return 2 * ($Length + $Width)
}

# 测试函数
Write-Output "加法: $(Add-Numbers -A 10 -B 5)"
Write-Output "减法: $(Subtract-Numbers -A 10 -B 5)"
Write-Output "乘法: $(Multiply-Numbers -A 10 -B 5)"
Write-Output "除法: $(Divide-Numbers -A 10 -B 5)"
Write-Output "矩形面积: $(Get-RectangleArea -Length 10 -Width 5)"
Write-Output "矩形周长: $(Get-RectanglePerimeter -Length 10 -Width 5)"
```

### 扩展任务

1. 添加求平方根的函数
2. 添加判断质数的函数
3. 添加阶乘计算函数（递归实现）
4. 创建一个交互式计算器菜单

---

## 答案参考

### 练习 2.3 参考

```powershell
# 哈希表遍历的另一种方式
$person.GetEnumerator() | ForEach-Object {
    "$($_.Key) = $($_.Value)"
}
```

### 练习 2.5 参考

```powershell
# switch 处理多个值
$score = 85

switch ($score) {
    { $_ -ge 90 } { "A"; break }
    { $_ -ge 80 } { "B"; break }
    { $_ -ge 70 } { "C"; break }
    { $_ -ge 60 } { "D"; break }
    default { "F" }
}
```

---

## 下一步

完成以上练习后，继续学习 [Lesson 3: 文件系统操作](../03_filesystem/课程说明.md)
