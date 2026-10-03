"""
Step 2：BM25 搜索 + 摘要
========================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import BM25, build_index, load_corpus, load_queries, snippet, tokenize  # noqa: E402


def main() -> None:
    docs = load_corpus()
    index = build_index(docs)
    bm25 = BM25(docs, index, k1=1.5, b=0.75)

    print(f"BM25 参数：k1={bm25.k1}, b={bm25.b}, 平均文档长度={bm25.avgdl:.1f} 词")

    for q in load_queries():
        print("\n" + "=" * 60)
        print(f"查询：{q['query']}")
        print(f"分词：{tokenize(q['query'])}")
        for doc_id, score in bm25.search(q["query"], top_k=3):
            doc = next(d for d in docs if d["id"] == doc_id)
            print(f"  [{doc_id}] {score:.3f}  {snippet(doc, q['query'])}")


if __name__ == "__main__":
    main()
