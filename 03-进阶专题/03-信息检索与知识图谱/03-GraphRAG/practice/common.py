"""
GraphRAG 实战公共模块
=====================
职责：
1. 读取样例文档
2. LLM 抽取三元组（Ollama），失败时用内置规则兜底
3. 构建 / 保存 / 加载 NetworkX 图
4. 提供 chat / embed / 子图序列化等公共函数
"""

import io
import json
import re
import sys
from pathlib import Path

import httpx
import networkx as nx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OLLAMA_URL = "http://localhost:11434"
CHAT_MODEL = "qwen2.5:7b"          # 对话与抽取
EMBED_MODEL = "qwen3-embedding:4b"  # 向量

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "sample_docs.md"
KG_FILE = BASE_DIR / "kg.json"

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
NODE_TYPES = {
    "张三": "Person", "李四": "Person", "王五": "Person", "赵六": "Person",
    "研发部": "Department", "市场部": "Department",
    "项目X": "Project", "项目Y": "Project", "项目Z": "Project",
    "Python": "Technology", "FastAPI": "Technology", "PostgreSQL": "Technology",
    "Redis": "Technology", "ClickHouse": "Technology", "React": "Technology",
    "TypeScript": "Technology", "Next.js": "Technology", "Vercel": "Technology",
}

RELATION_TYPES = {
    "REPORTS_TO": ("Person", "Person"),   # 汇报给
    "MANAGES": ("Person", "Department"),  # 管理
    "OWNS": ("Department", "Project"),    # 拥有
    "WORKS_ON": ("Person", "Project"),    # 参与
    "USES": ("Project", "Technology"),    # 使用
}

# 别名 → 规范名（实体消歧演示）
ALIASES = {
    "张总": "张三", "Zhang San": "张三", "张三": "张三",
    "李总": "李四", "Li Si": "李四", "李四": "李四",
    "王工": "王五", "王五": "王五",
    "赵总": "赵六", "赵六": "赵六",
    "智云平台": "项目X", "项目X": "项目X",
    "星图分析": "项目Y", "项目Y": "项目Y",
    "品牌官网": "项目Z", "项目Z": "项目Z",
}

EXTRACT_PROMPT = """你是知识图谱构建器。从文本中抽取实体和关系。

节点类型（只能使用这些）：
- Person: 人员
- Department: 部门
- Project: 项目
- Technology: 技术

关系类型（只能使用这些）：
- REPORTS_TO: Person -> Person（汇报给）
- MANAGES: Person -> Department（管理）
- OWNS: Department -> Project（拥有）
- WORKS_ON: Person -> Project（参与/负责）
- USES: Project -> Technology（使用）

输出严格 JSON（不要输出其他内容）：
{{"entities": [{{"name": "...", "type": "..."}}],
 "relations": [{{"source": "...", "relation": "...", "target": "..."}}]}}

实体 name 必须使用规范名（中文）。只抽取与上述类型相关的信息。

文本：
{text}
"""

# ---------------------------------------------------------------------------
# LLM 与向量工具
# ---------------------------------------------------------------------------
def chat(prompt: str, system: str = "", max_tokens: int = 500) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": CHAT_MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": max_tokens},
        },
        timeout=180.0,
    )
    return resp.json()["message"]["content"]


def chat_safe(prompt: str, system: str = "", max_tokens: int = 500) -> str | None:
    try:
        return chat(prompt, system, max_tokens)
    except Exception:
        return None


def embed(texts: list[str]) -> list[list[float]] | None:
    try:
        resp = httpx.post(
            f"{OLLAMA_URL}/api/embed",
            json={"model": EMBED_MODEL, "input": texts},
            timeout=180.0,
        )
        return resp.json().get("embeddings")
    except Exception:
        return None


def cosine(a: list[float], b: list[float]) -> float:
    import math

    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb + 1e-12)


# ---------------------------------------------------------------------------
# 文档读取
# ---------------------------------------------------------------------------
def load_docs() -> list[dict]:
    text = DATA_FILE.read_text(encoding="utf-8")
    docs = []
    title = None
    buf = []
    for line in text.splitlines():
        if line.startswith("## "):
            if title:
                docs.append({"title": title, "content": "\n".join(buf).strip()})
            title = line[3:].strip()
            buf = []
        elif title is not None:
            buf.append(line)
    if title:
        docs.append({"title": title, "content": "\n".join(buf).strip()})
    return [d for d in docs if d["content"]]


