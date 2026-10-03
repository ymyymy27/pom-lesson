"""
迷你搜索引擎公共模块
====================
1. 中文分词：词典正向最大匹配 + 字符 bigram 兜底
2. 语料/查询加载
3. 倒排索引构建
4. BM25 打分
5. 向量化（Ollama 可选，失败退回 bigram 向量）与 RRF 融合
"""

import io
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_DIR = Path(__file__).parent
CORPUS_FILE = BASE_DIR / "data" / "corpus.txt"
QUERIES_FILE = BASE_DIR / "data" / "queries.tsv"

OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "qwen3-embedding:4b"

# ---------------------------------------------------------------------------
# 1. 分词
# ---------------------------------------------------------------------------
DICTIONARY = [
    "报销", "超过", "财务总监", "部门主管", "发票", "差旅", "审批",
    "年假", "入职", "带薪", "工作日", "申请", "远程办公", "登记", "发布周",
    "加班", "工资", "法定节假日", "后端", "技术栈", "FastAPI", "Python",
    "PostgreSQL", "Redis", "ClickHouse", "数据库", "缓存", "分析", "备份",
    "智云平台", "订单", "服务", "Kubernetes", "星图分析", "可视化",
    "数据大屏", "指标", "报表", "新员工", "入职流程", "身份证", "学历证书",
    "离职证明", "工位", "培训", "薪资", "发放", "工资条", "机器学习",
    "训练", "GPU", "模型", "模型仓库", "部署", "vLLM", "推理服务",
    "灰度发布", "回滚", "监控", "告警", "限流", "数据", "存储", "主库",
    "读写分离", "大屏", "训练队列", "注册", "版本", "压测", "评测",
    "远程", "办公", "每周", "两天", "主管", "流程", "制度", "公司",
    "研发部", "项目", "技术", "系统", "规范", "在线",
]

STOPWORDS = {"的", "了", "是", "在", "和", "与", "及", "或", "吗", "呢",
             "啊", "吧", "得", "地", "有", "对", "从", "为", "上", "下"}

MAX_WORD_LEN = 4


def tokenize(text: str) -> list[str]:
    """词典正向最大匹配 + bigram 兜底（文档与查询共用）。"""
    text = text.lower().replace(" ", "")
    words = {w.lower() for w in DICTIONARY}
    tokens: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        matched = None
        for L in range(MAX_WORD_LEN, 1, -1):
            if i + L <= n and text[i:i + L] in words:
                matched = text[i:i + L]
                break
        if matched:
            tokens.append(matched)
            i += len(matched)
        else:
            # 连续字母/数字整体保留（如 5000、vllm）
            if text[i].isascii() and text[i].isalnum():
                j = i
                while j < n and text[j].isascii() and text[j].isalnum():
                    j += 1
                tokens.append(text[i:j])
                i = j
            else:
                # bigram 兜底：保证任何文本都能切出词项
                tokens.append(text[i:i + 2] if i + 1 < n else text[i])
                i += 1
    return [t for t in tokens
            if t not in STOPWORDS and re.search(r"[\u4e00-\u9fff0-9a-z]", t)]


# ---------------------------------------------------------------------------
# 2. 数据加载
# ---------------------------------------------------------------------------
def load_corpus() -> list[dict]:
    docs: list[dict] = []
    cur_id, cur_title, buf = None, None, []
    for line in CORPUS_FILE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\[(\d+)\]\s*(.*)", line)
        if m:
            if cur_id is not None:
                docs.append({"id": cur_id, "title": cur_title, "content": " ".join(buf).strip()})
            cur_id = int(m.group(1))
            cur_title = m.group(2).strip()
            buf = []
        else:
            buf.append(line.strip())
    if cur_id is not None:
        docs.append({"id": cur_id, "title": cur_title, "content": " ".join(buf).strip()})
    return docs


def load_queries() -> list[dict]:
    out = []
    for line in QUERIES_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        q, rel = line.split("\t")
        rel_ids = [int(x) for x in rel.split(",") if x.strip()]
        out.append({"query": q.strip(), "relevant": rel_ids})
    return out


