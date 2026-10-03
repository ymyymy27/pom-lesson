import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第5课：文本分块策略与实践
==============================================================================

长文档不能直接 Embedding，需要先分块（Chunking）。
分块质量直接影响 RAG 检索效果。

本课内容：
1. 为什么需要分块
2. 分块策略对比
3. 递归字符分割
4. 语义分割
5. 分块参数优化
6. 分块最佳实践
==============================================================================
"""

import json
import re

print("=" * 60)
print("第5课：文本分块")
print("=" * 60)

# ============================================================================
# 1. 为什么分块
# ============================================================================
print("\n--- 1. 为什么分块 ---")
print("""
Embedding 模型有输入长度限制：
  nomic-embed-text: 8192 tokens
  bge-large-zh:     512 tokens
  OpenAI:           8191 tokens

即使模型支持长文本，分块也有好处：
  ✅ 检索更精准（只返回相关段落，不是整篇文章）
  ✅ LLM 上下文更聚焦（减少无关信息干扰）
  ✅ 节省 LLM token 成本

  文档(10000字) → 分块(20块×500字) → Embedding → 向量DB
                                                      ↓
  用户查询 → query Embedding → 向量搜索 → Top-3块 → LLM回答
""")

# ============================================================================
# 2. 分块策略对比
# ============================================================================
print("\n--- 2. 分块策略 ---")
print("""
┌──────────────────┬──────────────────────────────────────┐
│  策略             │  说明                                 │
├──────────────────┼──────────────────────────────────────┤
│  固定长度        │  每N个字符切一刀                     │
│                  │  简单但可能切断句子                   │
├──────────────────┼──────────────────────────────────────┤
│  递归字符分割    │  按分隔符层级切割                    │
│  (推荐！)        │  \\n\\n → \\n → 。→ 空格 → 字符     │
│                  │  LangChain 默认方式                   │
├──────────────────┼──────────────────────────────────────┤
│  句子分割        │  按句子边界切割                      │
│                  │  保证句子完整性                       │
├──────────────────┼──────────────────────────────────────┤
│  语义分割        │  按语义相似度切割                    │
│                  │  效果最好，但最慢                    │
├──────────────────┼──────────────────────────────────────┤
│  Markdown/HTML   │  按标题/标签结构切割                 │
│  结构分割        │  适合结构化文档                      │
├──────────────────┼──────────────────────────────────────┤
│  Token 分割      │  按 token 数切割                     │
│                  │  精确控制 token 数量                  │
└──────────────────┴──────────────────────────────────────┘
""")

# ============================================================================
# 3. 递归字符分割
# ============================================================================
print("\n--- 3. 递归字符分割 ---")

class RecursiveTextSplitter:
    """递归字符文本分割器（简化版，模拟 LangChain）"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50,
                 separators: list = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", "。", "！", "？", ".", " ", ""]

    def split_text(self, text: str) -> list:
        chunks = self._split_recursive(text, self.separators)
        # 合并过小的块
        merged = self._merge_chunks(chunks)
        return merged

    def _split_recursive(self, text: str, separators: list) -> list:
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        # 找到能用的最高级分隔符
        for sep in separators:
            if sep == "":
                # 最后手段：按字符切割
                return [text[i:i+self.chunk_size]
                        for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]
            if sep in text:
                parts = text.split(sep)
                result = []
                current = ""
                for part in parts:
                    candidate = current + sep + part if current else part
                    if len(candidate) <= self.chunk_size:
                        current = candidate
                    else:
                        if current:
                            result.append(current.strip())
                        current = part
                if current:
                    result.append(current.strip())
                # 递归处理仍然过大的块
                final = []
                remaining_seps = separators[separators.index(sep) + 1:]
                for chunk in result:
                    if len(chunk) > self.chunk_size and remaining_seps:
                        final.extend(self._split_recursive(chunk, remaining_seps))
                    elif chunk.strip():
                        final.append(chunk.strip())
                return final
        return [text]

    def _merge_chunks(self, chunks: list) -> list:
        if not chunks:
            return []
        merged = []
        for chunk in chunks:
            if not chunk.strip():
                continue
            if merged and len(merged[-1]) + len(chunk) < self.chunk_size // 2:
                merged[-1] += "\n" + chunk
            else:
                merged.append(chunk)

        # 添加 overlap
        if self.chunk_overlap > 0 and len(merged) > 1:
            overlapped = [merged[0]]
            for i in range(1, len(merged)):
                prev_tail = merged[i-1][-self.chunk_overlap:]
                overlapped.append(prev_tail + "\n" + merged[i])
            return overlapped
        return merged

