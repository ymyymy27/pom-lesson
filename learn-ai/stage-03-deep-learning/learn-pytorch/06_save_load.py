import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第6课：模型保存与加载
==============================================================================

训练一个模型可能要花几小时甚至几天，所以必须会保存和加载模型！

两种保存方式：
1. 只保存参数（推荐）：体积小，灵活性好
2. 保存整个模型：简单但不太灵活

还会学习：
- 保存训练检查点（checkpoint），断点续训
- 保存最佳模型
==============================================================================
"""

import torch
import torch.nn as nn
import torch.optim as optim
import os

print("=" * 60)
print("第6课：模型保存与加载")
print("=" * 60)

# 创建保存目录
os.makedirs('saved_models', exist_ok=True)

# ============================================================================
# 先创建一个示例模型
# ============================================================================


class MyModel(nn.Module):
    def __init__(self, input_size=10, hidden_size=20, output_size=5):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size)
        )
    
    def forward(self, x):
        return self.network(x)


model = MyModel()
print(f"模型结构:\n{model}")

# ============================================================================
# 1. 方式一：只保存模型参数（推荐）
# ============================================================================
print("\n--- 1. 只保存模型参数（推荐） ---")

# 保存
save_path = 'saved_models/model_state_dict.pth'
torch.save(model.state_dict(), save_path)
print(f"[OK] 模型参数已保存到: {save_path}")

# 查看 state_dict 的内容
print(f"\nstate_dict 包含的参数：")
for key, value in model.state_dict().items():
    print(f"  {key}: 形状={value.shape}")

# 加载
print(f"\n加载模型参数...")
# 第1步：创建一个新的空模型（结构必须和保存时一样）
loaded_model = MyModel()
# 第2步：加载参数
loaded_model.load_state_dict(torch.load(save_path, weights_only=True))
# 第3步：设置为评估模式（如果只是推理的话）
loaded_model.eval()
print(f"[OK] 模型参数加载成功！")

# 验证：两个模型的输出应该一样
x = torch.randn(1, 10)
with torch.no_grad():
    out1 = model(x)
    out2 = loaded_model(x)
print(f"\n验证：原模型输出 = {out1}")
print(f"验证：新模型输出 = {out2}")
print(f"输出一致: {torch.allclose(out1, out2)}")

# ============================================================================
# 2. 方式二：保存整个模型
# ============================================================================
print("\n--- 2. 保存整个模型 ---")

save_path = 'saved_models/model_full.pth'
torch.save(model, save_path)
print(f"[OK] 整个模型已保存到: {save_path}")

# 加载（不需要先创建模型）
loaded_model2 = torch.load(save_path, weights_only=False)
loaded_model2.eval()
print(f"[OK] 整个模型加载成功！")

with torch.no_grad():
    out3 = loaded_model2(x)
print(f"输出一致: {torch.allclose(out1, out3)}")

print("""
[注意] 为什么推荐方式一？
  - 方式二依赖于完全相同的类定义和目录结构
  - 方式二在重构代码后可能无法加载
  - 方式一更灵活，可以跨项目使用
  - 方式一文件体积更小
""")

# ============================================================================
# 3. 保存训练检查点（Checkpoint）
# ============================================================================
print("--- 3. 保存训练检查点（Checkpoint） ---")
print("""
检查点不仅保存模型参数，还保存：
- 优化器状态（学习率等）
- 当前训练的epoch
- 当前的损失值
- 任何你想保存的信息

