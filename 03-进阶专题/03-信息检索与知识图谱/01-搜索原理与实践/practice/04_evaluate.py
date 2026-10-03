"""
Step 4：离线评估 MRR / NDCG@K / Recall@K
=========================================
对比纯 BM25 与混合检索。
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import BM25, build_index, dense_search, load_corpus, load_queries, rrf_fuse  # noqa: E402


def mrr(ranked_ids: list[int], relevant: set[int]) -> float:
    for i, doc_id in enumerate(ranked_ids, start=1):
        if doc_id in relevant:
            return 1.0 / i
    return 0.0


def ndcg_at_k(ranked_ids: list[int], relevant: set[int], k: int = 3) -> float:
    dcg = 0.0
    for i, doc_id in enumerate(ranked_ids[:k], start=1):
        if doc_id in relevant:
            dcg += 1.0 / math.log2(i + 1)
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(k, len(relevant)) + 1))
    return dcg / ideal if ideal > 0 else 0.0


def recall_at_k(ranked_ids: list[int], relevant: set[int], k: int = 5) -> float:
    if not relevant:
        return 0.0
    return len(set(ranked_ids[:k]) & relevant) / len(relevant)


def main() -> None:
    docs = load_corpus()
    index = build_index(docs)
    bm25 = BM25(docs, index)
    queries = load_queries()

    print(f"评估集：{len(queries)} 个查询\n")
    print(f"{'查询':<22}{'方法':<8}{'MRR':<8}{'NDCG@3':<10}{'Recall@5'}")
    print("-" * 58)

    agg = {"bm25": [0.0, 0.0, 0.0], "hybrid": [0.0, 0.0, 0.0]}
    for q in queries:
        rel = set(q["relevant"])
        bm25_ids = [i for i, _ in bm25.search(q["query"], top_k=5)]
        hybrid_ids = [i for i, _ in rrf_fuse(
            [bm25.search(q["query"], top_k=5), dense_search(q["query"], docs)]
        )[:5]]

        for name, ids in (("bm25", bm25_ids), ("hybrid", hybrid_ids)):
            m, n, r = mrr(ids, rel), ndcg_at_k(ids, rel), recall_at_k(ids, rel)
            agg[name][0] += m
            agg[name][1] += n
            agg[name][2] += r
            print(f"{q['query']:<20}{name:<10}{m:<8.3f}{n:<10.3f}{r:.3f}")
        print("-" * 58)

    nq = len(queries)
    print(f"\n平均（共 {nq} 个查询）")
    for name, vals in agg.items():
        print(f"  {name}: MRR={vals[0]/nq:.3f}  NDCG@3={vals[1]/nq:.3f}  Recall@5={vals[2]/nq:.3f}")


if __name__ == "__main__":
    main()
