import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第7课：向量存储与检索器
==============================================================================

什么是向量存储（VectorStore）？
----------------------------
向量存储是专门用来存储和检索"向量"的数据库。

工作流程：
  文本 → Embedding模型 → 向量 → 存入VectorStore
  查询 → Embedding模型 → 向量 → 在VectorStore中找最近的向量 → 返回原文

LangChain 的向量存储抽象：
- 统一接口：不管底层用 Chroma/FAISS/Milvus，代码都一样
- 自动 Embedding：传入文本，自动调用 Embedding 模型转换
- 检索器接口：.as_retriever() 无缝接入 LCEL 链

本课使用 ChromaDB（轻量、零配置、适合学习）。

检索器（Retriever）：
- 向量存储的"查询接口"
- 输入：查询字符串
- 输出：相关的 Document 列表
==============================================================================
"""

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.chat_models import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

llm = ChatOllama(model="qwen2.5:7b", temperature=0)

print("=" * 60)
print("第7课：向量存储与检索器")
print("=" * 60)

# ============================================================================
# 1. Embedding 模型
# ============================================================================
print("\n--- 1. Embedding 模型 ---")
print("""
Embedding 模型把文本转为向量（一组浮点数）。
语义相近的文本 → 向量距离近。

LangChain 支持多种 Embedding：
┌────────────────────────┬─────────────────────────────┐
│  来源                   │  类                          │
├────────────────────────┼─────────────────────────────┤
│  OpenAI                │  OpenAIEmbeddings            │
│  Ollama（本地免费）     │  OllamaEmbeddings            │
│  HuggingFace（本地）   │  HuggingFaceEmbeddings       │
│  Sentence Transformers │  SentenceTransformerEmbeddings│
└────────────────────────┴─────────────────────────────┘
""")

# 使用 Ollama Embedding（本地免费）
# 需要先: ollama pull nomic-embed-text
from langchain_community.embeddings import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="nomic-embed-text")

# 测试 Embedding
text = "LangChain 是构建 LLM 应用的框架"
vector = embeddings.embed_query(text)
print(f"文本: {text}")
print(f"向量维度: {len(vector)}")
print(f"前5个值: {vector[:5]}")

# 批量 Embedding
texts = ["Python 编程", "机器学习", "做饭技巧"]
vectors = embeddings.embed_documents(texts)
print(f"\n批量 Embedding: {len(vectors)} 个文本 → {len(vectors)} 个向量")

# 计算相似度
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

sim_01 = cosine_similarity(vectors[0], vectors[1])  # Python vs ML
sim_02 = cosine_similarity(vectors[0], vectors[2])  # Python vs 做饭
print(f"\n'Python编程' vs '机器学习': {sim_01:.4f}（较高，都是技术）")
print(f"'Python编程' vs '做饭技巧': {sim_02:.4f}（较低，不相关）")

# ============================================================================
# 2. ChromaDB 向量存储
# ============================================================================
print("\n--- 2. ChromaDB 向量存储 ---")
print("""
ChromaDB 特点：
- 零配置，开箱即用
- 支持内存和持久化两种模式
- 内置元数据过滤
- 与 LangChain 深度集成
""")

from langchain_chroma import Chroma

# 准备示例文档
documents = [
    Document(page_content="Python 是一种通用编程语言，以简洁易读著称。广泛用于 Web 开发、数据分析、AI 等领域。",
             metadata={"topic": "python", "level": "beginner"}),
    Document(page_content="FastAPI 是一个现代的 Python Web 框架，基于类型注解自动生成文档，性能极高。",
             metadata={"topic": "python", "level": "intermediate"}),
    Document(page_content="PyTorch 是 Facebook 开发的深度学习框架，以动态计算图和 Pythonic 的 API 著称。",
             metadata={"topic": "deep_learning", "level": "intermediate"}),
    Document(page_content="LangChain 是一个用于构建 LLM 应用的框架，提供了 Prompt 管理、链、记忆、检索等核心功能。",
             metadata={"topic": "llm", "level": "intermediate"}),
    Document(page_content="向量数据库用于存储和检索高维向量，是 RAG 系统的核心组件。常用的有 Chroma、FAISS、Milvus。",
             metadata={"topic": "llm", "level": "advanced"}),
    Document(page_content="机器学习是 AI 的子领域，让计算机从数据中学习规律，而非显式编程。",
             metadata={"topic": "machine_learning", "level": "beginner"}),
    Document(page_content="Transformer 是一种基于注意力机制的神经网络架构，是所有现代大语言模型的基础。",
             metadata={"topic": "deep_learning", "level": "advanced"}),
    Document(page_content="RAG（检索增强生成）通过检索外部知识库来增强 LLM 的回答，减少幻觉问题。",
             metadata={"topic": "llm", "level": "advanced"}),
]

# 2.1 创建内存向量存储（数据不持久化）
vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    collection_name="demo_collection",
)

print(f"向量存储创建完成，包含 {vectorstore._collection.count()} 个文档")

# 2.2 基本相似度搜索
results = vectorstore.similarity_search("什么是深度学习框架？", k=3)
print(f"\n查询: '什么是深度学习框架？'  Top-3:")
for i, doc in enumerate(results):
    print(f"  {i+1}. [{doc.metadata['topic']}] {doc.page_content[:50]}...")

# 2.3 带分数的搜索
results_with_scores = vectorstore.similarity_search_with_score("Python Web 开发", k=3)
print(f"\n查询: 'Python Web 开发'  Top-3（带距离分数）:")
for doc, score in results_with_scores:
    print(f"  距离={score:.4f} | {doc.page_content[:50]}...")

# ============================================================================
# 3. 元数据过滤
# ============================================================================
print("\n--- 3. 元数据过滤 ---")
print("""
不只按语义搜索，还可以按元数据字段过滤。
例如：只搜索 topic="llm" 的文档。
""")

# 只搜索 LLM 相关文档
results = vectorstore.similarity_search(
    "如何构建 AI 应用？",
    k=3,
    filter={"topic": "llm"},
)
print(f"查询 + 过滤(topic=llm):")
for doc in results:
    print(f"  [{doc.metadata['topic']}|{doc.metadata['level']}] {doc.page_content[:50]}...")

# 只搜索初级内容
results = vectorstore.similarity_search(
    "编程入门",
    k=3,
    filter={"level": "beginner"},
)
print(f"\n查询 + 过滤(level=beginner):")
for doc in results:
    print(f"  [{doc.metadata['topic']}|{doc.metadata['level']}] {doc.page_content[:50]}...")

# ============================================================================
# 4. 检索器（Retriever）
# ============================================================================
print("\n--- 4. 检索器（Retriever）---")
print("""
Retriever 是向量存储的"查询封装"，可以直接接入 LCEL 链。

  vectorstore.as_retriever()  → Retriever 对象
  retriever.invoke("查询")    → [Document, Document, ...]

