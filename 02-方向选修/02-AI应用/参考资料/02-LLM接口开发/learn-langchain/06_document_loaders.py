import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第6课：文档加载与文本分割
==============================================================================

为什么需要文档加载和分割？
---------------------
AI 应用经常需要处理外部文档（PDF、Word、网页、代码文件等）。
但 LLM 有上下文长度限制，不能一次吃进一本书。

解决方案：
1. 文档加载（Document Loading）：把各种格式的文件读入内存
2. 文本分割（Text Splitting）：把长文档切成小块（chunk）
3. 每个小块可以独立做 Embedding 和检索（→ RAG）

本课核心组件：
- Document:          LangChain 中文档的统一表示
- DocumentLoader:    各种格式的加载器
- TextSplitter:      文本分割器

Document 结构：
  - page_content: str      文本内容
  - metadata: dict         元数据（来源、页码、日期等）
==============================================================================
"""

from langchain_core.documents import Document

print("=" * 60)
print("第6课：文档加载与文本分割")
print("=" * 60)

# ============================================================================
# 1. Document 对象
# ============================================================================
print("\n--- 1. Document 对象 ---")
print("""
Document 是 LangChain 中文档的统一表示。
无论原始格式是 PDF/Word/HTML，加载后都变成 Document 对象。

  Document(
      page_content="文本内容...",
      metadata={"source": "file.pdf", "page": 1}
  )
""")

# 手动创建 Document
doc = Document(
    page_content="LangChain 是一个用于构建 LLM 应用的框架。它提供了模型调用、Prompt 管理、记忆、检索等功能。",
    metadata={"source": "manual", "topic": "langchain", "author": "demo"}
)

print(f"内容: {doc.page_content[:50]}...")
print(f"元数据: {doc.metadata}")
print(f"内容长度: {len(doc.page_content)} 字符")

# ============================================================================
# 2. 文本文件加载器
# ============================================================================
print("\n--- 2. 文本文件加载器 ---")
print("""
TextLoader 是最基础的加载器，读取纯文本文件。

其他常用加载器：
┌─────────────────────┬────────────────────────────────┐
│  格式                │  加载器                         │
├─────────────────────┼────────────────────────────────┤
│  .txt               │  TextLoader                     │
│  .pdf               │  PyPDFLoader                    │
│  .docx              │  Docx2txtLoader                 │
│  .csv               │  CSVLoader                      │
│  .md                │  UnstructuredMarkdownLoader     │
│  .html              │  BSHTMLLoader                   │
│  .json              │  JSONLoader                     │
│  网页 URL            │  WebBaseLoader                  │
│  整个目录            │  DirectoryLoader                │
└─────────────────────┴────────────────────────────────┘
""")

# 2.1 创建示例文件用于演示
import os
import tempfile

demo_dir = tempfile.mkdtemp(prefix="langchain_demo_")

# 创建示例文本文件
sample_text = """# Python 设计模式

## 1. 单例模式（Singleton）

单例模式确保一个类只有一个实例，并提供全局访问点。

应用场景：
- 数据库连接池
- 配置管理器
- 日志记录器

