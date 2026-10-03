import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：自动求导 (Autograd) 机制
==============================================================================

为什么需要自动求导？
------------------
深度学习的核心是"梯度下降"优化算法：
1. 给模型一些数据，模型做出预测
2. 计算预测结果与正确答案的差距（损失/loss）
3. 计算损失对每个参数的导数（梯度）  ← 这一步就是自动求导！
4. 沿着梯度的反方向调整参数，使损失减小
5. 重复以上步骤

手动计算梯度非常复杂且容易出错。
PyTorch 的 autograd 可以自动完成这个过程！

什么是导数/梯度？（简单理解）
---------------------------
- 导数 = 函数的变化率
- 比如 y = x²，导数 dy/dx = 2x
- 当 x=3 时，导数 = 6，意思是"x增加一点点，y会增加约6倍"
- 梯度就是多变量情况下的导数
==============================================================================
"""

import torch

print("=" * 60)
print("第2课：自动求导 (Autograd) 机制")
print("=" * 60)

# ============================================================================
# 1. 基本概念：requires_grad
# ============================================================================
print("\n--- 1. 基本概念：requires_grad ---")

# 创建一个需要计算梯度的张量
# requires_grad=True 告诉PyTorch："请记录对这个张量的所有操作，以便之后求导"
x = torch.tensor([2.0, 3.0], requires_grad=True)
print(f"x = {x}")
print(f"x.requires_grad = {x.requires_grad}")  # True

# 普通张量默认不需要梯度
y = torch.tensor([4.0, 5.0])
print(f"\ny = {y}")
print(f"y.requires_grad = {y.requires_grad}")  # False

# ============================================================================
# 2. 简单的自动求导示例
# ============================================================================
print("\n--- 2. 简单的自动求导示例 ---")

# 例子：y = x² + 3
# 数学上，dy/dx = 2x
# 当 x=2 时，dy/dx = 4；当 x=3 时，dy/dx = 6

x = torch.tensor([2.0, 3.0], requires_grad=True)

# 前向计算
y = x ** 2 + 3       # y = [4+3, 9+3] = [7, 12]
print(f"x = {x}")
print(f"y = x² + 3 = {y}")

# 为了调用 backward()，我们需要一个标量（单个数字）
# 所以先对 y 求和
z = y.sum()           # z = 7 + 12 = 19
print(f"z = sum(y) = {z}")

# 反向传播：计算 z 对 x 的梯度
z.backward()

# 查看梯度
# dz/dx = d(x² + 3)/dx = 2x
# 当 x=[2, 3] 时，梯度 = [4, 6]
print(f"\n梯度 dz/dx = 2x = {x.grad}")  # tensor([4., 6.])
print("验证：x=2时梯度=2*2=4 ✓，x=3时梯度=2*3=6 ✓")

# ============================================================================
# 3. 计算图的概念
# ============================================================================
print("\n--- 3. 计算图的概念 ---")
print("""
PyTorch 在执行运算时，会在幕后构建一个"计算图"：

    x (叶子节点, requires_grad=True)
    |
    ↓  x²
    |
    ↓  +3
    |
    y
    |
    ↓  sum()
    |
    z (输出)

调用 z.backward() 时，PyTorch 会沿着这个图"反向"走一遍，
利用链式法则自动计算出 z 对 x 的梯度。
""")

# grad_fn 属性告诉我们这个张量是由什么操作产生的
x = torch.tensor([1.0], requires_grad=True)
y = x * 2
z = y + 3
print(f"x.grad_fn = {x.grad_fn}")      # None（叶子节点没有grad_fn）
print(f"y.grad_fn = {y.grad_fn}")      # MulBackward0（乘法操作）
print(f"z.grad_fn = {z.grad_fn}")      # AddBackward0（加法操作）

# ============================================================================
# 4. 更复杂的例子
# ============================================================================
print("\n--- 4. 更复杂的例子 ---")

# 模拟一个简单的线性模型：y_pred = w * x + b
# w 和 b 是我们要学习的参数

# 参数（需要梯度）
w = torch.tensor([1.0], requires_grad=True)  # 权重
b = torch.tensor([0.0], requires_grad=True)  # 偏置

# 数据（不需要梯度）
x = torch.tensor([2.0])    # 输入
y_true = torch.tensor([5.0])  # 真实标签（正确答案）

# 前向传播
y_pred = w * x + b          # 预测值 = 1*2 + 0 = 2
print(f"预测值: {y_pred.item():.2f}")
print(f"真实值: {y_true.item():.2f}")

# 计算损失（预测值与真实值的差距）
loss = (y_pred - y_true) ** 2   # 均方误差 = (2-5)² = 9
print(f"损失: {loss.item():.2f}")

# 反向传播
loss.backward()

# 查看梯度
print(f"\nw的梯度: {w.grad}")     # d(loss)/dw
print(f"b的梯度: {b.grad}")     # d(loss)/db
print("""
解释：
  loss = (w*x + b - y_true)²
  d(loss)/dw = 2*(w*x + b - y_true) * x = 2*(2-5)*2 = -12
  d(loss)/db = 2*(w*x + b - y_true) * 1 = 2*(2-5)*1 = -6
  
  w的梯度=-12，意味着w应该增大（梯度为负，反方向增大）
  这是合理的！因为当前 w*x=2 太小了，需要增大 w。
