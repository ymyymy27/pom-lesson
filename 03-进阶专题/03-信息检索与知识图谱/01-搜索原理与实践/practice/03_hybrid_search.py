"""
Step 3：BM25 + 向量 + RRF 混合检索
==================================
向量优先用 Ollama qwen3-embedding:4b；不可用时退回字符 bigram 向量。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    BM25,
    build_index,
    dense_search,
    load_corpus,
    load_queries,
    rrf_fuse,
    snippet,
)


def main() -> None:
    docs = load_corpus()
    index = build_index(docs)
    bm25 = BM25(docs, index)

    print("混合检索：BM25（词面）+ 向量（语义）+ RRF 融合")
    for q in load_queries()[:4]:
        print("\n" + "=" * 60)
        print(f"查询：{q['query']}")

        lexical = bm25.search(q["query"], top_k=5)
        semantic = dense_search(q["query"], docs)
        fused = rrf_fuse([lexical, semantic])[:3]

        print("  [BM25]  ", [(i, round(s, 3)) for i, s in lexical[:3]])
        print("  [向量]  ", [(i, round(s, 3)) for i, s in semantic[:3]])
        print("  [RRF]   ", [(i, round(s, 3)) for i, s in fused])
        for doc_id, _ in fused:
            doc = next(d for d in docs if d["id"] == doc_id)
            print(f"    → [{doc_id}] {snippet(doc, q['query'])}")


if __name__ == "__main__":
    main()
