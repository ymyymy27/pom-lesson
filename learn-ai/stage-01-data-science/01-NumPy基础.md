# NumPy 基础

## 学习目标

- 理解 NumPy 数组（ndarray）的核心概念
- 掌握数组创建、索引、切片操作
- 学会广播机制和向量化运算
- 能用 NumPy 高效处理数值计算

## 1. NumPy 简介

NumPy（Numerical Python）是 Python 数据科学的基石。它提供高性能的多维数组对象和大量数学函数。

```bash
pip install numpy
```

## 2. 数组创建

```python
import numpy as np

# 从列表创建
a = np.array([1, 2, 3, 4, 5])
b = np.array([[1, 2, 3], [4, 5, 6]])

# 常用创建函数
zeros = np.zeros((3, 4))          # 全零数组
ones = np.ones((2, 3))            # 全一数组
empty = np.empty((2, 2))          # 未初始化数组
arange = np.arange(0, 10, 2)     # [0, 2, 4, 6, 8]
linspace = np.linspace(0, 1, 5)  # 等间距 5 个点
eye = np.eye(3)                   # 3x3 单位矩阵
rand = np.random.rand(3, 3)      # 随机数组

# 查看属性
print(a.shape)    # (5,)
print(b.shape)    # (2, 3)
print(b.ndim)     # 2
print(b.dtype)    # int64
print(b.size)     # 6
```

## 3. 数组索引与切片

```python
a = np.array([10, 20, 30, 40, 50])

# 基本索引
print(a[0])      # 10
print(a[-1])     # 50

# 切片
print(a[1:4])    # [20, 30, 40]
print(a[::2])    # [10, 30, 50]

# 多维索引
b = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
print(b[0, 1])     # 2
print(b[1:, :2])   # [[4, 5], [7, 8]]

# 布尔索引
mask = a > 25
print(a[mask])     # [30, 40, 50]

# 花式索引
idx = [0, 2, 4]
print(a[idx])      # [10, 30, 50]
```

## 4. 数组运算（向量化）

```python
a = np.array([1, 2, 3, 4])
b = np.array([10, 20, 30, 40])

# 逐元素运算（无需 for 循环）
print(a + b)       # [11, 22, 33, 44]
print(a * b)       # [10, 40, 90, 160]
print(a ** 2)      # [1, 4, 9, 16]
print(np.sqrt(a))  # [1.0, 1.414, 1.732, 2.0]

# 比较运算
print(a > 2)       # [False, False, True, True]

# 聚合函数
print(a.sum())     # 10
print(a.mean())    # 2.5
print(a.std())     # 1.118
print(a.max())     # 4
print(a.argmax())  # 3（最大值的索引）
```

## 5. 广播机制（Broadcasting）

当两个形状不同的数组进行运算时，NumPy 会自动扩展较小的数组。

```python
# 标量广播
a = np.array([[1, 2, 3], [4, 5, 6]])
print(a * 10)
# [[10, 20, 30],
#  [40, 50, 60]]

# 向量广播
row = np.array([1, 0, 1])
print(a + row)
# [[2, 2, 4],
#  [5, 5, 7]]

# 广播规则：
# 1. 如果数组维度不同，在较小数组的形状前面补 1
# 2. 如果某个维度大小为 1，沿该维度扩展
# 3. 如果某个维度大小不兼容且都不为 1，报错
```

## 6. 形状操作

```python
a = np.arange(12)

# reshape - 改变形状
b = a.reshape(3, 4)
c = a.reshape(2, -1)    # -1 自动计算

# flatten / ravel - 展平
flat = b.flatten()       # 返回副本
rav = b.ravel()          # 返回视图

# 转置
print(b.T)
print(b.transpose())

# 堆叠
x = np.array([1, 2, 3])
y = np.array([4, 5, 6])
print(np.vstack([x, y]))   # 垂直堆叠 (2, 3)
print(np.hstack([x, y]))   # 水平堆叠 (6,)
print(np.column_stack([x, y]))  # 列堆叠 (3, 2)
```

## 7. 线性代数

```python
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

# 矩阵乘法
print(A @ B)              # 或 np.dot(A, B)
print(np.matmul(A, B))

# 常用线代操作
print(np.linalg.det(A))        # 行列式
print(np.linalg.inv(A))        # 逆矩阵
eigenvalues, eigenvectors = np.linalg.eig(A)  # 特征值/向量
print(np.linalg.norm(A))       # 范数
```

## 8. 性能对比：NumPy vs 纯 Python

```python
import time

size = 1_000_000

# 纯 Python
a_list = list(range(size))
b_list = list(range(size))
start = time.time()
c_list = [a + b for a, b in zip(a_list, b_list)]
print(f"Python: {time.time() - start:.4f}s")

# NumPy
a_np = np.arange(size)
b_np = np.arange(size)
start = time.time()
c_np = a_np + b_np
print(f"NumPy:  {time.time() - start:.4f}s")

# NumPy 通常快 50-100 倍
```

## 练习

1. 创建一个 5x5 的随机矩阵，找出每行的最大值
2. 生成两个 3x3 矩阵，计算矩阵乘积和逐元素乘积
3. 创建一个 100 个元素的数组，将所有大于均值的元素替换为 1，其余为 0
4. 用 NumPy 实现两个向量的余弦相似度计算

## 下一节

→ [02-Pandas数据处理](02-Pandas数据处理.md)