# ---------------------------------------------------------------------------
# 3. 倒排索引
# ---------------------------------------------------------------------------
def build_index(docs: list[dict]) -> dict:
    index: dict[str, list] = defaultdict(list)  # term -> [(doc_id, tf, [positions])]
    for doc in docs:
        text = doc["title"] + " " + doc["content"]
        pos = 0
        for term in tokenize(text):
            if term in index and index[term][-1][0] == doc["id"]:
                entry = index[term][-1]
                entry[1] += 1
                entry[2].append(pos)
            else:
                index[term].append([doc["id"], 1, [pos]])
            pos += 1
    return dict(index)


# ---------------------------------------------------------------------------
# 4. BM25
# ---------------------------------------------------------------------------
class BM25:
    def __init__(self, docs: list[dict], index: dict, k1: float = 1.5, b: float = 0.75):
        self.docs = docs
        self.index = index
        self.k1 = k1
        self.b = b
        self.doc_len = {d["id"]: len(tokenize(d["title"] + " " + d["content"])) for d in docs}
        self.avgdl = sum(self.doc_len.values()) / max(1, len(docs))
        self.N = len(docs)
        self.df = {term: len(postings) for term, postings in index.items()}

    def idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log((self.N - df + 0.5) / (df + 0.5) + 1e-6)

    def score(self, query: str, doc_id: int) -> float:
        terms = tokenize(query)
        dl = self.doc_len.get(doc_id, 0)
        tf_map = Counter()
        for term in terms:
            for entry in self.index.get(term, []):
                if entry[0] == doc_id:
                    tf_map[term] = entry[1]
                    break
        total = 0.0
        for term in set(terms):
            tf = tf_map.get(term, 0)
            if tf == 0:
                continue
            norm = 1 - self.b + self.b * dl / self.avgdl
            total += self.idf(term) * (tf * (self.k1 + 1)) / (tf + self.k1 * norm)
        return total

    def search(self, query: str, top_k: int = 5) -> list[tuple[int, float]]:
        scored = [(d["id"], self.score(query, d["id"])) for d in self.docs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [x for x in scored if x[1] > 0][:top_k]


# ---------------------------------------------------------------------------
# 5. 向量化与 RRF
# ---------------------------------------------------------------------------
def embed(texts: list[str]) -> list[list[float]] | None:
    try:
        import httpx

        resp = httpx.post(
            f"{OLLAMA_URL}/api/embed",
            json={"model": EMBED_MODEL, "input": texts},
            timeout=180.0,
        )
        return resp.json().get("embeddings")
    except Exception:
        return None


def bigram_vector(text: str) -> Counter:
    """离线兜底：字符 bigram 词袋向量。"""
    t = re.sub(r"\s+", "", text.lower())
    return Counter(t[i:i + 2] for i in range(max(0, len(t) - 1)))


def cosine(a: Counter | list, b: Counter | list) -> float:
    if isinstance(a, Counter):
        common = set(a) & set(b)
        dot = sum(a[k] * b[k] for k in common)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
    else:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb + 1e-12)


def dense_search(query: str, docs: list[dict]) -> list[tuple[int, float]]:
    texts = [d["title"] + " " + d["content"] for d in docs]
    vecs = embed(texts)
    if vecs:
        qv = embed([query])[0]
        scored = [(d["id"], cosine(qv, v)) for d, v in zip(docs, vecs)]
    else:
        qv = bigram_vector(query)
        scored = [(d["id"], cosine(qv, bigram_vector(d["title"] + " " + d["content"]))) for d in docs]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:5]


def rrf_fuse(ranked_lists: list[list[tuple[int, float]]], k: int = 60) -> list[tuple[int, float]]:
    scores: dict[int, float] = {}
    for ranked in ranked_lists:
        for rank, (doc_id, _) in enumerate(ranked):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def snippet(doc: dict, query: str, size: int = 60) -> str:
    text = doc["title"] + "：" + doc["content"]
    terms = [t for t in tokenize(query) if len(t) > 1]
    low = text.lower()
    pos = -1
    for term in terms:
        p = low.find(term.lower())
        if p >= 0:
            pos = p
            break
    if pos < 0:
        return text[:size] + "…"
    start = max(0, pos - size // 3)
    return text[start:start + size] + "…"
