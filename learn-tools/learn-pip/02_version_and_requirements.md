# 第2课：版本管理 & requirements.txt

## 1. 为什么版本很重要？

### 真实案例
你写了一个程序，用的是 `numpy 1.24`，一切正常。
半年后你升级了 numpy 到 `2.0`，突然程序报错了！

为什么？因为新版本可能：
- 删除了旧的函数
- 改变了函数的参数
- 修改了默认行为

所以我们需要**记录每个包的精确版本**，确保程序能稳定运行。

---

## 2. 版本号的含义

Python 包的版本号通常是 `主版本.次版本.补丁版本`，例如 `1.24.3`：

```
1.24.3
|  |  |
|  |  +-- 补丁版本：修复bug，不改功能
|  +----- 次版本：增加新功能，但向后兼容
+-------- 主版本：大改动，可能不兼容旧代码
```

**实际意义：**
- `1.24.3` -> `1.24.4`：修了bug，放心升级
- `1.24.3` -> `1.25.0`：加了新功能，一般安全
- `1.24.3` -> `2.0.0`：大改动，升级前要小心测试

---

## 3. pip 中的版本控制语法

```
pip install numpy==1.24.3      # 精确版本：只要 1.24.3
pip install numpy>=1.24        # 最低版本：1.24 或更高
pip install numpy<2.0          # 最高版本：低于 2.0
pip install numpy>=1.24,<2.0   # 范围：1.24 到 2.0 之间
pip install numpy~=1.24        # 兼容版本：>=1.24, <2.0（自动推算）
pip install numpy!=1.25.0      # 排除版本：不要 1.25.0
```

**最常用的：**
- `==` 精确指定（生产环境推荐）
- `>=` 最低版本（开发时常用）

---

## 4. requirements.txt —— 包的"购物清单"

### 它是什么？

`requirements.txt` 是一个纯文本文件，记录你的项目需要哪些包。
就像一个购物清单：

```
numpy==1.24.3
matplotlib==3.8.0
torch==2.2.0
```

### 为什么需要它？

场景1：你把代码发给同学，同学怎么知道要安装什么包？
场景2：你换了电脑，怎么快速恢复开发环境？
场景3：半年后你回来改代码，怎么保证环境一样？

答案都是：**用 requirements.txt 一键安装所有依赖。**

### 怎么创建？

**方法1：手动创建（适合新项目）**

在项目根目录创建一个 `requirements.txt` 文件，写入：
```
numpy>=1.24
matplotlib>=3.8
```

**方法2：自动生成（适合已有项目）**

```
pip freeze > requirements.txt
```

`pip freeze` 会列出当前环境中**所有已安装的包及其精确版本**，
然后 `>` 把输出写入文件。

生成的文件长这样：
```
certifi==2024.2.2
charset-normalizer==3.3.2
matplotlib==3.8.0
numpy==1.24.3
pillow==10.2.0
torch==2.2.0
...
```

> [注意] `pip freeze` 会列出所有包，包括依赖的依赖，
> 可能有几十上百个。这是正常的，确保了完全可复现的环境。

**方法3：只记录你主动安装的包（更简洁）**

手动写 requirements.txt，只写你项目直接用到的包：
```
numpy==1.24.3
matplotlib==3.8.0
torch==2.2.0
```
它们的依赖（比如 pillow）会在安装时自动处理。

### 怎么使用？

拿到别人的项目（或换了电脑），一条命令安装所有依赖：

```
pip install -r requirements.txt
```

`-r` 是 `--requirement` 的缩写，意思是"按照这个文件安装"。

---

## 5. pip freeze vs pip list 的区别

```
pip list      # 人类友好的格式，有表头
pip freeze    # 机器友好的格式，可以直接写入 requirements.txt
```

对比输出：

**pip list 输出：**
```
Package         Version
--------------- -------
numpy           1.24.3
matplotlib      3.8.0
```

**pip freeze 输出：**
```
numpy==1.24.3
matplotlib==3.8.0
```

`pip freeze` 的格式直接就是 requirements.txt 的格式！

---

## 6. 动手练习

在终端中依次运行：

```
# 1. 查看当前所有包（freeze格式）
pip freeze

# 2. 生成 requirements.txt（在你的项目目录下运行）
pip freeze > my_requirements.txt

# 3. 查看生成的文件内容
type my_requirements.txt

# 4. 查看某个包的可用版本（以 numpy 为例）
pip index versions numpy

# 5. 如果上面的命令不支持，可以用这个：
pip install numpy==999
# 故意写一个不存在的版本，pip 会报错并列出所有可用版本！
```

---

## 7. 实际工作流程

```
开始新项目
    |
    v
创建虚拟环境（第3课会讲）
    |
    v
pip install 需要的包
    |
    v
写代码、测试
    |
    v
pip freeze > requirements.txt   <-- 记录环境
    |
    v
把代码 + requirements.txt 一起分享/提交
    |
    v
别人拿到后: pip install -r requirements.txt   <-- 一键恢复
```

---

## 8. 小结

| 概念 | 说明 |
|------|------|
| 版本号 `1.24.3` | 主版本.次版本.补丁 |
| `pip install 包==版本` | 安装指定版本 |
| `pip freeze` | 列出所有包及版本（freeze格式） |
| `pip freeze > requirements.txt` | 导出依赖清单 |
| `pip install -r requirements.txt` | 按清单安装所有依赖 |
| `requirements.txt` | 项目的依赖清单文件 |

---

**下一课：** `03_venv.md` - 虚拟环境（venv）与 pip 配合使用
