# Lesson 4: Conda 环境管理

> conda 不仅是包管理器，更是全能环境与包管理器，适合数据科学和机器学习领域

---

## 4.1 Conda 是什么？

Conda 是一个**跨平台的全能包和环境管理器**，可以管理：
- Python 包（替代 pip）
- 非 Python 依赖（如 C 库、CUDA、cuDNN）
- 任意编程语言的环境

```
pip:  只管理 Python 包
conda: 管理 Python + 非 Python 依赖 + 环境
```

### Conda vs pip vs venv

| 维度 | pip | venv | conda |
|-----|-----|------|-------|
| 包类型 | Python 包 | 无包管理 | Python + 非 Python |
| 环境隔离 | 需要配合 venv | Python 隔离 | 完全隔离 |
| GPU 支持 | 需手动配置 CUDA | 同 pip | 动安装 CUDA/cuDNN |
| 依赖解析 | 较简单 | 无 | 复杂但强大 |
| 预编译包 | wheel | 无 | conda 格式 |
| 安装速度 | 一般 | 无 | 快 |
| 适用场景 | 通用 Web 开发 | 轻量隔离 | 数据科学 / ML |

---

## 4.2 Miniconda vs Anaconda

| | Miniconda | Anaconda |
|--|-----------|----------|
| 大小 | ~400MB | ~3GB |
| 内容 | conda + Python + 基础工具 | Miniconda + 250+ 科学计算包 |
| 推荐 | **日常使用首选** | 需要大量科学包时 |
| 卸载包 | 支持 | 支持，但包多 |

**推荐**：安装 **Miniconda**，按需安装需要的包。

### 安装 Miniconda

下载地址：https://docs.conda.io/en/latest/miniconda.html

安装后验证：

```powershell
conda --version
# 输出: conda 24.x.x
```

---

## 4.3 conda 基本命令

### 环境管理

```powershell
# 创建新环境（默认带当前 conda 版本的 Python）
conda create --name myenv

# 创建指定 Python 版本的环境
conda create --name myenv python=3.11

# 创建环境并安装包
conda create --name myenv python=3.11 numpy pandas

# 克隆环境
conda create --name myenv_clone --clone myenv

# 删除环境
conda remove --name myenv --all

# 重命名环境（需要克隆 + 删除）
conda create --name new_name --clone old_name
conda remove --name old_name --all
```

### 环境切换

```powershell
# 激活环境
# Windows PowerShell:
conda activate myenv

# Windows CMD:
conda activate myenv

# 停用（返回 base 环境）
conda deactivate

# 查看所有环境
conda env list
# 或
conda info --envs
```

### 包管理（conda）

```powershell
# 安装包
conda install numpy

# 安装指定版本
conda install numpy=1.24

# 安装多个包
conda install pandas matplotlib scikit-learn

# 从指定频道安装
conda install --channel conda-forge 包名

# 更新包
conda update numpy

# 卸载包
conda remove numpy
```

### 搜索与查看

```powershell
# 搜索包
conda search numpy

# 查看已安装的包
conda list

# 查看某个环境中的包
conda list -n myenv

# 查看环境信息
conda info
conda info -e  # 等同于 conda env list
```

---

## 4.4 conda 环境目录结构

```
C:\Users\22271\.conda\           # conda 默认环境存储位置
│
├─ envs/
│   └─ myenv/                   # 名为 myenv 的环境
│       ├─ python.exe           # 环境专属的 Python
│       ├─ Scripts/             # Scripts 目录
│       ├─ Library/             # 非 Python 库
│       └─ Lib/
│           └─ site-packages/    # Python 包
│
└─ pkgs/                        # 缓存的包安装文件
```

> 注意：`conda create` 创建的不是一个 `.venv` 目录，而是放在 `~/.conda/envs/` 下的完整环境目录。

---

## 4.5 conda 与 pip 混用

### 在 conda 环境中使用 pip

Conda 环境中可以使用 pip，但需要注意：

```powershell
# 激活 conda 环境
conda activate myenv

# 使用 pip 安装 conda 仓库没有的包
pip install some-package

# pip 安装的包用 conda list 也能看到
conda list
# 显示:
# some-package    pip  1.2.3
```

### 混用风险

```powershell
# 警告：pip 和 conda 安装的包可能在依赖解析上产生冲突
conda install pytorch          # conda 依赖 torch==2.0
pip install transformers       # transformers 依赖 torch>=2.1
# → 可能出现 torch 的两个版本被安装，冲突！
```

### 最佳实践

