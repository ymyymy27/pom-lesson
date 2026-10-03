# Lesson 2: pip 包管理器详解

> 掌握 pip 的全部核心用法，理解包版本冲突的机制

---

## 2.1 pip 是什么？

pip 是 Python 官方推荐的包管理器，用于从 [PyPI (Python Package Index)](https://pypi.org/) 下载和安装第三方包。

```
当你运行: pip install langchain
流程如下:
1. pip 连接 pypi.org
2. 下载 langchain 及其依赖
3. 解压安装到当前 Python 的 site-packages
4. 记录到 pip 的内部数据库（installed-files.txt）
```

---

## 2.2 pip 基础命令

### 安装包

```powershell
# 安装最新版本
pip install 包名

# 安装指定版本
pip install 包名==1.2.3

# 安装版本范围
pip install 包名>=1.0,<2.0

# 安装预发布版本
pip install 包名==1.3.0a1

# 从 GitHub 安装
pip install git+https://github.com/user/repo.git

# 从本地 wheel 文件安装
pip install ./package.whl
```

### 常用选项

| 选项 | 作用 |
|-----|------|
| `-i <url>` | 指定 PyPI 源（国内镜像） |
| `-U` / `--upgrade` | 升级到最新版本 |
| `-r <file>` | 从 requirements.txt 安装 |
| `--no-deps` | 不安装依赖 |
| `--force-reinstall` | 强制重新安装 |
| `-q` / `--quiet` | 安静模式，减少输出 |
| `--dry-run` | 模拟运行，不实际安装 |

```powershell
# 升级已安装的包
pip install -U 包名

# 安装但不安装依赖（谨慎使用）
pip install --no-deps 包名

# 模拟安装（查看会做什么，但不实际安装）
pip install 包名 --dry-run
```

### 卸载包

```powershell
# 卸载
pip uninstall 包名

# 卸载多个
pip uninstall 包名1 包名2

# 自动确认（无需交互）
pip uninstall -y 包名

# 卸载 requirements.txt 中的所有包
pip uninstall -r requirements.txt -y
```

### 查看已安装的包

```powershell
# 列出所有已安装的包
pip list

# 列出可升级的包
pip list --outdated

# 列出某个包的详细信息
pip show 包名

# 列出包的依赖
pip show -f 包名

# 检查已安装包的兼容性
pip check
```

---

## 2.3 PyPI 镜像源（国内加速）

默认 PyPI 在国外，下载慢。国内常用镜像：

| 镜像 | 地址 |
|-----|------|
| 清华 | `https://pypi.tuna.tsinghua.edu.cn/simple` |
| 阿里云 | `https://mirrors.aliyun.com/pypi/simple` |
| 腾讯云 | `https://mirrors.cloud.tencent.com/pypi/simple` |
| 华为云 | `https://repo.huaweicloud.com/repository/pypi/simple` |

### 临时使用镜像

```powershell
pip install 包名 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 永久配置镜像（推荐）

创建或编辑 `pip.ini`（Windows）：

```powershell
# 打开配置文件（用户级）
notepad $env:APPDATA\pip\pip.ini
```

内容：
```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple

[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
```

> 注意：某些镜像会同步延迟，建议同时添加备用源。

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
extra-index-url = https://mirrors.aliyun.com/pypi/simple

[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
trusted-host = mirrors.aliyun.com
```

### 验证镜像配置

```powershell
pip config list
```

---

## 2.4 包版本冲突的原理

### 什么是依赖冲突？

假设项目 A 需要 `requests>=2.28`，项目 B 需要 `requests<2.28`，两个版本的 API 不兼容。如果把 A 和 B 装到同一个环境，就会冲突。

### 依赖解析过程

pip 在安装时会尝试满足所有依赖要求。过程如下：

```powershell
# 例如安装 langchain-openai 时
pip install langchain-openai

# pip 发现 langchain-openai 需要:
#   - langchain-core >= 1.0
#   - openai >= 1.0
#   - tiktoken >= 0.5

# pip 尝试找到兼容所有要求的版本组合
# 如果 langchain-core 2.0 已安装但要求 < 2.0 → 冲突！
```

### 查看依赖树

```powershell
# 查看某个包的依赖
pip show langchain-openai

# 使用 pipdeptree 查看完整依赖树
pip install pipdeptree
pipdeptree
pipdeptree --warn fail  # 标记冲突
```

### 解决冲突的方法

1. **升级/降级相关包**：调整版本约束
2. **使用虚拟环境**：为不同项目使用不同的环境
3. **强制安装**：`pip install --force-reinstall`（慎用，可能导致运行时错误）
4. **使用 pip-tools** 生成锁定文件

---

## 2.5 pip cache（缓存）

pip 会缓存下载的包，避免重复下载。

```powershell
# 查看缓存大小
pip cache dir

# 列出缓存的包
pip cache list

# 清除缓存
pip cache purge
```

**什么时候需要清缓存？**
- 包安装失败后重试
- 下载了错误的 wheel 文件
- 磁盘空间不足

---

## 2.6 pip freeze（导出依赖）

```powershell
# 导出所有已安装的包及其精确版本
pip freeze > requirements.txt
```

**输出示例：**
```txt
langchain==1.2.15
langchain-core==1.2.27
langchain-openai==1.1.12
numpy==1.26.0
```

### freeze 的局限性

1. **包含所有包**：包括 pip、setuptools 等自动安装的包
2. **不区分直接依赖和传递依赖**：freeze 出来的文件包含了项目并不直接需要的包
3. **版本可能不兼容**：pip freeze 导出的环境不一定能完整复现

### 更好的做法

```powershell
# 使用 pipreqs 只导出项目实际使用的包
pip install pipreqs
pipreqs ./ --force

# 使用 pip-tools 锁定依赖
pip install pip-tools
pip-compile requirements.in
```

---

## 2.7 pip install 的工作原理

```
pip install langchain
│
├─ 1. 查询 PyPI API（https://pypi.org/pypi/langchain/json）
│   获取: 最新版本号、下载地址、依赖列表、wheel 文件信息
│
├─ 2. 下载文件
│   优先下载 wheel（.whl，预编译格式，安装快）
│   其次下载源码包（.tar.gz，需要编译）
│
├─ 3. 依赖解析
│   检查已安装的包是否满足要求
│   如果不满足，递归下载依赖
│
├─ 4. 安装
│   - 解压 wheel → site-packages/
│   - 执行 setup.py 或 pyproject.toml 中的安装脚本
│   - 写入安装记录（installed-files.txt）
│
└─ 5. 完成
    langchain 已安装到: sys.prefix + site-packages/langchain/
```

---

## 2.8 常见问题

### Q1: pip install 报错 "externally-managed-environment"

Python 3.11+ 在某些发行版（Debian, Ubuntu 等）中有 PEP 668 保护，禁止在系统 Python 中直接 pip install。

**解决方法**：
- 使用虚拟环境（推荐）
- 或使用 `pip install --break-system-packages`（临时方案）

### Q2: 报错 "could not find a version that satisfies the requirement"

可能原因：
1. 包名拼写错误
2. 包不存在于 PyPI
3. Python 版本不兼容（某些包不支持 3.11）
4. 系统架构不支持（某些包无 Windows 版本）

### Q3: ImportError 明明安装了这个包

```python
import langchain  # 报错: No module named 'langchain'
```

检查：
1. `pip show langchain` — 确认包存在
2. `python -c "import sys; print(sys.path)"` — 确认 site-packages 在路径中
3. **IDE 的 Python 解释器**与 pip 使用的 Python 是否一致？

---

## 课后练习

1. 配置 pip 镜像源（清华源）
2. 运行 `pip list` 查看你当前安装的所有包
3. 运行 `pip check` 检查依赖冲突
4. 运行 `pip freeze > requirements.txt` 导出依赖
5. 使用 `pip show langchain` 查看 langchain 的详细信息

---

## 下一步

→ [Lesson 3: 虚拟环境完全指南（venv & virtualenv）](../03_venv_virtualenv/README.md)
