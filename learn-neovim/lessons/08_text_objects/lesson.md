# 第 8 课：文本对象

> 目标：理解文本对象，实现精准的整块操作

## 8.1 什么是文本对象

文本对象（text object）= **一个完整语义单元**（词、句子、段落、代码块……）

**格式**：

```
{operator}{a|i}{object}
```

- `a` = around（含边界，如引号/括号本身）
- `i` = inside（不含边界，只内部）

## 8.2 常用文本对象

| 命令 | 含义 |
|------|------|
| `iw` | 当前词（inside word） |
| `aw` | 当前词含空格（around word） |
| `iW` | 当前 WORD（大写 WORD，忽略标点） |
| `aW` | 当前 WORD 含空格 |
| `is` | 当前句子（inside sentence） |
| `as` | 当前句子含空格 |
| `ip` | 当前段落（inside paragraph） |
| `ap` | 当前段落含空行 |
| `i"` | 引号**内**内容 |
| `a"` | 引号及**内**内容 |
| `i'` | 单引号内 |
| `a'` | 单引号及内 |
| `` i` `` | 反引号内 |
| `` a` `` | 反引号及内 |
| `i(` 或 `ib` | 括号**内** |
| `a(` 或 `ab` | 括号及**内** |
| `i)` / `a)` | 同上 |
| `i{` / `a{` | 大括号 |
| `iB` / `aB` | 大括号块 |
| `i[` / `a[` | 方括号 |
| `i<` / `a<` | 尖括号 |
| `i<Tab>` | 制表符分隔的区域 |
| `at` | XML/HTML 标签块（如 `<div>...</div>`） |
| `it` | 标签块内部 |

## 8.3 实际应用

### 删除整个词

```
daw              " delete around word — 删除当前词（含前后空格）
diw              " delete inside word — 只删词本身
```

### 修改引号内的内容

```
ci"              " change inside quotes
ca"              " change around quotes
ci'              " change inside single quotes
```

### 修改括号/函数参数

```
ci(              " change inside parentheses
ci)              " 同上
ca(              " change around parentheses
cib              " 同上（b = bracket）
```

### 删除括号内的内容

```
di(              " delete inside parentheses
da(              " delete parentheses and inside
```

### 快速选中整个文件内容

```
ggVG             " gg=到开头，V=行可视化，G=到结尾
```

## 8.4 数字 + 文本对象

```
ci3w             " 修改 3 个连续的词
da2a(            " 删除周围 2 个括号块
```

## 8.5 练习任务

在 `lessons/08_text_objects/practice.txt` 中：

1. 用 `ci"` 修改引号里的内容
2. 用 `ci(` 修改括号里的内容
3. 用 `daw` 删除一个完整的词
4. 用 `yi( yi)` 复制括号里的内容
5. 用 `dat` 或 `it` 选中 HTML/标签块（如果文件中有）

## 8.6 进度检查

- [ ] 理解 `i` vs `a` 的区别
- [ ] 能用 `ci" ci( ci{` 修改引号/括号/花括号内容
- [ ] 能用 `da" da( da{` 删除整块内容
- [ ] 能用 `daw` 删除整个词
