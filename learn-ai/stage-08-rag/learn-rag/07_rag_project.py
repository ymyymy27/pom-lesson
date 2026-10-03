import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第7课：完整项目 - 知识库问答系统
==============================================================================

整合前6课知识，构建一个端到端的知识库问答系统：

功能：
1. 文档管理（加载/分块/索引）
2. 多模式检索（向量/BM25/混合）
3. 上下文优化（重排序/压缩）
4. 生成回答（引用/验证）
5. 评估系统

架构：
  文档 → 分块 → Embedding → 向量库
  用户问题 → 检索 → 上下文优化 → LLM生成 → 回答
==============================================================================
"""

import json
import re
import math
import hashlib
import numpy as np
from collections import Counter
from datetime import datetime

import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"

def chat(prompt: str, system: str = "", temperature: float = 0.0) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL, "messages": messages, "stream": False,
            "options": {"temperature": temperature, "num_predict": 600}
        }, timeout=180.0)
        return resp.json().get("message", {}).get("content", "")
    except:
        return "[模拟回答] 这是基于检索到的文档生成的回答。"

def embed(texts: list) -> list:
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/embed", json={
            "model": "qwen3-embedding:4b", "input": texts,
        }, timeout=180.0)
        return resp.json().get("embeddings", [])
    except:
        np.random.seed(hash(str(texts)) % 2**31)
        return [np.random.randn(2560).tolist() for _ in texts]

print("=" * 60)
print("第7课：完整项目 - 知识库问答系统")
print("=" * 60)

# ============================================================================
# 1. 文本分块器
# ============================================================================

class TextChunker:
    def __init__(self, chunk_size=400, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str, metadata: dict = None) -> list:
        chunks = self._recursive_split(text)
        return [{"text": c.strip(), "metadata": {**(metadata or {}), "chunk_id": i}}
                for i, c in enumerate(chunks) if c.strip()]

    def _recursive_split(self, text: str) -> list:
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []
        for sep in ["\n\n", "\n", "。", "！", "？", ".", " "]:
            if sep not in text:
                continue
            parts = text.split(sep)
            merged, current = [], ""
            for part in parts:
                candidate = current + sep + part if current else part
                if len(candidate) <= self.chunk_size:
                    current = candidate
                else:
                    if current.strip():
                        merged.append(current.strip())
                    current = part
            if current.strip():
                merged.append(current.strip())
            if len(merged) > 1:
                return merged
        return [text[i:i+self.chunk_size]
                for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]

# ============================================================================
# 2. BM25 索引
# ============================================================================

class BM25Index:
    def __init__(self, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.docs, self.tf_per_doc, self.doc_lens = [], [], []
        self.doc_freqs = {}
        self.avg_len = 0

    def _tokenize(self, text):
        return re.findall(r'[\u4e00-\u9fff]{1,4}|[a-zA-Z]+[\-]?[a-zA-Z]*\d*', text.lower())

    def index(self, documents):
        self.docs = documents
        self.doc_freqs, self.tf_per_doc, self.doc_lens = {}, [], []
        for doc in documents:
            tokens = self._tokenize(doc)
            self.doc_lens.append(len(tokens))
            tf = Counter(tokens)
            self.tf_per_doc.append(tf)
            for w in set(tokens):
                self.doc_freqs[w] = self.doc_freqs.get(w, 0) + 1
        self.avg_len = sum(self.doc_lens) / len(self.doc_lens) if self.doc_lens else 1

    def search(self, query, top_k=10):
        tokens = self._tokenize(query)
        n = len(self.docs)
        scores = []
        for i in range(n):
            score = 0
            for t in tokens:
                df = self.doc_freqs.get(t, 0)
                if df == 0: continue
                idf = math.log((n - df + 0.5) / (df + 0.5) + 1)
                tf = self.tf_per_doc[i].get(t, 0)
                dl = self.doc_lens[i]
                score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avg_len))
            scores.append((i, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

# ============================================================================
# 3. 知识库问答系统
# ============================================================================
print("\n--- 1. 构建系统 ---")

class KnowledgeQA:
    """知识库问答系统"""

    def __init__(self, chunk_size=400):
        self.chunker = TextChunker(chunk_size)
        self.bm25 = BM25Index()
        self.chunks = []
        self.embeddings = []
        self.doc_hashes = set()
        self.history = []
        self.stats = {"docs": 0, "chunks": 0, "queries": 0}

    # --- 文档管理 ---

    def add_document(self, text: str, source: str = "unknown") -> dict:
        doc_hash = hashlib.md5(text.encode()).hexdigest()
        if doc_hash in self.doc_hashes:
            return {"status": "duplicate"}
        self.doc_hashes.add(doc_hash)

        new_chunks = self.chunker.split(text, {"source": source})
        self.chunks.extend(new_chunks)
        self.stats["docs"] += 1
        self.stats["chunks"] = len(self.chunks)
        return {"status": "ok", "chunks": len(new_chunks)}

    def build_index(self) -> dict:
        texts = [c["text"] for c in self.chunks]
        self.embeddings = embed(texts)
        self.bm25.index(texts)
        return {"indexed": len(texts), "dim": len(self.embeddings[0]) if self.embeddings else 0}

    # --- 检索 ---

    def _vector_search(self, query, top_k=10):
        q_emb = embed([query])[0]
        scores = []
        for i, emb in enumerate(self.embeddings):
            a, b = np.array(q_emb), np.array(emb)
            norm = np.linalg.norm(a) * np.linalg.norm(b)
            sim = float(np.dot(a, b) / norm) if norm > 0 else 0
            scores.append((i, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def retrieve(self, query: str, top_k: int = 5,
                 mode: str = "hybrid", alpha: float = 0.5) -> list:
        """多模式检索"""
        if mode == "vector":
            scored = self._vector_search(query, top_k)
        elif mode == "bm25":
            scored = self.bm25.search(query, top_k)
        else:
            # RRF 混合
            k_rrf = 60
            vec_results = self._vector_search(query, len(self.chunks))
            vec_ranks = {idx: rank for rank, (idx, _) in enumerate(vec_results)}
            bm25_results = self.bm25.search(query, len(self.chunks))
            bm25_ranks = {idx: rank for rank, (idx, _) in enumerate(bm25_results)}
            rrf = {}
            for i in range(len(self.chunks)):
                rrf[i] = (alpha / (k_rrf + vec_ranks.get(i, 999)) +
                          (1 - alpha) / (k_rrf + bm25_ranks.get(i, 999)))
            scored = sorted(rrf.items(), key=lambda x: x[1], reverse=True)[:top_k]

        return [{"text": self.chunks[idx]["text"],
                 "score": round(score, 4),
                 "metadata": self.chunks[idx]["metadata"]}
                for idx, score in scored]

    # --- 上下文优化 ---

    def _reorder_docs(self, docs: list) -> list:
        """Lost-in-the-Middle 重排"""
        if len(docs) <= 2:
            return docs
        reordered = []
        for i, doc in enumerate(docs):
            if i % 2 == 0:
                reordered.insert(0, doc)
            else:
                reordered.append(doc)
        return reordered

    # --- 生成 ---

    def answer(self, question: str, top_k: int = 5,
               mode: str = "hybrid", with_citation: bool = True) -> dict:
        """端到端问答"""
        self.stats["queries"] += 1

        # 1. 检索
        retrieved = self.retrieve(question, top_k, mode)

        # 2. 重排
        retrieved = self._reorder_docs(retrieved)

        # 3. 构建上下文
        context_parts = []
        for i, r in enumerate(retrieved):
            src = r["metadata"].get("source", "未知")
            context_parts.append(f"[来源{i+1}: {src}]\n{r['text']}")
        context = "\n\n".join(context_parts)

        # 4. 生成
        system = """你是知识库问答助手。根据检索到的文档回答问题。