常用检索参数：
- search_type: "similarity"（默认）或 "mmr"（多样性）
- search_kwargs: {"k": 5, "filter": {...}}
""")

# 4.1 基本检索器
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3},
)

docs = retriever.invoke("LLM 应用开发")
print(f"检索 'LLM 应用开发':")
for doc in docs:
    print(f"  → {doc.page_content[:60]}...")

# 4.2 MMR 检索（Maximum Marginal Relevance）
# MMR 在保持相关性的同时增加结果多样性
mmr_retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 3, "fetch_k": 6},  # 先取6个，再从中选3个最多样的
)

docs_mmr = mmr_retriever.invoke("AI 技术")
print(f"\nMMR 检索 'AI 技术'（结果更多样）:")
for doc in docs_mmr:
    print(f"  → [{doc.metadata['topic']}] {doc.page_content[:50]}...")

# 4.3 带过滤的检索器
filtered_retriever = vectorstore.as_retriever(
    search_kwargs={"k": 3, "filter": {"topic": "llm"}},
)

docs_filtered = filtered_retriever.invoke("AI")
print(f"\n带过滤检索(topic=llm):")
for doc in docs_filtered:
    print(f"  → [{doc.metadata['topic']}] {doc.page_content[:50]}...")

# ============================================================================
# 5. 检索器 + LLM = 简单 RAG
# ============================================================================
print("\n--- 5. 检索器 + LLM = 简单 RAG ---")
print("""
最经典的 RAG 链：

  用户问题 → 检索相关文档 → 拼入 Prompt → LLM 回答

