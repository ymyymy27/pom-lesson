# AI 工程化 从零开始深入学习教程

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 第1课 | `01_fastapi_ai_service.py` | FastAPI 构建 AI 服务 |
| 第2课 | `02_streaming_sse.py` | 流式输出与 SSE |
| 第3课 | `03_session_and_cache.py` | 会话管理与缓存 |
| 第4课 | `04_llm_router.py` | LLM 路由与模型管理 |
| 第5课 | `05_observability.py` | 可观测性（日志/追踪/监控） |
| 第6课 | `06_safety_and_guard.py` | 安全护栏与生产实践 |
| 第7课 | `07_ai_service_project.py` | 完整项目：AI 服务平台 |

## 环境配置

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

ollama pull qwen2.5:7b
```

## 学习方式

按顺序学习，每个文件可直接运行：`python 01_fastapi_ai_service.py`