# 测试文本
sample_text = """人工智能概述

人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，致力于创建能够模拟人类智能的系统。AI的发展经历了多个阶段，从早期的规则系统到现代的深度学习。

机器学习

机器学习是AI的核心子领域。它让计算机能够从数据中学习，而无需显式编程。常见的机器学习方法包括：监督学习、无监督学习和强化学习。监督学习使用标注数据训练模型，无监督学习发现数据中的隐藏模式，强化学习通过试错来优化决策。

深度学习

深度学习是机器学习的一个子集，使用多层神经网络处理复杂数据。卷积神经网络（CNN）擅长图像处理，循环神经网络（RNN）处理序列数据，Transformer架构则革命性地改变了自然语言处理领域。

大语言模型

大语言模型（LLM）如GPT-4、Claude和Gemini，基于Transformer架构，通过海量文本预训练获得强大的语言理解和生成能力。它们能够完成翻译、写作、编程等多种任务。"""

splitter = RecursiveTextSplitter(chunk_size=200, chunk_overlap=30)
chunks = splitter.split_text(sample_text)

print(f"原文长度: {len(sample_text)} 字符")
print(f"分块数: {len(chunks)}")
print(f"分块详情:")
for i, chunk in enumerate(chunks):
    print(f"  [{i+1}] ({len(chunk)}字) {chunk[:60]}...")

# ============================================================================
# 4. 语义分割
# ============================================================================
print("\n--- 4. 语义分割 ---")
print("""
语义分割 = 当相邻句子语义变化大时切割

原理：
  句子1: "机器学习用于数据分析"     ┐
  句子2: "深度学习是ML的子集"       ┤ 相似 → 同一块
  句子3: "CNN处理图像数据"          ┘
  ------- 语义跳变 -------
  句子4: "今天的股市下跌了"         ┐
  句子5: "经济形势不太乐观"         ┤ 相似 → 同一块
  句子6: "专家预测将继续调整"       ┘

实现（需要 Embedding 模型）：
```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

splitter = SemanticChunker(
    OpenAIEmbeddings(),
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=90,
)
chunks = splitter.split_text(long_text)
```

优点：语义完整性最好
缺点：需要 Embedding 计算，速度慢
""")

