import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第7课：GPU 加速与实用技巧
==============================================================================

这一课涵盖实际开发中的重要技巧：
1. GPU 加速（CUDA）
2. 学习率调度器
3. 早停法（Early Stopping）
4. 权重初始化
5. 批归一化（BatchNorm）
6. 常见错误与调试技巧

这些技巧能让你的模型训练更快、效果更好！
==============================================================================
"""

import torch
import torch.nn as nn
import torch.optim as optim

print("=" * 60)
print("第7课：GPU 加速与实用技巧")
print("=" * 60)

# ============================================================================
# 1. GPU 加速（CUDA）
# ============================================================================
print("\n--- 1. GPU 加速（CUDA） ---")

# 检查 GPU 是否可用
print(f"CUDA 是否可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU 数量: {torch.cuda.device_count()}")
    print(f"GPU 名称: {torch.cuda.get_device_name(0)}")
    print(f"当前 GPU: {torch.cuda.current_device()}")

# 设备选择的标准写法
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"\n使用设备: {device}")

# 把张量移到 GPU
x_cpu = torch.randn(3, 3)
print(f"\nCPU 张量: device={x_cpu.device}")

x_gpu = x_cpu.to(device)     # 移到 GPU（如果有的话）
print(f"GPU 张量: device={x_gpu.device}")

# 也可以直接在 GPU 上创建
x_direct = torch.randn(3, 3, device=device)
print(f"直接创建: device={x_direct.device}")

# [重要] CPU和GPU上的张量不能直接运算！
print("""
[注意] 常见错误：
  x_cpu = torch.randn(3, 3)           # 在CPU上
  x_gpu = torch.randn(3, 3).cuda()    # 在GPU上
  result = x_cpu + x_gpu              # [X] 报错！设备不一致

  解决：确保所有数据和模型在同一个设备上
  x_cpu = x_cpu.to(device)            # 移到同一设备
  result = x_cpu + x_gpu              # [OK] 正确
""")

# 把模型移到 GPU
model = nn.Linear(10, 5).to(device)
print(f"模型设备: {next(model.parameters()).device}")

# GPU 上的数据需要转回 CPU 才能转 NumPy
x_gpu = torch.randn(3, device=device)
# x_gpu.numpy()  # [X] 如果在GPU上会报错
x_np = x_gpu.cpu().numpy()   # [OK] 先移到CPU再转NumPy
print(f"GPU→CPU→NumPy: {x_np}")

# ============================================================================
# 2. 学习率调度器（Learning Rate Scheduler）
# ============================================================================
print("\n--- 2. 学习率调度器 ---")
print("""
为什么要调整学习率？
- 训练初期：用大学习率快速收敛
- 训练后期：用小学习率精细调整
- 固定学习率可能导致：太大→震荡不收敛，太小→收敛太慢
""")

model = nn.Linear(10, 5)
optimizer = optim.Adam(model.parameters(), lr=0.01)

# 2.1 StepLR：每隔N个epoch，学习率乘以gamma
scheduler1 = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)
print("StepLR (每10个epoch学习率减半):")
temp_optimizer = optim.Adam(model.parameters(), lr=0.01)
temp_scheduler = optim.lr_scheduler.StepLR(temp_optimizer, step_size=10, gamma=0.5)
for epoch in range(31):
    if epoch % 10 == 0:
        print(f"  Epoch {epoch:2d}: lr = {temp_optimizer.param_groups[0]['lr']:.6f}")
    temp_scheduler.step()

# 2.2 ReduceLROnPlateau：当指标不再改善时降低学习率（最实用！）
print("\nReduceLROnPlateau (损失停滞时自动降低):")
print("  用法：scheduler.step(val_loss)  # 传入验证损失")
print("  当验证损失连续patience个epoch没有改善时，学习率乘以factor")

optimizer = optim.Adam(model.parameters(), lr=0.01)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, 
    mode='min',        # 监控指标越小越好（损失）
    factor=0.5,        # 学习率乘以0.5
    patience=5,        # 5个epoch没改善就降低
    verbose=True       # 打印信息
)

# 模拟：损失一直不降
print("  模拟损失停滞...")
for epoch in range(15):
    fake_loss = 1.0     # 假装损失一直是1.0
    scheduler.step(fake_loss)
    if epoch % 5 == 0:
        lr = optimizer.param_groups[0]['lr']
        print(f"  Epoch {epoch}: lr = {lr:.6f}")

# 2.3 CosineAnnealingLR：余弦退火
print("\nCosineAnnealingLR (余弦退火):")
temp_optimizer = optim.Adam(model.parameters(), lr=0.01)
temp_scheduler = optim.lr_scheduler.CosineAnnealingLR(temp_optimizer, T_max=20)
lrs = []
for epoch in range(40):
    lrs.append(temp_optimizer.param_groups[0]['lr'])
    temp_scheduler.step()
    if epoch % 10 == 0:
        print(f"  Epoch {epoch:2d}: lr = {lrs[-1]:.6f}")

# ============================================================================
# 3. 早停法（Early Stopping）
# ============================================================================
print("\n--- 3. 早停法（Early Stopping） ---")
print("""
什么是过拟合？
- 模型在训练集上表现很好，但在新数据上表现差
- 就像学生"背答案"而不是"理解知识"