规则：
1. 只基于提供的文档回答，不编造信息
2. 关键论述后用 [来源X] 标注出处
3. 无法回答时明确说明"根据已有资料无法回答"
4. 回答简洁、准确、有条理"""

        prompt = f"检索到的文档：\n{context}\n\n问题：{question}"
        answer_text = chat(prompt, system)

        # 5. 记录历史
        record = {
            "question": question,
            "answer": answer_text,
            "sources": [r["metadata"].get("source") for r in retrieved],
            "top_scores": [r["score"] for r in retrieved[:3]],
            "timestamp": datetime.now().isoformat(),
        }
        self.history.append(record)

        return {
            "answer": answer_text,
            "sources": retrieved,
            "context_length": len(context),
        }

    def get_stats(self) -> dict:
        return {**self.stats, "history": len(self.history)}

# ============================================================================
# 4. 使用系统
# ============================================================================
print("\n--- 2. 导入文档 ---")

qa = KnowledgeQA(chunk_size=300)

# 导入知识文档
documents = {
    "公司制度.md": """# 公司员工手册

## 年假制度
员工入职满一年可享受5天年假，满三年10天，满五年15天。年假需提前3个工作日在OA系统中申请，经直属主管审批后生效。未使用的年假可顺延至次年3月底前使用。

## 报销制度
员工需在费用发生后30天内提交报销申请。报销需附上发票原件、费用明细和部门审批单。单笔超过5000元需部门经理审批，超过20000元需总监审批。差旅报销标准：住宿一线城市500元/晚，二线城市350元/晚。

## 远程办公
员工每周可申请2天远程办公，需提前1天在OA系统中提交申请。远程期间需保持9:00-18:00在线，参加所有已排会议。团队会议日不可远程。""",

    "技术架构.md": """# 技术架构文档

## 后端架构
后端使用 Python + FastAPI 框架，采用分层架构：API层 → Service层 → Repository层 → Database层。数据库使用 PostgreSQL 14，缓存使用 Redis 7，消息队列使用 RabbitMQ。

## 前端架构
前端使用 React 18 + TypeScript 5，状态管理使用 Zustand，UI组件库为 Ant Design 5。构建工具为 Vite，包管理器为 pnpm。

