import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第3课：构建神经网络 (nn.Module)
==============================================================================

什么是神经网络？
--------------
神经网络是一种模仿人脑的计算模型，由多层"神经元"组成：

输入层 → 隐藏层1 → 隐藏层2 → ... → 输出层

每一层做的事情：
  输出 = 激活函数(权重 × 输入 + 偏置)

PyTorch 提供了 torch.nn 模块来方便地构建神经网络，
不需要手动管理每一个权重和偏置。

关键概念：
- nn.Module：所有神经网络的基类
- nn.Linear：全连接层（最基本的层）
- 激活函数：给网络加入非线性（没有它，多层网络等于单层）
- 损失函数：衡量预测结果和真实值的差距
- 优化器：自动更新参数的工具
==============================================================================
"""

import torch
import torch.nn as nn         # 神经网络模块
import torch.optim as optim   # 优化器模块

print("=" * 60)
print("第3课：构建神经网络 (nn.Module)")
print("=" * 60)

# ============================================================================
# 1. nn.Linear - 全连接层（最基础的网络层）
# ============================================================================
print("\n--- 1. nn.Linear - 全连接层 ---")
print("""
全连接层做的事情很简单：y = x × W^T + b
- x: 输入，形状 [batch_size, in_features]
- W: 权重矩阵，形状 [out_features, in_features]  
- b: 偏置，形状 [out_features]
- y: 输出，形状 [batch_size, out_features]
""")

# 创建一个全连接层：输入3个特征，输出2个特征
linear = nn.Linear(in_features=3, out_features=2)

# 查看自动创建的参数
print(f"权重 W 的形状: {linear.weight.shape}")    # [2, 3]
print(f"权重 W:\n{linear.weight}")
print(f"\n偏置 b 的形状: {linear.bias.shape}")      # [2]
print(f"偏置 b: {linear.bias}")

# 使用全连接层
x = torch.tensor([[1.0, 2.0, 3.0]])   # 1个样本，3个特征
y = linear(x)                          # 等价于 x @ W^T + b
print(f"\n输入 x: {x} 形状: {x.shape}")
print(f"输出 y: {y} 形状: {y.shape}")

# 批量处理：一次传入多个样本
batch = torch.randn(5, 3)   # 5个样本，每个3个特征
output = linear(batch)
print(f"\n批量输入形状: {batch.shape}")
print(f"批量输出形状: {output.shape}")   # [5, 2]

# ============================================================================
# 2. 激活函数
# ============================================================================
print("\n--- 2. 激活函数 ---")
print("""
为什么需要激活函数？
- 没有激活函数，多层线性层叠加还是线性的（等于一层）
- 激活函数引入非线性，让网络能学习复杂的模式

