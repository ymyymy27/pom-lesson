"""
Step 1：从文档构建知识图谱
==========================
用法：
  python 01_build_kg.py            # LLM 抽取（Ollama）
  python 01_build_kg.py --rules    # 规则抽取（离线兜底）
  python 01_build_kg.py --limit 3  # 只处理前 3 篇文档
"""

import argparse
import sys
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).parent))
from common import build_graph, ensure_graph, load_docs, save_graph  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rules", action="store_true", help="使用规则抽取（不调 LLM）")
    parser.add_argument("--limit", type=int, default=None, help="只处理前 N 篇文档")
    args = parser.parse_args()

    docs = load_docs()
    print(f"读取文档：{len(docs)} 篇")

    use_llm = not args.rules
    G = build_graph(use_llm=use_llm, max_docs=args.limit)
    save_graph(G)

    print(f"\n图谱构建完成：{G.number_of_nodes()} 个节点，{G.number_of_edges()} 条边")

    print("\n--- 节点（按类型） ---")
    by_type: dict[str, list[str]] = {}
    for n, data in G.nodes(data=True):
        by_type.setdefault(data.get("type", "?"), []).append(n)
    for t, names in sorted(by_type.items()):
        print(f"  {t}: {', '.join(names)}")

    print("\n--- 边样例 ---")
    for u, v, k, d in list(G.edges(keys=True, data=True))[:12]:
        print(f"  {u} -{d.get('relation')}-> {v}")

    print("\n--- 示例路径：张三 → 项目X（组织链：汇报→管理→拥有） ---")
    org_chain = nx.MultiDiGraph()
    for u, v, k, d in G.edges(keys=True, data=True):
        if d.get("relation") in ("REPORTS_TO", "MANAGES", "OWNS"):
            org_chain.add_edge(u, v, key=k, relation=d["relation"])
    if nx.has_path(org_chain, "张三", "项目X"):
        print("  " + " → ".join(nx.shortest_path(org_chain, "张三", "项目X")))
    else:
        print("  （组织链上无路径；说明关系链断裂，需要检查抽取质量）")

    print("\n完成！图谱已保存到 kg.json")


if __name__ == "__main__":
    main()
