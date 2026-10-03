import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第1课：PyTorch 张量 (Tensor) 基础
==============================================================================

什么是张量？
-----------
张量是 PyTorch 中最基本的数据结构，可以理解为：
- 0维张量 = 一个数字（标量）        例如: 3.14
- 1维张量 = 一组数字（向量）        例如: [1, 2, 3]
- 2维张量 = 一个表格（矩阵）        例如: [[1,2], [3,4]]
- 3维张量 = 多个表格堆叠            例如: 一张彩色图片(高x宽x3个颜色通道)
- 更高维 = 以此类推...              例如: 一批图片(批量x高x宽x通道)

张量和 NumPy 的数组很像，但张量可以在 GPU 上运算，还支持自动求导。
==============================================================================
"""

import torch
import numpy as np

print("=" * 60)
print("第1课：PyTorch 张量 (Tensor) 基础")
print("=" * 60)

# ============================================================================
# 1. 创建张量的各种方式
# ============================================================================
print("\n--- 1. 创建张量 ---")

# 1.1 从 Python 列表创建
a = torch.tensor([1, 2, 3])
print(f"从列表创建:        {a}")
print(f"  形状(shape):     {a.shape}")       # torch.Size([3]) 表示1维，3个元素
print(f"  数据类型(dtype):  {a.dtype}")       # int64，因为输入是整数

# 1.2 从列表创建浮点数张量（深度学习中最常用的类型）
b = torch.tensor([1.0, 2.0, 3.0])
print(f"\n浮点数张量:         {b}")
print(f"  数据类型:         {b.dtype}")       # float32

# 1.3 创建2维张量（矩阵）
c = torch.tensor([[1, 2, 3],
                   [4, 5, 6]])
print(f"\n2维张量:\n{c}")
print(f"  形状: {c.shape}")                   # torch.Size([2, 3]) 表示2行3列

# 1.4 常用的快捷创建方式
zeros = torch.zeros(2, 3)          # 全0张量，2行3列
ones = torch.ones(2, 3)            # 全1张量
rand = torch.rand(2, 3)            # 随机张量(0~1之间的均匀分布)
randn = torch.randn(2, 3)          # 随机张量(标准正态分布，均值0方差1)
arange = torch.arange(0, 10, 2)    # 等差数列 [0, 2, 4, 6, 8]
eye = torch.eye(3)                 # 单位矩阵

print(f"\n全0张量:\n{zeros}")
print(f"\n全1张量:\n{ones}")
print(f"\n随机张量(0~1):\n{rand}")
print(f"\n等差数列: {arange}")
print(f"\n单位矩阵:\n{eye}")

# 1.5 创建与已有张量形状相同的张量
same_shape_zeros = torch.zeros_like(c)   # 与c形状相同的全0张量
same_shape_rand = torch.rand_like(c.float())  # 需要先转为float
print(f"\n与c形状相同的全0张量:\n{same_shape_zeros}")

# ============================================================================
# 2. 张量的基本属性
# ============================================================================
print("\n--- 2. 张量的基本属性 ---")

x = torch.randn(3, 4, 5)  # 创建一个3x4x5的随机张量
print(f"张量 x 的属性：")
print(f"  形状 (shape):    {x.shape}")          # torch.Size([3, 4, 5])
print(f"  维度数 (ndim):   {x.ndim}")           # 3
print(f"  总元素数:         {x.numel()}")        # 3*4*5 = 60
print(f"  数据类型 (dtype): {x.dtype}")          # float32
print(f"  所在设备:         {x.device}")          # cpu (如果有GPU可能是cuda:0)

# ============================================================================
# 3. 张量的数学运算
# ============================================================================
print("\n--- 3. 张量的数学运算 ---")

a = torch.tensor([1.0, 2.0, 3.0])
b = torch.tensor([4.0, 5.0, 6.0])

# 3.1 基本四则运算（逐元素操作）
print(f"a = {a}")
print(f"b = {b}")
print(f"a + b = {a + b}")          # [5, 7, 9]
print(f"a - b = {a - b}")          # [-3, -3, -3]
print(f"a * b = {a * b}")          # [4, 10, 18]  注意：这是逐元素乘法！
print(f"a / b = {a / b}")          # [0.25, 0.4, 0.5]
print(f"a ** 2 = {a ** 2}")        # [1, 4, 9]  幂运算

# 3.2 常用数学函数
print(f"\nsqrt(a) = {torch.sqrt(a)}")      # 开平方
print(f"exp(a)  = {torch.exp(a)}")         # e的幂次
print(f"log(a)  = {torch.log(a)}")         # 自然对数
print(f"abs(-a) = {torch.abs(-a)}")        # 绝对值

# 3.3 聚合运算
print(f"\nsum(a)  = {a.sum()}")             # 求和: 6
print(f"mean(a) = {a.mean()}")             # 平均值: 2
print(f"max(a)  = {a.max()}")              # 最大值: 3
print(f"min(a)  = {a.min()}")              # 最小值: 1
print(f"argmax  = {a.argmax()}")           # 最大值的索引: 2

# 3.4 矩阵乘法（深度学习中非常重要！）
# 矩阵乘法 vs 逐元素乘法
m1 = torch.tensor([[1.0, 2.0],
                    [3.0, 4.0]])     # 2x2 矩阵
m2 = torch.tensor([[5.0, 6.0],
                    [7.0, 8.0]])     # 2x2 矩阵

print(f"\n矩阵 m1:\n{m1}")
print(f"矩阵 m2:\n{m2}")
print(f"逐元素乘法 m1 * m2:\n{m1 * m2}")       # 对应位置相乘
print(f"矩阵乘法 m1 @ m2:\n{m1 @ m2}")         # 真正的矩阵乘法
# 矩阵乘法也可以用 torch.matmul(m1, m2) 或 m1.mm(m2)

# ============================================================================
# 4. 张量的索引和切片
# ============================================================================
print("\n--- 4. 张量的索引和切片 ---")

t = torch.tensor([[1, 2, 3, 4],
                   [5, 6, 7, 8],
                   [9, 10, 11, 12]])
print(f"原始张量:\n{t}")

# 4.1 基本索引（和Python列表一样）
print(f"\n第0行:          {t[0]}")           # [1, 2, 3, 4]
print(f"第1行第2列:      {t[1, 2]}")         # 7
print(f"最后一行:        {t[-1]}")           # [9, 10, 11, 12]

# 4.2 切片
print(f"\n前两行:\n{t[:2]}")                  # 第0、1行
print(f"所有行的第1列:   {t[:, 1]}")          # [2, 6, 10]
print(f"第0-1行，第1-2列:\n{t[:2, 1:3]}")     # [[2,3], [6,7]]

# 4.3 条件索引
print(f"\n大于5的元素:     {t[t > 5]}")        # [6, 7, 8, 9, 10, 11, 12]

# ============================================================================
# 5. 张量形状变换（非常常用！）
# ============================================================================
print("\n--- 5. 张量形状变换 ---")

x = torch.arange(12)  # [0, 1, 2, ..., 11]
print(f"原始张量: {x}  形状: {x.shape}")

# 5.1 reshape - 改变形状
x_3x4 = x.reshape(3, 4)       # 变成3行4列
print(f"\nreshape(3, 4):\n{x_3x4}")

x_2x6 = x.reshape(2, 6)       # 变成2行6列
print(f"\nreshape(2, 6):\n{x_2x6}")

# 用 -1 让PyTorch自动计算某个维度的大小
x_auto = x.reshape(3, -1)     # 3行，列数自动算出=4
print(f"\nreshape(3, -1):\n{x_auto}")

# 5.2 view - 和reshape类似（要求内存连续）
x_view = x.view(4, 3)
print(f"\nview(4, 3):\n{x_view}")

# 5.3 unsqueeze / squeeze - 增加/删除维度
x = torch.tensor([1, 2, 3])   # 形状: [3]
print(f"\n原始: {x}, 形状: {x.shape}")

x_unsq = x.unsqueeze(0)       # 在第0维增加一个维度
print(f"unsqueeze(0): {x_unsq}, 形状: {x_unsq.shape}")  # [1, 3]

x_unsq2 = x.unsqueeze(1)      # 在第1维增加一个维度
print(f"unsqueeze(1):\n{x_unsq2}, 形状: {x_unsq2.shape}")  # [3, 1]

x_sq = x_unsq.squeeze(0)      # 删除第0维（如果该维度大小为1）
print(f"squeeze(0): {x_sq}, 形状: {x_sq.shape}")  # 回到 [3]

# 5.4 转置
m = torch.tensor([[1, 2, 3],
                   [4, 5, 6]])     # 2x3
print(f"\n原始矩阵 (2x3):\n{m}")
print(f"转置后 (3x2):\n{m.T}")     # 或 m.t() 或 m.transpose(0, 1)

# ============================================================================
# 6. 张量与 NumPy 互转
# ============================================================================
print("\n--- 6. 张量与 NumPy 互转 ---")

# PyTorch张量 → NumPy数组
tensor = torch.tensor([1.0, 2.0, 3.0])
numpy_arr = tensor.numpy()
print(f"张量: {tensor}")
print(f"转NumPy: {numpy_arr}  类型: {type(numpy_arr)}")

# NumPy数组 → PyTorch张量
np_arr = np.array([4.0, 5.0, 6.0])
tensor_from_np = torch.from_numpy(np_arr)
print(f"\nNumPy: {np_arr}")
print(f"转张量: {tensor_from_np}  类型: {type(tensor_from_np)}")

# [注意] 共享内存！修改一个会影响另一个
tensor_shared = torch.tensor([1.0, 2.0, 3.0])
np_shared = tensor_shared.numpy()
tensor_shared[0] = 999
print(f"\n[注意] 共享内存演示：")
print(f"修改张量后，NumPy也变了: {np_shared}")  # [999, 2, 3]

# 如果不想共享，用 .clone()
tensor_clone = torch.tensor([1.0, 2.0, 3.0])
np_copy = tensor_clone.clone().numpy()
tensor_clone[0] = 999
print(f"使用clone()后互不影响: {np_copy}")  # [1, 2, 3] 不变

# ============================================================================
# 7. 数据类型转换
# ============================================================================
print("\n--- 7. 数据类型转换 ---")

x_int = torch.tensor([1, 2, 3])        # 默认int64
x_float = x_int.float()                 # 转为float32
x_double = x_int.double()               # 转为float64
x_long = x_float.long()                 # 转为int64

print(f"int64:   {x_int.dtype}")
print(f"float32: {x_float.dtype}")
print(f"float64: {x_double.dtype}")
print(f"回到int: {x_long.dtype}")

# 也可以用 .to() 方法
x_to = x_int.to(torch.float32)
print(f".to()转换: {x_to.dtype}")

print("\n" + "=" * 60)
print("[完成] 第1课完成！你已经学会了：")
print("  [v] 创建张量的多种方式")
print("  [v] 张量的基本属性")
print("  [v] 数学运算（逐元素运算 & 矩阵乘法）")
print("  [v] 索引和切片")
print("  [v] 形状变换（reshape, view, unsqueeze, squeeze）")
print("  [v] 与 NumPy 互转")
print("  [v] 数据类型转换")
print("=" * 60)
print("\n下一课：02_autograd.py - 自动求导机制")
