# RAG 检索增强生成 从零开始深入学习教程

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 第1课 | `01_rag_overview.py` | RAG 架构与原理 |
| 第2课 | `02_document_loading.py` | 文档加载与解析 |
| 第3课 | `03_indexing_pipeline.py` | 索引管道（分块→Embedding→存储） |
| 第4课 | `04_retrieval_strategies.py` | 检索策略（向量/BM25/混合/重排序） |
| 第5课 | `05_rag_optimization.py` | RAG 优化（Query改写/上下文/生成） |
| 第6课 | `06_rag_evaluation.py` | RAG 评估（忠实度/相关性/召回率） |
| 第7课 | `07_rag_project.py` | 完整项目：知识库问答系统 |

## 环境配置

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 本地模型（已就绪）
ollama pull qwen2.5:7b
ollama pull qwen3-embedding:4b
```

## 学习方式

按顺序学习，每个文件可直接运行：`python 01_rag_overview.py`
