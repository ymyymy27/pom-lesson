# 第4课：国内镜像源加速 & 常见问题排查

## 1. 为什么 pip install 很慢？

pip 默认从 **PyPI**（https://pypi.org）下载包，服务器在国外。
在国内下载速度可能很慢（几KB/s），甚至超时失败。

解决办法：使用**国内镜像源** —— 国内大学和公司把 PyPI 的内容复制（镜像）了一份，
从国内服务器下载，速度快几十倍。

---

## 2. 常用国内镜像源

| 镜像源 | 地址 | 推荐度 |
|--------|------|--------|
| 清华大学 | https://pypi.tuna.tsinghua.edu.cn/simple | 最推荐 |
| 阿里云 | https://mirrors.aliyun.com/pypi/simple | 推荐 |
| 中科大 | https://pypi.mirrors.ustc.edu.cn/simple | 推荐 |
| 豆瓣 | https://pypi.douban.com/simple | 可用 |
| 华为云 | https://repo.huaweicloud.com/repository/pypi/simple | 可用 |

---

## 3. 临时使用镜像源（一次性）

在 `pip install` 后面加 `-i 镜像地址`：

```
pip install numpy -i https://pypi.tuna.tsinghua.edu.cn/simple
```

只对这一次安装生效，下次还是默认源。

多个包也可以：
```
pip install numpy matplotlib torch -i https://pypi.tuna.tsinghua.edu.cn/simple
```

从 requirements.txt 安装时：
```
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 4. 永久设置镜像源（推荐！）

设置一次，以后所有 pip 命令自动走镜像：

### 方法1：命令行设置（最简单）

```
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

执行后会提示配置文件保存位置，之后所有 `pip install` 自动走清华源。

### 方法2：手动创建配置文件

Windows 下配置文件位置：`C:\Users\你的用户名\pip\pip.ini`

创建文件 `pip.ini`，写入：
```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

### 验证设置是否生效

```
pip config list
```

应该看到：
```
global.index-url='https://pypi.tuna.tsinghua.edu.cn/simple'
```

### 恢复默认源

```
pip config unset global.index-url
```

---

## 5. 常见错误与解决方法

### 错误1：网络超时

```
ERROR: Could not fetch URL https://pypi.org/simple/numpy/
Connection timed out
```

**原因：** 网络不好，连不上 PyPI

**解决：**
- 换镜像源：`pip install numpy -i https://pypi.tuna.tsinghua.edu.cn/simple`
- 增加超时时间：`pip install numpy --timeout 120`
- 检查网络/VPN

---

### 错误2：权限不足

```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**原因：** 没有写入权限

**解决：**
- 推荐：使用虚拟环境（第3课），就不会有权限问题
- 或者加 `--user` 安装到用户目录：`pip install numpy --user`
- Windows 下以管理员身份运行终端（不太推荐）

---

### 错误3：版本冲突

```
ERROR: package-a 1.0 requires numpy>=2.0, but you have numpy 1.24
```

**原因：** 两个包需要的 numpy 版本不兼容

**解决：**
- 查看冲突详情：`pip check`
- 尝试升级/降级相关包
- 最终方案：为不同项目使用不同的虚拟环境

---

### 错误4：找不到包

```
ERROR: Could not find a version that satisfies the requirement numpyy
```

**原因：** 包名拼错了

**解决：**
- 检查拼写！（`numpyy` -> `numpy`）
- 去 https://pypi.org 搜索正确的包名
- 注意有些包的安装名和导入名不一样：

| 安装名（pip install） | 导入名（import） |
|----------------------|------------------|
| `pip install Pillow` | `import PIL` |
| `pip install scikit-learn` | `import sklearn` |
| `pip install opencv-python` | `import cv2` |
| `pip install pytorch`（错误！） | - |
| `pip install torch`（正确） | `import torch` |

---

### 错误5：pip 版本太旧

```
WARNING: You are using pip version 21.0; however, version 24.0 is available.
```

**解决：**
```
python -m pip install --upgrade pip
```

---

### 错误6：Microsoft Visual C++ 编译错误

```
error: Microsoft Visual C++ 14.0 or greater is required.
```

**原因：** 某些包需要编译 C 代码，但你没有装编译工具

**解决：**
- 安装 Visual Studio Build Tools：
  https://visualstudio.microsoft.com/visual-cpp-build-tools/
- 或者尝试安装预编译版本：`pip install 包名 --prefer-binary`

---

## 6. 实用 pip 命令速查

```
# 检查环境中的包冲突
pip check

# 查看一个包的所有可用版本
pip install numpy==999         # 故意写错版本，会列出所有可用版本

# 下载包但不安装（离线安装用）
pip download numpy -d ./packages

# 从本地文件安装
pip install ./packages/numpy-1.24.3-xxx.whl

# 查看 pip 的所有配置
pip config list

# 查看 pip 缓存
pip cache info

# 清除 pip 缓存（释放磁盘空间）
pip cache purge

# 安装时不使用缓存
pip install numpy --no-cache-dir

# 安装时显示详细信息（调试用）
pip install numpy -v
```

---

## 7. 动手练习

```
# 1. 设置清华镜像源（永久）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 验证设置
pip config list

# 3. 检查当前环境有没有包冲突
pip check

# 4. 试试安装一个小包（看看速度是不是快了）
pip install requests

# 5. 查看 requests 的信息
pip show requests

# 6. 如果不需要，卸载它
pip uninstall requests -y
```

---

## 8. 小结

| 场景 | 解决方案 |
|------|---------|
| 下载慢 | 换国内镜像源 |
| 临时换源 | `pip install 包 -i 镜像地址` |
| 永久换源 | `pip config set global.index-url 镜像地址` |
| 网络超时 | 换源 / `--timeout 120` |
| 权限不足 | 用虚拟环境 / `--user` |
| 版本冲突 | `pip check` 查看 / 用虚拟环境隔离 |
| 包名不对 | 去 pypi.org 搜索正确名称 |
| pip 太旧 | `python -m pip install --upgrade pip` |

---

**下一课：** `05_practice.py` - 实战演练脚本
