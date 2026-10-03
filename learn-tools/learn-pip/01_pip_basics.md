# 第1课：pip 是什么 & 基本命令

## 1. pip 是什么？

### 一句话解释
**pip 就是 Python 的"应用商店"** —— 别人写好的 Python 工具包，你用 pip 一条命令就能下载安装到你的电脑上。

### 类比理解
| 你熟悉的 | 对应的 pip 概念 |
|---------|---------------|
| 手机应用商店 | pip（包管理器） |
| 一个 App | 一个 Python 包（package） |
| 安装 App | `pip install 包名` |
| 卸载 App | `pip uninstall 包名` |
| 查看已安装的 App | `pip list` |
| App Store / Google Play | PyPI（Python Package Index，官方包仓库） |

### 为什么需要 pip？

你在作业里用的 `numpy`、`matplotlib`，以及之前学的 `torch`（PyTorch），
它们都**不是 Python 自带的**，是全世界的开发者写好后上传到 PyPI 的。

没有 pip 的话，你需要：
1. 去网站手动下载源码
2. 手动解压
3. 手动放到正确的目录
4. 手动处理依赖关系...

有了 pip，一条命令搞定：`pip install numpy`

---

## 2. 检查 pip 是否已安装

打开终端（Windsurf/VS Code 底部的终端，或 Windows 搜索"PowerShell"），输入：

```
pip --version
```

你应该看到类似这样的输出：
```
pip 24.0 from C:\Users\22271\...\pip (python 3.12)
```

这说明：
- pip 版本是 24.0
- pip 的安装路径
- 它关联的 Python 版本是 3.12

> 如果报错"pip 不是内部命令"，说明 Python 安装时没有勾选"Add to PATH"，
> 可以试试 `python -m pip --version`

---

## 3. 最常用的 pip 命令

### 3.1 安装包

```
pip install 包名
```

例子：
```
pip install numpy              # 安装 numpy（最新版）
pip install numpy==1.24.0      # 安装指定版本
pip install numpy>=1.20        # 安装 1.20 或更高版本
pip install numpy matplotlib   # 一次安装多个包（空格分隔）
```

**安装时发生了什么？**
1. pip 连接到 PyPI（https://pypi.org）
2. 找到你要的包
3. 下载到你电脑上
4. 自动安装这个包**依赖的其他包**（比如安装 matplotlib 时会自动装 numpy）
5. 放到 Python 的 `site-packages` 目录下

### 3.2 卸载包

```
pip uninstall 包名
```

例子：
```
pip uninstall numpy           # 卸载 numpy
pip uninstall numpy -y        # 加 -y 跳过确认提示，直接卸载
```

### 3.3 查看已安装的包

```
pip list
```

输出类似：
```
Package         Version
--------------- -------
matplotlib      3.8.0
numpy           1.24.0
pip             24.0
torch           2.2.0
```

### 3.4 查看某个包的详细信息

```
pip show numpy
```

输出类似：
```
Name: numpy
Version: 1.24.0
Summary: Fundamental package for array computing in Python
Home-page: https://numpy.org
Location: C:\Users\22271\...\site-packages
Requires:                          ← numpy 不依赖其他包
Required-by: matplotlib, torch     ← 这些包依赖 numpy
```

**重点看这几项：**
- **Version**：当前安装的版本
- **Location**：安装在哪个目录
- **Requires**：它依赖哪些包
- **Required-by**：哪些包依赖它（卸载前要注意！）

### 3.5 搜索可更新的包

```
pip list --outdated
```

输出有新版本可用的包：
```
Package    Version  Latest   Type
---------- -------- -------- -----
numpy      1.24.0   1.26.0   wheel
```

### 3.6 升级包

```
pip install --upgrade 包名
pip install -U 包名            # -U 是 --upgrade 的缩写
```

例子：
```
pip install -U numpy           # 升级 numpy 到最新版
pip install -U pip             # 升级 pip 自己！（推荐定期做）
```

### 3.7 升级 pip 自己

pip 本身也是一个包，也需要更新：
```
python -m pip install --upgrade pip
```

---

## 4. 动手练习

请在终端中依次运行以下命令，观察输出：

```
# 1. 查看 pip 版本
pip --version

# 2. 查看已安装的所有包
pip list

# 3. 查看 numpy 的详细信息（你作业里用到的）
pip show numpy

# 4. 查看 matplotlib 的详细信息
pip show matplotlib

# 5. 查看有哪些包可以更新
pip list --outdated
```

---

## 5. 小结

| 命令 | 作用 | 例子 |
|------|------|------|
| `pip install 包名` | 安装包 | `pip install numpy` |
| `pip install 包名==版本` | 安装指定版本 | `pip install numpy==1.24.0` |
| `pip uninstall 包名` | 卸载包 | `pip uninstall numpy` |
| `pip list` | 列出所有已安装的包 | |
| `pip show 包名` | 查看包的详细信息 | `pip show numpy` |
| `pip list --outdated` | 查看可更新的包 | |
| `pip install -U 包名` | 升级包 | `pip install -U numpy` |
| `pip --version` | 查看 pip 版本 | |

---

**下一课：** `02_version_and_requirements.md` - 版本管理 & requirements.txt
