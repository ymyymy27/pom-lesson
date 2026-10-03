> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第3课：虚拟环境（venv）与 pip 配合使用

## 1. 什么是虚拟环境？

### 问题场景

你有两个项目：
- **机器学习作业**：需要 `numpy 1.24`（旧版）
- **learn-pytorch**：需要 `numpy 1.26`（新版）

但一台电脑只有一个 Python，`numpy` 只能装一个版本，怎么办？

### 答案：虚拟环境

虚拟环境就是给每个项目创建一个**独立的小 Python 世界**，
每个世界有自己的包，互不干扰。

```
你的电脑
├── 项目A 的虚拟环境 (.venv)
|   ├── Python 3.12
|   ├── numpy 1.24
|   └── matplotlib 3.7
|
├── 项目B 的虚拟环境 (.venv)
|   ├── Python 3.12
|   ├── numpy 1.26
|   └── torch 2.2
|
└── 系统全局 Python（尽量不在这里装包）
```

### 你之前遇到的 .venv 文件夹

你在运行作业时，IDE 提示你创建虚拟环境，你选了之后出现的
`C:\Users\<用户名>\CascadeProjects\.venv` 就是一个虚拟环境！

---

## 2. 创建虚拟环境

### 命令

```
python -m venv 虚拟环境名称
```

> `python -m venv` 意思是"用 Python 运行 venv 模块"

### 推荐用法

```
# 进入你的项目目录后（在终端中）：

# 创建虚拟环境（名字推荐用 .venv）
python -m venv .venv
```

执行后，项目目录会多一个 `.venv` 文件夹：
```
你的项目/
├── .venv/              <-- 新出现的虚拟环境
|   ├── Scripts/        <-- Windows: Python和pip在这里
|   ├── Lib/            <-- 安装的包放在这里
|   └── pyvenv.cfg      <-- 配置文件
├── your_code.py
└── requirements.txt
```

### 为什么叫 .venv？

- 开头的 `.` 表示"隐藏文件夹"（约定俗成）
- `venv` 是 "virtual environment" 的缩写
- 你也可以取别的名字，但 `.venv` 是最通用的惯例

---

## 3. 激活虚拟环境

创建后必须**激活**才能使用。激活的意思是：
"从现在开始，`python` 和 `pip` 命令都指向这个虚拟环境"

### Windows PowerShell

```
.venv\Scripts\Activate.ps1
```

### Windows CMD

```
.venv\Scripts\activate.bat
```

### 激活成功的标志

终端提示符前面会出现 `(.venv)`：
```
(.venv) PS C:\Users\<用户名>\CascadeProjects\你的项目>
```

看到 `(.venv)` 就说明你**正在使用虚拟环境**里的 Python 和 pip。

### 验证

```
# 激活后运行这些命令，确认路径指向 .venv
python --version
pip --version          # 路径应该包含 .venv

# 查看已安装的包（新环境应该很干净，只有 pip 和 setuptools）
pip list
```

---

## 4. 在虚拟环境中安装包

激活后，`pip install` 会把包装到虚拟环境里，不会影响系统全局：

```
# 确保已激活（提示符有 (.venv)）
pip install numpy matplotlib
pip install torch
```

这些包只存在于这个虚拟环境中。

---

## 5. 退出（停用）虚拟环境

```
deactivate
```

执行后 `(.venv)` 消失，回到系统全局 Python。

---

## 6. 虚拟环境 + requirements.txt 配合

这是实际开发中最标准的工作流：

### 初始化项目

```
# 1. 创建项目目录
mkdir my_project

# 2. 创建虚拟环境
python -m venv .venv

# 3. 激活
.venv\Scripts\Activate.ps1

# 4. 安装需要的包
pip install numpy matplotlib

# 5. 记录依赖
pip freeze > requirements.txt

# 6. 开始写代码...
```

### 别人拿到你的项目后

