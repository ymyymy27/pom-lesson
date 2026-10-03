import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第4课：数据加载 (Dataset & DataLoader)
==============================================================================

为什么需要 Dataset 和 DataLoader？
---------------------------------
实际项目中，数据量通常很大（几万甚至几百万条）：
- 不能一次性把所有数据塞进模型（内存不够）
- 需要把数据分成小批次(batch)来训练
- 还需要打乱数据顺序（防止模型记住数据顺序）
- 可能需要对数据做预处理（归一化、数据增强等）

PyTorch 提供了优雅的解决方案：
- Dataset：定义如何获取一条数据
- DataLoader：自动分批、打乱、多线程加载

核心流程：
  原始数据 → Dataset(定义如何读取) → DataLoader(分批+打乱) → 模型训练
==============================================================================
"""

import torch
from torch.utils.data import Dataset, DataLoader, TensorDataset, random_split
import numpy as np

print("=" * 60)
print("第4课：数据加载 (Dataset & DataLoader)")
print("=" * 60)

# ============================================================================
# 1. 最简单的方式：TensorDataset
# ============================================================================
print("\n--- 1. TensorDataset（最简单） ---")

# 假设我们有一些数据
X = torch.randn(100, 3)          # 100个样本，每个3个特征
y = torch.randint(0, 2, (100,))  # 100个标签（0或1）

# 用 TensorDataset 把特征和标签打包在一起
dataset = TensorDataset(X, y)

print(f"数据集大小: {len(dataset)}")
print(f"第0条数据: 特征={dataset[0][0]}, 标签={dataset[0][1]}")
print(f"第1条数据: 特征={dataset[1][0]}, 标签={dataset[1][1]}")

# ============================================================================
# 2. DataLoader - 自动分批和打乱
# ============================================================================
print("\n--- 2. DataLoader - 自动分批和打乱 ---")

# 创建 DataLoader
dataloader = DataLoader(
    dataset,          # 数据集
    batch_size=16,    # 每批16个样本
    shuffle=True,     # 每个epoch开始时打乱数据
    # num_workers=2,  # 多线程加载（Windows上建议注释掉或设为0）
)

print(f"数据集总量: {len(dataset)}")
print(f"批次大小: 16")
print(f"总批次数: {len(dataloader)}")  # 100/16 ≈ 7 批

# 遍历一个epoch（所有数据过一遍）
print(f"\n遍历所有批次：")
for batch_idx, (batch_X, batch_y) in enumerate(dataloader):
    print(f"  第{batch_idx}批: X形状={batch_X.shape}, y形状={batch_y.shape}")

# ============================================================================
# 3. 自定义 Dataset（重点！）
# ============================================================================
print("\n--- 3. 自定义 Dataset ---")
print("""
自定义Dataset需要实现3个方法：
  __init__():     初始化，加载数据
  __len__():      返回数据集大小
  __getitem__(i): 返回第i条数据
""")


class MyDataset(Dataset):
    """
    自定义数据集示例
    模拟场景：我们有一些房屋数据
    - 特征：面积、房间数、楼层
    - 标签：价格
    """
    
    def __init__(self, num_samples=200):
        """初始化：生成或加载数据"""
        super().__init__()
        
        # 在实际项目中，这里通常是读取文件
        # 例如：self.data = pd.read_csv("data.csv")
        
        # 这里我们生成一些假数据
        torch.manual_seed(42)
        
        # 特征：面积(50-200m²), 房间数(1-5), 楼层(1-30)
        self.area = torch.rand(num_samples) * 150 + 50      # 50~200
        self.rooms = torch.randint(1, 6, (num_samples,)).float()  # 1~5
        self.floor = torch.randint(1, 31, (num_samples,)).float() # 1~30
        
        # 标签：价格（简单线性关系 + 噪声）
        self.price = (self.area * 2 + self.rooms * 50 + 
                      self.floor * 5 + torch.randn(num_samples) * 20)
        
        # 组合特征
        self.features = torch.stack([self.area, self.rooms, self.floor], dim=1)
    
    def __len__(self):
        """返回数据集大小"""
        return len(self.features)
    
    def __getitem__(self, idx):
        """返回第idx条数据"""
        return self.features[idx], self.price[idx]


# 使用自定义数据集
dataset = MyDataset(num_samples=200)
print(f"数据集大小: {len(dataset)}")
print(f"第0条: 特征={dataset[0][0]}, 价格={dataset[0][1]:.1f}")
print(f"第1条: 特征={dataset[1][0]}, 价格={dataset[1][1]:.1f}")

# ============================================================================
# 4. 划分训练集和测试集
# ============================================================================
print("\n--- 4. 划分训练集和测试集 ---")
print("""
为什么要划分？
- 训练集：用来训练模型
- 测试集：用来评估模型在"没见过的数据"上的表现
- 如果只用训练集评估，模型可能"死记硬背"（过拟合）
""")

dataset = MyDataset(num_samples=200)

# 方法1：使用 random_split
train_size = int(0.8 * len(dataset))   # 80% 训练
test_size = len(dataset) - train_size   # 20% 测试

train_dataset, test_dataset = random_split(dataset, [train_size, test_size])

print(f"总数据: {len(dataset)}")
print(f"训练集: {len(train_dataset)} ({train_size/len(dataset)*100:.0f}%)")
print(f"测试集: {len(test_dataset)} ({test_size/len(dataset)*100:.0f}%)")

# 分别创建 DataLoader
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)  # 测试集不需要打乱

print(f"\n训练集批次数: {len(train_loader)}")
print(f"测试集批次数: {len(test_loader)}")

# ============================================================================
# 5. 数据预处理 / 数据变换 (Transform)
# ============================================================================
print("\n--- 5. 数据预处理 / 数据变换 ---")
print("""
常见的预处理操作：
- 归一化（把数据缩放到0~1或均值0方差1）
- 数据增强（翻转、旋转、裁剪等，主要用于图像）

