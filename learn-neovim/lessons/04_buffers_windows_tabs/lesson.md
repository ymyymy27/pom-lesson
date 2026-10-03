# 第 4 课：Buffer / Window / Tab

> 目标：理解并熟练管理多文件

## 4.1 三个概念

```
Buffer  → 内存中的文件（不一定显示）
Window  → 显示 Buffer 的"窗口"
Tab     → 存放 Window 的"标签页"
```

### 类比

- **Buffer** = 打开的文件（在内存里，看不见不一定不存在）
- **Window** = 你看文件的"窗户"（一个窗口看一个 Buffer）
- **Tab** = 窗口的分组（类似浏览器标签页）

## 4.2 Buffer 管理

```vim
:ls               " 列出所有 buffer
:ls!              " 列出所有 buffer（含不可见）
:b {name-or-num}  " 切换到指定 buffer（可补全）
:bn               " 下一个 buffer (buffer next)
:bp               " 上一个 buffer (buffer previous)
:bw               " 删除当前 buffer（从内存移除）
:bd               " 同上
:bfirst           " 第一个 buffer
:blast            " 最后一个 buffer
```

> 注意：`:bd` 删除 buffer 时，如果文件未保存会提示，可加 `!` 强制删除。

## 4.3 Window 分屏

```vim
:sp {file}        " 水平分割 (split)
:vsp {file}       " 垂直分割 (vertical split)
:sp               " 水平分割当前文件
:vsp              " 垂直分割当前文件
Ctrl+w s          " 同 :sp
Ctrl+w v          " 同 :vsp
```

### 窗口间移动

```vim
Ctrl+w h          " 移动到左边的窗口
Ctrl+w j          " 移动到下面的窗口
Ctrl+w k          " 移动到上面的窗口
Ctrl+w l          " 移动到右边的窗口
Ctrl+w w          " 切换到下一个窗口（循环）
Ctrl+w t          " 切换到最左上角的窗口
Ctrl+w p          " 切换到上一个窗口
```

### 窗口调整

```vim
Ctrl+w =          " 所有窗口等宽等高
Ctrl+w _          " 当前窗口最大化高度
Ctrl+w |          " 当前窗口最大化宽度
Ctrl+w -          " 减小高度
Ctrl+w +          " 增加高度
Ctrl+w <          " 减小宽度
Ctrl+w >          " 增加宽度
:res {n}          " 高度设为 n 行
:vertical res {n} " 宽度设为 n 列
```

### 关闭窗口

```vim
:q                " 关闭当前窗口
:on               " 只保留当前窗口，其他关闭 (only)
Ctrl+w c          " 关闭当前窗口
```

## 4.4 Tab 管理

```vim
:tabnew           " 新建空白标签页
:tabnew {file}   " 新建标签页并打开文件
gt                " 下一个标签页
gT                " 上一个标签页
{num}gt           " 跳到第 num 个标签页
:tabclose         " 关闭当前标签页
:tabonly          " 只保留当前标签页
:tabmove {n}      " 移动标签页到第 n 位
:tabs             " 列出所有标签页
```

## 4.5 练习任务

1. 用 `:sp` 分屏打开两个文件
2. 用 `Ctrl+w w` 在窗口间切换
3. 用 `:ls` 查看所有 buffer
4. 新建一个 tab，在新 tab 中打开文件
5. 用 `gt` / `gT` 在标签页间切换

## 4.6 进度检查

- [ ] 理解 Buffer / Window / Tab 的区别
- [ ] 能分屏打开文件
- [ ] 能在窗口间自由切换
- [ ] 能用 buffer 切换文件
- [ ] 能用标签页管理多组窗口
