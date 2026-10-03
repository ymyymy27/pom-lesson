import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：完整项目 - 手写数字识别 (MNIST)
==============================================================================

这是一个真正的深度学习项目！
我们要训练一个神经网络来识别手写数字（0-9）。

MNIST 数据集：
- 60,000张训练图片 + 10,000张测试图片
- 每张图片是 28×28 像素的灰度图
- 标签是 0-9 的数字

项目流程：
1. 加载和预处理数据
2. 定义神经网络模型
3. 训练模型
4. 评估模型
5. 可视化结果

这一课会把前面学的所有知识串联起来！
==============================================================================
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，适合没有GUI的环境
import matplotlib.pyplot as plt
import os

print("=" * 60)
print("第5课：完整项目 - 手写数字识别 (MNIST)")
print("=" * 60)

# ============================================================================
# 1. 超参数设置
# ============================================================================
print("\n--- 1. 超参数设置 ---")

# 超参数：需要我们自己设定的参数（不是模型学习的参数）
BATCH_SIZE = 64        # 每批64张图片
LEARNING_RATE = 0.001  # 学习率
EPOCHS = 5             # 训练5个轮次（遍历整个数据集5次）
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

print(f"批次大小:   {BATCH_SIZE}")
print(f"学习率:     {LEARNING_RATE}")
print(f"训练轮次:   {EPOCHS}")
print(f"计算设备:   {DEVICE}")

# ============================================================================
# 2. 数据加载与预处理
# ============================================================================
print("\n--- 2. 数据加载与预处理 ---")

# 定义数据变换（预处理流水线）
transform = transforms.Compose([
    transforms.ToTensor(),           # 图片转张量 (0~255 → 0~1)
    transforms.Normalize((0.1307,),  # 减去均值
                         (0.3081,))  # 除以标准差
    # 这两个数字是MNIST数据集的全局均值和标准差
])

# 下载并加载训练集
print("正在加载训练数据...")
train_dataset = datasets.MNIST(
    root='./data',         # 数据存放目录
    train=True,            # 训练集
    download=True,         # 如果没有就自动下载
    transform=transform    # 应用预处理
)

# 下载并加载测试集
print("正在加载测试数据...")
test_dataset = datasets.MNIST(
    root='./data',
    train=False,           # 测试集
    download=True,
    transform=transform
)

# 创建 DataLoader
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

print(f"\n训练集: {len(train_dataset)} 张图片")
print(f"测试集: {len(test_dataset)} 张图片")
print(f"训练批次数: {len(train_loader)}")

# 看看数据长什么样
sample_data, sample_label = train_dataset[0]
print(f"\n单张图片形状: {sample_data.shape}")    # [1, 28, 28] = 1通道×28高×28宽
print(f"标签: {sample_label}")
print(f"像素值范围: [{sample_data.min():.2f}, {sample_data.max():.2f}]")

# ============================================================================
# 3. 可视化一些样本
# ============================================================================
print("\n--- 3. 可视化样本 ---")

fig, axes = plt.subplots(2, 5, figsize=(12, 5))
for i, ax in enumerate(axes.flat):
    image, label = train_dataset[i]
    ax.imshow(image.squeeze(), cmap='gray')  # squeeze去掉通道维度
    ax.set_title(f'标签: {label}', fontsize=12)
    ax.axis('off')
plt.suptitle('MNIST 手写数字样本', fontsize=14)
plt.tight_layout()
plt.savefig('mnist_samples.png', dpi=100)
print("样本图片已保存到 mnist_samples.png")

# ============================================================================
# 4. 定义神经网络模型
# ============================================================================
print("\n--- 4. 定义神经网络模型 ---")


class MNISTNet(nn.Module):
    """
    手写数字识别网络
    
    网络结构：
    输入(784) → 隐藏层1(256) → 隐藏层2(128) → 输出(10)
    
    为什么输入是784？
    - 图片是28×28=784个像素
    - 我们把2D图片"展平"成1D向量
    
    为什么输出是10？
    - 10个数字(0-9)，每个输出对应一个类别的得分
    """
    
    def __init__(self):
        super().__init__()
        
        self.network = nn.Sequential(
            # 第1层：784 → 256
            nn.Linear(28 * 28, 256),
            nn.ReLU(),
            nn.Dropout(0.2),    # 随机丢弃20%的神经元（防止过拟合）
            
            # 第2层：256 → 128
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            # 输出层：128 → 10（10个类别）
            nn.Linear(128, 10)
            # 注意：不需要加Softmax，CrossEntropyLoss会自动处理
        )
    
    def forward(self, x):
        # x 的形状: [batch_size, 1, 28, 28]
        x = x.view(x.size(0), -1)  # 展平为 [batch_size, 784]
        return self.network(x)


# 创建模型并移到设备上
model = MNISTNet().to(DEVICE)
print(f"模型结构：\n{model}")

# 统计参数量
total_params = sum(p.numel() for p in model.parameters())
print(f"\n总参数量: {total_params:,}")  # 约23万参数

# ============================================================================
# 5. 定义损失函数和优化器
# ============================================================================
print("\n--- 5. 定义损失函数和优化器 ---")

criterion = nn.CrossEntropyLoss()   # 多分类交叉熵损失
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

print(f"损失函数: CrossEntropyLoss")
print(f"优化器: Adam (lr={LEARNING_RATE})")

# ============================================================================
# 6. 训练模型
# ============================================================================
print("\n--- 6. 开始训练！ ---")