早停法：当验证集上的表现不再提升时，停止训练
- 防止过拟合
- 节省训练时间
""")


class EarlyStopping:
    """早停法实现"""
    
    def __init__(self, patience=5, min_delta=0.001):
        """
        Args:
            patience: 连续多少个epoch没有改善就停止
            min_delta: 最小改善量，小于这个值不算改善
        """
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.should_stop = False
    
    def __call__(self, val_loss):
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            # 没有改善
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop = True
                print(f"  [STOP] 早停！连续{self.patience}个epoch没有改善")
        else:
            # 有改善，重置计数器
            self.best_loss = val_loss
            self.counter = 0


# 演示
print("\n演示早停法：")
early_stopping = EarlyStopping(patience=3)
fake_losses = [1.0, 0.8, 0.6, 0.5, 0.5, 0.51, 0.52, 0.53]

for epoch, loss in enumerate(fake_losses):
    print(f"  Epoch {epoch}: val_loss = {loss}")
    early_stopping(loss)
    if early_stopping.should_stop:
        break

# ============================================================================
# 4. 权重初始化
# ============================================================================
print("\n--- 4. 权重初始化 ---")
print("""
好的初始化可以加速训练，避免梯度消失/爆炸。

常用初始化方法：
- Xavier/Glorot: 适合Sigmoid/Tanh激活函数
- Kaiming/He:    适合ReLU激活函数（最常用）
- 正态分布/均匀分布: 基本方法
""")


def init_weights(m):
    """自定义权重初始化函数"""
    if isinstance(m, nn.Linear):
        # Kaiming初始化（适合ReLU）
        nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu')
        if m.bias is not None:
            nn.init.zeros_(m.bias)  # 偏置初始化为0


model = nn.Sequential(
    nn.Linear(10, 20),
    nn.ReLU(),
    nn.Linear(20, 5)
)

# 应用初始化
model.apply(init_weights)   # apply会递归地对每一层调用init_weights

print("初始化后的权重统计：")
for name, param in model.named_parameters():
    if 'weight' in name:
        print(f"  {name}: 均值={param.data.mean():.4f}, "
              f"标准差={param.data.std():.4f}")

# ============================================================================
# 5. 批归一化（BatchNorm）
# ============================================================================
print("\n--- 5. 批归一化（BatchNorm） ---")
print("""
BatchNorm 的作用：
- 让每一层的输入保持在稳定的分布
- 加速训练收敛（可以用更大的学习率）
- 有轻微的正则化效果（防过拟合）
- 几乎是现代网络的标配

用法：加在线性层/卷积层和激活函数之间
""")

# 带 BatchNorm 的网络
model_with_bn = nn.Sequential(
    nn.Linear(784, 256),
    nn.BatchNorm1d(256),    # 1d 用于全连接层
    nn.ReLU(),
    nn.Linear(256, 128),
    nn.BatchNorm1d(128),
    nn.ReLU(),
    nn.Linear(128, 10)
)

print(f"带BatchNorm的网络:\n{model_with_bn}")

# BatchNorm 在训练和评估时行为不同！
# 训练时：用当前batch的均值和方差
# 评估时：用训练时积累的全局均值和方差
print("""
[重要]
  model.train()  # 训练时必须调用！BatchNorm用batch统计量
  model.eval()   # 评估时必须调用！BatchNorm用全局统计量
""")

# ============================================================================
# 6. Dropout（随机丢弃）
# ============================================================================
print("--- 6. Dropout ---")
print("""
Dropout 的作用：
- 训练时随机"关闭"一部分神经元（设为0）
- 强迫网络学习更鲁棒的特征（不依赖某几个神经元）
- 有效防止过拟合