# ---------------------------------------------------------------------------
# 三元组抽取
# ---------------------------------------------------------------------------
def extract_triples_llm(doc: dict) -> list[dict]:
    """LLM 抽取；失败返回 []（由调用方决定是否用规则兜底）。"""
    raw = chat_safe(EXTRACT_PROMPT.format(text=doc["content"]), max_tokens=600)
    if not raw:
        return []
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []

    triples = []
    for e in data.get("entities", []):
        name = ALIASES.get(str(e.get("name", "")).strip(), str(e.get("name", "")).strip())
        if name and name in NODE_TYPES:
            triples.append({
                "kind": "node",
                "name": name,
                "type": NODE_TYPES[name],
                "description": f"来自文档《{doc['title']}》",
                "source": doc["title"],
            })
    for r in data.get("relations", []):
        s = ALIASES.get(str(r.get("source", "")).strip(), str(r.get("source", "")).strip())
        t = ALIASES.get(str(r.get("target", "")).strip(), str(r.get("target", "")).strip())
        rel = str(r.get("relation", "")).strip().upper()
        if s in NODE_TYPES and t in NODE_TYPES and rel in RELATION_TYPES:
            s_type, t_type = RELATION_TYPES[rel]
            if NODE_TYPES[s] == s_type and NODE_TYPES[t] == t_type:
                triples.append({
                    "kind": "edge",
                    "source": s, "target": t, "relation": rel,
                    "description": f"来自文档《{doc['title']}》",
                    "source_doc": doc["title"],
                })
    return triples


# 内置规则兜底：演示"规则抽取"路线（生产环境应来自领域规则库）
RULE_TRIPLES: dict[str, list[dict]] = {
    "组织架构": [
        {"kind": "edge", "source": "李四", "target": "研发部", "relation": "MANAGES", "description": "李四管理研发部", "source_doc": "组织架构"},
        {"kind": "edge", "source": "张三", "target": "李四", "relation": "REPORTS_TO", "description": "张三汇报给李四", "source_doc": "组织架构"},
        {"kind": "edge", "source": "王五", "target": "李四", "relation": "REPORTS_TO", "description": "王五汇报给李四", "source_doc": "组织架构"},
        {"kind": "edge", "source": "赵六", "target": "市场部", "relation": "MANAGES", "description": "赵六管理市场部", "source_doc": "组织架构"},
    ],
    "项目概览": [
        {"kind": "edge", "source": "研发部", "target": "项目X", "relation": "OWNS", "description": "研发部拥有项目X", "source_doc": "项目概览"},
        {"kind": "edge", "source": "研发部", "target": "项目Y", "relation": "OWNS", "description": "研发部拥有项目Y", "source_doc": "项目概览"},
        {"kind": "edge", "source": "市场部", "target": "项目Z", "relation": "OWNS", "description": "市场部拥有项目Z", "source_doc": "项目概览"},
    ],
    "智云平台（项目X）": [
        {"kind": "edge", "source": "项目X", "target": "Python", "relation": "USES", "description": "项目X使用Python", "source_doc": "项目X"},
        {"kind": "edge", "source": "项目X", "target": "FastAPI", "relation": "USES", "description": "项目X使用FastAPI", "source_doc": "项目X"},
        {"kind": "edge", "source": "项目X", "target": "PostgreSQL", "relation": "USES", "description": "项目X使用PostgreSQL", "source_doc": "项目X"},
        {"kind": "edge", "source": "项目X", "target": "Redis", "relation": "USES", "description": "项目X使用Redis", "source_doc": "项目X"},
        {"kind": "edge", "source": "张三", "target": "项目X", "relation": "WORKS_ON", "description": "张三参与项目X", "source_doc": "项目X"},
        {"kind": "edge", "source": "王五", "target": "项目X", "relation": "WORKS_ON", "description": "王五参与项目X", "source_doc": "项目X"},
    ],
    "星图分析（项目Y）": [
        {"kind": "edge", "source": "项目Y", "target": "Python", "relation": "USES", "description": "项目Y使用Python", "source_doc": "项目Y"},
        {"kind": "edge", "source": "项目Y", "target": "ClickHouse", "relation": "USES", "description": "项目Y使用ClickHouse", "source_doc": "项目Y"},
        {"kind": "edge", "source": "项目Y", "target": "React", "relation": "USES", "description": "项目Y使用React", "source_doc": "项目Y"},
        {"kind": "edge", "source": "李四", "target": "项目Y", "relation": "WORKS_ON", "description": "李四负责项目Y", "source_doc": "项目Y"},
    ],
    "品牌官网（项目Z）": [
        {"kind": "edge", "source": "项目Z", "target": "Next.js", "relation": "USES", "description": "项目Z使用Next.js", "source_doc": "项目Z"},
        {"kind": "edge", "source": "项目Z", "target": "Vercel", "relation": "USES", "description": "项目Z使用Vercel", "source_doc": "项目Z"},
        {"kind": "edge", "source": "赵六", "target": "项目Z", "relation": "WORKS_ON", "description": "赵六负责项目Z", "source_doc": "项目Z"},
    ],
}


