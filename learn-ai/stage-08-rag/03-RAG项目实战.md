# RAG 项目实战

## 学习目标

- 从零构建一个完整的 RAG 知识库问答系统
- 整合文档加载、分块、检索、生成全流程
- 实现 Web 界面交互

## 1. 项目架构

```
knowledge-qa/
├── app.py              # FastAPI 后端
├── rag_engine.py       # RAG 核心引擎
├── ingest.py           # 文档导入脚本
├── config.py           # 配置管理
├── docs/               # 知识库文档
├── chroma_data/        # 向量数据库存储
└── requirements.txt
```

## 2. RAG 核心引擎

```python
# rag_engine.py
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, UnstructuredMarkdownLoader, DirectoryLoader
)
import os

class RAGEngine:
    def __init__(self, persist_dir="./chroma_data", model="gpt-4o-mini"):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.llm = ChatOpenAI(model=model, temperature=0, streaming=True)
        self.persist_dir = persist_dir
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50,
            separators=["\n\n", "\n", "。", ".", " ", ""],
        )
        self.vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个知识库问答助手。根据以下检索到的上下文回答问题。

规则：
1. 只基于上下文回答，不编造信息
2. 无法回答时明确说明
3. 回答简洁有条理
4. 标注信息来源

上下文：
{context}"""),
            ("user", "{question}"),
        ])

    def ingest(self, file_path: str):
        """导入文档到向量库"""
        ext = os.path.splitext(file_path)[1].lower()
        loader_map = {
            ".pdf": PyPDFLoader,
            ".txt": lambda p: TextLoader(p, encoding="utf-8"),
            ".md": UnstructuredMarkdownLoader,
        }
        loader_cls = loader_map.get(ext)
        if not loader_cls:
            raise ValueError(f"不支持的文件格式: {ext}")

        loader = loader_cls(file_path)
        docs = loader.load()
        chunks = self.splitter.split_documents(docs)

        self.vectorstore.add_documents(chunks)
        return len(chunks)

    def ingest_directory(self, dir_path: str):
        """批量导入目录中的文档"""
        total = 0
        for root, _, files in os.walk(dir_path):
            for f in files:
                try:
                    n = self.ingest(os.path.join(root, f))
                    total += n
                    print(f"  ✓ {f}: {n} chunks")
                except ValueError:
                    pass
        print(f"共导入 {total} 个文档块")
        return total

    def query(self, question: str, top_k: int = 5) -> str:
        """同步查询"""
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": top_k}
        )

        def format_docs(docs):
            return "\n\n".join(
                f"[来源: {d.metadata.get('source', '未知')}]\n{d.page_content}"
                for d in docs
            )

        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        return chain.invoke(question)

    async def astream(self, question: str, top_k: int = 5):
        """异步流式查询"""
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": top_k}
        )

        def format_docs(docs):
            return "\n\n".join(
                f"[来源: {d.metadata.get('source', '未知')}]\n{d.page_content}"
                for d in docs
            )

        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

        async for chunk in chain.astream(question):
            yield chunk

    def get_stats(self) -> dict:
        """获取向量库统计"""
        collection = self.vectorstore._collection
        return {"total_documents": collection.count()}
```

## 3. FastAPI 后端

```python
# app.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil, os

from rag_engine import RAGEngine

app = FastAPI(title="知识库问答系统")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

rag = RAGEngine()

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5

@app.post("/query")
async def query(req: QueryRequest):
    answer = rag.query(req.question, req.top_k)
    return {"answer": answer}

@app.post("/query/stream")
async def query_stream(req: QueryRequest):
    async def generate():
        async for chunk in rag.astream(req.question, req.top_k):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    os.makedirs("./docs", exist_ok=True)
    path = f"./docs/{file.filename}"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    n_chunks = rag.ingest(path)
    return {"message": f"已导入 {n_chunks} 个文档块", "filename": file.filename}

@app.get("/stats")
async def stats():
    return rag.get_stats()
```

## 4. 运行项目

```bash
# 安装依赖
pip install fastapi uvicorn langchain langchain-openai langchain-chroma
pip install python-multipart pypdf unstructured

# 导入文档
python -c "
from rag_engine import RAGEngine
rag = RAGEngine()
rag.ingest_directory('./docs')
"

# 启动服务
uvicorn app:app --reload --port 8000
```

## 5. 测试

```python
import requests

# 上传文档
with open("document.pdf", "rb") as f:
    resp = requests.post("http://localhost:8000/upload", files={"file": f})
    print(resp.json())

# 查询
resp = requests.post("http://localhost:8000/query", json={
    "question": "文档中提到了哪些关键概念？"
})
print(resp.json()["answer"])

# 流式查询
resp = requests.post("http://localhost:8000/query/stream", json={
    "question": "总结文档的主要内容"
}, stream=True)
for chunk in resp.iter_content(decode_unicode=True):
    print(chunk, end="", flush=True)
```

## 练习

1. 完成上述项目，导入至少 5 个文档
2. 添加混合检索（BM25 + 向量）
3. 实现对话历史功能（多轮问答）
4. 添加 Reranking 步骤并评估效果提升

## 阶段总结

本阶段你已掌握：
- ✅ RAG 架构与核心流程
- ✅ 检索优化（Multi-Query、HyDE、Reranking）
- ✅ 上下文与生成优化
- ✅ 完整 RAG 项目实战

→ 下一阶段：[stage-09 AI Agent 与工具调用](../stage-09-ai-agent/)
