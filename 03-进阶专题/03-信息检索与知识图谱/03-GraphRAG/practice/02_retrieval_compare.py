"""
Step 2：纯向量 RAG vs 图检索 vs 混合
====================================
对比同一批多跳问题在三类检索下的表现。
"""

import sys
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).parent))
from common import (  # noqa: E402
    ALIASES,
    chat_safe,
    cosine,
    embed,
    ensure_graph,
    load_docs,
    serialize_subgraph,
)


SYSTEM = (
    "你是公司知识库问答助手。请严格基于提供的上下文回答，"
    "不要编造；如果上下文不足，请说'信息不足'。回答要简洁并给出依据。"
)


def vector_retrieve(question: str, docs: list[dict], doc_embs: list, top_k: int = 3) -> list[dict]:
    qv = embed([question])[0]
    scored = sorted(
        ((cosine(qv, e), i) for i, e in enumerate(doc_embs)),
        reverse=True,
    )[:top_k]
    return [docs[i] for _, i in scored]


def graph_retrieve(G: nx.DiGraph, question: str, hops: int = 2) -> list[str]:
    seeds = [alias for alias in ALIASES if alias in question]
    nodes: set[str] = set()
    for seed in seeds:
        if seed in G:
            nodes.update(nx.single_source_shortest_path_length(G, seed, cutoff=hops))
    if not nodes:
        # 没有命中实体：用 PageRank 取最重要的节点（全局兜底）
        pr = nx.pagerank(G)
        nodes = set(sorted(pr, key=pr.get, reverse=True)[:12])
    return list(nodes)


def main() -> None:
    G = ensure_graph(use_llm=False)
    docs = load_docs()
    print(f"图：{G.number_of_nodes()} 节点 / {G.number_of_edges()} 边；文档 {len(docs)} 篇")

    print("正在生成向量索引...")
    doc_embs = embed([d["title"] + "：" + d["content"] for d in docs])
    if doc_embs is None:
        print("Embedding 服务不可用，跳过向量部分。")
        return

    questions = [
        "张三的上级管理的部门负责什么项目？",
        "王五参与的项目用了哪些技术？",
        "公司研发团队主要使用哪些技术？",
    ]

    for q in questions:
        print("\n" + "=" * 66)
        print(f"问题：{q}")

        # 1) 纯向量
        hits = vector_retrieve(q, docs, doc_embs)
        vec_ctx = "\n\n".join(f"[{d['title']}]\n{d['content']}" for d in hits)
        vec_answer = chat_safe(f"上下文：\n{vec_ctx}\n\n问题：{q}", SYSTEM, 200)
        print("\n[纯向量 RAG] 检索到：", "；".join(d["title"] for d in hits))
        print("  回答：", (vec_answer or "[生成失败]").replace("\n", " "))

        # 2) 纯图
        nodes = graph_retrieve(G, q)
        graph_ctx = serialize_subgraph(G, nodes)
        graph_answer = chat_safe(f"上下文（知识图谱）：\n{graph_ctx}\n\n问题：{q}", SYSTEM, 200)
        print("\n[图检索] 命中实体/节点：", "，".join(nodes[:10]))
        print("  回答：", (graph_answer or "[生成失败]").replace("\n", " "))

        # 3) 混合：拼接两路上下文
        hybrid_ctx = "【文档检索结果】\n" + vec_ctx + "\n\n【图谱检索结果】\n" + graph_ctx
        hybrid_answer = chat_safe(f"上下文：\n{hybrid_ctx}\n\n问题：{q}", SYSTEM, 200)
        print("\n[混合检索] 回答：", (hybrid_answer or "[生成失败]").replace("\n", " "))


if __name__ == "__main__":
    main()
