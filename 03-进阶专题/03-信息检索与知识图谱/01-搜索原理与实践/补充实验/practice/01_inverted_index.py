"""
迷你搜索引擎 v0.1 —— 倒排索引 + BM25

只用一个文件、零第三方依赖，演示搜索引擎最核心的两个部件：
1. 倒排索引：词 -> 出现在哪些文档（含位置）
2. BM25：给文档与查询的相关性打分

运行：python 01_inverted_index.py
"""

import math
import re
from collections import defaultdict

# 语料库：doc_id -> 文档内容（第 1 课练习：往这里添加你自己的文档）
CORPUS = {
    "d1": "搜索引擎通过倒排索引快速找到包含关键词的网页",
    "d2": "倒排索引是信息检索中最核心的数据结构，类似书的目录",
    "d3": "BM25 是一种经典的相关性排序算法，广泛用于搜索引擎",
    "d4": "数据库的 LIKE 查询会扫描全表，而搜索引擎用索引加速",
    "d5": "The quick brown fox jumps over the lazy dog.",
}


def tokenize(text: str) -> list[str]:
    """简易分词：英文按单词切分，中文用两字窗口（bigram）。

    真实系统会用 jieba、IK 等分词器，这里是为了演示。
    中文 bigram 的含义：『搜索引擎』 -> 搜索 / 索引 / 引擎
    """
    tokens = []
    for part in re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]+", text):
        if part.isascii():
            part = part.lower()
            tokens.extend(w for w in re.findall(r"[a-z0-9]+", part))
        else:
            if len(part) == 1:
                tokens.append(part)
            else:
                tokens.extend(part[i : i + 2] for i in range(len(part) - 1))
    return tokens


def build_index(corpus: dict[str, str]):
    """构建倒排索引：term -> {doc_id: [出现位置]}，并记录每篇文档长度。"""
    index = defaultdict(lambda: defaultdict(list))
    doc_len = {}
    for doc_id, text in corpus.items():
        tokens = tokenize(text)
        doc_len[doc_id] = len(tokens)
        for pos, term in enumerate(tokens):
            index[term][doc_id].append(pos)
    return index, doc_len


def bm25(query_terms: list[str], index, doc_len: dict, corpus_size: int,
         k1: float = 1.5, b: float = 0.75) -> dict[str, float]:
    """BM25 相关性打分：查询词在文档中出现越多、文档越短，分数越高。"""
    scores = defaultdict(float)
    avg_len = sum(doc_len.values()) / len(doc_len)

    for term in query_terms:
        postings = index.get(term, {})
        df = len(postings)  # 包含该词的文档数
        idf = math.log(1 + (corpus_size - df + 0.5) / (df + 0.5))
        for doc_id, positions in postings.items():
            tf = len(positions)  # 词在文档中出现的次数
            dl = doc_len[doc_id]
            tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg_len))
            scores[doc_id] += idf * tf_norm
    return scores


def search(query: str, index, doc_len: dict, corpus: dict[str, str]):
    terms = tokenize(query)
    print(f"查询: {query}")
    print(f"分词: {terms}")

    scores = bm25(terms, index, doc_len, len(corpus))
    results = sorted(scores.items(), key=lambda x: -x[1])
    if not results:
        print("没有找到结果")
    else:
        for doc_id, score in results:
            print(f"  {doc_id}  分数={score:.4f}  {corpus[doc_id]}")

    # 布尔 AND：所有查询词都必须出现在文档中（注意去重）
    unique_terms = list(dict.fromkeys(terms))
    if unique_terms:
        and_docs = set.intersection(*(set(index[t]) for t in unique_terms))
    else:
        and_docs = set()
    print("同时包含所有查询词的文档:", sorted(and_docs) if and_docs else "无")
    print()


if __name__ == "__main__":
    index, doc_len = build_index(CORPUS)

    print("=== 倒排索引示例（前 10 个词）===")
    for i, (term, postings) in enumerate(index.items()):
        if i >= 10:
            break
        shown = ", ".join(f"{doc_id}{positions}" for doc_id, positions in postings.items())
        print(f"  {term!r}: {shown}")
    print()

    search("搜索引擎 倒排索引", index, doc_len, CORPUS)
    search("BM25 排序", index, doc_len, CORPUS)
