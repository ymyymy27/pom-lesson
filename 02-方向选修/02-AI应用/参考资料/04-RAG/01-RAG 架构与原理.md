> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# RAG 架构与原理

## 学习目标

- 深入理解 RAG（Retrieval-Augmented Generation）的架构
- 掌握 RAG 的核心流程和各环节优化策略
- 了解 RAG 与微调的区别和组合方式

## 1. 什么是 RAG

RAG = 检索（Retrieval）+ 生成（Generation），让 LLM 基于检索到的外部知识进行回答。

```
用户问题 → 向量化 → 向量数据库检索 → 获取相关文档片段 → 拼入 Prompt → LLM 生成回答

解决的问题：
- LLM 知识截止日期
- 减少幻觉（有据可查）
- 私域知识问答
- 无需微调即可注入知识
```

## 2. RAG 核心流程

```
┌─────────────────── 离线索引阶段 ───────────────────┐
│                                                      │
│  文档加载 → 文本分块 → Embedding → 存入向量数据库     │
│                                                      │
└──────────────────────────────────────────────────────┘

┌─────────────────── 在线查询阶段 ───────────────────┐
│                                                      │
│  用户问题 → Query Embedding → 向量检索 → 重排序      │
│     ↓                                                │
│  构建 Prompt（问题 + 检索结果） → LLM 生成 → 回答    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## 3. 文档加载

```python
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
    UnstructuredMarkdownLoader,
    WebBaseLoader,
    DirectoryLoader,
)

# 文本文件
loader = TextLoader("document.txt", encoding="utf-8")
docs = loader.load()

# PDF
loader = PyPDFLoader("paper.pdf")
docs = loader.load()  # 每页一个 Document

# Word
loader = Docx2txtLoader("report.docx")
docs = loader.load()

# CSV
loader = CSVLoader("data.csv", encoding="utf-8")
docs = loader.load()

# Markdown
loader = UnstructuredMarkdownLoader("README.md")
docs = loader.load()

# 网页
loader = WebBaseLoader("https://example.com/article")
docs = loader.load()

# 整个目录
loader = DirectoryLoader("./docs/", glob="**/*.md", loader_cls=TextLoader)
docs = loader.load()
print(f"加载了 {len(docs)} 个文档")
```

## 4. 文本分块策略

```python
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    TokenTextSplitter,
)

# 1. 递归字符分割（最通用）
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "！", "？", "；", ".", " ", ""],
    length_function=len,
)
chunks = splitter.split_documents(docs)

# 2. Markdown 结构化分割
headers_to_split = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]
md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split)
md_chunks = md_splitter.split_text(markdown_text)

# 3. Token 分割（精确控制 token 数）
token_splitter = TokenTextSplitter(chunk_size=256, chunk_overlap=32)
token_chunks = token_splitter.split_documents(docs)

# 查看分块结果
for i, chunk in enumerate(chunks[:3]):
    print(f"--- Chunk {i} ({len(chunk.page_content)} chars) ---")
    print(chunk.page_content[:100])
    print(f"Metadata: {chunk.metadata}")
```

## 5. 检索策略

### 基础向量检索

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# 构建向量库
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="./db")

# 相似度检索
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5},
)
docs = retriever.invoke("什么是 RAG？")
```

### 混合检索（向量 + 关键词）

```python
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

# BM25 关键词检索
bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 5

# 向量检索
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# 混合（加权融合）
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.4, 0.6],  # 关键词 40%，语义 60%
)
docs = ensemble_retriever.invoke("RAG 的检索策略")
```

### 重排序（Reranking）

```python
# 用 Cross-Encoder 对检索结果重排序
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker

# 加载 reranker 模型
cross_encoder = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")
compressor = CrossEncoderReranker(model=cross_encoder, top_n=3)

# 先检索再重排
rerank_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vector_retriever,
)
docs = rerank_retriever.invoke("什么是 RAG？")
```

## 6. Prompt 构建

```python
from langchain_core.prompts import ChatPromptTemplate

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的知识问答助手。请根据以下检索到的上下文回答用户的问题。

规则：
1. 只基于提供的上下文回答，不要编造信息
2. 如果上下文中没有相关信息，请明确说"根据已有资料，我无法回答这个问题"
3. 回答要准确、简洁、有条理
4. 适当引用来源

上下文：
{context}"""),
    ("user", "{question}"),
])
```

## 7. 完整 RAG Pipeline

```python
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

def format_docs(docs):
    return "\n\n".join(
        f"[来源: {d.metadata.get('source', '未知')}]\n{d.page_content}"
        for d in docs
    )

# 组装 RAG 链
llm = ChatOpenAI(model="gpt-4o", temperature=0)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | rag_prompt
    | llm
    | StrOutputParser()
)

# 使用
answer = rag_chain.invoke("RAG 和微调有什么区别？")
print(answer)

# 流式输出
for chunk in rag_chain.stream("如何优化 RAG 的检索质量？"):
    print(chunk, end="", flush=True)
```

## 练习

1. 加载 3 个不同格式的文档（PDF、Markdown、TXT），构建向量库
2. 实现一个完整的 RAG Pipeline，能正确回答文档中的问题
3. 对比纯向量检索 vs 混合检索的效果
4. 测试当问题超出文档范围时，模型是否会说"不知道"

## 下一节

→ [02-RAG进阶优化](<02-RAG 进阶优化.md>)
