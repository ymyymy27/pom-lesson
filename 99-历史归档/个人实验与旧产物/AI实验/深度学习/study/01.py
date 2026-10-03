import torch

# w = torch.tensor([1.0],requires_grad=True)
# b = torch.tensor([0.0],requires_grad=True)

# x = torch.tensor([2.0])
# y_true = torch.tensor([5.0])

# y_pred = w*x+b
# print(f"预测值: {y_pred.item():.2f}")

# loss = (y_pred - y_true) ** 2
# print(f"损失：{loss.item():.2f}")

# loss.backward()

# print(f"\nw的梯度: {w.grad}")
# print(f"b的梯度: {b.grad}") 

w = torch.tensor([0.0],requires_grad=True)
b = torch.tensor([0.0],requires_grad=True)

x_data = torch.tensor([1.0,2.0,3.0,4.0])
y_data = torch.tensor([4.0,7.0,10.0,13.0])

learning_rate = 0.01

for i in range(100):
    y_pred = w*x_data+b
    loss = ((y_pred - y_data) ** 2).mean()
    loss.backward()

    with torch.no_grad():
        w -= learning_rate * w.grad
        b -= learning_rate * b.grad

    w.grad.zero_()
    b.grad.zero_()

    if i % 20 == 0:
        print(f"Epoch {i:3d}: loss={loss.item():.4f}, w={w.item():.4f}, b={b.item():.4f}")

print(f"预测值: {w*x_data+b}")
print(f"真实值: {y_data}")


