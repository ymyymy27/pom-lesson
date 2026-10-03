import torch
import torch.nn as nn

rnn = nn.RNN(
    input_size=10,
    hidden_size=20,
    num_layers=2,
    batch_first=True
)

# x = torch.randn(32,15,10)
# output,h_n = rnn(x)
# print(output.shape)
# print(h_n.shape)

lstm = nn.LSTM(
    input_size = 10,
    hidden_size = 20,
    num_layers = 2,
    batch_first = True,
    bidirectional = True
)

x = torch.randn(32,15,10)
output,(h_n,c_n) = lstm(x)
print(output.shape)
print(h_n.shape)

gru = nn.GRU(
    input_size = 10,
    hidden_size = 20,
    num_layers = 2,
    batch_first = True
)

output,h_n = gru(x)