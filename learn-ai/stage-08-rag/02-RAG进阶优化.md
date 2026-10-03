# RAG 进阶优化

## 学习目标

- 掌握 RAG 各环节的优化技巧
- 学会 Query 改写、Multi-Query、Parent-Child 等高级策略
- 实现生产级 RAG 系统

## 1. RAG 优化全景

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Query 优化│ → │ 检索优化  │ → │ 上下文优化│ → │ 生成优化  │
├──────────┤   ├──────────┤   ├──────────┤   ├──────────┤
│ Query 改写│   │ 混合检索  │   │ 重排序    │   │ 引用来源  │
│ Multi-Query│  │ 元数据过滤│   │ 上下文压缩│   │ 自一致性  │
│ HyDE      │   │ 递归检索  │   │ 窗口扩展  │   │ 答案验证  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
```

## 2. Query 优化

### Multi-Query（多查询）

```python
from langchain.retrievers import MultiQueryRetriever
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

multi_retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    llm=llm,
)

# "RAG 是什么？" → 自动生成多个变体查询：
# - "什么是检索增强生成技术？"
# - "RAG 的工作原理是怎样的？"
# - "Retrieval-Augmented Generation 有什么应用？"
docs = multi_retriever.invoke("RAG 是什么？")
```

### HyDE（假设文档嵌入）

先让 LLM 生成假设答案，用假设答案去检索。

```python
from langchain.chains import HypotheticalDocumentEmbedder

hyde_embeddings = HypotheticalDocumentEmbedder.from_llm(
    llm=ChatOpenAI(model="gpt-4o-mini"),
    base_embeddings=OpenAIEmbeddings(),
    prompt_key="web_search",
)
# 问题 → LLM 生成假设答案 → embedding → 检索
# 优势：假设答案的 embedding 与真实文档更接近
```

### Query 改写

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", """将用户的问题改写为更适合向量检索的形式。
保持原意，补充上下文，使用精确关键词。只输出改写后的查询。"""),
    ("user", "{question}"),
])

rewrite_chain = rewrite_prompt | llm | StrOutputParser()
# "RAG 咋用？" → "如何使用 RAG 检索增强生成技术构建知识问答系统？"
```

## 3. 检索优化

### Parent-Child 检索

小块精确检索，返回大块完整上下文。

```python
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)

store = InMemoryStore()
parent_retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)
parent_retriever.add_documents(docs)

# 用 child chunk 匹配，返回 parent chunk（上下文更完整）
results = parent_retriever.invoke("查询内容")
```

### 自查询（Self-Query）

LLM 自动从问题中提取过滤条件。

```python
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.schema import AttributeInfo

metadata_field_info = [
    AttributeInfo(name="source", description="文档来源", type="string"),
    AttributeInfo(name="date", description="文档日期", type="string"),
]

self_query_retriever = SelfQueryRetriever.from_llm(
    llm=llm,
    vectorstore=vectorstore,
    document_contents="技术文档",
    metadata_field_info=metadata_field_info,
)
# "2024年关于RAG的论文" → 自动提取 date过滤 + 语义搜索 "RAG论文"
```

## 4. 上下文优化

### 上下文压缩

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

compressor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever,
)
# 只保留与问题相关的段落，去除无关信息
```

### Lost in the Middle 问题

LLM 对上下文中间部分的信息关注度低。

```python
def reorder_documents(docs):
    """将最相关的文档放在首尾，不太相关的放中间"""
    reordered = []
    for i, doc in enumerate(docs):
        if i % 2 == 0:
            reordered.insert(0, doc)  # 偶数位插入开头
        else:
            reordered.append(doc)      # 奇数位追加末尾
    return reordered
```

## 5. 生成优化

### 引用来源

```python
rag_prompt_with_citation = ChatPromptTemplate.from_messages([
    ("system", """根据上下文回答问题。每个关键论述后用 [来源X] 标注出处。

上下文：
{context}

如果无法回答，说明原因。"""),
    ("user", "{question}"),
])
```

### 答案验证（Hallucination Check）

```python
verify_prompt = ChatPromptTemplate.from_messages([
    ("system", """判断以下回答是否完全基于给定的上下文。
上下文：{context}
回答：{answer}

输出 JSON：{{"is_grounded": true/false, "unsupported_claims": ["..."]}}"""),
    ("user", "请验证"),
])
```

## 6. RAG 评估

```python
# 评估维度
# 1. 检索质量：召回率、精确率、MRR
# 2. 生成质量：忠实度、相关性、完整性

# 使用 RAGAS 框架评估
# pip install ragas
from ragas import evaluate
from ragas.metrics import (
    faithfulness,       # 忠实度：回答是否基于检索内容
    answer_relevancy,   # 相关性：回答是否切题
    context_precision,  # 精确率：检索内容是否相关
    context_recall,     # 召回率：是否检索到所有必要信息
)

result = evaluate(
    dataset=eval_dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
)
print(result)
```

## 7. 生产级 RAG 检查清单

```
□ 文档加载器支持多格式（PDF/Word/Markdown/HTML）
□ 分块策略适配文档类型
□ 混合检索（向量 + 关键词）
□ Reranking 重排序
□ Query 改写/扩展
□ 上下文长度控制
□ 引用来源标注
□ 幻觉检测
□ 流式输出
□ 缓存常见问题
□ 日志与监控
□ 评估指标跟踪
```

## 练习

1. 实现 Multi-Query RAG，对比单查询的检索效果
2. 实现 Parent-Child 检索策略
3. 添加 Reranking 步骤，评估对结果质量的影响
4. 用 RAGAS 评估你的 RAG 系统各项指标

## 下一节

→ [03-RAG项目实战](03-RAG项目实战.md)