def extract_triples_rules(doc: dict) -> list[dict]:
    return RULE_TRIPLES.get(doc["title"], [])


# ---------------------------------------------------------------------------
# 建图 / 存取
# ---------------------------------------------------------------------------
def build_graph(use_llm: bool = True, max_docs: int | None = None) -> nx.MultiDiGraph:
    docs = load_docs()
    if max_docs:
        docs = docs[:max_docs]

    G = nx.MultiDiGraph()
    for doc in docs:
        triples = extract_triples_llm(doc) if use_llm else []
        if not triples:
            triples = extract_triples_rules(doc)

        for tr in triples:
            if tr["kind"] == "node":
                if not G.has_node(tr["name"]):
                    G.add_node(tr["name"], type=tr["type"], description=tr["description"])
                else:
                    desc = G.nodes[tr["name"]].get("description", "")
                    if tr["description"] not in desc:
                        G.nodes[tr["name"]]["description"] = desc + "；" + tr["description"]
            else:
                s, t, rel = tr["source"], tr["target"], tr["relation"]
                for n in (s, t):
                    if not G.has_node(n):
                        G.add_node(n, type=NODE_TYPES[n], description="")
                key = (s, t, rel)
                if G.has_edge(s, t, key=key):
                    G.edges[s, t, key]["count"] += 1
                    if tr["description"] not in G.edges[s, t, key]["description"]:
                        G.edges[s, t, key]["description"] += "；" + tr["description"]
                else:
                    G.add_edge(s, t, key=key, relation=rel, count=1,
                               description=tr["description"], source_doc=tr["source_doc"])
    return G


def save_graph(G: nx.DiGraph) -> None:
    nodes = [
        {"id": n, "type": data.get("type", ""), "description": data.get("description", "")}
        for n, data in G.nodes(data=True)
    ]
    edges = [
        {"source": u, "target": v, "relation": d.get("relation", ""),
         "description": d.get("description", ""), "count": d.get("count", 1)}
        for u, v, d in G.edges(data=True)
    ]
    KG_FILE.write_text(
        json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_graph() -> nx.MultiDiGraph:
    data = json.loads(KG_FILE.read_text(encoding="utf-8"))
    G = nx.MultiDiGraph()
    for n in data["nodes"]:
        G.add_node(n["id"], type=n.get("type", ""), description=n.get("description", ""))
    for e in data["edges"]:
        G.add_edge(e["source"], e["target"], key=e.get("relation", ""), relation=e.get("relation", ""),
                   description=e.get("description", ""), count=e.get("count", 1))
    return G


def ensure_graph(use_llm: bool = True, max_docs: int | None = None) -> nx.DiGraph:
    if KG_FILE.exists():
        return load_graph()
    G = build_graph(use_llm=use_llm, max_docs=max_docs)
    save_graph(G)
    return G


# ---------------------------------------------------------------------------
# 序列化
# ---------------------------------------------------------------------------
def serialize_subgraph(G: nx.DiGraph, nodes: list[str], max_nodes: int = 40) -> str:
    selected = nodes[:max_nodes]
    sub = G.subgraph(selected)
    lines = ["【节点】"]
    for n, data in sub.nodes(data=True):
        lines.append(f"- {n} ({data.get('type', '')}): {data.get('description', '')}")
    lines.append("【关系】")
    for u, v, k, d in sub.edges(keys=True, data=True):
        lines.append(f"- {u} -{d.get('relation', '')}-> {v}（{d.get('description', '')}）")
    return "\n".join(lines)
