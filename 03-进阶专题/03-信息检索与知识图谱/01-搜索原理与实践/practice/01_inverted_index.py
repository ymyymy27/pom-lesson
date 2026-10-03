"""
Step 1：倒排索引构建与布尔/短语查询
====================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import build_index, load_corpus, tokenize  # noqa: E402


def boolean_and(index: dict, query: str) -> set[int]:
    terms = tokenize(query)
    if not terms:
        return set()
    result = None
    for term in terms:
        ids = {entry[0] for entry in index.get(term, [])}
        result = ids if result is None else result & ids
    return result or set()


def phrase_search(index: dict, phrase: str) -> set[int]:
    terms = tokenize(phrase)
    if not terms:
        return set()
    hits: set[int] = set()
    first = index.get(terms[0], [])
    for entry in first:
        doc_id, _, positions = entry
        for pos in positions:
            ok = True
            for offset, term in enumerate(terms[1:], start=1):
                found = any(
                    e[0] == doc_id and (pos + offset) in e[2]
                    for e in index.get(term, [])
                )
                if not found:
                    ok = False
                    break
            if ok:
                hits.add(doc_id)
                break
    return hits


def main() -> None:
    docs = load_corpus()
    index = build_index(docs)
    print(f"语料：{len(docs)} 篇文档；词项数：{len(index)}")

    print("\n--- 词项示例（含倒排长度） ---")
    for term, postings in sorted(index.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"  {term}: {len(postings)} 篇")

    print("\n--- 布尔 AND 查询：报销 5000 ---")
    print("  命中文档：", sorted(boolean_and(index, "报销 5000")))

    print("\n--- 布尔 AND 查询：模型 部署 ---")
    print("  命中文档：", sorted(boolean_and(index, "模型 部署")))

    print("\n--- 短语查询：远程办公 ---")
    print("  命中文档：", sorted(phrase_search(index, "远程办公")))

    print("\n--- 未登录词兜底演示：输入 '智云平台' ---")
    print("  分词结果：", tokenize("智云平台"))


if __name__ == "__main__":
    main()