# 记录训练过程（用于后续绘图）
train_losses = []
test_accuracies = []


def train_one_epoch(model, loader, criterion, optimizer, device):
    """训练一个epoch"""
    model.train()  # 设置为训练模式（启用Dropout等）
    total_loss = 0
    correct = 0
    total = 0
    
    for batch_idx, (data, target) in enumerate(loader):
        # 把数据移到设备上
        data, target = data.to(device), target.to(device)
        
        # 前向传播
        output = model(data)
        loss = criterion(output, target)
        
        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # 统计
        total_loss += loss.item()
        predicted = output.argmax(dim=1)
        correct += (predicted == target).sum().item()
        total += target.size(0)
        
        # 每100批打印一次进度
        if (batch_idx + 1) % 200 == 0:
            print(f"    批次 {batch_idx+1}/{len(loader)}, "
                  f"当前损失: {loss.item():.4f}")
    
    avg_loss = total_loss / len(loader)
    accuracy = correct / total
    return avg_loss, accuracy


def evaluate(model, loader, device):
    """在测试集上评估模型"""
    model.eval()  # 设置为评估模式（关闭Dropout等）
    correct = 0
    total = 0
    
    with torch.no_grad():  # 不需要计算梯度
        for data, target in loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            predicted = output.argmax(dim=1)
            correct += (predicted == target).sum().item()
            total += target.size(0)
    
    return correct / total


# 训练循环
for epoch in range(EPOCHS):
    print(f"\nEpoch {epoch+1}/{EPOCHS}")
    print("-" * 40)
    
    # 训练
    train_loss, train_acc = train_one_epoch(
        model, train_loader, criterion, optimizer, DEVICE
    )
    
    # 评估
    test_acc = evaluate(model, test_loader, DEVICE)
    
    # 记录
    train_losses.append(train_loss)
    test_accuracies.append(test_acc)
    
    print(f"  训练损失: {train_loss:.4f}")
    print(f"  训练准确率: {train_acc*100:.2f}%")
    print(f"  测试准确率: {test_acc*100:.2f}%")

# ============================================================================
# 7. 可视化训练过程
# ============================================================================
print("\n--- 7. 可视化训练过程 ---")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

# 损失曲线
ax1.plot(range(1, EPOCHS+1), train_losses, 'b-o')
ax1.set_xlabel('Epoch')
ax1.set_ylabel('Loss')
ax1.set_title('Training Loss')
ax1.grid(True)

# 准确率曲线
ax2.plot(range(1, EPOCHS+1), [a*100 for a in test_accuracies], 'r-o')
ax2.set_xlabel('Epoch')
ax2.set_ylabel('Accuracy (%)')
ax2.set_title('Test Accuracy')
ax2.grid(True)

plt.tight_layout()
plt.savefig('training_progress.png', dpi=100)
print("训练过程图已保存到 training_progress.png")

# ============================================================================
# 8. 查看一些预测结果
# ============================================================================
print("\n--- 8. 查看预测结果 ---")

model.eval()
fig, axes = plt.subplots(2, 5, figsize=(12, 5))

with torch.no_grad():
    for i, ax in enumerate(axes.flat):
        image, true_label = test_dataset[i]
        # 预测
        output = model(image.unsqueeze(0).to(DEVICE))  # 加一个batch维度
        pred_label = output.argmax(dim=1).item()
        confidence = torch.softmax(output, dim=1).max().item()
        
        # 显示
        ax.imshow(image.squeeze(), cmap='gray')
        color = 'green' if pred_label == true_label else 'red'
        ax.set_title(f'预测:{pred_label} 真实:{true_label}\n'
                     f'置信度:{confidence:.1%}',
                     color=color, fontsize=10)
        ax.axis('off')

plt.suptitle('模型预测结果（绿色=正确，红色=错误）', fontsize=13)
plt.tight_layout()
plt.savefig('predictions.png', dpi=100)
print("预测结果已保存到 predictions.png")

# ============================================================================
# 9. 每个数字的准确率
# ============================================================================
print("\n--- 9. 每个数字的准确率 ---")

class_correct = [0] * 10
class_total = [0] * 10

model.eval()
with torch.no_grad():
    for data, target in test_loader:
        data, target = data.to(DEVICE), target.to(DEVICE)
        output = model(data)
        predicted = output.argmax(dim=1)
        
        for i in range(target.size(0)):
            label = target[i].item()
            class_correct[label] += (predicted[i] == target[i]).item()
            class_total[label] += 1

print(f"{'数字':>4} {'正确/总数':>10} {'准确率':>8}")
print("-" * 28)
for i in range(10):
    acc = class_correct[i] / class_total[i] * 100
    print(f"{i:>4} {class_correct[i]:>5}/{class_total[i]:<5} {acc:>7.1f}%")

overall_acc = sum(class_correct) / sum(class_total) * 100
print(f"\n总体准确率: {overall_acc:.2f}%")

print("\n" + "=" * 60)
print("[完成] 第5课完成！你已经完成了第一个深度学习项目：")
print("  [v] 加载和预处理MNIST数据集")
print("  [v] 搭建多层全连接神经网络")
print("  [v] 完整的训练和评估流程")
print("  [v] 可视化训练过程和预测结果")
print("  [v] 分析每个类别的准确率")
print(f"\n  最终准确率: {overall_acc:.2f}%")
print("=" * 60)
print("\n下一课：06_save_load.py - 模型保存与加载")