归一化的好处：
- 让不同特征的数值范围统一
- 加速训练收敛
- 防止某些特征因为数值大而主导训练
""")


class NormalizedDataset(Dataset):
    """带归一化的数据集"""
    
    def __init__(self, num_samples=200):
        super().__init__()
        torch.manual_seed(42)
        
        area = torch.rand(num_samples) * 150 + 50
        rooms = torch.randint(1, 6, (num_samples,)).float()
        floor = torch.randint(1, 31, (num_samples,)).float()
        
        self.features = torch.stack([area, rooms, floor], dim=1)
        self.price = (area * 2 + rooms * 50 + floor * 5 + 
                      torch.randn(num_samples) * 20)
        
        # 计算均值和标准差（用于归一化）
        self.feature_mean = self.features.mean(dim=0)
        self.feature_std = self.features.std(dim=0)
        self.price_mean = self.price.mean()
        self.price_std = self.price.std()
        
        print(f"  特征均值: {self.feature_mean}")
        print(f"  特征标准差: {self.feature_std}")
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        # 归一化：(x - 均值) / 标准差
        # 这样数据变成均值≈0，标准差≈1
        x = (self.features[idx] - self.feature_mean) / self.feature_std
        y = (self.price[idx] - self.price_mean) / self.price_std
        return x, y


norm_dataset = NormalizedDataset()
x, y = norm_dataset[0]
print(f"\n归一化后的第0条数据:")
print(f"  特征: {x}  (接近0附近)")
print(f"  标签: {y:.4f}")

# ============================================================================
# 6. 完整示例：用自定义数据集训练模型
# ============================================================================
print("\n--- 6. 完整示例：用自定义数据集训练模型 ---")

import torch.nn as nn
import torch.optim as optim

# 准备数据
dataset = NormalizedDataset(num_samples=500)
train_size = int(0.8 * len(dataset))
test_size = len(dataset) - train_size
train_set, test_set = random_split(dataset, [train_size, test_size])

train_loader = DataLoader(train_set, batch_size=32, shuffle=True)
test_loader = DataLoader(test_set, batch_size=32, shuffle=False)

# 定义模型（回归任务，输出1个值）
model = nn.Sequential(
    nn.Linear(3, 16),
    nn.ReLU(),
    nn.Linear(16, 8),
    nn.ReLU(),
    nn.Linear(8, 1)
)

criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

# 训练
print("\n开始训练...")
for epoch in range(50):
    model.train()   # 设置为训练模式
    total_loss = 0
    
    for batch_X, batch_y in train_loader:
        # 前向传播
        pred = model(batch_X).squeeze()  # squeeze去掉多余的维度
        loss = criterion(pred, batch_y)
        
        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    avg_loss = total_loss / len(train_loader)
    
    if (epoch + 1) % 10 == 0:
        # 在测试集上评估
        model.eval()
        test_loss = 0
        with torch.no_grad():
            for batch_X, batch_y in test_loader:
                pred = model(batch_X).squeeze()
                test_loss += criterion(pred, batch_y).item()
        avg_test_loss = test_loss / len(test_loader)
        
        print(f"  Epoch {epoch+1:3d}: 训练损失={avg_loss:.4f}, "
              f"测试损失={avg_test_loss:.4f}")

print("\n训练完成！")

# ============================================================================
# 7. 补充：torchvision 内置数据集
# ============================================================================
print("\n--- 7. 补充知识：torchvision 内置数据集 ---")
print("""
PyTorch 提供了很多现成的经典数据集（下一课会用到）：

  from torchvision import datasets, transforms
  
  # MNIST手写数字（0-9的灰度图片）
  dataset = datasets.MNIST(
      root='./data',           # 数据存放目录
      train=True,              # 训练集
      download=True,           # 自动下载
      transform=transforms.ToTensor()  # 图片转张量
  )
  
  # 其他常用数据集：
  # datasets.CIFAR10()    - 10类彩色图片
  # datasets.FashionMNIST() - 时尚物品图片
  # datasets.ImageFolder()  - 从文件夹读取图片
""")

print("\n" + "=" * 60)
print("[完成] 第4课完成！你已经学会了：")
print("  [v] TensorDataset 快速包装数据")
print("  [v] DataLoader 自动分批和打乱")
print("  [v] 自定义 Dataset（__init__, __len__, __getitem__）")
print("  [v] random_split 划分训练集/测试集")
print("  [v] 数据归一化预处理")
print("  [v] 完整的数据加载+训练流程")
print("=" * 60)
print("\n下一课：05_mnist_project.py - 完整项目：手写数字识别")
