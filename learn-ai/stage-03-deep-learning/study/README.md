# GPT 训练项目

## 项目概述

本项目实现了一个简化版 GPT 模型，用于学习古诗词生成。

## 数据集

- **唐诗宋词**：共 78,666 首诗歌，字符集大小 6086
- 训练集：70,800 首（2,453,978 字符）
- 验证集：7,866 首（275,868 字符）

## 项目结构

```
stage-03-deep-learning/
├── data/                          # 数据目录
│   ├── shakespeare.txt             # 莎士比亚数据集（英文）
│   ├── train.txt                   # 唐诗宋词训练集
│   ├── val.txt                     # 唐诗宋词验证集
│   └── prepare_data.py             # 数据预处理脚本
│
├── study/
│   ├── train.py                    # 训练脚本
│   ├── demo.py                     # 生成演示脚本
│   └── 06.py                       # 模型定义
│
└── checkpoints/                    # 保存的模型
    └── best_model.pt               # 最优模型
```

## 快速开始

### 第一步：准备环境

```bash
# 激活虚拟环境
e:\code\Projects\learn\llm_env\Scripts\Activate.ps1
```

### 第二步：运行训练

```bash
cd e:\code\Projects\learn\learn-ai\stage-03-deep-learning
python study/train.py
```

训练过程会：
- 每轮输出训练损失和验证损失
- 自动保存验证损失最低的模型
- 在 RTX 4080 笔记本 GPU 上预计每轮约 30-60 秒

### 第三步：查看生成效果

训练完成后运行：

```bash
python study/demo.py
```

## 模型配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| SEQ_LEN | 128 | 输入序列长度 |
| EMBED_DIM | 256 | 词嵌入维度 |
| NUM_HEADS | 8 | 注意力头数 |
| NUM_LAYERS | 6 | Transformer 层数 |
| FF_DIM | 1024 | 前馈网络维度 |
| BATCH_SIZE | 32 | 批大小 |
| LR | 1e-3 | 学习率 |
| EPOCHS | 50 | 训练轮数 |

## 模型参数量

约 **1300 万参数**（约 50MB），适合在个人 GPU 上训练。

## 自定义训练数据

如果你想用自己的数据，修改 `study/train.py` 中的数据加载部分：

```python
# 加载你自己的文本文件
with open('your_data.txt', 'r', encoding='utf-8') as f:
    train_text = f.read()
```

## 使用莎士比亚数据集

如需使用莎士比亚英文数据集，修改 `train.py` 中的路径：

```python
with open('data/shakespeare.txt', 'r', encoding='utf-8') as f:
    train_text = f.read()
```
