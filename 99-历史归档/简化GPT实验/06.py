import torch
import torch.nn as nn
import math

class MultiHeadAttention(nn.Module):
    def __init__(self,embed_dim,num_heads):
        super().__init__()
        assert embed_dim % num_heads == 0
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        self.W_q = nn.Linear(embed_dim,embed_dim)
        self.W_k = nn.Linear(embed_dim,embed_dim)
        self.W_v = nn.Linear(embed_dim,embed_dim)
        self.W_o = nn.Linear(embed_dim,embed_dim)

    def forward(self,x,mask=None):
        batch_size,seq_len,embed_dim = x.shape
        Q = self.W_q(x).view(batch_size,seq_len,self.num_heads,self.head_dim).transpose(1,2)
        K = self.W_k(x).view(batch_size,seq_len,self.num_heads,self.head_dim).transpose(1,2)
        V = self.W_v(x).view(batch_size,seq_len,self.num_heads,self.head_dim).transpose(1,2)

        scores = torch.matmul(Q,K.transpose(-2,-1)) / math.sqrt(self.head_dim)

        mask = torch.tril(torch.ones(seq_len,seq_len,device=x.device)).unsqueeze(0).unsqueeze(0)
        scores = scores.masked_fill(mask == 0,float('-inf'))

        attn = torch.softmax(scores,dim=-1)

        output = torch.matmul(attn,V)
        output = output.transpose(1,2).contiguous().view(batch_size,seq_len,embed_dim)
        return self.W_o(output)

class TransformerBlock(nn.Module):
    def __init__(self,embed_dim,num_heads,ff_dim):
        super().__init__()
        self.attention = MultiHeadAttention(embed_dim,num_heads)
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.ff = nn.Sequential(
            nn.Linear(embed_dim,ff_dim),
            nn.GELU(),
            nn.Linear(ff_dim,embed_dim)
        )

    def forward(self,x):
        x = x + self.attention(self.norm1(x))
        x = x + self.ff(self.norm2(x))
        return x

class pom(nn.Module):
    def __init__(self,vocab_size,embed_dim=256,num_heads=8,num_layers=6,ff_dim=1024,max_len=128):
        super().__init__()
        self.max_len = max_len
        self.embedding = nn.Embedding(vocab_size,embed_dim)
        self.position_embedding = nn.Embedding(max_len,embed_dim)

        self.transformerblocks = nn.ModuleList([
            TransformerBlock(embed_dim,num_heads,ff_dim) for _ in range(num_layers)
        ])

        self.norm = nn.LayerNorm(embed_dim)
        self.linear = nn.Linear(embed_dim,vocab_size)
    
    def forward(self,x):
        batch_size,seq_len = x.shape
        assert seq_len <= self.max_len, f"输入序列长度不能超过{self.max_len}"

        token_embeddings = self.embedding(x)
        position_embeddings = self.position_embedding(torch.arange(seq_len,device=x.device))
        x = token_embeddings + position_embeddings

        for block in self.transformerblocks:
            x = block(x)

        x = self.norm(x)
        return self.linear(x)

import torch
from torch.utils.data import DataLoader, Dataset

class CharTokenizer:
    def __init__(self,texts):
        chars = sorted(set(texts))
        self.stoi = {ch: i for i,ch in enumerate(chars)}
        self.itos = {i: ch for i,ch in enumerate(chars)}
        self.vocab_size = len(chars)

    def encode(self,text):
        return [self.stoi[c] for c in text]

    def decode(self,ids):
        return ''.join(self.itos[i] for i in ids)

class TextDataset(Dataset):
    def __init__(self, text, seq_len=64):
        self.tokenizer = CharTokenizer(text)
        self.seq_len = seq_len
        self.data = torch.tensor(self.tokenizer.encode(text), dtype=torch.long)

    def __len__(self):
        return max(0, len(self.data) - self.seq_len)
    
    def __getitem__(self, idx):
        x = self.data[idx:idx + self.seq_len]
        y = self.data[idx + 1:idx + self.seq_len + 1]
        return x, y



def train():
    text = open('text.txt','r',encoding='utf-8').read()

    dataset = TextDataset(text,seq_len=64)
    dataloader = DataLoader(dataset,batch_size=16,shuffle=True)

    model = pom(dataset.tokenizer.vocab_size)
    device = torch.device('cuda')
    model = model.to(device)

    optimizer = torch.optim.Adam(model.parameters(),lr=3e-4)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer,T_max=100)

    for epoch in range(100):
        total_loss = 0
        for batch,(x,y) in enumerate(dataloader):
            x,y = x.to(device),y.to(device)

            optimizer.zero_grad()
            output = model(x)

            loss = nn.functional.cross_entropy(
                output.view(-1,output.size(-1)),
                y.view(-1)
            )

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1:02d}, Loss: {avg_loss:.4f}")

    torch.save(model.state_dict(),'pom.pth')
    print("模型已保存")



@torch.no_grad()
def generate(model, tokenizer, prompt, max_new_tokens=100):
    device = next(model.parameters()).device
    model.eval()
    
    input_ids = torch.tensor(
        [tokenizer.encode(prompt)],
        dtype=torch.long
    ).to(device)
    
    for _ in range(max_new_tokens):
        input_ids_cond = input_ids if input_ids.size(1) <= 128 else input_ids[:, -128:]
        
        output = model(input_ids_cond)
        next_token_logits = output[:, -1, :]
        
        next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)
        input_ids = torch.cat([input_ids, next_token], dim=1)
        
        if next_token.item() == tokenizer.stoi.get('\n', -1):
            break
    
    return tokenizer.decode(input_ids[0].tolist())


