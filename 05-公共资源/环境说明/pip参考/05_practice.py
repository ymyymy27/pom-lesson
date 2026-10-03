import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：实战演练 - 验证你的 pip 环境
==============================================================================

这个脚本会自动检查你的 Python 和 pip 环境，
帮你确认一切是否正常工作。

直接运行：python 05_practice.py
==============================================================================
"""

import subprocess
import importlib
import os

print("=" * 60)
print("第5课：pip 环境检查与实战演练")
print("=" * 60)

# ============================================================================
# 1. 基本环境信息
# ============================================================================
print("\n--- 1. 基本环境信息 ---")

print(f"Python 版本:  {sys.version}")
print(f"Python 路径:  {sys.executable}")
print(f"当前目录:     {os.getcwd()}")

# 检查是否在虚拟环境中
in_venv = hasattr(sys, 'real_prefix') or (
    hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
)
if in_venv:
    print(f"虚拟环境:     [是] 你正在使用虚拟环境")
    print(f"  环境路径:   {sys.prefix}")
else:
    print(f"虚拟环境:     [否] 你在使用系统全局 Python")
    print(f"  (建议为每个项目创建虚拟环境，参见第3课)")

# ============================================================================
# 2. 检查 pip 信息
# ============================================================================
print("\n--- 2. pip 信息 ---")

try:
    result = subprocess.run(
        [sys.executable, '-m', 'pip', '--version'],
        capture_output=True, text=True, encoding='utf-8'
    )
    print(f"pip 信息:     {result.stdout.strip()}")
except Exception as e:
    print(f"[错误] 无法获取 pip 信息: {e}")

# 检查 pip 镜像源设置
try:
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'config', 'list'],
        capture_output=True, text=True, encoding='utf-8'
    )
    config = result.stdout.strip()
    if config:
        print(f"\npip 配置:")
        for line in config.split('\n'):
            print(f"  {line}")
        if 'tuna' in config or 'aliyun' in config or 'ustc' in config:
            print("  --> [好] 你已经设置了国内镜像源，下载会很快")
    else:
        print(f"\npip 配置:     (使用默认设置)")
        print("  --> [建议] 建议设置国内镜像源加速下载，参见第4课")
        print("  --> 运行: pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple")
except Exception:
    pass

# ============================================================================
# 3. 检查常用包是否已安装
# ============================================================================
print("\n--- 3. 常用包检查 ---")

packages_to_check = [
    ("numpy",      "科学计算基础包（你作业里用到的）"),
    ("matplotlib", "绘图工具（你作业里画爱心用的）"),
    ("torch",      "PyTorch 深度学习框架"),
    ("torchvision","PyTorch 视觉工具包"),
    ("pandas",     "数据分析工具"),
    ("requests",   "HTTP 网络请求库"),
    ("PIL",        "图像处理（安装名: Pillow）"),
    ("sklearn",    "机器学习（安装名: scikit-learn）"),
]

installed = []
not_installed = []

for pkg_import, description in packages_to_check:
    try:
        mod = importlib.import_module(pkg_import)
        version = getattr(mod, '__version__', '未知版本')
        print(f"  [已安装] {pkg_import:12s} {version:15s}  -- {description}")
        installed.append(pkg_import)
    except ImportError:
        print(f"  [未安装] {pkg_import:12s} {'':15s}  -- {description}")
        not_installed.append(pkg_import)

print(f"\n  已安装: {len(installed)} 个，未安装: {len(not_installed)} 个")

if not_installed:
    print(f"\n  如果需要安装缺失的包，可以运行:")
    # 映射导入名到安装名
    install_name_map = {
        "PIL": "Pillow",
        "sklearn": "scikit-learn",
        "cv2": "opencv-python",
    }
    for pkg in not_installed:
        install_name = install_name_map.get(pkg, pkg)
        print(f"    pip install {install_name}")

# ============================================================================
# 4. 检查包冲突
# ============================================================================
print("\n--- 4. 包依赖冲突检查 ---")

try:
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'check'],
        capture_output=True, text=True, encoding='utf-8'
    )
    output = result.stdout.strip()
    if "No broken requirements found" in output or not output:
        print("  [好] 没有发现包冲突，环境健康")
    else:
        print("  [警告] 发现以下冲突:")
        for line in output.split('\n'):
            print(f"    {line}")
        print("  (可以尝试升级相关包来解决)")
except Exception as e:
    print(f"  无法检查: {e}")

# ============================================================================
# 5. 已安装包的总数
# ============================================================================
print("\n--- 5. 已安装包统计 ---")

try:
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'list', '--format=columns'],
        capture_output=True, text=True, encoding='utf-8'
    )
    lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
    # 减去表头2行
    pkg_count = max(0, len(lines) - 2)
    print(f"  当前环境共安装了 {pkg_count} 个包")
except Exception:
    pass

# ============================================================================
# 6. 小测验：验证你学到的知识
# ============================================================================
print("\n--- 6. 知识小测验 ---")
print("""
回答以下问题（答案在下方）：

Q1: 安装 numpy 1.24.0 版本的命令是什么？
Q2: 如何一键安装 requirements.txt 中的所有包？
Q3: 如何查看 matplotlib 的详细信息（版本、依赖等）？
Q4: 如何创建一个虚拟环境？
Q5: pip 下载太慢怎么办？

---------- 答案 ----------

A1: pip install numpy==1.24.0
A2: pip install -r requirements.txt
A3: pip show matplotlib
A4: python -m venv .venv
A5: 设置国内镜像源:
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
""")

# ============================================================================
# 7. 总结
# ============================================================================
print("=" * 60)
print("[完成] pip 教程全部5课学习完毕！")
print("=" * 60)
print("""
核心知识回顾：

  第1课 - 基本命令
    pip install / uninstall / list / show

  第2课 - 版本管理
    requirements.txt / pip freeze

  第3课 - 虚拟环境
    python -m venv .venv / activate / deactivate

  第4课 - 镜像加速
    pip config set global.index-url 清华源地址

  第5课 - 环境检查（本文件）

日常工作中最常用的命令：
  pip install 包名            # 安装
  pip install -r requirements.txt  # 按清单安装
  pip list                    # 查看已安装
  pip freeze > requirements.txt    # 导出依赖
""")
