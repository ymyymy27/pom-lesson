# LLM 微调 从零开始深入学习教程

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 第1课 | `01_fine_tuning_overview.py` | 微调概述（原理/场景/方式对比） |
| 第2课 | `02_data_preparation.py` | 数据准备（格式/清洗/增强/验证） |
| 第3课 | `03_lora_and_qlora.py` | LoRA / QLoRA 原理与实践 |
| 第4课 | `04_training_practice.py` | 训练实战（SFTTrainer/超参数/监控） |
| 第5课 | `05_openai_fine_tuning.py` | OpenAI Fine-tuning API |
| 第6课 | `06_evaluation.py` | 评估与对比（指标/LLM-Judge/A/B） |
| 第7课 | `07_fine_tuning_project.py` | 完整项目：领域专家微调平台 |

## 环境配置

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 本地模型
ollama pull qwen2.5:7b
```

## 学习方式

按顺序学习，每个文件可直接运行：`python 01_fine_tuning_overview.py`
