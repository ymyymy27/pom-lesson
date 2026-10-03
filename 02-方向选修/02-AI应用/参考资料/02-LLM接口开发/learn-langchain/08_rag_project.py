import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第8课：完整项目 - RAG 知识库问答系统
==============================================================================

本课将前面所有知识整合，构建一个完整的 RAG 问答系统：

┌──────────────────────────────────────────────────────────┐
│                    RAG 知识库问答系统                      │
│                                                          │
│  1. 文档导入: 加载各种格式的文档                          │
│  2. 文本分割: 按语义切分为小块                            │
│  3. 向量化:   用 Embedding 模型转为向量                   │
│  4. 存储:     存入 ChromaDB 向量数据库                    │
│  5. 检索:     根据用户问题检索相关文档                    │
│  6. 生成:     将检索结果 + 问题交给 LLM 生成答案          │
│  7. 记忆:     支持多轮追问                                │
│                                                          │
│  完整链路：                                               │
│  文档 → 分块 → Embedding → VectorStore                   │
│  问题 → 检索 → Prompt(问题+上下文+历史) → LLM → 回答     │
└──────────────────────────────────────────────────────────┘

这个项目用到了前 7 课的所有核心知识！
==============================================================================
"""

import os
import tempfile
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage, AIMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma

print("=" * 60)
print("第8课：完整项目 - RAG 知识库问答系统")
print("=" * 60)

# ============================================================================
# 1. 配置
# ============================================================================
print("\n--- 1. 系统配置 ---")

class RAGConfig:
    """RAG 系统配置"""
    # 模型配置
    LLM_MODEL = "qwen2.5:7b"
    EMBEDDING_MODEL = "nomic-embed-text"
    TEMPERATURE = 0

    # 分块配置
    CHUNK_SIZE = 400
    CHUNK_OVERLAP = 50

    # 检索配置
    TOP_K = 4
    SEARCH_TYPE = "similarity"   # "similarity" 或 "mmr"

    # 存储配置
    PERSIST_DIR = None  # None = 内存模式

config = RAGConfig()
print(f"  LLM: {config.LLM_MODEL}")
print(f"  Embedding: {config.EMBEDDING_MODEL}")
print(f"  Chunk: {config.CHUNK_SIZE} chars, overlap {config.CHUNK_OVERLAP}")
print(f"  检索: Top-{config.TOP_K}, {config.SEARCH_TYPE}")

# ============================================================================
# 2. RAG 引擎
# ============================================================================
print("\n--- 2. 构建 RAG 引擎 ---")

class RAGEngine:
    """
    RAG 知识库问答引擎
    
    整合了：
    - 第1课: Chat Model
    - 第2课: Prompt Template
    - 第3课: Output Parser
    - 第4课: LCEL Chain
    - 第5课: Memory
    - 第6课: Document Loader & Splitter
    - 第7课: VectorStore & Retriever
    """

    def __init__(self, config: RAGConfig):
        self.config = config

        # 初始化模型
        self.llm = ChatOllama(
            model=config.LLM_MODEL,
            temperature=config.TEMPERATURE,
        )
        self.embeddings = OllamaEmbeddings(model=config.EMBEDDING_MODEL)

        # 文本分割器
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
        )

        # 向量存储（延迟初始化）
        self.vectorstore = None

        # 对话历史（按 session 隔离）
        self.sessions: dict[str, list] = {}

        # Prompt 模板
        self.rag_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的知识库问答助手。请严格根据检索到的上下文回答用户问题。

【回答规则】
1. 只基于上下文中的信息回答，不要编造
2. 如果上下文中没有相关信息，明确说"根据知识库中的资料，我无法回答这个问题"
3. 回答要准确、简洁、有条理
4. 如果适用，用列表或分点说明
5. 标注信息来源（如有）

【检索到的上下文】
{context}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ])

    # ---- 文档导入 ----

    def add_texts(self, texts: list[str], metadatas: list[dict] = None):
        """导入纯文本列表"""
        docs = [
            Document(page_content=t, metadata=m or {})
            for t, m in zip(texts, metadatas or [{}] * len(texts))
        ]
        return self.add_documents(docs)

    def add_documents(self, documents: list[Document]) -> int:
        """导入 Document 列表（会自动分块）"""
        # 分块
        chunks = self.splitter.split_documents(documents)

        # 为每个块添加索引元数据
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = i

        # 创建或更新向量存储
        if self.vectorstore is None:
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.config.PERSIST_DIR,
            )
        else:
            self.vectorstore.add_documents(chunks)

        return len(chunks)

    # ---- 检索 ----

    def _get_retriever(self):
        """获取检索器"""
        if self.vectorstore is None:
            raise ValueError("知识库为空！请先用 add_texts() 或 add_documents() 导入文档。")

        return self.vectorstore.as_retriever(
            search_type=self.config.SEARCH_TYPE,
            search_kwargs={"k": self.config.TOP_K},
        )

    @staticmethod
    def _format_docs(docs: list[Document]) -> str:
        """格式化检索到的文档"""
        if not docs:
            return "（未检索到相关文档）"
        parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "知识库")
            parts.append(f"[文档{i} | 来源: {source}]\n{doc.page_content}")
        return "\n\n".join(parts)

    # ---- 对话 ----

    def _get_history(self, session_id: str) -> list:
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]

    def chat(self, question: str, session_id: str = "default") -> str:
        """带记忆的问答"""
        retriever = self._get_retriever()
        history = self._get_history(session_id)

        # 构建 RAG 链
        chain = (
            {
                "context": RunnableLambda(lambda x: x["question"]) | retriever | self._format_docs,
                "question": RunnableLambda(lambda x: x["question"]),
                "chat_history": RunnableLambda(lambda x: x["chat_history"]),
            }
            | self.rag_prompt
            | self.llm
            | StrOutputParser()
        )

        answer = chain.invoke({
            "question": question,
            "chat_history": history[-6:],  # 窗口记忆：最近3轮
        })

        # 保存历史
        history.append(HumanMessage(content=question))
        history.append(AIMessage(content=answer))

        return answer

    def search(self, query: str, top_k: int = None) -> list[Document]:
        """纯检索（不调用 LLM）"""
        retriever = self._get_retriever()
        if top_k:
            retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": top_k}
            )
        return retriever.invoke(query)

    # ---- 信息 ----

    def get_stats(self) -> dict:
        count = self.vectorstore._collection.count() if self.vectorstore else 0
        return {
            "total_chunks": count,
            "sessions": len(self.sessions),
            "config": {
                "llm": self.config.LLM_MODEL,
                "embedding": self.config.EMBEDDING_MODEL,
                "chunk_size": self.config.CHUNK_SIZE,
                "top_k": self.config.TOP_K,
            }
        }

    def clear_history(self, session_id: str = None):
        if session_id:
            self.sessions.pop(session_id, None)
        else:
            self.sessions.clear()

print("RAGEngine 类定义完成 ✓")

# ============================================================================
# 3. 准备知识库数据
# ============================================================================
print("\n--- 3. 准备知识库数据 ---")

# 模拟一个技术知识库
knowledge_base = [
    {
        "text": """# Python 虚拟环境