这样可以在训练中断后，从上次的位置继续训练！
""")

# 模拟一个训练过程
model = MyModel()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# 假设训练到第 epoch=3，loss=0.5
epoch = 3
loss = 0.5

# 保存检查点
checkpoint = {
    'epoch': epoch,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'loss': loss,
    # 可以添加任何额外信息
    'learning_rate': 0.001,
    'best_accuracy': 0.95,
}

checkpoint_path = 'saved_models/checkpoint.pth'
torch.save(checkpoint, checkpoint_path)
print(f"[OK] 检查点已保存到: {checkpoint_path}")
print(f"   保存内容: epoch={epoch}, loss={loss}")

# 从检查点恢复
print(f"\n从检查点恢复训练...")
checkpoint = torch.load(checkpoint_path, weights_only=False)

# 创建新模型和优化器
model_resumed = MyModel()
optimizer_resumed = optim.Adam(model_resumed.parameters())

# 加载状态
model_resumed.load_state_dict(checkpoint['model_state_dict'])
optimizer_resumed.load_state_dict(checkpoint['optimizer_state_dict'])
start_epoch = checkpoint['epoch']
last_loss = checkpoint['loss']

print(f"[OK] 恢复成功！")
print(f"   继续从 epoch {start_epoch + 1} 开始训练")
print(f"   上次的 loss: {last_loss}")

# ============================================================================
# 4. 实战：训练中自动保存最佳模型
# ============================================================================
print("\n--- 4. 实战：训练中自动保存最佳模型 ---")

# 创建模型和数据
torch.manual_seed(42)
model = MyModel(input_size=4, hidden_size=16, output_size=2)
optimizer = optim.Adam(model.parameters(), lr=0.01)
criterion = nn.CrossEntropyLoss()

X = torch.randn(200, 4)
y = (X[:, 0] + X[:, 1] > 0).long()

# 划分数据
X_train, X_val = X[:160], X[160:]
y_train, y_val = y[:160], y[160:]

best_val_loss = float('inf')   # 初始化为无穷大
best_epoch = 0

print("开始训练（自动保存最佳模型）...")
for epoch in range(50):
    # 训练
    model.train()
    output = model(X_train)
    loss = criterion(output, y_train)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    # 验证
    model.eval()
    with torch.no_grad():
        val_output = model(X_val)
        val_loss = criterion(val_output, y_val).item()
        val_acc = (val_output.argmax(1) == y_val).float().mean().item()
    
    # 如果验证损失创新低，保存模型
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        best_epoch = epoch + 1
        torch.save(model.state_dict(), 'saved_models/best_model.pth')
    
    if (epoch + 1) % 10 == 0:
        print(f"  Epoch {epoch+1:3d}: "
              f"train_loss={loss.item():.4f}, "
              f"val_loss={val_loss:.4f}, "
              f"val_acc={val_acc*100:.1f}%")

print(f"\n最佳模型来自 Epoch {best_epoch}，验证损失: {best_val_loss:.4f}")
print(f"最佳模型已保存到: saved_models/best_model.pth")

# 加载最佳模型进行预测
best_model = MyModel(input_size=4, hidden_size=16, output_size=2)
best_model.load_state_dict(torch.load('saved_models/best_model.pth', weights_only=True))
best_model.eval()

with torch.no_grad():
    final_output = best_model(X_val)
    final_acc = (final_output.argmax(1) == y_val).float().mean()
    print(f"最佳模型在验证集上的准确率: {final_acc.item()*100:.1f}%")

# ============================================================================
# 5. 文件大小对比
# ============================================================================
print("\n--- 5. 文件大小对比 ---")

files = [
    'saved_models/model_state_dict.pth',
    'saved_models/model_full.pth',
    'saved_models/checkpoint.pth',
    'saved_models/best_model.pth',
]

for f in files:
    if os.path.exists(f):
        size_kb = os.path.getsize(f) / 1024
        print(f"  {f}: {size_kb:.1f} KB")

print("\n" + "=" * 60)
print("[完成] 第6课完成！你已经学会了：")
print("  [v] 保存和加载模型参数（state_dict）")
print("  [v] 保存和加载整个模型")
print("  [v] 训练检查点（断点续训）")
print("  [v] 自动保存最佳模型")
print("=" * 60)
print("\n下一课：07_gpu_tips.py - GPU加速与实用技巧")
