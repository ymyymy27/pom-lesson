# 视觉模型与图像理解 从零开始深入学习教程

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 第1课 | `01_vision_overview.py` | 视觉 AI 概述（CV发展/多模态视觉/模型对比） |
| 第2课 | `02_image_understanding.py` | 图像理解（GPT-4o/Qwen-VL 视觉问答） |
| 第3课 | `03_ocr_and_extraction.py` | OCR 与信息提取（文字识别/表格/票据） |
| 第4课 | `04_object_detection.py` | 目标检测与图像分割（YOLO/SAM） |
| 第5课 | `05_image_search.py` | 图像搜索与 CLIP 嵌入 |
| 第6课 | `06_video_understanding.py` | 视频理解（关键帧/摘要/多模态分析） |
| 第7课 | `07_vision_project.py` | 完整项目：智能图像分析助手 |

## 环境配置

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 模型配置（二选一）
# Ollama 本地: ollama pull llava:7b (或 qwen2-vl)
# OpenAI: set OPENAI_API_KEY=sk-xxx
```

## 学习方式

按顺序学习，每个文件可直接运行：`python 01_vision_overview.py`