""")

# ============================================================================
# 5. 手动实现梯度下降（理解训练过程）
# ============================================================================
print("--- 5. 手动实现梯度下降 ---")

# 目标：学习 y = 3x + 1 这条直线
# 也就是要让模型自己发现 w=3, b=1

# 初始化参数（随机值）
w = torch.tensor([0.0], requires_grad=True)
b = torch.tensor([0.0], requires_grad=True)

# 训练数据
x_data = torch.tensor([1.0, 2.0, 3.0, 4.0])
y_data = torch.tensor([4.0, 7.0, 10.0, 13.0])  # y = 3x + 1

learning_rate = 0.01  # 学习率：每次调整参数的步长

print(f"目标: y = 3x + 1")
print(f"初始参数: w={w.item():.4f}, b={b.item():.4f}")
print()

for epoch in range(100):
    # 前向传播：用当前参数做预测
    y_pred = w * x_data + b
    
    # 计算损失（所有样本的平均损失）
    loss = ((y_pred - y_data) ** 2).mean()
    
    # 反向传播：计算梯度
    loss.backward()
    
    # 更新参数（梯度下降）
    # [重要] 更新参数时不能让PyTorch记录这个操作
    with torch.no_grad():
        w -= learning_rate * w.grad
        b -= learning_rate * b.grad
    
    # [重要] 每次迭代后必须清零梯度！
    # 否则梯度会累积（PyTorch默认累加梯度）
    w.grad.zero_()
    b.grad.zero_()
    
    # 每20轮打印一次
    if (epoch + 1) % 20 == 0:
        print(f"Epoch {epoch+1:3d}: loss={loss.item():.4f}, "
              f"w={w.item():.4f}, b={b.item():.4f}")

print(f"\n最终结果: w={w.item():.4f}, b={b.item():.4f}")
print(f"目标值:   w=3.0000, b=1.0000")
print("（已经非常接近了！训练更多轮次会更精确）")

# ============================================================================
# 6. 重要注意事项
# ============================================================================
print("\n--- 6. 重要注意事项 ---")

# 6.1 梯度会累积，必须手动清零
print("注意1: 梯度会累积")
x = torch.tensor([2.0], requires_grad=True)

y = (x ** 2).sum()
y.backward()
print(f"  第1次 backward: x.grad = {x.grad}")   # 4

y = (x ** 2).sum()
y.backward()
print(f"  第2次 backward: x.grad = {x.grad}")   # 8！梯度累积了

x.grad.zero_()   # 清零
print(f"  清零后:          x.grad = {x.grad}")   # 0

# 6.2 detach() - 从计算图分离
print("\n注意2: detach() 分离计算图")
x = torch.tensor([1.0], requires_grad=True)
y = x * 2
y_detached = y.detach()  # y_detached 不再追踪梯度
print(f"  y.requires_grad = {y.requires_grad}")            # True
print(f"  y_detached.requires_grad = {y_detached.requires_grad}")  # False

# 6.3 torch.no_grad() - 暂时关闭梯度追踪
print("\n注意3: torch.no_grad() 上下文")
x = torch.tensor([1.0], requires_grad=True)
with torch.no_grad():
    y = x * 2
    print(f"  no_grad内: y.requires_grad = {y.requires_grad}")  # False
# 在评估模型（不需要训练）时，用 torch.no_grad() 可以节省内存

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] requires_grad 追踪梯度")
print("  [v] backward() 反向传播计算梯度")
print("  [v] 计算图的概念")
print("  [v] 手动实现梯度下降训练")
print("  [v] 梯度清零、detach、no_grad 等重要技巧")
print("=" * 60)
print("\n下一课：03_neural_network.py - 构建神经网络")
