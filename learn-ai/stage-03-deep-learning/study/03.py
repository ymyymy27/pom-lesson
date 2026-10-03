import torch
import torch.nn as nn

# conv = nn.Conv2d(
#     in_channels=3,
#     out_channels=16,
#     kernel_size=3,
#     stride=1,
#     padding=1
# )

# x = torch.randn(1,3,32,32)
# out = conv(x)
# print(out.shape)

# pool = nn.MaxPool2d(kernel_size=2, stride=2)
# out = pool(out)
# print(out.shape)


class cnn(nn.Module):
    def __init__(self,num_classes=10):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1,32,3,padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32,64,3,padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64*7*7,128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128,num_classes),
        )

    def forward(self,x):
        x = self.features(x)
        x = self.classifier(x)
        return x

model = cnn()
print(model)