| 场景 | 推荐 |
|-----|------|
| 纯 Python 项目 | 用 pip + venv |
| 数据科学 / ML | 用 conda + pip（conda 装 CUDA 包，pip 装纯 Python 包） |
| 需要 conda-forge 的包 | conda 优先 |

**数据科学推荐工作流**：

```powershell
# 1. 创建环境
conda create --name ml-env python=3.11
conda activate ml-env

# 2. 用 conda 装重型依赖（CUDA 相关）
conda install pytorch cuda-toolkit cudnn

# 3. 用 pip 装纯 Python 包
pip install transformers langchain datasets
```

---

## 4.6 conda 频道

频道（Channel）是包的来源仓库。

```powershell
# 添加频道
conda config --add channels conda-forge
conda config --add channels pytorch

# 查看当前频道
conda config --show channels

# 安装时指定频道（优先级最高）
conda install --channel conda-forge 包名
```

### 常用频道

| 频道 | 说明 |
|-----|------|
| defaults | Anaconda 官方仓库 |
| conda-forge | 社区维护，更新快，包更全 |
| pytorch | PyTorch 相关包 |
| nvidia | NVIDIA GPU 相关驱动 |

> 注意：_channels 的优先级从上到下，conda 会优先从上往下查找包。

---

## 4.7 conda 环境导出与复现

### 导出环境

```powershell
# 导出为 yaml 文件（推荐，可读性好）
conda env export > environment.yml

# 只导出你显式安装的包（不含传递依赖）
conda env export --from-history > environment.yml
```

### environment.yml 示例

```yaml
name: myenv
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.11
  - numpy=1.24.0
  - pandas=2.0.0
  - pip
  - pip:
    - langchain
    - langchain-openai
```

### 复现环境

```powershell
# 从 yaml 创建环境
conda env create --file environment.yml

# 如果环境已存在
conda env update --file environment.yml --prune
```

---

## 4.8 conda 与 pip 的选择建议

```
需要非 Python 依赖（CUDA, MKL, R）?
    │
    ├─ 是 → 使用 conda（或 conda + pip 混合）
    │
    └─ 否 → 项目类型？
            │
            ├─ 数据科学 / 机器学习 / AI → conda（方便 GPU 支持）
            ├─ Web 开发 / API / 后端 → pip + venv
            ├─ 轻量脚本 / 工具 → pip + venv
            └─ 需要精确复现依赖 → Poetry / PDM
```

---

## 4.9 常见问题

### Q1: conda activate 报错

**症状**：
```
CommandNotFoundError: Shell not initialized
```

**原因**：conda 未初始化。运行：

```powershell
conda init powershell
# 然后关闭并重新打开终端
```

### Q2: conda 安装包很慢

**原因**：默认源在国外。

**解决**：添加国内镜像。

```powershell
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/pytorch
conda config --set show_channel_urls yes
```

### Q3: conda 环境与 IDE 不兼容

conda 环境默认存储在 `~/.conda/envs/` 下，在 IDE 中选择解释器时需要找到对应环境目录中的 `python.exe`。

**路径**：`C:\Users\<用户>\.conda\envs\<环境名>\python.exe`

---

## 4.10 conda 与虚拟环境（venv）的对比总结

```
┌─────────────────────────────────────────────────────────┐
│                    Conda 风格                            │
│  conda create --name myenv                             │
│  conda activate myenv                                  │
│  conda install numpy                                   │
│  环境位置: ~/.conda/envs/myenv/                        │
│  python.exe: ~/.conda/envs/myenv/python.exe             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    venv 风格                            │
│  python -m venv .venv                                   │
│  .\.venv\Scripts\Activate.ps1                          │
│  pip install numpy                                     │
│  环境位置: 项目目录/.venv/                             │
│  python.exe: 项目目录/.venv\Scripts\python.exe         │
└─────────────────────────────────────────────────────────┘

两者的核心思想完全一致：创建独立的 Python 环境
只是实现方式和管理工具不同
```

---

## 课后练习

1. 如果你还没安装 conda，访问 https://docs.conda.io/en/latest/miniconda.html 下载安装 Miniconda
2. 运行 `conda --version` 验证安装
3. 创建一个名为 `test-conda` 的 conda 环境，指定 Python 3.11
4. 在该环境中安装 `numpy` 和 `pandas`
5. 运行 `conda list` 查看已安装的包
6. 尝试 `conda activate test-conda` 激活环境

---

## 下一步

→ [Lesson 5: 依赖管理（requirements.txt 与 pyproject.toml）](../05_dependency_management/README.md)
