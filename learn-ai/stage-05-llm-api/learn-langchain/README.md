# LangChain 从零开始深入学习教程

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 第1课 | `01_chat_models.py` | Chat Model 与消息类型 |
| 第2课 | `02_prompt_templates.py` | Prompt 模板与动态提示 |
| 第3课 | `03_output_parsers.py` | 输出解析器（字符串/JSON/Pydantic） |
| 第4课 | `04_lcel_chains.py` | LCEL 链式表达式语言 |
| 第5课 | `05_memory_history.py` | 对话记忆与历史管理 |
| 第6课 | `06_document_loaders.py` | 文档加载与文本分割 |
| 第7课 | `07_retrievers_vectorstore.py` | 向量存储与检索器 |
| 第8课 | `08_rag_project.py` | 完整项目：RAG 知识库问答 |

## 环境配置

```bash
# 1. 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate    # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key（二选一）
# 方式A：使用 OpenAI
set OPENAI_API_KEY=sk-xxx

# 方式B：使用 Ollama（免费本地模型）
# 先安装 Ollama: https://ollama.ai
# 然后运行: ollama pull qwen2.5:7b
```

## 学习方式

建议按顺序学习每个文件，每个文件都可以直接运行：
```bash
python 01_chat_models.py
```

每个文件都有详细的中文注释，建议边读代码边运行，观察输出结果。

## 注意事项

- 本课程默认使用 Ollama 本地模型（免费），你也可以切换为 OpenAI
- 如果使用 Ollama，请确保 Ollama 服务已启动且模型已下载
- 每个文件顶部的 `get_llm()` 函数可以切换模型来源