## 部署架构
使用 Docker + Kubernetes 部署在阿里云 ACK 集群。CI/CD 流水线基于 GitHub Actions，包含代码检查、单元测试、构建镜像、部署到预发环境、自动化测试、部署到生产环境等步骤。监控使用 Prometheus + Grafana。""",

    "产品手册.md": """# 产品使用手册

## 用户注册
用户可通过手机号或邮箱注册。手机号注册需短信验证码，邮箱注册需点击验证链接。注册后可设置个人头像和昵称。

## 订单管理
用户下单后可在订单页面查看订单状态。订单状态包括：待支付、已支付、配送中、已完成、已取消。支付超时30分钟自动取消。已支付订单可在发货前申请退款。

## 会员体系
会员分为银卡、金卡、钻石三个等级。银卡：累计消费满1000元自动升级，享95折。金卡：累计消费满5000元，享9折+包邮。钻石：累计消费满20000元，享85折+包邮+专属客服。""",
}

for filename, content in documents.items():
    result = qa.add_document(content, source=filename)
    print(f"  {filename}: {result}")

index_info = qa.build_index()
print(f"索引构建: {index_info}")

# ============================================================================
# 5. 问答演示
# ============================================================================
print("\n--- 3. 问答演示 ---")

questions = [
    "年假有几天？怎么申请？",
    "报销超过5000元怎么办？",
    "公司后端用什么技术栈？",
    "会员有哪些等级和权益？",
    "CI/CD 流程是什么？",
]

for q in questions:
    result = qa.answer(q, top_k=3)
    print(f"\n  Q: {q}")
    print(f"  A: {result['answer'][:120]}...")
    print(f"  来源: {[s['metadata'].get('source','?') for s in result['sources'][:2]]}")

# ============================================================================
# 6. 检索模式对比
# ============================================================================
print("\n\n--- 4. 模式对比 ---")

test_q = "FastAPI PostgreSQL 部署"
for mode in ["vector", "bm25", "hybrid"]:
    results = qa.retrieve(test_q, 2, mode=mode)
    docs_str = " | ".join(r["text"][:30] for r in results)
    print(f"  {mode:>7}: {docs_str}")

# ============================================================================
# 7. 统计
# ============================================================================
stats = qa.get_stats()
print(f"""
┌────────────────────────────────────────────────────────┐
│         知识库问答系统 - 项目架构                       │
├────────────────────────────────────────────────────────┤
│                                                        │
│  KnowledgeQA（主系统）                                 │
│  ├── add_document()    添加文档                        │
│  ├── build_index()     构建索引（向量+BM25）           │
│  ├── retrieve()        多模式检索                      │
│  │   ├── vector        纯向量语义搜索                  │
│  │   ├── bm25          纯关键词搜索                    │
│  │   └── hybrid        RRF混合检索                     │
│  ├── answer()          端到端问答                      │
│  │   ├── 检索          多模式检索                      │
│  │   ├── 重排          Lost-in-the-Middle              │
│  │   ├── 构建上下文    带来源标注                      │
│  │   └── LLM生成       带引用的回答                    │
│  └── get_stats()       系统统计                        │
│                                                        │
│  TextChunker（分块器）                                 │
│  └── 递归字符分割 + 元数据                             │
│                                                        │
│  BM25Index（关键词索引）                               │
│  └── TF-IDF 变体关键词检索                             │
│                                                        │
│  整合的知识                                            │
│  ├── 第1课: RAG 架构与原理                            │
│  ├── 第2课: 文档加载与解析                            │
│  ├── 第3课: 索引管道（分块→Embedding→存储）          │
│  ├── 第4课: 检索策略（向量/BM25/混合/重排序）        │
│  ├── 第5课: RAG 优化（Query改写/上下文/生成）        │
│  └── 第6课: RAG 评估（忠实度/相关性/召回率）         │
│                                                        │
│  统计: 文档{stats['docs']}篇, 块{stats['chunks']}个, 查询{stats['queries']}次        │
│                                                        │
│  扩展方向                                              │
│  → ChromaDB/Milvus 持久化存储                          │
│  → Reranker 精排序（bge-reranker）                     │
│  → Multi-Query / HyDE 查询优化                         │
│  → 多轮对话（对话历史上下文）                         │
│  → FastAPI Web 接口 + 流式输出                         │
│  → RAGAS 自动化评估                                    │
│  → 文档增量更新                                        │
└────────────────────────────────────────────────────────┘
""")

print("=" * 60)
print("[完成] 第7课完成！你已经学会了：")
print("  [v] 端到端知识库问答系统")
print("  [v] 文档管理（加载/分块/去重/索引）")
print("  [v] 多模式检索（向量/BM25/混合RRF）")
print("  [v] 上下文优化（Lost-in-the-Middle重排）")
print("  [v] 带引用的 LLM 生成")
print("  [v] 整合前6课全部核心知识")
print("=" * 60)
print("\nlearn-rag 课程全部完成！🎉")