常用激活函数：
- ReLU:    max(0, x)     最常用！简单高效
- Sigmoid: 1/(1+e^(-x))  输出在0~1之间，用于二分类
- Tanh:    双曲正切       输出在-1~1之间
- Softmax: 多分类输出     所有输出加起来=1（概率分布）
""")

x = torch.tensor([-2.0, -1.0, 0.0, 1.0, 2.0])
print(f"输入 x:    {x}")

# ReLU：负数变0，正数不变
relu = nn.ReLU()
print(f"ReLU(x):   {relu(x)}")        # [0, 0, 0, 1, 2]

# Sigmoid：压缩到0~1
sigmoid = nn.Sigmoid()
print(f"Sigmoid(x): {sigmoid(x)}")     # 接近[0, 0.27, 0.5, 0.73, 0.88]

# Tanh：压缩到-1~1
tanh = nn.Tanh()
print(f"Tanh(x):   {tanh(x)}")

# Softmax：转为概率分布
softmax = nn.Softmax(dim=0)
print(f"Softmax(x): {softmax(x)}")     # 所有值加起来=1
print(f"Softmax求和: {softmax(x).sum()}")  # 1.0

# ============================================================================
# 3. 用 nn.Module 构建自定义神经网络
# ============================================================================
print("\n--- 3. 用 nn.Module 构建自定义神经网络 ---")


class SimpleNet(nn.Module):
    """
    一个简单的3层神经网络：
    输入(4) → 隐藏层1(8) → 隐藏层2(8) → 输出(2)
    
    适用于：4个特征的输入，2个类别的分类任务
    """
    
    def __init__(self):
        super().__init__()  # [必须] 调用父类的__init__
        
        # 定义网络层
        self.layer1 = nn.Linear(4, 8)     # 第1层：4→8
        self.layer2 = nn.Linear(8, 8)     # 第2层：8→8
        self.layer3 = nn.Linear(8, 2)     # 第3层：8→2
        self.relu = nn.ReLU()             # 激活函数
    
    def forward(self, x):
        """
        前向传播：定义数据如何流过网络
        这个方法在调用 model(x) 时自动执行
        """
        x = self.relu(self.layer1(x))  # 第1层 + 激活
        x = self.relu(self.layer2(x))  # 第2层 + 激活
        x = self.layer3(x)             # 第3层（输出层通常不加激活）
        return x


# 创建模型
model = SimpleNet()
print(f"模型结构：\n{model}")

# 查看所有参数
print(f"\n模型参数：")
for name, param in model.named_parameters():
    print(f"  {name}: 形状={param.shape}, 需要梯度={param.requires_grad}")

# 统计参数总数
total_params = sum(p.numel() for p in model.parameters())
print(f"\n总参数量: {total_params}")

# 使用模型做预测
x = torch.randn(3, 4)     # 3个样本，4个特征
output = model(x)           # 自动调用 forward()
print(f"\n输入形状:  {x.shape}")
print(f"输出形状:  {output.shape}")    # [3, 2]
print(f"输出:\n{output}")

# ============================================================================
# 4. 用 nn.Sequential 快速构建网络（更简洁的方式）
# ============================================================================
print("\n--- 4. 用 nn.Sequential 快速构建网络 ---")

# 和上面 SimpleNet 完全等价，但写法更简洁
model_seq = nn.Sequential(
    nn.Linear(4, 8),
    nn.ReLU(),
    nn.Linear(8, 8),
    nn.ReLU(),
    nn.Linear(8, 2)
)

print(f"Sequential模型：\n{model_seq}")

output_seq = model_seq(torch.randn(3, 4))
print(f"\n输出形状: {output_seq.shape}")

# ============================================================================
# 5. 损失函数
# ============================================================================
print("\n--- 5. 损失函数 ---")
print("""
损失函数衡量预测值与真实值的差距：
- MSELoss:           均方误差，用于回归任务
- CrossEntropyLoss:  交叉熵，用于多分类任务（最常用）
- BCELoss:           二元交叉熵，用于二分类任务
""")

# 5.1 均方误差（回归）
mse_loss = nn.MSELoss()
pred = torch.tensor([2.5, 0.0, 2.1])
target = torch.tensor([3.0, -0.5, 2.0])
loss = mse_loss(pred, target)
print(f"MSE Loss: {loss.item():.4f}")
# = ((2.5-3)² + (0-(-0.5))² + (2.1-2)²) / 3 = (0.25+0.25+0.01)/3 ≈ 0.17

# 5.2 交叉熵损失（分类）
ce_loss = nn.CrossEntropyLoss()
# 模型输出：3个样本，4个类别的得分（不需要softmax，CrossEntropyLoss会自动做）
pred = torch.tensor([[2.0, 1.0, 0.1, 0.5],    # 样本1的4个类别得分
                      [0.5, 2.5, 0.3, 0.2],    # 样本2
                      [0.3, 0.2, 0.1, 3.0]])    # 样本3
target = torch.tensor([0, 1, 3])                # 真实类别索引
loss = ce_loss(pred, target)
print(f"CrossEntropy Loss: {loss.item():.4f}")

# ============================================================================
# 6. 优化器
# ============================================================================
print("\n--- 6. 优化器 ---")
print("""
优化器自动完成"梯度下降"过程：
- SGD:    随机梯度下降，最基础
- Adam:   自适应学习率，最常用，通常效果好
- AdamW:  Adam的改进版，带权重衰减
""")

# 创建一个简单模型
model = SimpleNet()

# 创建优化器，把模型的参数交给它管理
optimizer = optim.Adam(model.parameters(), lr=0.001)  # lr = learning rate
print(f"优化器: {optimizer}")

# ============================================================================
# 7. 完整的训练循环！
# ============================================================================
print("\n--- 7. 完整的训练循环 ---")

# ---- 准备工作 ----
# 创建一些假数据（4个特征 → 2个类别的分类任务）
torch.manual_seed(42)  # 固定随机种子，保证结果可复现

# 生成100个训练样本
X_train = torch.randn(100, 4)        # 100个样本，4个特征
# 简单规则：如果前两个特征之和 > 0，则类别1，否则类别0
y_train = (X_train[:, 0] + X_train[:, 1] > 0).long()

print(f"训练数据: X形状={X_train.shape}, y形状={y_train.shape}")
print(f"类别分布: 类别0={(y_train==0).sum()}, 类别1={(y_train==1).sum()}")

# ---- 创建模型、损失函数、优化器 ----
model = SimpleNet()
criterion = nn.CrossEntropyLoss()    # 分类任务用交叉熵
optimizer = optim.Adam(model.parameters(), lr=0.01)

# ---- 训练循环 ----
print(f"\n开始训练...")
for epoch in range(100):
    # [1] 前向传播：模型做预测
    y_pred = model(X_train)
    
    # [2] 计算损失
    loss = criterion(y_pred, y_train)
    
    # [3] 反向传播：计算梯度
    optimizer.zero_grad()   # 先清零梯度（必须的！）
    loss.backward()         # 计算梯度
    
    # [4] 更新参数
    optimizer.step()        # 优化器根据梯度更新参数
    
    # 打印进度
    if (epoch + 1) % 20 == 0:
        # 计算准确率
        predicted = y_pred.argmax(dim=1)   # 取概率最大的类别
        accuracy = (predicted == y_train).float().mean()
        print(f"  Epoch {epoch+1:3d}: loss={loss.item():.4f}, "
              f"accuracy={accuracy.item()*100:.1f}%")

# ---- 测试模型 ----
print(f"\n--- 测试模型 ---")
# 创建一些测试数据
X_test = torch.randn(10, 4)
y_test = (X_test[:, 0] + X_test[:, 1] > 0).long()

# 评估模式 + 不计算梯度（节省内存）
model.eval()
with torch.no_grad():
    y_pred = model(X_test)
    predicted = y_pred.argmax(dim=1)
    accuracy = (predicted == y_test).float().mean()
    
    print(f"测试数据预测结果: {predicted.tolist()}")
    print(f"测试数据真实标签: {y_test.tolist()}")
    print(f"测试准确率: {accuracy.item()*100:.1f}%")

print("\n" + "=" * 60)
print("[完成] 第3课完成！你已经学会了：")
print("  [v] nn.Linear 全连接层")
print("  [v] 常用激活函数（ReLU, Sigmoid, Softmax等）")
print("  [v] 用 nn.Module 自定义网络")
print("  [v] 用 nn.Sequential 快速搭建网络")
print("  [v] 损失函数（MSE, CrossEntropy）")
print("  [v] 优化器（SGD, Adam）")
print("  [v] 完整的训练循环（前向->损失->反向->更新）")
print("=" * 60)
print("\n下一课：04_data_loading.py - 数据加载与预处理")
