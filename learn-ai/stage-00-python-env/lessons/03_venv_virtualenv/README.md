# Lesson 3: 虚拟环境完全指南（venv & virtualenv）

> 理解虚拟环境的本质，掌握项目依赖隔离的核心技能

---

## 3.1 什么是虚拟环境？

**虚拟环境（Virtual Environment）** 是一个独立的 Python 运行环境，拥有自己独立的：
- Python 解释器副本
- site-packages 目录（包的安装位置）
- pip 副本

```
无虚拟环境（全局环境）
┌─────────────────────────────────────┐
│ 系统 Python                          │
│  site-packages/                     │
│    ├─ langchain v1.2               │
│    ├─ numpy v1.24                  │
│    └─ django v4.0                  │
│  (所有项目共用同一个环境)             │
└─────────────────────────────────────┘

有虚拟环境（每个项目独立）
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 项目 A 的环境 │  │ 项目 B 的环境 │  │ 项目 C 的环境 │
│ .venv/        │  │ .venv/        │  │ .venv/        │
│  langchain   │  │  django 4.0   │  │  numpy 2.0    │
│  numpy 1.24  │  │  flask 2.0    │  │  pandas 1.5   │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 为什么需要虚拟环境？

1. **避免版本冲突**：项目 A 需要 numpy 1.24，项目 B 需要 numpy 2.0，没有虚拟环境就无法共存
2. **环境可复现**：团队成员或部署服务器可以用完全相同的依赖版本
3. **保持全局环境干净**：不污染系统 Python
4. **轻松重置**：删掉 .venv 重建即可

---

## 3.2 venv vs virtualenv 区别

| 特性 | venv | virtualenv |
|-----|------|------------|
| 是否需要安装 | Python 3.3+ 内置，无需安装 | 需要 `pip install virtualenv` |
| 跨 Python 版本 | 只创建同版本 | 可创建不同 Python 版本的环境 |
| 速度 | 较快 | 较快 |
| 符号链接 | Windows 不支持，用复制 | 可用符号链接 |
| 推荐场景 | Python 3.3+ 项目首选 | 需要跨 Python 版本时使用 |

**推荐**：Python 3.3+ 使用 `venv`，已经足够了。

---

## 3.3 创建虚拟环境

### 基本命令

```powershell
# 在当前目录下创建名为 .venv 的虚拟环境
python -m venv .venv
```

> 注意：`.venv` 是一个约定俗成的目录名，你可以用任何名字如 `venv`、`env`、`myenv` 等。

### 查看创建的内容

```powershell
# Windows PowerShell 中查看 .venv 目录结构
Get-ChildItem -Recurse .venv | Select-Object FullName
```

创建后 `.venv` 目录结构如下：

```
.venv/
│
├─ Include/                  # C 头文件（Windows 下通常为空）
├─ Lib/
│   └─ site-packages/       # ★ 包的安装目录
│       └─ (空的，刚创建时)
├─ Scripts/
│   ├─ python.exe            # ★ Windows 上的 Python 解释器
│   ├─ pythonw.exe          # GUI Python（Windows）
│   ├─ pip.exe              # 虚拟环境专属的 pip
│   ├─ Activate.ps1         # PowerShell 激活脚本
│   └─ activate.bat         # CMD 激活脚本
├─ pyvenv.cfg               # 配置文件，指向系统 Python
└─ .gitignore（可选）
```

---

## 3.4 激活虚拟环境

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

**注意**：如果遇到执行策略错误：

```powershell
# 查看当前执行策略
Get-ExecutionPolicy

# 临时允许运行脚本（当前会话）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# 或者使用（更安全的方式）
powershell -ExecutionPolicy Bypass -File .\.venv\Scripts\Activate.ps1
```

### Windows CMD

```cmd
.\.venv\Scripts\activate.bat
```

### 验证激活成功

激活后，终端提示符前会显示 `(.venv)` 标记：

```powershell
(.venv) PS E:\code\Projects\learn\project>
```

同时 `python` 和 `pip` 命令会指向虚拟环境内的版本：

```powershell
# 应该指向 .venv 下的 python.exe
where python

# 应该指向 .venv 下的 pip.exe
where python
```

---

## 3.5 停用虚拟环境

```powershell
deactivate
```

执行后，提示符恢复正常，`python` 和 `pip` 回到系统 Python。

---

## 3.6 在虚拟环境中安装包

激活后，安装操作只在虚拟环境内生效：

```powershell
# 激活
.\.venv\Scripts\Activate.ps1

# 安装包（只影响当前虚拟环境）
pip install langchain langchain-openai