## 什么是虚拟环境
虚拟环境是一个独立的 Python 运行环境，每个项目可以有自己的依赖包版本，互不干扰。

## 为什么需要虚拟环境
1. 不同项目可能需要同一个包的不同版本
2. 避免全局安装导致的版本冲突
3. 便于项目的依赖管理和部署

## 创建虚拟环境
```bash
# 使用 venv（Python 自带）
python -m venv myenv

# 激活
myenv\\Scripts\\activate     # Windows
source myenv/bin/activate    # macOS/Linux

# 退出
deactivate
```

## 常用工具
- venv: Python 内置，最基础
- virtualenv: 第三方，功能更丰富
- conda: Anaconda 的环境管理器，支持非 Python 包
- poetry: 现代包管理器，集成环境管理""",
        "metadata": {"source": "python-guide", "topic": "环境管理"}
    },
    {
        "text": """# FastAPI 入门指南

## 什么是 FastAPI
FastAPI 是一个现代的 Python Web 框架，特点：
- 极高性能（基于 Starlette 和 Pydantic）
- 自动生成 API 文档（Swagger UI）
- 基于类型注解，开发体验好
- 原生支持异步（async/await）

## 安装
```bash
pip install fastapi uvicorn
```

## 第一个 API
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```

## 运行
```bash
uvicorn main:app --reload
```

## 请求体验证
FastAPI 使用 Pydantic 模型自动验证请求数据：
```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False

@app.post("/items/")
def create_item(item: Item):
    return item
