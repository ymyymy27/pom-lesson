> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# PyTorch 基础

## 学习目标

- 理解深度学习的基本概念（神经网络、反向传播）
- 掌握 PyTorch 张量操作和自动求导
- 构建第一个神经网络

## 1. 深度学习简介

深度学习是机器学习的子集，使用多层神经网络从数据中自动学习特征表示。

```
传统 ML：手动特征工程 → 模型
深度学习：原始数据 → 神经网络自动提取特征 → 输出
```

### 为什么选择 PyTorch

- Pythonic 的 API 设计，易于调试
- 动态计算图，灵活性高
- 学术界和工业界广泛使用
- HuggingFace 生态核心框架

```bash
pip install torch torchvision torchaudio
```

## 2. 张量（Tensor）

PyTorch 的核心数据结构，类似 NumPy 数组但支持 GPU 加速。

```python
import torch

# 创建张量
a = torch.tensor([1, 2, 3])
b = torch.zeros(3, 4)
c = torch.ones(2, 3)
d = torch.randn(3, 3)          # 标准正态分布
e = torch.arange(0, 10, 2)

# 属性
print(a.shape)     # torch.Size([3])
print(a.dtype)     # torch.int64
print(a.device)    # cpu

# NumPy 互转
import numpy as np
np_array = a.numpy()
tensor = torch.from_numpy(np.array([1, 2, 3]))

# GPU 操作
if torch.cuda.is_available():
    x = torch.randn(3, 3).cuda()    # 移到 GPU
    x = torch.randn(3, 3).to('cuda')
    x_cpu = x.cpu()                   # 移回 CPU
```

## 3. 张量运算

```python
a = torch.tensor([[1., 2.], [3., 4.]])
b = torch.tensor([[5., 6.], [7., 8.]])

# 逐元素运算
print(a + b)
print(a * b)

# 矩阵乘法
print(a @ b)           # 或 torch.matmul(a, b)
print(torch.mm(a, b))

# 形状操作
x = torch.arange(12)
x = x.reshape(3, 4)     # 或 x.view(3, 4)
x = x.unsqueeze(0)      # 增加维度 (1, 3, 4)
x = x.squeeze(0)        # 移除维度 (3, 4)
x = x.permute(1, 0)     # 转置/维度重排

# 聚合
print(a.sum())
print(a.mean())
print(a.max())
print(a.argmax())
```

## 4. 自动求导（Autograd）

PyTorch 的核心机制，自动计算梯度。

```python
# 标记需要计算梯度的张量
x = torch.tensor(3.0, requires_grad=True)
y = x ** 2 + 2 * x + 1    # y = x² + 2x + 1

# 反向传播计算梯度
y.backward()
print(x.grad)    # dy/dx = 2x + 2 = 8.0

# 多变量
w = torch.tensor([1.0, 2.0], requires_grad=True)
x = torch.tensor([3.0, 4.0])
y = (w * x).sum()      # y = w1*x1 + w2*x2
y.backward()
print(w.grad)           # [3.0, 4.0]

# 训练循环中需要手动清零梯度
w.grad.zero_()
```

## 5. 构建神经网络（nn.Module）

```python
import torch.nn as nn

class SimpleNet(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.layer1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.layer2 = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        x = self.layer1(x)
        x = self.relu(x)
        x = self.layer2(x)
        return x

# 实例化
model = SimpleNet(input_dim=4, hidden_dim=16, output_dim=3)
print(model)

# 查看参数
for name, param in model.named_parameters():
    print(f"{name}: {param.shape}")
```

## 6. 训练循环

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset

# 准备数据
iris = load_iris()
X = torch.FloatTensor(iris.data)
y = torch.LongTensor(iris.target)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

train_dataset = TensorDataset(X_train, y_train)
train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)

# 模型、损失函数、优化器
model = SimpleNet(4, 32, 3)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

# 训练
num_epochs = 100
for epoch in range(num_epochs):
    model.train()
    total_loss = 0

    for batch_X, batch_y in train_loader:
        # 前向传播
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)

        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    if (epoch + 1) % 20 == 0:
        print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {total_loss/len(train_loader):.4f}")

# 评估
model.eval()
with torch.no_grad():
    outputs = model(X_test)
    _, predicted = torch.max(outputs, 1)
    accuracy = (predicted == y_test).float().mean()
    print(f"Test Accuracy: {accuracy:.4f}")
```

## 7. 常用组件速查

| 组件 | 用途 |
|------|------|
| `nn.Linear` | 全连接层 |
| `nn.Conv2d` | 2D 卷积 |
| `nn.LSTM` | 长短期记忆网络 |
| `nn.ReLU` | 激活函数 |
| `nn.Dropout` | 正则化 |
| `nn.BatchNorm1d` | 批归一化 |
| `nn.CrossEntropyLoss` | 分类损失 |
| `nn.MSELoss` | 回归损失 |
| `torch.optim.Adam` | Adam 优化器 |
| `torch.optim.SGD` | 随机梯度下降 |

## 练习

1. 用 PyTorch 实现线性回归（对比 Scikit-learn 实现）
2. 修改 SimpleNet 的层数和隐藏维度，观察效果
3. 在 MNIST 数据集上实现手写数字分类
4. 绘制训练过程中的 loss 曲线

## 下一节

→ [02-CNN与图像分类](<02-CNN 与图像分类.md>)