# 查看虚拟环境中的包（只包含你安装的 + 少量基础包）
pip list
```

### .venv 与系统环境对比

```powershell
# 在虚拟环境中
python -c "import sys; print('\n'.join(sys.path))"

# 对比系统环境（在项目外运行）
python -c "import sys; print('\n'.join(sys.path))"
```

注意虚拟环境中的 `sys.path` 开头会有一个空字符串（代表当前目录）和 `.venv\Lib\site-packages`。

---

## 3.7 删除虚拟环境

最安全的方式：停用后，直接删除 `.venv` 目录。

```powershell
deactivate
Remove-Item -Recurse -Force .venv
```

> 虚拟环境没有"卸载"过程，删除目录就是"卸载"。

---

## 3.8 .gitignore 配置

如果用 Git 管理项目，在 `.gitignore` 中添加：

```gitignore
# 虚拟环境
.venv/
venv/
env/
*.venv/

# 但保留 pyvenv.cfg（如果需要）
# !注意：通常不需要保留，整个 .venv 应该被忽略
```

---

## 3.9 virtualenv 进阶用法

### 安装

```powershell
pip install virtualenv
```

### 创建不同 Python 版本的环境

```powershell
# 指定使用某个 Python 版本
virtualenv -p C:\Python310\python.exe myenv

# 使用系统上所有可用的 Python
virtualenv -p python3.11 myenv
```

### 常用选项

```powershell
virtualenv --system-site-packages myenv    # 继承系统 site-packages
virtualenv --no-download myenv              # 不下载新包
virtualenv --copies myenv                    # 复制文件而非符号链接
```

---

## 3.10 常见问题与解决方案

### 问题 1: "不是内部或外部命令"

**症状**：
```
.venv\Scripts\activate.ps1 : 无法将 ".venv\Scripts\activate.ps1" 项识别为 cmdlet、函数、脚本文件或可运行程序的名称。
```

**原因**：未使用 `.\` 前缀指定当前目录路径。

**解决**：
```powershell
.\.venv\Scripts\Activate.ps1
# 或者先切换到项目目录
cd 项目路径
.\.venv\Scripts\Activate.ps1
```

### 问题 2: 虚拟环境中的包 IDE 仍然找不到

**这是你遇到的问题！** 核心原因：IDE 没有将虚拟环境的 Python 设为解释器。

**解决**：
1. 在 IDE 中选择 `.venv\Scripts\python.exe` 作为解释器
2. 具体见 Lesson 6: IDE 环境配置

### 问题 3: 虚拟环境创建的 .venv 目录很大

**原因**：每个 venv 都会复制一份完整的标准库和 pip/wheel/setuptools。

**优化**：使用 `--without-pip` 创建极简环境，然后手动安装 pip：

```powershell
python -m venv --without-pip .venv
```

### 问题 4: 激活脚本被系统策略阻止

Windows PowerShell 默认不允许执行本地脚本。

**解决方案**（按推荐顺序）：
1. 改用 CMD：`.\.venv\Scripts\activate.bat`
2. 临时修改策略：`Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
3. 永久允许（不推荐）：`Set-ExecutionPolicy RemoteSigned -Scope LocalMachine`

### 问题 5: pip install 报错 "externally-managed-environment"

Python 3.11+ 的系统保护。

**解决**：在虚拟环境中不会遇到此问题。确保你确实在虚拟环境内运行 pip：

```powershell
.\.venv\Scripts\Activate.ps1  # 先激活
pip install 包名               # 再安装
```

---

## 3.11 最佳实践

### 项目结构推荐

```
my-project/
│
├─ .venv/                 # 虚拟环境（不提交到 Git）
├─ src/                   # 源代码
├─ tests/                 # 测试代码
├─ docs/                  # 文档
│
├─ requirements.txt       # 开发依赖
├─ requirements-dev.txt   # 开发/测试依赖
├─ requirements-prod.txt  # 生产依赖
│
├─ .gitignore
└─ README.md
```

### 使用虚拟环境的正确流程

```
1. 创建项目目录
2. 进入目录
3. python -m venv .venv
4. .\.venv\Scripts\Activate.ps1
5. pip install -r requirements.txt
6. 开始开发
```

---

## 课后练习

1. 在 `stage-00-python-env/study/` 目录下创建一个虚拟环境
2. 激活虚拟环境，安装 `langchain` 和 `langchain-openai`
3. 运行 `pip list` 对比激活前后的包列表
4. 运行 `where python` 对比激活前后的 Python 路径
5. 停用虚拟环境，确认回到了系统 Python

---

## 下一步

→ [Lesson 4: Conda 环境管理](../04_conda/README.md)
