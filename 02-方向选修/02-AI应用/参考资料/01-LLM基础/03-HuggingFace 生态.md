> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# HuggingFace 生态

## 学习目标

- 掌握 HuggingFace Transformers 库的使用
- 学会使用 Pipeline 快速完成 NLP 任务
- 了解 HuggingFace Hub 模型和数据集

## 1. HuggingFace 简介

HuggingFace 是 AI 社区的核心平台，提供：
- **Transformers**：统一的模型调用库
- **Hub**：模型和数据集共享平台（70万+模型）
- **Datasets**：数据集加载库
- **Tokenizers**：高效的分词器
- **PEFT**：高效微调库
- **Accelerate**：分布式训练

```bash
pip install transformers datasets tokenizers accelerate
```

## 2. Pipeline - 最简单的用法

```python
from transformers import pipeline

# 情感分析
classifier = pipeline("sentiment-analysis")
result = classifier("I love this product!")
print(result)  # [{'label': 'POSITIVE', 'score': 0.9998}]

# 文本生成
generator = pipeline("text-generation", model="gpt2")
result = generator("The future of AI is", max_length=50)
print(result[0]['generated_text'])

# 问答
qa = pipeline("question-answering")
result = qa(
    question="What is PyTorch?",
    context="PyTorch is an open-source machine learning library developed by Meta."
)
print(result)  # {'answer': 'an open-source machine learning library', 'score': 0.95}

# 文本摘要
summarizer = pipeline("summarization")
text = "长文本..."
result = summarizer(text, max_length=100, min_length=30)

# 翻译
translator = pipeline("translation_en_to_zh", model="Helsinki-NLP/opus-mt-en-zh")
result = translator("Hello, how are you?")

# 零样本分类
classifier = pipeline("zero-shot-classification")
result = classifier(
    "这款手机拍照效果很好",
    candidate_labels=["电子产品", "食品", "服装"]
)
```

## 3. 模型加载与使用

```python
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification

# 加载 tokenizer 和模型
model_name = "bert-base-chinese"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# 编码文本
inputs = tokenizer(
    "今天天气真好",
    return_tensors="pt",
    padding=True,
    truncation=True,
    max_length=128
)
print(inputs.keys())  # input_ids, attention_mask, token_type_ids

# 获取模型输出
outputs = model(**inputs)
print(outputs.last_hidden_state.shape)  # (1, seq_len, 768)

# 分类模型
cls_model = AutoModelForSequenceClassification.from_pretrained(
    model_name, num_labels=2
)
outputs = cls_model(**inputs)
print(outputs.logits)  # (1, 2) 分类 logits
```

## 4. Datasets 库

```python
from datasets import load_dataset, Dataset

# 加载 Hub 上的数据集
dataset = load_dataset("imdb")
print(dataset)
# DatasetDict({
#     train: Dataset({features: ['text', 'label'], num_rows: 25000}),
#     test: Dataset({features: ['text', 'label'], num_rows: 25000})
# })

# 数据操作
train_data = dataset['train']
print(train_data[0])        # 第一条数据
print(train_data[:5])       # 前 5 条

# 过滤
positive = train_data.filter(lambda x: x['label'] == 1)

# 映射（预处理）
def tokenize(example):
    return tokenizer(example['text'], truncation=True, max_length=128)

tokenized = train_data.map(tokenize, batched=True)

# 从本地数据创建
data = {
    'text': ['句子1', '句子2', '句子3'],
    'label': [0, 1, 0]
}
my_dataset = Dataset.from_dict(data)

# 从 CSV/JSON 加载
dataset = load_dataset('csv', data_files='data.csv')
dataset = load_dataset('json', data_files='data.json')
```

## 5. 文本 Embedding

获取文本的向量表示（后续 RAG 的基础）。

```python
from transformers import AutoTokenizer, AutoModel
import torch

model_name = "BAAI/bge-small-zh-v1.5"  # 中文 embedding 模型
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    # 使用 [CLS] token 的输出作为句子表示
    embedding = outputs.last_hidden_state[:, 0, :]
    return embedding

# 计算两个句子的相似度
emb1 = get_embedding("机器学习是人工智能的一个分支")
emb2 = get_embedding("深度学习是 ML 的子集")
emb3 = get_embedding("今天天气真好")

from torch.nn.functional import cosine_similarity
print(f"语义相关: {cosine_similarity(emb1, emb2).item():.4f}")  # 高
print(f"语义无关: {cosine_similarity(emb1, emb3).item():.4f}")  # 低
```

## 6. HuggingFace Hub

```python
# 搜索和下载模型
from huggingface_hub import HfApi, snapshot_download

api = HfApi()

# 搜索模型
models = api.list_models(
    filter="text-classification",
    sort="downloads",
    direction=-1,
    limit=5
)

# 下载模型到本地
snapshot_download("BAAI/bge-small-zh-v1.5", local_dir="./models/bge")

# 使用镜像（国内加速）
# 设置环境变量
# HF_ENDPOINT=https://hf-mirror.com
```

## 练习

1. 使用 Pipeline 完成：情感分析、文本摘要、零样本分类
2. 加载 `bert-base-chinese`，获取一段中文文本的 embedding
3. 用 Datasets 加载 IMDB 数据集并做预处理
4. 计算 10 个句子两两之间的余弦相似度，构建相似度矩阵

## 阶段总结

本阶段你已掌握：
- ✅ LLM 基本原理与主流模型
- ✅ Prompt Engineering 核心技巧
- ✅ HuggingFace 生态（Transformers/Datasets/Hub）

→ 下一阶段：[stage-05 LLM API 开发](../02-LLM接口开发)
