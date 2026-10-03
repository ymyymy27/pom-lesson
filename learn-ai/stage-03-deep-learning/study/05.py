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
        Q = self.W_q(x)
        K = self.W_k(x)
        V = self.W_v(x)

        scores = torch.matmul(Q,K.transpose(-2,-1)) / math.sqrt(self.embed_dim)
        attention_weights = torch.softmax(scores, dim=-1)

        output = torch.matmul(attention_weights, V)
        return output,attention_weights


class MultiHeadAttention(nn.Module):
    def __init__(self,embed_dim,num_heads):
        super().__init__()
        assert embed_dim % num_heads == 0
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        self.W_q = nn.Linear(embed_dim, embed_dim)
        self.W_k = nn.Linear(embed_dim,embed_dim)
        self.W_v = nn.Linear(embed_dim,embed_dim)
        self.W_o = nn.Linear(embed_dim,embed_dim)

    def forward(self,x,mask=None):
        batch_size,seq_len,embed_dim = x.shape
        
        Q = self.W_q(x).view(batch_size,seq_len,self.num_heads,self.head_dim).transpose(1,2)
        K = self.W_k(x).view(batch_size,seq_len,self.num_heads,self.head_dim).transpose(1,2)
        V = self.W_v(x).view(batch_size,seq_len,self.num_heads,self.head_dim).transpose(1,2)

        scores = torch.matmul(Q,K.transpose(-2,-1)) / math.sqrt(self.head_dim)
        if mask is not None:
            scores = scores.masked_fill(mask == 0,float('-inf'))
        attn = torch.softmax(scores,dim=-1)
        output = torch.matmul(attn,V)

        output = output.transpose(1,2)
        contiguous().view(batch_size,seq_len,embed_dim)
        return self.W_o(output)


class MultiHeadCrossAttention(nn.Module):
    def __init__(self, embed_dim, num_heads):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        
        self.Wq = nn.Linear(embed_dim, embed_dim)
        self.Wk = nn.Linear(embed_dim, embed_dim)  # K 和 V 用同一个 Linear
        self.Wv = nn.Linear(embed_dim, embed_dim)
        self.out = nn.Linear(embed_dim, embed_dim)
    
    def forward(self, decoder_x, encoder_output, mask=None):   
        batch, dec_len, _ = decoder_x.shape
        enc_len = encoder_output.shape[1]

        Q = self.Wq(decoder_x)
        K = self.Wk(encoder_output)
        V = self.Wv(encoder_output)

        Q = Q.view(batch, dec_len, self.num_heads, self.head_dim).transpose(1, 2)
        K = K.view(batch, enc_len, self.num_heads, self.head_dim).transpose(1, 2)
        V = V.view(batch, enc_len, self.num_heads, self.head_dim).transpose(1, 2)
        
        scores = Q @ K.transpose(-2, -1) / (self.head_dim ** 0.5)
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attn_weights = F.softmax(scores, dim=-1)
        attention_output = attn_weights @ V
        attention_output = attention_output.transpose(1, 2).contiguous()
        attention_output = attention_output.view(batch, dec_len, embed_dim)
        
        return self.out(attention_output)

class EncoderBlock(nn.Module):
    def __init__(self,embed_dim,num_heads,ff_dim,dropout=0.1):
            super().__init__()
            self.attention = MultiHeadAttention(embed_dim,num_heads)
            self.norm1 = nn.LayerNorm(embed_dim)
            self.norm2 = nn.LayerNorm(embed_dim)
            self.ff = nn.Sequential(
                nn.Linear(embed_dim,ff_dim),
                nn.GELU(),
                nn.Linear(ff_dim,embed_dim)
            )
            self.dropout = nn.Dropout(dropout)

    def forward(self,x,mask=None):
        attn_out = self.attention(self.norm1(x),mask)
        x = x + self.dropout(attn_out)

        ff_out = self.ff(self.norm2(x))
        x = x+self.dropout(ff_out)

class DecoderBlock(nn.Module):
    def __init__(self,embed_dim,num_heads,ff_dim,dropout=0.1):
        super().__init__()
        self.masked_attention = MultiHeadAttention(embed_dim,num_heads)
        self.cross_attention = MultiHeadCrossAttention(embed_dim,num_heads)
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.norm3 = nn.LayerNorm(embed_dim)
        self.ff = nn.Sequential(
            nn.Linear(embed_dim,ff_dim),
            nn.GELU(),
            nn.Linear(ff_dim,embed_dim)
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self,x,encoder_output,mask=None):
        attn1 = self.masked_attention(self.norm1(x),mask)
        x = x + self.dropout(attn1)

        attn2 = self.cross_attention(self.norm2(x),encoder_output,mask)
        x = x + self.dropout(attn2)

        ff_out = self.ff(self.norm3(x))
        x = x+self.dropout(ff_out)

        return x

class PositionalEncoding(nn.Module):
    def __init__(self,embed_dim,max_len=5000):
        super().__init__()
        pe = torch.zeros(max_len,embed_dim)
        position = torch.arange(0,max_len)
        unsqueeze(1).float()
        div_term = torch.exp(torch.arange(0,embed_dim,2).float()*(-math.log(10000.0)/embed_dim))
        pe[:,0::2] = torch.sin(position*div_term)
        pe[:,1::2] = torch.cos(position*div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe',pe)

    def forward(self,x):
        return x + self.pe[:, :x.size(1)]

