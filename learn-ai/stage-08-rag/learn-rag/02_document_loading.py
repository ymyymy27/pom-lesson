import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第2课：文档加载与解析
==============================================================================

RAG 的第一步：把各种格式的文档加载进来。
支持 PDF、Word、Markdown、CSV、HTML、网页等。

本课内容：
1. 文档加载概述
2. 文本文件加载
3. Markdown 结构化解析
4. PDF 加载策略
5. 网页与 CSV 加载
6. 自定义文档加载器
==============================================================================
"""

import json
import os
import re
import tempfile

print("=" * 60)
print("第2课：文档加载")
print("=" * 60)

# ============================================================================
# 1. 文档加载概述
# ============================================================================
print("\n--- 1. 概述 ---")
print("""
文档加载 = 从各种格式文件中提取纯文本 + 元数据

  ┌──────────┐
  │  PDF     │──→ 文本 + 页码
  │  Word    │──→ 文本 + 段落
  │  Markdown│──→ 文本 + 标题层级
  │  CSV     │──→ 每行一条
  │  HTML    │──→ 去标签后文本
  │  网页    │──→ 抓取+提取
  └──────────┘
       ↓
  Document(page_content="...", metadata={...})

LangChain 提供的加载器：
```python
from langchain_community.document_loaders import (
    TextLoader,          # .txt
    PyPDFLoader,         # .pdf
    Docx2txtLoader,      # .docx
    CSVLoader,           # .csv
    UnstructuredMarkdownLoader,  # .md
    WebBaseLoader,       # 网页
    DirectoryLoader,     # 整个目录
)
```

我们这里用纯 Python 实现，不依赖 LangChain。
""")

# ============================================================================
# 2. 文本文件加载
# ============================================================================
print("\n--- 2. 文本加载 ---")

class Document:
    """文档对象（模拟 LangChain Document）"""
    def __init__(self, page_content: str, metadata: dict = None):
        self.page_content = page_content
        self.metadata = metadata or {}

    def __repr__(self):
        return f"Document(len={len(self.page_content)}, meta={self.metadata})"

class TextFileLoader:
    """文本文件加载器"""

    def __init__(self, file_path: str, encoding: str = "utf-8"):
        self.file_path = file_path
        self.encoding = encoding

    def load(self) -> list:
        with open(self.file_path, "r", encoding=self.encoding) as f:
            content = f.read()
        return [Document(
            page_content=content,
            metadata={"source": self.file_path, "type": "text"}
        )]

# 创建测试文件
temp_dir = tempfile.mkdtemp(prefix="rag_docs_")

txt_path = os.path.join(temp_dir, "sample.txt")
with open(txt_path, "w", encoding="utf-8") as f:
    f.write("""Python 编程语言

Python 是一种高级通用编程语言。它支持多种编程范式，包括面向对象、函数式和过程式编程。

Python 的核心设计哲学是代码可读性和简洁性。它使用缩进来定义代码块，而不是大括号。

Python 广泛应用于 Web 开发、数据科学、人工智能、自动化等领域。""")

loader = TextFileLoader(txt_path)
docs = loader.load()
print(f"文本加载: {docs[0]}")
print(f"  内容前50字: {docs[0].page_content[:50]}...")

# ============================================================================
# 3. Markdown 加载
# ============================================================================
print("\n--- 3. Markdown ---")

class MarkdownLoader:
    """Markdown 文件加载器（按标题拆分）"""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> list:
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return [Document(
            page_content=content,
            metadata={"source": self.file_path, "type": "markdown"}
        )]

    def load_by_headers(self) -> list:
        """按标题拆分为多个文档"""
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        docs = []
        sections = re.split(r'\n(#{1,3}\s+.+)\n', content)

        current_header = ""
        current_content = ""
        header_level = 0

        for part in sections:
            header_match = re.match(r'^(#{1,3})\s+(.+)$', part.strip())
            if header_match:
                if current_content.strip():
                    docs.append(Document(
                        page_content=current_content.strip(),
                        metadata={
                            "source": self.file_path,
                            "header": current_header,
                            "level": header_level,
                        }
                    ))
                current_header = header_match.group(2)
                header_level = len(header_match.group(1))
                current_content = f"{'#' * header_level} {current_header}\n"
            else:
                current_content += part

        if current_content.strip():
            docs.append(Document(
                page_content=current_content.strip(),
                metadata={"source": self.file_path, "header": current_header, "level": header_level}
            ))

        return docs

md_path = os.path.join(temp_dir, "sample.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write("""# 机器学习入门

机器学习是人工智能的一个子领域。

## 监督学习

监督学习使用标注数据训练模型。常见算法包括线性回归、决策树。

## 无监督学习

无监督学习从无标注数据中发现模式。常见方法有聚类和降维。

## 深度学习