# 模拟语义分割
class SimpleSemanticSplitter:
    """简化的语义分割（基于句子长度和关键词变化模拟）"""

    def split(self, text: str) -> list:
        # 按句子分割
        sentences = re.split(r'(?<=[。！？\n])', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current = []
        current_keywords = set()

        for sent in sentences:
            # 提取关键词（简化：取所有2字以上的词）
            words = set(re.findall(r'[\u4e00-\u9fff]{2,}', sent))

            # 判断语义跳变（关键词重叠少）
            if current_keywords and words:
                overlap = len(current_keywords & words) / max(len(current_keywords), 1)
                if overlap < 0.1 and len("".join(current)) > 100:
                    chunks.append("".join(current))
                    current = []
                    current_keywords = set()

            current.append(sent)
            current_keywords.update(words)

        if current:
            chunks.append("".join(current))
        return chunks

semantic_splitter = SimpleSemanticSplitter()
sem_chunks = semantic_splitter.split(sample_text)
print(f"语义分割结果: {len(sem_chunks)} 块")
for i, chunk in enumerate(sem_chunks):
    print(f"  [{i+1}] ({len(chunk)}字) {chunk[:50]}...")

# ============================================================================
# 5. 参数优化
# ============================================================================
print("\n--- 5. 参数优化 ---")
print("""
chunk_size 选择：
  ┌──────────────────────────────────────────────────────┐
  │  chunk_size    效果              适用场景             │
  ├──────────────────────────────────────────────────────┤
  │  100-200      精确检索，段落级    FAQ/短问答          │
  │  300-500      平衡选择（推荐）   通用RAG             │
  │  500-1000     完整上下文         技术文档/论文       │
  │  1000-2000    大段落             书籍/报告           │
  └──────────────────────────────────────────────────────┘

chunk_overlap 选择：
  通常为 chunk_size 的 10%-20%
  太小：跨块信息丢失
  太大：浪费存储和计算

不同文档类型的推荐：
  FAQ/知识库:  chunk_size=200, overlap=20
  技术文档:    chunk_size=500, overlap=50
  法律合同:    chunk_size=300, overlap=50
  代码文件:    按函数/类分割
  Markdown:    按标题层级分割
""")

# 对比不同 chunk_size
print("不同 chunk_size 对比:")
for size in [100, 300, 500, 1000]:
    s = RecursiveTextSplitter(chunk_size=size, chunk_overlap=int(size*0.1))
    c = s.split_text(sample_text)
    avg_len = sum(len(x) for x in c) / len(c) if c else 0
    print(f"  size={size:>4}: {len(c):>2}块, 平均{avg_len:.0f}字/块")

# ============================================================================
# 6. 最佳实践
# ============================================================================
print("\n--- 6. 最佳实践 ---")
print("""
分块最佳实践清单：

  1. 保持语义完整性
     ✅ 按段落/句子边界切割
     ❌ 在句子中间切断

  2. 添加上下文
     在每个 chunk 前面加上文档标题/章节名
     "## 第3章 深度学习\\n\\n深度学习是..."

  3. 元数据记录
     每个 chunk 记录来源（文件名/页码/章节）
     方便后续引用和溯源

  4. 重叠（Overlap）
     10-20% 的重叠防止信息丢失
     尤其是段落跨块时

  5. 多粒度索引（Parent-Child）
     粗粒度（整段）用于召回
     细粒度（句子）用于精确匹配
     检索时先找小块，返回时用大块

  6. 先测试再上线
     用实际查询测试检索效果
     调整参数直到满意

```python
# 添加上下文的分块
def chunk_with_context(text, title, chunk_size=500):
    splitter = RecursiveTextSplitter(chunk_size=chunk_size)
    chunks = splitter.split_text(text)
    return [f"文档：{title}\\n\\n{chunk}" for chunk in chunks]
```
""")

# 带上下文的分块演示
def chunk_with_context(text: str, title: str, chunk_size: int = 200) -> list:
    splitter = RecursiveTextSplitter(chunk_size=chunk_size, chunk_overlap=20)
    chunks = splitter.split_text(text)
    return [{"text": f"[{title}] {chunk}", "metadata": {"source": title, "chunk_id": i}}
            for i, chunk in enumerate(chunks)]

result = chunk_with_context(sample_text, "AI概述文档", 200)
print("带上下文的分块:")
for item in result[:3]:
    print(f"  [{item['metadata']['chunk_id']}] {item['text'][:60]}...")
    print(f"       metadata: {item['metadata']}")

print("\n" + "=" * 60)
print("[完成] 第5课完成！你已经学会了：")
print("  [v] 分块的必要性和价值")
print("  [v] 六种分块策略对比")
print("  [v] 递归字符分割（最常用）")
print("  [v] 语义分割（最精确）")
print("  [v] chunk_size / overlap 参数优化")
print("  [v] 分块最佳实践（上下文/元数据/多粒度）")
print("=" * 60)
print("\n下一课：06_advanced_search.py - 高级搜索")
