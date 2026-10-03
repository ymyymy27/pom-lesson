# Neovim 速查表 (Cheat Sheet)

## 三种模式

| 模式 | 进入方式 | 用途 |
|------|----------|------|
| Normal | `Esc` | 导航、删除、复制（不编辑文本） |
| Insert | `i`, `a`, `o`, `I`, `A`, `O` | 插入文本 |
| Command | `:` | 执行命令 |
| Visual | `v`, `V`, `Ctrl+v` | 选中文本 |
| Replace | `R` | 覆盖文本 |

## 基础操作

### 退出保存

```
:w              保存
:wq             保存并退出
:q!             不保存强制退出
:x              保存并退出 (等价 :wq)
ZZ              保存并退出 (大写 ZZ)
ZQ              不保存退出 (大写 ZQ)
```

### 光标移动

```
h j k l         左/下/上/右 (基本)
w / b           下一个词首 / 上一个词首
e / ge          下一个词尾 / 上一个词尾
0               行首
^               行首非空字符
$               行尾
gg              文件首行
G               文件末行
{line}G         跳转到指定行
%               跳转到匹配括号
Ctrl+o / Ctrl+i 跳转历史前进/后退
```

### 文本编辑

```
i               在光标前插入
a               在光标后插入
o               在下行插入
O               在上行插入
s               删除当前字符并进入插入
S               删除整行并进入插入
cc              删除整行并进入插入
dd              删除当前行
dw              删除到词尾
d$              删除到行尾
d^              删除到行首
x               删除当前字符
p               粘贴 (在光标后)
P               粘贴 (在光标前)
yy              复制当前行
yw              复制到词尾
y$              复制到行尾
u               撤销
Ctrl+r          重做
.               重复上一次操作
~               切换大小写
```

### 查找与替换

```
/{pattern}      向下查找
?{pattern}      向上查找
n               下一个匹配
N               上一个匹配
:f {text}       快速查找行 (或 :{num})
:s/old/new/g    替换当前行所有
:%s/old/new/g   替换所有行
:%s/old/new/gc  替换所有 (逐个确认)
```

### 缩进

```
>>               向右缩进
<<               向左缩进
==               自动格式化当前行
```

## Buffers / Windows / Tabs

```
:ls              列出所有 buffer
:b {n}           切换到 buffer n
:bd              删除当前 buffer
:sp {file}       水平分屏
:vsp {file}      垂直分屏
Ctrl+w h/j/k/l   窗口间移动
Ctrl+w w         切换到下一个窗口
Ctrl+w q         关闭当前窗口
Ctrl+w =         等分窗口
:tabnew          新建标签页
gt / gT          下一个/上一个标签页
```

## 进阶

```
Ctrl+v 然后 I/A 然后 {text} 然后 Esc  多行编辑
Ctrl+v 然后 d/j/x/y             块操作
qa ... q                      录制宏到寄存器 a
@{a}                          执行宏
:!{cmd}                       执行 shell 命令
:r !{cmd}                     插入命令输出
```

## 命令行模式技巧

```
Ctrl+b / Ctrl+e           行首/行尾
Ctrl+w                    删除上一个词
Ctrl+u                    删除到行首
↑ / ↓                     历史命令
Tab / Shift+Tab           补全
```

## 模式切换速记

```
i  → 从当前字符前进入插入
a  → 从当前字符后进入插入 (append)
A  → 从行尾进入插入
I  → 从行首非空字符进入插入
o  → 从当前行下方新建行进入插入
O  → 从当前行上方新建行进入插入
s  → 删除当前字符进入插入 (substitute char)
S  → 删除整行进入插入 (substitute line)
C  → 删除到行尾进入插入 (change to end)
R  → 进入替换模式
```