深度学习使用多层神经网络。CNN 处理图像，Transformer 处理文本。
""")

md_loader = MarkdownLoader(md_path)
md_docs = md_loader.load_by_headers()
print(f"Markdown 按标题拆分: {len(md_docs)} 段")
for doc in md_docs:
    print(f"  [{doc.metadata.get('header', 'intro')[:20]}] {doc.page_content[:40]}...")

# ============================================================================
# 4. CSV 加载
# ============================================================================
print("\n--- 4. CSV ---")

class CSVDocLoader:
    """CSV 加载器"""

    def __init__(self, file_path: str, content_columns: list = None,
                 metadata_columns: list = None):
        self.file_path = file_path
        self.content_columns = content_columns
        self.metadata_columns = metadata_columns

    def load(self) -> list:
        import csv
        docs = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if self.content_columns:
                    content = " | ".join(f"{col}: {row[col]}" for col in self.content_columns if col in row)
                else:
                    content = " | ".join(f"{k}: {v}" for k, v in row.items())

                metadata = {"source": self.file_path, "row": i}
                if self.metadata_columns:
                    for col in self.metadata_columns:
                        if col in row:
                            metadata[col] = row[col]

                docs.append(Document(page_content=content, metadata=metadata))
        return docs

csv_path = os.path.join(temp_dir, "faq.csv")
with open(csv_path, "w", encoding="utf-8") as f:
    f.write("question,answer,category\n")
    f.write("退款多久到账,3-5个工作日,售后\n")
    f.write("如何修改地址,订单详情页修改,物流\n")
    f.write("能开发票吗,支持电子和纸质发票,财务\n")

csv_loader = CSVDocLoader(csv_path, content_columns=["question", "answer"], metadata_columns=["category"])
csv_docs = csv_loader.load()
print(f"CSV 加载: {len(csv_docs)} 条")
for doc in csv_docs:
    print(f"  [{doc.metadata.get('category')}] {doc.page_content}")

# ============================================================================
# 5. 目录批量加载
# ============================================================================
print("\n--- 5. 目录加载 ---")

class DirectoryDocLoader:
    """目录批量加载器"""

    LOADER_MAP = {
        ".txt": TextFileLoader,
        ".md": MarkdownLoader,
    }

    def __init__(self, dir_path: str, glob: str = "*"):
        self.dir_path = dir_path
        self.glob = glob

    def load(self) -> list:
        all_docs = []
        for root, _, files in os.walk(self.dir_path):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                loader_cls = self.LOADER_MAP.get(ext)
                if not loader_cls:
                    continue
                path = os.path.join(root, filename)
                try:
                    loader = loader_cls(path)
                    docs = loader.load()
                    all_docs.extend(docs)
                except Exception as e:
                    print(f"  ⚠ 跳过 {filename}: {e}")
        return all_docs

dir_loader = DirectoryDocLoader(temp_dir)
all_docs = dir_loader.load()
print(f"目录加载: {len(all_docs)} 个文档")
for doc in all_docs:
    print(f"  {doc.metadata.get('source', '?').split(os.sep)[-1]}: {len(doc.page_content)}字")

# ============================================================================
# 6. 自定义加载器
# ============================================================================
print("\n--- 6. 自定义加载器 ---")
print("""
自定义加载器模板：

```python
class MyCustomLoader:
    def __init__(self, source):
        self.source = source

    def load(self) -> list[Document]:
        # 1. 读取/获取数据
        raw_data = self._fetch_data()

        # 2. 解析为 Document
        docs = []
        for item in raw_data:
            docs.append(Document(
                page_content=item["text"],
                metadata={"source": self.source, ...}
            ))
        return docs

    def _fetch_data(self):
        ...
```

常见自定义场景：
  • 数据库加载器（SQL查询结果→文档）
  • API 加载器（REST API→文档）
  • 日志加载器（日志文件→结构化文档）
  • 邮件加载器（邮件→文档）
""")

# JSON 加载器示例
class JSONDocLoader:
    """JSON 文档加载器"""

    def __init__(self, file_path: str, content_key: str = "content"):
        self.file_path = file_path
        self.content_key = content_key

    def load(self) -> list:
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            data = [data]
        docs = []
        for i, item in enumerate(data):
            content = item.get(self.content_key, str(item))
            metadata = {k: v for k, v in item.items() if k != self.content_key}
            metadata["source"] = self.file_path
            metadata["index"] = i
            docs.append(Document(page_content=content, metadata=metadata))
        return docs

json_path = os.path.join(temp_dir, "data.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump([
        {"content": "RAG 是检索增强生成技术", "topic": "rag"},
        {"content": "向量数据库存储高维向量", "topic": "vector_db"},
    ], f, ensure_ascii=False)

json_loader = JSONDocLoader(json_path)
json_docs = json_loader.load()
print(f"JSON 加载: {len(json_docs)} 条")
for doc in json_docs:
    print(f"  [{doc.metadata.get('topic')}] {doc.page_content}")

# 清理
import shutil
shutil.rmtree(temp_dir, ignore_errors=True)

print("\n" + "=" * 60)
print("[完成] 第2课完成！你已经学会了：")
print("  [v] Document 对象（page_content + metadata）")
print("  [v] 文本文件加载器")
print("  [v] Markdown 按标题拆分加载")
print("  [v] CSV 加载（指定内容列/元数据列）")
print("  [v] 目录批量加载")
print("  [v] 自定义加载器模板（JSON示例）")
print("=" * 60)
print("\n下一课：03_indexing_pipeline.py - 索引管道")