```python
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

## 2. 工厂模式（Factory）

工厂模式定义一个创建对象的接口，让子类决定实例化哪个类。

应用场景：
- 根据配置创建不同的数据库连接
- 根据文件类型选择不同的解析器

## 3. 观察者模式（Observer）

观察者模式定义对象间的一对多依赖关系，
当一个对象状态改变时，所有依赖它的对象都会收到通知。

应用场景：
- 事件系统
- 消息订阅
- GUI 事件处理
"""

sample_file = os.path.join(demo_dir, "design_patterns.md")
with open(sample_file, "w", encoding="utf-8") as f:
    f.write(sample_text)

# 使用 TextLoader 加载
from langchain_community.document_loaders import TextLoader

loader = TextLoader(sample_file, encoding="utf-8")
docs = loader.load()

print(f"加载了 {len(docs)} 个文档")
print(f"  内容长度: {len(docs[0].page_content)} 字符")
print(f"  元数据: {docs[0].metadata}")
print(f"  前100字: {docs[0].page_content[:100]}...")

# 2.2 创建多个文件，演示 DirectoryLoader
for i, topic in enumerate(["变量和类型", "函数和模块", "面向对象"]):
    filepath = os.path.join(demo_dir, f"lesson_{i+1}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# 第{i+1}课: {topic}\n\n这是关于{topic}的详细内容。\n" * 3)

from langchain_community.document_loaders import DirectoryLoader

dir_loader = DirectoryLoader(
    demo_dir,
    glob="**/*.txt",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
)
dir_docs = dir_loader.load()
print(f"\n目录加载: 共 {len(dir_docs)} 个文档")
for doc in dir_docs:
    print(f"  {os.path.basename(doc.metadata['source'])}: {len(doc.page_content)} 字符")

# ============================================================================
# 3. RecursiveCharacterTextSplitter（最常用的分割器）
# ============================================================================
print("\n--- 3. RecursiveCharacterTextSplitter ---")
print("""
递归字符分割器的工作方式：
1. 尝试按第一个分隔符（如 \\n\\n）分割
2. 如果块仍然太大，用下一个分隔符（如 \\n）继续分
3. 依次尝试，直到块大小满足要求

参数：
- chunk_size:    每块的最大字符数（核心参数）
- chunk_overlap: 相邻块的重叠字符数（防止信息丢失）
- separators:    分隔符优先级列表
""")

from langchain_text_splitters import RecursiveCharacterTextSplitter

# 3.1 基本用法
splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,         # 每块最多200字符
    chunk_overlap=30,       # 相邻块重叠30字符
    separators=["\n\n", "\n", "。", ".", " ", ""],
    length_function=len,
)

chunks = splitter.split_text(sample_text)

print(f"原文长度: {len(sample_text)} 字符")
print(f"分割为: {len(chunks)} 块")
print()
for i, chunk in enumerate(chunks):
    print(f"  Chunk {i}: [{len(chunk):3d}字符] {chunk[:60].replace(chr(10), '↵')}...")

# 3.2 分割 Document 对象（保留元数据）
doc_chunks = splitter.split_documents(docs)
print(f"\n分割 Document: {len(docs)} 个文档 → {len(doc_chunks)} 块")
for i, chunk in enumerate(doc_chunks[:3]):
    print(f"  Chunk {i}: [{len(chunk.page_content):3d}字符] 元数据={chunk.metadata}")

# ============================================================================
# 4. 不同的分割策略
# ============================================================================
print("\n--- 4. 不同的分割策略 ---")

# 4.1 按字符分割（不推荐，太粗暴）
from langchain_text_splitters import CharacterTextSplitter

char_splitter = CharacterTextSplitter(
    separator="\n\n",
    chunk_size=200,
    chunk_overlap=0,
)
char_chunks = char_splitter.split_text(sample_text)
print(f"[CharacterTextSplitter] {len(char_chunks)} 块")

# 4.2 按 Markdown 标题分割（结构化文档推荐）
from langchain_text_splitters import MarkdownHeaderTextSplitter

md_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ]
)
md_chunks = md_splitter.split_text(sample_text)
print(f"\n[MarkdownHeaderTextSplitter] {len(md_chunks)} 块")
for i, chunk in enumerate(md_chunks):
    print(f"  Chunk {i}: 标题={chunk.metadata}, 内容={chunk.page_content[:50].replace(chr(10), '↵')}...")

# 4.3 按 Token 分割（精确控制 token 数）
from langchain_text_splitters import TokenTextSplitter

token_splitter = TokenTextSplitter(
    chunk_size=100,      # 每块100个token
    chunk_overlap=10,
)
token_chunks = token_splitter.split_text(sample_text)
print(f"\n[TokenTextSplitter] {len(token_chunks)} 块")

# ============================================================================
# 5. chunk_size 选择指南
# ============================================================================
print("\n--- 5. chunk_size 选择指南 ---")
print("""
chunk_size 的选择直接影响 RAG 的质量：

┌──────────────┬──────────────────────────────────────┐
│  chunk_size  │  特点                                 │
├──────────────┼──────────────────────────────────────┤
│  < 100       │  太小，语义不完整，检索噪音多          │
│  100 - 300   │  适合精确匹配的FAQ场景                 │
│  300 - 500   │  通用推荐，平衡精度和完整性             │
│  500 - 1000  │  适合长文档，每块信息量大               │
│  > 1000      │  太大，检索精度下降                    │
└──────────────┴──────────────────────────────────────┘

chunk_overlap：
- 通常为 chunk_size 的 10-20%
- 作用：确保跨块信息不丢失（如一个句子被切成两半）

最佳实践：
1. 先用 300-500 开始
2. 评估检索效果
3. 根据结果调整
""")

# 演示不同 chunk_size 的效果
for size in [100, 300, 500, 1000]:
    s = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=int(size * 0.15))
    chunks = s.split_text(sample_text)
    avg_len = sum(len(c) for c in chunks) / len(chunks) if chunks else 0
    print(f"  chunk_size={size:4d}: {len(chunks):2d} 块, 平均 {avg_len:.0f} 字符/块")

# ============================================================================
# 6. 实用工具：自定义文档处理流水线
# ============================================================================
print("\n--- 6. 自定义文档处理流水线 ---")

class DocumentPipeline:
    """文档处理流水线：加载 → 清洗 → 分割 → 输出"""

    def __init__(self, chunk_size=400, chunk_overlap=50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
        )

    def clean_text(self, text: str) -> str:
        """清洗文本"""
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)  # 多余空行
        text = re.sub(r' {2,}', ' ', text)       # 多余空格
        return text.strip()

    def process_file(self, file_path: str) -> list[Document]:
        """处理单个文件"""
        loader = TextLoader(file_path, encoding="utf-8")
        docs = loader.load()

        # 清洗
        for doc in docs:
            doc.page_content = self.clean_text(doc.page_content)
            doc.metadata["char_count"] = len(doc.page_content)

        # 分割
        chunks = self.splitter.split_documents(docs)

        # 为每个块添加索引
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)

        return chunks

    def process_directory(self, dir_path: str, glob="**/*.txt") -> list[Document]:
        """处理整个目录"""
        all_chunks = []
        for root, _, files in os.walk(dir_path):
            for f in files:
                if f.endswith(('.txt', '.md')):
                    filepath = os.path.join(root, f)
                    try:
                        chunks = self.process_file(filepath)
                        all_chunks.extend(chunks)
                        print(f"  ✓ {f}: {len(chunks)} 块")
                    except Exception as e:
                        print(f"  ✗ {f}: {e}")
        return all_chunks

# 使用
pipeline = DocumentPipeline(chunk_size=200, chunk_overlap=30)
all_chunks = pipeline.process_directory(demo_dir)

print(f"\n总计: {len(all_chunks)} 块")
for chunk in all_chunks[:3]:
    print(f"  [{chunk.metadata.get('chunk_index', '?')}/{chunk.metadata.get('total_chunks', '?')}] "
          f"{chunk.page_content[:50].replace(chr(10), '↵')}...")

# 清理临时文件
import shutil
shutil.rmtree(demo_dir)

print("\n" + "=" * 60)
print("[完成] 第6课完成！你已经学会了：")
print("  [v] Document 对象结构")
print("  [v] TextLoader / DirectoryLoader 加载文件")
print("  [v] RecursiveCharacterTextSplitter 递归分割")
print("  [v] MarkdownHeaderTextSplitter 结构化分割")
print("  [v] TokenTextSplitter 按 token 分割")
print("  [v] chunk_size 选择策略")
print("  [v] 自定义文档处理流水线")
print("=" * 60)
print("\n下一课：07_retrievers_vectorstore.py - 向量存储与检索器")
