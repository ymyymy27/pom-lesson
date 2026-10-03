> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# CNN 与图像分类

## 学习目标

- 理解卷积神经网络的核心组件（卷积层、池化层）
- 用 PyTorch 构建 CNN 模型
- 学会迁移学习

## 1. CNN 核心概念

```
输入图像 → [卷积层 → 激活 → 池化] × N → 展平 → 全连接层 → 输出

- 卷积层：提取局部特征（边缘、纹理、形状）
- 池化层：降低空间维度，减少计算量
- 全连接层：综合特征做最终分类
```

## 2. 卷积层详解

```python
import torch
import torch.nn as nn

# Conv2d 参数
conv = nn.Conv2d(
    in_channels=3,      # 输入通道数（RGB=3）
    out_channels=16,     # 输出通道数（卷积核数量）
    kernel_size=3,       # 卷积核大小 3x3
    stride=1,            # 步幅
    padding=1             # 填充（保持尺寸不变）
)

# 输入: (batch, channels, height, width)
x = torch.randn(1, 3, 32, 32)    # 1张 32x32 RGB 图片
out = conv(x)
print(out.shape)    # (1, 16, 32, 32)

# 池化层
pool = nn.MaxPool2d(kernel_size=2, stride=2)
out = pool(out)
print(out.shape)    # (1, 16, 16, 16)
```

## 3. 构建 CNN

```python
class CNN(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),   # (32, 28, 28)
            nn.ReLU(),
            nn.MaxPool2d(2),                    # (32, 14, 14)

            nn.Conv2d(32, 64, 3, padding=1),   # (64, 14, 14)
            nn.ReLU(),
            nn.MaxPool2d(2),                    # (64, 7, 7)
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 7 * 7, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x
```

## 4. MNIST 手写数字分类

```python
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader

# 数据加载
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])

train_dataset = torchvision.datasets.MNIST(
    root='./data', train=True, download=True, transform=transform
)
test_dataset = torchvision.datasets.MNIST(
    root='./data', train=False, download=True, transform=transform
)

train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=64)

# 训练
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = CNN().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

for epoch in range(5):
    model.train()
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    # 评估
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    print(f"Epoch {epoch+1}: Accuracy = {correct/total:.4f}")
```

## 5. 迁移学习

利用预训练模型（在 ImageNet 上训练），加速自己的任务。

```python
from torchvision import models

# 加载预训练 ResNet
model = models.resnet18(weights='IMAGENET1K_V1')

# 冻结所有参数
for param in model.parameters():
    param.requires_grad = False

# 替换最后的分类层
num_classes = 10
model.fc = nn.Linear(model.fc.in_features, num_classes)

# 只训练新的分类层
optimizer = torch.optim.Adam(model.fc.parameters(), lr=0.001)
```

## 6. 数据增强

```python
train_transform = transforms.Compose([
    transforms.RandomResizedCrop(224),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])
```

## 练习

1. 在 MNIST 上训练 CNN，达到 99%+ 准确率
2. 用迁移学习（ResNet18）在 CIFAR-10 上训练分类器
3. 对比有/无数据增强的效果差异
4. 可视化 CNN 各层的特征图

## 下一节

→ [03-RNN与序列模型](<03-RNN 与序列模型.md>)
