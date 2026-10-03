"""
GPT 模型训练脚本
功能：
  1. 从预处理好的文本文件加载训练集/验证集
  2. 用字符级 BPE tokenizer
  3. 训练 GPT 模型，同时输出训练损失和验证损失
  4. 自动保存最优模型
  5. 训练完成后运行 demo 生成诗歌
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
import math
import os
import time

# ===================== 1. 模型定义 =====================

class CasualAttention(nn.Module):
    """因果注意力——每个位置只能看到自己和之前的词"""
    def __init__(self, embed_dim, num_heads):
        super().__init__()
        assert embed_dim % num_heads == 0
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        self.W_q = nn.Linear(embed_dim, embed_dim)
        self.W_k = nn.Linear(embed_dim, embed_dim)
        self.W_v = nn.Linear(embed_dim, embed_dim)
        self.W_o = nn.Linear(embed_dim, embed_dim)

    def forward(self, x):
        B, T, C = x.shape

        Q = self.W_q(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        K = self.W_k(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        V = self.W_v(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)

        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.head_dim)

        # 因果掩码：遮住未来
        mask = torch.tril(torch.ones(T, T, device=x.device)).unsqueeze(0).unsqueeze(0)
        scores = scores.masked_fill(mask == 0, float('-inf'))

        attn = torch.softmax(scores, dim=-1)
        out = torch.matmul(attn, V)
        out = out.transpose(1, 2).contiguous().view(B, T, C)
        return self.W_o(out)


class TransformerBlock(nn.Module):
    """单个 Transformer 解码器块"""
    def __init__(self, embed_dim, num_heads, ff_dim, dropout=0.1):
        super().__init__()
        self.attention = CasualAttention(embed_dim, num_heads)
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.ff = nn.Sequential(
            nn.Linear(embed_dim, ff_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim, embed_dim),
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        x = x + self.dropout(self.attention(self.norm1(x)))
        x = x + self.ff(self.norm2(x))
        return x


class GPT(nn.Module):
    """简化版 GPT 模型"""
    def __init__(self, vocab_size, embed_dim=256, num_heads=8,
                 num_layers=6, ff_dim=1024, max_seq_len=256, dropout=0.1):
        super().__init__()
        self.max_seq_len = max_seq_len

        self.token_embedding = nn.Embedding(vocab_size, embed_dim)
        self.position_embedding = nn.Embedding(max_seq_len, embed_dim)
        self.dropout = nn.Dropout(dropout)

        self.blocks = nn.ModuleList([
            TransformerBlock(embed_dim, num_heads, ff_dim, dropout)
            for _ in range(num_layers)
        ])

        self.norm = nn.LayerNorm(embed_dim)
        self.lm_head = nn.Linear(embed_dim, vocab_size, bias=False)

    def forward(self, x):
        B, T = x.shape
        assert T <= self.max_seq_len, f"序列长度 {T} 超出最大长度 {self.max_seq_len}"

        token_emb = self.token_embedding(x)
        pos_emb = self.position_embedding(torch.arange(T, device=x.device))
        x = self.dropout(token_emb + pos_emb)

        for block in self.blocks:
            x = block(x)

        x = self.norm(x)
        return self.lm_head(x)


# ===================== 2. 分词器 =====================

class CharTokenizer:
    """字符级分词器（适合中文古诗词）"""
    def __init__(self, texts):
        chars = sorted(set(texts))
        self.stoi = {ch: i for i, ch in enumerate(chars)}
        self.itos = {i: ch for i, ch in enumerate(chars)}
        self.vocab_size = len(chars)

    def encode(self, text):
        return [self.stoi[c] for c in text if c in self.stoi]

    def decode(self, ids):
        return ''.join(self.itos[i] for i in ids if i in self.itos)


# ===================== 3. 数据集 =====================

class TextDataset(Dataset):
    def __init__(self, text, seq_len=64, tokenizer=None):
        if tokenizer is None:
            tokenizer = CharTokenizer(text)
        self.tokenizer = tokenizer
        self.seq_len = seq_len
        self.data = torch.tensor(self.tokenizer.encode(text), dtype=torch.long)

    def __len__(self):
        return max(0, len(self.data) - self.seq_len)

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.seq_len]
        y = self.data[idx + 1:idx + self.seq_len + 1]
        return x, y


# ===================== 4. 训练函数 =====================

@torch.no_grad()
def evaluate(model, val_loader, device):
    """在验证集上评估模型"""
    model.eval()
    total_loss = 0
    count = 0
    for x, y in val_loader:
        x, y = x.to(device), y.to(device)
        output = model(x)
        loss = F.cross_entropy(output.view(-1, output.size(-1)), y.view(-1))
        total_loss += loss.item() * x.size(0)
        count += x.size(0)
    return total_loss / count


def train():
    DATA_DIR = Path(__file__).resolve().parent / "data"
    OUT_DIR = Path(__file__).resolve().parent / "checkpoints"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- 超参数 ---
    SEQ_LEN = 128       # 序列长度
    EMBED_DIM = 256     # 嵌入维度
    NUM_HEADS = 8       # 注意力头数
    NUM_LAYERS = 6      # Transformer 层数
    FF_DIM = 1024      # 前馈网络维度
    BATCH_SIZE = 32     # 批大小
    LR = 1e-3           # 学习率
    EPOCHS = 50         # 训练轮数
    GRAD_CLIP = 1.0     # 梯度裁剪

    # --- 加载数据 ---
    import sys
    print("=" * 50, flush=True)
    print("加载数据集...", flush=True)
    with open(DATA_DIR / "train.txt", 'r', encoding='utf-8') as f:
        train_text = f.read()
    print(f"训练集文本加载完成: {len(train_text):,} 字符", flush=True)
    with open(DATA_DIR / "val.txt", 'r', encoding='utf-8') as f:
        val_text = f.read()
    print(f"验证集文本加载完成: {len(val_text):,} 字符", flush=True)

    # 创建分词器（只用训练集字符）
    tokenizer = CharTokenizer(train_text)
    print(f"词表大小: {tokenizer.vocab_size}", flush=True)

    # 创建数据集
    print("构建数据集...", flush=True)
    train_dataset = TextDataset(train_text, SEQ_LEN, tokenizer)
    val_dataset = TextDataset(val_text, SEQ_LEN, tokenizer)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,
                             num_workers=0, drop_last=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False,
                            num_workers=0, drop_last=False)
    print(f"数据集构建完成! 训练批次数: {len(train_loader)}", flush=True)

    # --- 模型 ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"设备: {device}", flush=True)

    model = GPT(
        vocab_size=tokenizer.vocab_size,
        embed_dim=EMBED_DIM,
        num_heads=NUM_HEADS,
        num_layers=NUM_LAYERS,
        ff_dim=FF_DIM,
        max_seq_len=SEQ_LEN,
    )
    model = model.to(device)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"模型参数量: {total_params:,}", flush=True)

    # --- 优化器 & 调度器 ---
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.1)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    # --- 训练循环 ---
    print("=" * 50, flush=True)
    print("开始训练", flush=True)
    print("=" * 50, flush=True)

    best_val_loss = float('inf')

    for epoch in range(EPOCHS):
        epoch_start = time.time()
        model.train()
        total_loss = 0
        batch_count = 0

        for batch_idx, (x, y) in enumerate(train_loader):
            x, y = x.to(device), y.to(device)

            optimizer.zero_grad()
            output = model(x)
            loss = F.cross_entropy(output.view(-1, output.size(-1)), y.view(-1))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()
            batch_count += 1

            # 每 200 个 batch 打印进度
            if (batch_idx + 1) % 200 == 0:
                avg_loss = total_loss / batch_count
                pct = (batch_idx + 1) / len(train_loader) * 100
                print(f"  Epoch {epoch+1:02d} [{pct:.0f}%] Batch {batch_idx+1}, Loss: {avg_loss:.4f}", flush=True)

        # 计算 epoch 平均损失
        avg_train_loss = total_loss / batch_count
        val_loss = evaluate(model, val_loader, device)
        elapsed = time.time() - epoch_start

        print(f"Epoch {epoch+1:02d}/{EPOCHS} | "
              f"Train Loss: {avg_train_loss:.4f} | "
              f"Val Loss: {val_loss:.4f} | "
              f"LR: {scheduler.get_last_lr()[0]:.6f} | "
              f"Time: {elapsed:.1f}s", flush=True)

        # 保存最优模型
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            ckpt_path = OUT_DIR / "best_model.pt"
            torch.save({
                'epoch': epoch,
                'model_state': model.state_dict(),
                'tokenizer': tokenizer,
                'val_loss': val_loss,
                'config': {
                    'vocab_size': tokenizer.vocab_size,
                    'embed_dim': EMBED_DIM,
                    'num_heads': NUM_HEADS,
                    'num_layers': NUM_LAYERS,
                    'ff_dim': FF_DIM,
                    'seq_len': SEQ_LEN,
                }
            }, ckpt_path)
            print(f"  [保存最优模型] Val Loss: {val_loss:.4f}", flush=True)

    print("=" * 50, flush=True)
    print("训练完成！", flush=True)
    print(f"最优验证损失: {best_val_loss:.4f}", flush=True)
    print(f"模型保存在: {OUT_DIR / 'best_model.pt'}", flush=True)
    print("=" * 50, flush=True)

    return model, tokenizer


# ===================== 5. 诗歌生成 =====================

@torch.no_grad()
def generate_poetry(model, tokenizer, prompt, max_new_tokens=100, temperature=1.0, top_k=None):
    """生成诗歌"""
    device = next(model.parameters()).device
    model.eval()

    input_ids = torch.tensor([tokenizer.encode(prompt)], dtype=torch.long).to(device)

    for _ in range(max_new_tokens):
        # 截断
        input_ids_cond = input_ids[:, -256:]
        output = model(input_ids_cond)
        logits = output[:, -1, :]

        # Temperature 采样
        if temperature != 1.0:
            logits = logits / temperature

        # Top-k 采样
        if top_k is not None and top_k > 0:
            v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
            logits[logits < v[:, [-1]]] = float('-inf')

        probs = F.softmax(logits, dim=-1)
        next_token = torch.multinomial(probs, num_samples=1)
        input_ids = torch.cat([input_ids, next_token], dim=1)

        # 遇到分隔符停止（如果 prompt 里包含的话）
        if next_token.item() == tokenizer.stoi.get('=', -1):
            break

    return tokenizer.decode(input_ids[0].tolist())


if __name__ == "__main__":
    train()