用 LCEL 表示：
  {"context": retriever, "question": passthrough} | prompt | llm | parser
""")

def format_docs(docs):
    """将检索到的文档格式化为字符串"""
    return "\n\n".join(
        f"[来源: {doc.metadata.get('topic', '未知')}] {doc.page_content}"
        for doc in docs
    )

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个技术知识助手。根据以下检索到的上下文回答问题。
规则：只基于上下文回答，如果上下文中没有相关信息，请说"我没有找到相关信息"。

上下文：
{context}"""),
    ("human", "{question}"),
])

# 组装 RAG 链
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | rag_prompt
    | llm
    | StrOutputParser()
)

# 测试
questions = [
    "LangChain 有什么功能？",
    "什么是 RAG？",
    "如何做蛋炒饭？",  # 故意问一个文档中没有的问题
]

for q in questions:
    answer = rag_chain.invoke(q)
    print(f"\nQ: {q}")
    print(f"A: {answer[:120]}...")

# ============================================================================
# 6. 持久化存储
# ============================================================================
print("\n--- 6. 持久化存储 ---")
print("""
内存模式：程序结束数据就丢失
持久化模式：数据保存到磁盘，下次启动还在

  # 创建持久化存储
  vectorstore = Chroma.from_documents(
      documents, embeddings,
      persist_directory="./chroma_data"
  )
  
  # 加载已有存储
  vectorstore = Chroma(
      persist_directory="./chroma_data",
      embedding_function=embeddings
  )
""")

import tempfile
persist_dir = tempfile.mkdtemp(prefix="chroma_persist_")

# 创建持久化存储
persistent_store = Chroma.from_documents(
    documents=documents[:3],
    embedding=embeddings,
    persist_directory=persist_dir,
)
print(f"持久化存储创建: {persistent_store._collection.count()} 个文档")

# 模拟重新加载
loaded_store = Chroma(
    persist_directory=persist_dir,
    embedding_function=embeddings,
)
print(f"重新加载: {loaded_store._collection.count()} 个文档")

# 追加文档
loaded_store.add_documents(documents[3:5])
print(f"追加后: {loaded_store._collection.count()} 个文档")

# 清理
import shutil
shutil.rmtree(persist_dir)

# ============================================================================
# 7. 向量存储操作汇总
# ============================================================================
print("\n--- 7. 操作汇总 ---")
print("""
┌──────────────────────────┬──────────────────────────────────┐
│  操作                     │  方法                             │
├──────────────────────────┼──────────────────────────────────┤
│  从文档创建               │  Chroma.from_documents(docs, emb) │
│  添加文档                 │  store.add_documents(docs)        │
│  相似度搜索               │  store.similarity_search(q, k=5)  │
│  带分数搜索               │  store.similarity_search_with_score│
│  转为检索器               │  store.as_retriever()             │
│  删除文档                 │  store.delete(ids=[...])          │
│  获取文档数               │  store._collection.count()        │
└──────────────────────────┴──────────────────────────────────┘
""")

print("\n" + "=" * 60)
print("[完成] 第7课完成！你已经学会了：")
print("  [v] Embedding 模型的使用")
print("  [v] ChromaDB 向量存储（创建/查询/持久化）")
print("  [v] 元数据过滤搜索")
print("  [v] Retriever 检索器（similarity/MMR）")
print("  [v] 检索器 + LLM = 简单 RAG")
print("  [v] 持久化存储与加载")
print("=" * 60)
print("\n下一课：08_rag_project.py - 完整项目：RAG 知识库问答")
