> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# RNN 与序列模型

## 学习目标

- 理解循环神经网络（RNN）的原理
- 掌握 LSTM/GRU 解决长期依赖问题
- 了解序列到序列模型
- 为 Transformer 学习打下基础

## 1. RNN 原理

处理序列数据（文本、时间序列），每个时间步的隐藏状态依赖于前一步。

```
h_t = tanh(W_hh * h_{t-1} + W_xh * x_t + b)

问题：梯度消失/爆炸，难以学习长距离依赖
```

```python
import torch
import torch.nn as nn

# 基本 RNN
rnn = nn.RNN(
    input_size=10,     # 每个时间步的输入维度
    hidden_size=20,    # 隐藏状态维度
    num_layers=2,      # 堆叠层数
    batch_first=True   # 输入格式 (batch, seq_len, features)
)

x = torch.randn(32, 15, 10)   # (batch=32, seq_len=15, features=10)
output, h_n = rnn(x)
print(output.shape)  # (32, 15, 20) - 所有时间步的输出
print(h_n.shape)     # (2, 32, 20)  - 最后时间步的隐藏状态
```

## 2. LSTM

通过门控机制解决长期依赖问题。

```
遗忘门：决定丢弃哪些旧信息
输入门：决定存入哪些新信息
输出门：决定输出哪些信息
```

```python
lstm = nn.LSTM(
    input_size=10,
    hidden_size=20,
    num_layers=2,
    batch_first=True,
    bidirectional=True   # 双向 LSTM
)

x = torch.randn(32, 15, 10)
output, (h_n, c_n) = lstm(x)
print(output.shape)  # (32, 15, 40)  双向：20*2=40
print(h_n.shape)     # (4, 32, 20)   双向*2层=4
```

## 3. GRU

LSTM 的简化版，参数更少，训练更快。

```python
gru = nn.GRU(input_size=10, hidden_size=20, num_layers=2, batch_first=True)
output, h_n = gru(x)
```

## 4. 文本分类实战

```python
class TextClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True,
                           bidirectional=True)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        # x: (batch, seq_len) - 整数序列
        embed = self.embedding(x)              # (batch, seq_len, embed_dim)
        output, (h_n, _) = self.lstm(embed)
        # 拼接双向最后隐藏状态
        hidden = torch.cat([h_n[-2], h_n[-1]], dim=1)
        hidden = self.dropout(hidden)
        return self.fc(hidden)

model = TextClassifier(vocab_size=10000, embed_dim=128,
                       hidden_dim=64, num_classes=2)
```

## 5. 序列到序列（Seq2Seq）

```
编码器：输入序列 → 上下文向量
解码器：上下文向量 → 输出序列

应用：机器翻译、文本摘要、对话系统
```

```python
class Encoder(nn.Module):
    def __init__(self, input_dim, embed_dim, hidden_dim):
        super().__init__()
        self.embedding = nn.Embedding(input_dim, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)

    def forward(self, x):
        embed = self.embedding(x)
        output, (hidden, cell) = self.lstm(embed)
        return hidden, cell

class Decoder(nn.Module):
    def __init__(self, output_dim, embed_dim, hidden_dim):
        super().__init__()
        self.embedding = nn.Embedding(output_dim, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x, hidden, cell):
        embed = self.embedding(x.unsqueeze(1))
        output, (hidden, cell) = self.lstm(embed, (hidden, cell))
        prediction = self.fc(output.squeeze(1))
        return prediction, hidden, cell
```

## 6. 从 RNN 到 Transformer

RNN 的局限性：
- 顺序处理，无法并行化
- 长距离依赖仍有困难
- 训练速度慢

→ Transformer 通过注意力机制解决了这些问题（下一节详解）

## 练习

1. 用 LSTM 实现情感分析（正面/负面分类）
2. 对比 RNN、LSTM、GRU 在同一任务上的表现
3. 实现一个简单的 Seq2Seq 模型
4. 用双向 LSTM 在文本分类上提升准确率

## 下一节

→ [04-Transformer与注意力机制](<04-Transformer 与注意力机制.md>)
