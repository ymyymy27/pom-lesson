"""
Step 3：mini GraphRAG（社区检测 + 社区摘要 + Global/Local 检索）
================================================================
用 NetworkX 复刻 Microsoft GraphRAG 的核心思想（简化版）：
  1. Leiden/Louvain 社区检测
  2. 社区摘要（LLM 或模板）
  3. Global Search：社区摘要 Map-Reduce
  4. Local Search：实体 k 跳子图
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
    serialize_subgraph,
)


SUMMARIZE_PROMPT = """你是一个社区分析师。以下是知识图谱中一个社区（关系紧密的实体群）的节点与关系。
请用 3~5 句话总结这个社区的主题、成员和关键事实，供全局问答使用。

社区内容：
{subgraph}
"""

MAP_PROMPT = """根据下面的社区摘要，回答用户问题。如果摘要与问题无关，请回答"无关"。
最后一行输出你的自信度（0~10 的整数）。

社区摘要：
{summary}

问题：{question}
"""

REDUCE_PROMPT = """以下是多个社区对同一问题的部分回答（含自信度）。
请综合它们，生成一个完整、简洁、有依据的最终答案；信息不足就说明不足。

部分回答：
{partials}

问题：{question}
"""


def detect_communities(G: nx.DiGraph) -> list[list[str]]:
    Gu = G.to_undirected()
    try:
        comms = nx.community.louvain_communities(Gu, weight="count", seed=42)
    except Exception:
        comms = nx.community.greedy_modularity_communities(Gu, weight="count")
    return [sorted(c) for c in comms if len(c) >= 2]


def summarize_community(G: nx.DiGraph, members: list[str]) -> str:
    ctx = serialize_subgraph(G, members, max_nodes=15)
    summary = chat_safe(SUMMARIZE_PROMPT.format(subgraph=ctx), max_tokens=200)
    if not summary:
        # 模板兜底：不依赖 LLM
        summary = "社区包含：" + "、".join(members[:10])
    return summary


def global_search(G: nx.DiGraph, summaries: list[tuple[str, str]], question: str) -> str:
    # 向量初筛最相关的社区
    texts = [s for _, s in summaries]
    embs = embed(texts)
    if embs:
        qv = embed([question])[0]
        ranked = sorted(
            ((cosine(qv, e), i) for i, e in enumerate(embs)),
            reverse=True,
        )[:2]
        selected = [summaries[i] for _, i in ranked]
    else:
        selected = summaries[:2]

    # Map：逐社区生成部分答案 + 自信度
    partials = []
    for cid, summary in selected:
        raw = chat_safe(MAP_PROMPT.format(summary=summary, question=question), max_tokens=180)
        if raw:
            partials.append(f"[社区{cid}]\n{raw}")
    if not partials:
        return "（无法生成全局答案：LLM 不可用）"

    # Reduce：汇总
    final = chat_safe(REDUCE_PROMPT.format(partials="\n\n".join(partials), question=question), max_tokens=250)
    return final or "[生成失败]"


def local_search(G: nx.DiGraph, question: str) -> str:
    seeds = [alias for alias in ALIASES if alias in question]
    nodes: set[str] = set()
    for seed in seeds:
        if seed in G:
            nodes.update(nx.single_source_shortest_path_length(G, seed, cutoff=2))
    if not nodes:
        nodes = set(list(G.nodes)[:10])
    ctx = serialize_subgraph(G, list(nodes))
    prompt = (
        "你是公司知识库问答助手。请基于下面的知识图谱上下文回答，"
        "展示推理路径，信息不足就说明不足。\n\n上下文：\n"
        + ctx
        + f"\n\n问题：{question}"
    )
    return chat_safe(prompt, max_tokens=250) or "[生成失败]"


def main() -> None:
    G = ensure_graph(use_llm=False)
    print(f"图：{G.number_of_nodes()} 节点 / {G.number_of_edges()} 边")

    # 1) 社区检测
    communities = detect_communities(G)
    tagged = list(enumerate(communities))  # (原始社区ID, 成员)
    print(f"\n[社区检测] 得到 {len(communities)} 个社区（≥2 节点）")
    for cid, members in tagged:
        print(f"  社区{cid}: {', '.join(members)}")

    # 2) 社区摘要（只对最大的 4 个社区生成，控制耗时）
    tagged.sort(key=lambda x: len(x[1]), reverse=True)
    print("\n[社区摘要] 生成中（最多 4 个社区）...")
    summaries: list[tuple[str, str]] = []
    for cid, members in tagged[:4]:
        s = summarize_community(G, members)
        summaries.append((str(cid), s))
        print(f"  社区{cid} 摘要: {s[:60]}...")

    # 3) Global Search
    q_global = "公司研发团队主要使用哪些技术？"
    print(f"\n[Global Search] 问题：{q_global}")
    print("  回答：", global_search(G, summaries, q_global).replace("\n", " "))

    # 4) Local Search
    q_local = "张三的上级管理的部门负责什么项目？"
    print(f"\n[Local Search] 问题：{q_local}")
    print("  回答：", local_search(G, q_local).replace("\n", " "))


if __name__ == "__main__":
    main()