dropout率：
- 0.2~0.5 比较常见
- 太高会欠拟合（丢弃太多信息）
""")

dropout = nn.Dropout(p=0.5)  # 50%的概率丢弃

x = torch.ones(1, 10)
print(f"输入:     {x}")

# 训练模式
dropout.train()
print(f"训练模式: {dropout(x)}")   # 一些位置变成0，其余放大2倍
print(f"训练模式: {dropout(x)}")   # 每次丢弃的位置不同

# 评估模式
dropout.eval()
print(f"评估模式: {dropout(x)}")   # 不丢弃，原样输出

# ============================================================================
# 7. 完整的实用模型模板
# ============================================================================
print("\n--- 7. 完整的实用模型模板 ---")


class PracticalNet(nn.Module):
    """
    一个包含所有最佳实践的模型模板
    可以作为你未来项目的起点
    """
    
    def __init__(self, input_size, hidden_sizes, output_size, dropout_rate=0.3):
        super().__init__()
        
        layers = []
        prev_size = input_size
        
        # 动态创建隐藏层
        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.BatchNorm1d(hidden_size),
                nn.ReLU(),
                nn.Dropout(dropout_rate),
            ])
            prev_size = hidden_size
        
        # 输出层（不加激活、BN、Dropout）
        layers.append(nn.Linear(prev_size, output_size))
        
        self.network = nn.Sequential(*layers)
        
        # 应用权重初始化
        self.apply(self._init_weights)
    
    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
            if m.bias is not None:
                nn.init.zeros_(m.bias)
    
    def forward(self, x):
        return self.network(x)


# 使用模板
model = PracticalNet(
    input_size=784,
    hidden_sizes=[256, 128, 64],    # 3个隐藏层
    output_size=10,
    dropout_rate=0.3
)
print(f"实用模型:\n{model}")
total = sum(p.numel() for p in model.parameters())
print(f"总参数量: {total:,}")

# ============================================================================
# 8. 常见错误与调试技巧
# ============================================================================
print("\n--- 8. 常见错误与调试技巧 ---")

print("""
常见错误清单：

1. 忘记清零梯度
   [X] loss.backward()
       optimizer.step()
   [OK] optimizer.zero_grad()  <-- 别忘了！
        loss.backward()
        optimizer.step()

2. 忘记切换 train/eval 模式
   [X] 直接预测
   [OK] model.train()  # 训练前
        model.eval()   # 评估前

3. 忘记 torch.no_grad()
   [X] output = model(test_data)  # 浪费内存计算梯度
   [OK] with torch.no_grad():
            output = model(test_data)

4. 数据和模型不在同一设备
   [X] model.cuda(); output = model(cpu_data)
   [OK] model.to(device); data = data.to(device)

5. 形状不匹配
   调试技巧：在forward()中加 print(x.shape) 追踪形状变化

6. 学习率不合适
   - 损失不下降 → 学习率太小，试试 0.01 或 0.001
   - 损失震荡/爆炸 → 学习率太大，试试 0.0001
   - 建议先用 Adam + lr=0.001 开始

7. 数据没有归一化
   - 输入数据最好归一化到均值0、方差1附近
   - 可以显著加速收敛
""")

# ============================================================================
# 9. 训练流程总结模板
# ============================================================================
print("--- 9. 训练流程总结模板 ---")
print("""
# ===== 完整训练模板 =====

# 1. 准备
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = YourModel().to(device)
criterion = nn.CrossEntropyLoss()  # 或 nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5)

# 2. 训练循环
best_val_loss = float('inf')
for epoch in range(num_epochs):
    
    # --- 训练阶段 ---
    model.train()
    for batch_x, batch_y in train_loader:
        batch_x, batch_y = batch_x.to(device), batch_y.to(device)
        
        optimizer.zero_grad()
        output = model(batch_x)
        loss = criterion(output, batch_y)
        loss.backward()
        optimizer.step()
    
    # --- 验证阶段 ---
    model.eval()
    val_loss = 0
    with torch.no_grad():
        for batch_x, batch_y in val_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            output = model(batch_x)
            val_loss += criterion(output, batch_y).item()
    val_loss /= len(val_loader)
    
    # --- 学习率调整 ---
    scheduler.step(val_loss)
    
    # --- 保存最佳模型 ---
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), 'best_model.pth')
    
    print(f'Epoch {epoch}: val_loss={val_loss:.4f}')

# 3. 加载最佳模型进行预测
model.load_state_dict(torch.load('best_model.pth'))
model.eval()
""")

print("=" * 60)
print("[完成] 第7课完成！你已经学会了：")
print("  [v] GPU加速（.to(device), .cuda(), .cpu()）")
print("  [v] 学习率调度器（StepLR, ReduceLROnPlateau等）")
print("  [v] 早停法防止过拟合")
print("  [v] 权重初始化（Kaiming, Xavier）")
print("  [v] BatchNorm 批归一化")
print("  [v] Dropout 随机丢弃")
print("  [v] 完整的实用模型模板")
print("  [v] 常见错误与调试技巧")
print("=" * 60)

print("\n" + "=" * 60)
print("[恭喜] 你已经完成了 PyTorch 入门教程的全部7课！")
print("=" * 60)
print("""
学习路线建议（接下来可以学）：

1. 卷积神经网络（CNN）
   - 用于图像识别、目标检测
   - nn.Conv2d, nn.MaxPool2d

2. 循环神经网络（RNN/LSTM）
   - 用于文本处理、时间序列
   - nn.LSTM, nn.GRU

3. Transformer
   - 现代NLP和CV的主流架构
   - nn.Transformer, nn.MultiheadAttention

4. 迁移学习
   - 用预训练模型（如ResNet）微调
   - torchvision.models

5. PyTorch Lightning
   - 简化训练代码的高级框架
   - pip install pytorch-lightning

推荐资源：
- PyTorch官方教程: https://pytorch.org/tutorials/
- 动手学深度学习: https://d2l.ai/
""")