```""",
        "metadata": {"source": "fastapi-guide", "topic": "Web开发"}
    },
    {
        "text": """# Docker 基础

## 什么是 Docker
Docker 是一个容器化平台，将应用和依赖打包到一个容器中运行。
容器比虚拟机更轻量，启动更快，资源占用更少。

## 核心概念
- 镜像（Image）：应用的打包，类似"模板"
- 容器（Container）：镜像的运行实例
- Dockerfile：定义如何构建镜像的脚本
- Docker Compose：多容器编排工具

## 常用命令
```bash
docker pull python:3.11      # 拉取镜像
docker run -it python:3.11   # 运行容器
docker ps                     # 查看运行中的容器
docker stop <id>              # 停止容器
docker build -t myapp .       # 构建镜像
```

## Dockerfile 示例
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

## Docker Compose
用于同时运行多个服务（如 API + 数据库 + Redis）：
```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
```""",
        "metadata": {"source": "docker-guide", "topic": "容器化"}
    },
    {
        "text": """# Git 进阶技巧

## 分支策略
- main/master: 生产分支，始终保持可部署状态
- develop: 开发分支，集成最新功能
- feature/*: 功能分支，每个新功能一个分支
- hotfix/*: 紧急修复分支

## 常用命令
```bash
git stash              # 暂存当前修改
git stash pop          # 恢复暂存
git rebase main        # 变基（保持线性历史）
git cherry-pick <hash> # 拣选特定提交
git reset --soft HEAD~1  # 撤销最近一次提交（保留修改）
git reflog             # 查看所有操作历史（救命工具）
```

## .gitignore 最佳实践
```
__pycache__/
*.pyc
.env
venv/
node_modules/
.idea/
.vscode/
```

## 提交规范
推荐使用 Conventional Commits：
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- refactor: 重构
- test: 测试相关""",
        "metadata": {"source": "git-guide", "topic": "版本控制"}
    },
]

# ============================================================================
# 4. 初始化 RAG 引擎并导入数据
# ============================================================================
print("\n--- 4. 初始化并导入知识库 ---")

engine = RAGEngine(config)

# 导入知识库
texts = [item["text"] for item in knowledge_base]
metadatas = [item["metadata"] for item in knowledge_base]
n_chunks = engine.add_texts(texts, metadatas)

stats = engine.get_stats()
print(f"导入完成:")
print(f"  原始文档: {len(knowledge_base)} 篇")
print(f"  分块后: {n_chunks} 块")
print(f"  配置: {stats['config']}")

# ============================================================================
# 5. 测试问答
# ============================================================================
print("\n--- 5. 测试问答 ---")

test_questions = [
    "Python 虚拟环境怎么创建？",
    "FastAPI 有什么特点？",
    "Docker 和虚拟机有什么区别？",
    "Git 的分支策略有哪些？",
    "如何做蛋炒饭？",  # 知识库中没有的问题
]

for q in test_questions:
    print(f"\n{'='*50}")
    print(f"Q: {q}")
    answer = engine.chat(q, session_id="test")
    print(f"A: {answer[:200]}{'...' if len(answer) > 200 else ''}")

# ============================================================================
# 6. 测试多轮对话（记忆能力）
# ============================================================================
print(f"\n\n--- 6. 测试多轮对话 ---")

# 新建一个 session
session = "multi_turn_demo"

print(f"\n[第1轮]")
a1 = engine.chat("FastAPI 怎么安装？", session_id=session)
print(f"  Q: FastAPI 怎么安装？")
print(f"  A: {a1[:120]}...")

print(f"\n[第2轮 - 追问]")
a2 = engine.chat("它的性能怎么样？为什么这么快？", session_id=session)
print(f"  Q: 它的性能怎么样？为什么这么快？")
print(f"  A: {a2[:120]}...")

print(f"\n[第3轮 - 追问]")
a3 = engine.chat("给我一个最简单的代码例子", session_id=session)
print(f"  Q: 给我一个最简单的代码例子")
print(f"  A: {a3[:150]}...")

# ============================================================================
# 7. 纯检索测试（不调用 LLM）
# ============================================================================
print(f"\n\n--- 7. 纯检索测试 ---")

docs = engine.search("容器化部署", top_k=3)
print(f"查询: '容器化部署' Top-3 结果:")
for i, doc in enumerate(docs, 1):
    print(f"  {i}. [{doc.metadata.get('source', '?')}] {doc.page_content[:60]}...")

# ============================================================================
# 8. 总结：RAG 系统的完整数据流
# ============================================================================
print(f"\n\n--- 8. RAG 系统完整数据流 ---")
print("""
┌─────────────────── 离线阶段（建库）───────────────────┐
│                                                        │
│  原始文档 → TextSplitter 分块 → Embedding → ChromaDB   │
│  (第6课)    (第6课)            (第7课)     (第7课)     │
│                                                        │
└────────────────────────────────────────────────────────┘

┌─────────────────── 在线阶段（问答）───────────────────┐
│                                                        │
│  用户问题 ─┬→ Retriever 检索 → 相关文档 ─┐            │
│            │   (第7课)                     │            │
│            └→ 对话历史 ──────────────────→ │            │
│               (第5课)                      ↓            │
│                              ChatPromptTemplate         │
│                                 (第2课)                 │
│                                    ↓                    │
│                              ChatModel (LLM)            │
│                                 (第1课)                 │
│                                    ↓                    │
│                              StrOutputParser            │
│                                 (第3课)                 │
│                                    ↓                    │
│                                回答文本                  │
│                                                        │
│  整个链用 LCEL (第4课) 连接：                           │
│  {context: retriever, question: passthrough}            │
│  | prompt | llm | parser                               │
│                                                        │
└────────────────────────────────────────────────────────┘

恭喜！你已经掌握了构建 RAG 系统的完整技能！
""")

print("\n" + "=" * 60)
print("[完成] 第8课完成！你已经学会了：")
print("  [v] 设计 RAG 系统架构")
print("  [v] 文档导入与分块流水线")
print("  [v] 向量存储与检索集成")
print("  [v] 带记忆的多轮 RAG 问答")
print("  [v] 整合前7课所有核心知识")
print("=" * 60)
print("\nLangChain 深入课程全部完成！🎉")
print("建议下一步学习：learn-langgraph（AI Agent 编排）")