```
# 1. 创建自己的虚拟环境
python -m venv .venv

# 2. 激活
.venv\Scripts\Activate.ps1

# 3. 一键安装所有依赖
pip install -r requirements.txt

# 4. 运行代码
python your_code.py
```

---

## 7. IDE（Windsurf/VS Code）中的虚拟环境

### IDE 会自动检测

当你打开一个包含 `.venv` 的项目时，IDE 通常会：
1. 自动发现虚拟环境
2. 提示你"是否使用这个解释器"
3. 在终端中自动激活虚拟环境

### 手动选择 Python 解释器

如果 IDE 没有自动检测到：
1. 按 `Ctrl + Shift + P`
2. 输入 `Python: Select Interpreter`
3. 选择 `.venv` 里的 Python

### 查看当前用的是哪个 Python

IDE 底部状态栏会显示当前 Python 解释器的路径，例如：
```
Python 3.12.0 ('.venv': venv)
```

如果显示的是 `.venv` 里的路径，说明你正在使用虚拟环境。

---

## 8. 重要注意事项

### 不要把 .venv 提交到 Git

`.venv` 文件夹很大（几十MB甚至几百MB），且每个人应该创建自己的。
在 `.gitignore` 中加入：
```
.venv/
```

只提交 `requirements.txt`，别人通过它来重建环境。

### 不要手动修改 .venv 里的文件

把它当作"只读"的就好，所有操作通过 pip 命令完成。

### 删除虚拟环境

直接删除 `.venv` 文件夹即可，不需要特殊命令：
```
# Windows
rmdir /s /q .venv

# 或者直接在文件管理器中删除
```

重新创建：`python -m venv .venv`

### 每个项目一个虚拟环境

推荐：
```
CascadeProjects/
├── learn-pytorch/
|   └── .venv/          <-- learn-pytorch 自己的环境
├── 机器学习作业/
|   └── .venv/          <-- 机器学习作业自己的环境
└── .venv/              <-- 这是你之前创建的，对应整个 CascadeProjects
```

> 你之前的 `.venv` 在 `CascadeProjects` 根目录下，
> 这意味着所有子项目共用一个环境。这对于初学者来说完全OK！
> 等项目多了、依赖冲突了，再改成每个项目一个环境。

---

## 9. 常见问题

### Q: PowerShell 报错"无法运行脚本"？

```
.venv\Scripts\Activate.ps1 : 无法加载文件...因为在此系统上禁止运行脚本
```

解决方法（以管理员身份运行 PowerShell）：
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然后重新激活即可。

### Q: 虚拟环境和 conda 有什么区别？

- `venv`：Python 自带的，轻量，够用
- `conda`：Anaconda 的工具，功能更多（可以管理非 Python 的包），但更重
- 初学者用 `venv + pip` 完全够了

### Q: 我需要为每一个 .py 文件创建虚拟环境吗？

不需要！一个**项目**（文件夹）一个就好。
项目里的所有 .py 文件共用同一个虚拟环境。

---

## 10. 小结

| 命令 | 作用 |
|------|------|
| `python -m venv .venv` | 创建虚拟环境 |
| `.venv\Scripts\Activate.ps1` | 激活（PowerShell） |
| `.venv\Scripts\activate.bat` | 激活（CMD） |
| `deactivate` | 退出虚拟环境 |
| `pip install -r requirements.txt` | 在虚拟环境中安装依赖 |
| `pip freeze > requirements.txt` | 导出当前环境的依赖 |

### 完整流程图

```
创建项目目录
     |
     v
python -m venv .venv        --> 创建虚拟环境
     |
     v
激活虚拟环境                  --> (.venv) 出现在提示符
     |
     v
pip install 需要的包          --> 包装到 .venv 里
     |
     v
写代码、运行、测试
     |
     v
pip freeze > requirements.txt --> 记录依赖
     |
     v
提交代码 + requirements.txt   --> 不提交 .venv！
```

---

**下一课：** `04-第4课国内镜像源加速 & 常见问题排查.md` - 国内镜像源加速 & 常见问题排查
