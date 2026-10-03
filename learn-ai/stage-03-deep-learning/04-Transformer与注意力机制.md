# Transformer 与注意力机制

## 学习目标

- 深入理解注意力机制（Self-Attention）
- 掌握 Transformer 架构的核心组件
- 了解 BERT、GPT 等模型的基本原理
- 为后续 LLM 学习打基础

## 1. 注意力机制

核心思想：让模型在处理每个位置时，能关注到输入序列中所有相关位置。

```
Query（查询）：当前位置想要关注什么
Key（键）：    每个位置能提供什么
Value（值）：  每个位置的实际内容

Attention(Q, K, V) = softmax(QK^T / √d_k) V
```

```python
import torch
import torch.nn as nn
import math

class SelfAttention(nn.Module):
    def __init__(self, embed_dim):
        super().__init__()
        self.embed_dim = embed_dim
        self.W_q = nn.Linear(embed_dim, embed_dim)
        self.W_k = nn.Linear(embed_dim, embed_dim)
        self.W_v = nn.Linear(embed_dim, embed_dim)

    def forward(self, x):
        # x: (batch, seq_len, embed_dim)
        Q = self.W_q(x)
        K = self.W_k(x)
        V = self.W_v(x)

        # 注意力分数
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.embed_dim)
        attention_weights = torch.softmax(scores, dim=-1)

        # 加权求和
        output = torch.matmul(attention_weights, V)
        return output, attention_weights
```

## 2. 多头注意力（Multi-Head Attention）

将注意力分成多个"头"，让模型同时关注不同方面的信息。

```python
class MultiHeadAttention(nn.Module):
    def __init__(self, embed_dim, num_heads):
        super().__init__()
        assert embed_dim % num_heads == 0
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        self.W_q = nn.Linear(embed_dim, embed_dim)
        self.W_k = nn.Linear(embed_dim, embed_dim)
        self.W_v = nn.Linear(embed_dim, embed_dim)
        self.W_o = nn.Linear(embed_dim, embed_dim)

    def forward(self, x, mask=None):
        batch_size, seq_len, embed_dim = x.shape

        # 线性变换并分头
        Q = self.W_q(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        K = self.W_k(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        V = self.W_v(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

        # 注意力计算
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.head_dim)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float('-inf'))
        attn = torch.softmax(scores, dim=-1)
        output = torch.matmul(attn, V)

        # 合并多头
        output = output.transpose(1, 2).contiguous().view(batch_size, seq_len, embed_dim)
        return self.W_o(output)
```

## 3. Transformer 架构

```
┌─────────────────────┐
│   输入嵌入 + 位置编码  │
├─────────────────────┤
│   Multi-Head Attention│
│   + Add & LayerNorm  │
├─────────────────────┤
│   Feed Forward Network│
│   + Add & LayerNorm  │
├─────────────────────┤
│   × N 层堆叠         │
└─────────────────────┘
```

```python
class TransformerBlock(nn.Module):
    def __init__(self, embed_dim, num_heads, ff_dim, dropout=0.1):
        super().__init__()
        self.attention = MultiHeadAttention(embed_dim, num_heads)
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.ff = nn.Sequential(
            nn.Linear(embed_dim, ff_dim),
            nn.GELU(),
            nn.Linear(ff_dim, embed_dim),
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        # 自注意力 + 残差连接
        attn_out = self.attention(self.norm1(x), mask)
        x = x + self.dropout(attn_out)

        # 前馈网络 + 残差连接
        ff_out = self.ff(self.norm2(x))
        x = x + self.dropout(ff_out)
        return x
```

## 4. 位置编码

Transformer 没有顺序信息，需要位置编码。

```python
class PositionalEncoding(nn.Module):
    def __init__(self, embed_dim, max_len=5000):
        super().__init__()
        pe = torch.zeros(max_len, embed_dim)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(torch.arange(0, embed_dim, 2).float()
                           * (-math.log(10000.0) / embed_dim))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x):
        return x + self.pe[:, :x.size(1)]
```

## 5. 预训练模型家族

| 模型 | 类型 | 架构 | 典型应用 |
|------|------|------|----------|
| BERT | 编码器 | 双向 | 文本分类、NER、问答 |
| GPT | 解码器 | 自回归 | 文本生成、对话 |
| T5 | 编码器-解码器 | Seq2Seq | 翻译、摘要、多任务 |
| ViT | 编码器 | 图像分块 | 图像分类 |

### BERT vs GPT

```
BERT（双向）：
  [CLS] I love [MASK] food [SEP]
  → 同时看左右上下文，适合理解任务

GPT（自回归）：
  I love → Chinese
  → 只看左侧上下文，适合生成任务
```

## 6. 使用 PyTorch 内置 Transformer

```python
# PyTorch 内置实现
encoder_layer = nn.TransformerEncoderLayer(
    d_model=512, nhead=8, dim_feedforward=2048, batch_first=True
)
transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=6)

x = torch.randn(32, 50, 512)   # (batch, seq_len, embed_dim)
out = transformer_encoder(x)
print(out.shape)   # (32, 50, 512)
```

## 练习

1. 实现 Self-Attention 并可视化注意力权重
2. 构建一个完整的 Transformer 编码器
3. 用 Transformer 做文本分类，对比 LSTM 的效果
4. 阅读论文 "Attention Is All You Need" 的关键章节

## 阶段总结

本阶段你已掌握：
- ✅ PyTorch 基础（张量、自动求导、nn.Module）
- ✅ CNN 与图像分类
- ✅ RNN/LSTM/GRU 与序列模型
- ✅ Transformer 与注意力机制

→ 下一阶段：[stage-04 LLM 基础与 Prompt Engineering](../stage-04-llm-basics/)
