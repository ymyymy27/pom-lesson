import torch
import torch.nn as nn
import torch.optim as optim

linear = nn.Linear(in_features=3,out_features=2)

x = torch.tensor([1.0,2.0,3.0])
y = linear(x)

# print(f"输入 x: {x} 形状: {x.shape}") 

batch = torch.randn(5,3)
output = linear(batch)

# print(f"批量输入形状: {batch.shape}")
# print(f"批量输出形状: {output.shape}")

x = torch.tensor([-2.0,-1.0,0.0,1.0,2.0])
relu = nn.ReLU()
# print(f"ReLU(x): {relu(x)}")

sigmoid = nn.Sigmoid()
# print(f"Sigmoid(x): {sigmoid(x)}")

tanh = nn.Tanh()
# print(f"Tanh(x): {tanh(x)}")

softmax = nn.Softmax(dim=0)
# print(f"Softmax(x): {softmax(x)}")

class simplenet(nn.Module):
    def __init__(self):
        super().__init__()

        self.layer1 = nn.Linear(4,8)
        self.layer2 = nn.Linear(8,8)
        self.layer3 = nn.Linear(8,2)
        self.relu = nn.ReLU()

    def forward(self,x):
        x = self.relu(self.layer1(x))
        x = self.relu(self.layer2(x))
        x = self.layer3(x)
        return x

model = simplenet()
# print(f"模型结构: {model}")

# for name,param in model.named_parameters():
#     print(f"  {name}: 形状={param.shape}, 需要梯度={param.requires_grad}")

x = torch.randn(1,4)
output = model(x)
# print(f"输入形状: {x.shape}")
# print(f"输出形状: {output.shape}")
# print(f"输出: {output}")

model_seq = nn.Sequential(
    nn.Linear(4,8),
    nn.ReLU(),
    nn.Linear(8,8),
    nn.ReLU(),
    nn.Linear(8,2)
)

output_seq = model_seq(x)
# print(f"输入形状: {x.shape}")
# print(f"输出形状: {output_seq.shape}")
# print(f"输出: {output_seq}")

mse_loss = nn.MSELoss()
pred = torch.tensor([2.5,0.0,2.1])
target = torch.tensor([3.0,-0.5,2.0])
loss = mse_loss(pred,target)
# print(f"MSE Loss: {loss.item():.4f}")

ce_loss = nn.CrossEntropyLoss()
pred = torch.tensor([[2.0,1.0,0.1,0.5],[0.5,2.5,0.3,0.2],[0.3,0.2,0.1,3.0]])
target = torch.tensor([0,1,3])
loss = ce_loss(pred,target)
# print(f"CrossEntropy Loss: {loss.item():.4f}")

model = simplenet()
optimizer = optim.Adam(model.parameters(),lr=0.001)


torch.manual_seed(42)
x = torch.randn(1000,4)
y = (x[:,0] + x[:,1] > 0).long()

model = simplenet()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(),lr=0.001)

for i in range(1000):
    y_pred = model(x)
    loss = criterion(y_pred,y)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    predicted = y_pred.argmax(dim=1)
    accuracy = (predicted == y).float().mean()
    print(f"Epoch {i+1:3d}: loss={loss.item():.4f} accuracy={accuracy.item():.4f}")

x_test = torch.randn(100,4)
y_test = (x_test[:,0] + x_test[:,1] > 0).long()

model.eval()
with torch.no_grad():
    y_pred = model(x_test)
    predicted = y_pred.argmax(dim=1)
    accuracy = (predicted == y_test).float().mean()
    print(f"测试集准确率: {accuracy.item():.4f}")