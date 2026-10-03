"""
诗歌生成演示脚本
加载训练好的模型，输入开头自动续写诗歌
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from pathlib import Path

# ===================== 模型定义（与 train.py 保持一致）=====================

class CasualAttention(nn.Module):
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

        mask = torch.tril(torch.ones(T, T, device=x.device)).unsqueeze(0).unsqueeze(0)
        scores = scores.masked_fill(mask == 0, float('-inf'))

        attn = torch.softmax(scores, dim=-1)
        out = torch.matmul(attn, V)
        out = out.transpose(1, 2).contiguous().view(B, T, C)
        return self.W_o(out)


class TransformerBlock(nn.Module):
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
        assert T <= self.max_seq_len

        token_emb = self.token_embedding(x)
        pos_emb = self.position_embedding(torch.arange(T, device=x.device))
        x = self.dropout(token_emb + pos_emb)

        for block in self.blocks:
            x = block(x)

        x = self.norm(x)
        return self.lm_head(x)


# ===================== 字符级分词器 =====================

class CharTokenizer:
    def __init__(self, texts):
        chars = sorted(set(texts))
        self.stoi = {ch: i for i, ch in enumerate(chars)}
        self.itos = {i: ch for i, ch in enumerate(chars)}
        self.vocab_size = len(chars)

    def encode(self, text):
        return [self.stoi[c] for c in text if c in self.stoi]

    def decode(self, ids):
        return ''.join(self.itos[i] for i in ids if i in self.itos)


# ===================== 生成函数 =====================

@torch.no_grad()
def generate_poetry(model, tokenizer, prompt, max_new_tokens=100,
                    temperature=1.0, top_k=30):
    device = next(model.parameters()).device
    model.eval()

    input_ids = torch.tensor([tokenizer.encode(prompt)], dtype=torch.long).to(device)

    for _ in range(max_new_tokens):
        input_ids_cond = input_ids[:, -256:]
        output = model(input_ids_cond)
        logits = output[:, -1, :]

        if temperature != 1.0:
            logits = logits / temperature

        if top_k is not None and top_k > 0:
            v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
            logits[logits < v[:, [-1]]] = float('-inf')

        probs = F.softmax(logits, dim=-1)
        next_token = torch.multinomial(probs, num_samples=1)
        input_ids = torch.cat([input_ids, next_token], dim=1)

        if next_token.item() == tokenizer.stoi.get('=', -1):
            break

    return tokenizer.decode(input_ids[0].tolist())


# ===================== 主函数 =====================

def main():
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    CKPT_PATH = Path(__file__).resolve().parent / "checkpoints/best_model.pt"

    print("=" * 50)
    print("诗歌生成演示")
    print(f"设备: {DEVICE}")
    print("=" * 50)

    # 检查是否有训练好的模型
    if not CKPT_PATH.exists():
        print(f"未找到模型文件: {CKPT_PATH}")
        print("请先运行 train.py 训练模型")
        return

    # 加载模型
    print(f"加载模型: {CKPT_PATH}")
    checkpoint = torch.load(CKPT_PATH, map_location=DEVICE, weights_only=False)
    config = checkpoint['config']

    model = GPT(
        vocab_size=config['vocab_size'],
        embed_dim=config['embed_dim'],
        num_heads=config['num_heads'],
        num_layers=config['num_layers'],
        ff_dim=config['ff_dim'],
        max_seq_len=config['seq_len'],
    )
    model.load_state_dict(checkpoint['model_state'])
    model = model.to(DEVICE)
    tokenizer = checkpoint['tokenizer']

    print(f"模型加载成功！")
    print(f"验证损失: {checkpoint['val_loss']:.4f}")
    print()

    # 演示生成
    prompts = [
        "床前明月光",
        "春眠不觉晓",
        "白日依山尽",
        "千山鸟飞绝",
        "月落乌啼霜满天",
        "大漠沙如雪",
        "独在异乡为异客",
        "春风得意马蹄疾",
    ]

    print("=" * 50)
    print("生成示例：")
    print("=" * 50)

    for i, prompt in enumerate(prompts):
        print(f"\n【{i+1}】输入: 「{prompt}」")
        result = generate_poetry(
            model, tokenizer, prompt,
            max_new_tokens=50,
            temperature=0.8,
            top_k=30
        )
        # 只显示新生成的部分
        new_text = result[len(prompt):]
        print(f"  生成: 「{new_text.strip('=')}」")

    print("\n" + "=" * 50)
    print("演示完成！")


if __name__ == "__main__":
    main()
