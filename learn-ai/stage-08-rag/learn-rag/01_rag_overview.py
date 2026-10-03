import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第1课：RAG 架构与原理
==============================================================================

RAG = Retrieval-Augmented Generation（检索增强生成）
让 LLM 基于检索到的外部知识回答问题，而非仅凭"记忆"。

核心思路：先搜索相关文档，再让 LLM 基于文档回答。

本课内容：
1. 为什么需要 RAG
2. RAG 核心架构
3. RAG 工作流程
4. RAG vs 微调 vs Prompt Engineering
5. RAG 的挑战
6. 简单 RAG 演示
==============================================================================
"""

import json
import numpy as np
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
            "options": {"temperature": temperature, "num_predict": 250}
        }, timeout=180.0)
        return resp.json().get("message", {}).get("content", "")
    except:
        return "[模拟回答]"

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
print("第1课：RAG 架构与原理")
print("=" * 60)

# ============================================================================
# 1. 为什么需要 RAG
# ============================================================================
print("\n--- 1. 为什么需要 RAG ---")
print("""
LLM 的三大问题：

  ❌ 知识截止：训练数据有截止日期，不知道最新信息
  ❌ 幻觉：当不确定时，LLM 会"编造"看似合理的答案
  ❌ 私域知识：不了解你公司的内部文档/数据

RAG 如何解决：

  ✅ 知识更新：检索最新文档，不受训练截止限制
  ✅ 减少幻觉：回答基于检索到的文档，有据可查
  ✅ 私域问答：索引你的内部文档，构建专属知识库
  ✅ 无需训练：不需要微调模型，只需要管理文档
  ✅ 可溯源：每个回答都能追溯到原始文档

典型应用：
  • 企业知识库问答（公司制度/产品手册）
  • 客服机器人（FAQ/操作指南）
  • 法律助手（法条/案例检索）
  • 学术助手（论文检索与总结）
  • 代码助手（项目文档/API文档）
""")

# ============================================================================
# 2. RAG 核心架构
# ============================================================================
print("\n--- 2. 核心架构 ---")
print("""
RAG 分两个阶段：

┌─────────────────── 离线索引阶段 ───────────────────┐
│                                                      │
│  原始文档                                            │
│  (PDF/Word/MD/HTML/CSV)                              │
│      ↓                                               │
│  文档加载 → 文本提取                                 │
│      ↓                                               │
│  文本分块 (Chunking)                                 │
│  - 每块 300-800 字符                                 │
│  - 保持语义完整                                      │
│      ↓                                               │
│  Embedding → 向量化                                  │
│      ↓                                               │
│  存入向量数据库 (ChromaDB/FAISS/Milvus)              │
│                                                      │
└──────────────────────────────────────────────────────┘

┌─────────────────── 在线查询阶段 ───────────────────┐
│                                                      │
│  用户提问                                            │
│      ↓                                               │
│  Query Embedding                                     │
│      ↓                                               │
│  向量检索 → Top-K 相关文档块                         │
│      ↓                                               │
│  (可选) 重排序 / 过滤                                │
│      ↓                                               │
│  构建 Prompt = 系统指令 + 检索结果 + 用户问题        │
│      ↓                                               │
│  LLM 生成回答                                        │
│      ↓                                               │
│  返回给用户（附引用来源）                            │
│                                                      │
└──────────────────────────────────────────────────────┘
""")

# ============================================================================
# 3. 工作流程演示
# ============================================================================
print("\n--- 3. 工作流程 ---")

# 模拟知识库
knowledge_base = [
    "公司年假制度：员工入职满一年可享受5天年假，满三年10天，满五年15天。年假需提前3个工作日申请。",
    "报销流程：员工需在费用发生后30天内提交报销申请，附上发票原件和审批单。超过5000元需部门经理审批。",
    "远程办公政策：员工每周可申请2天远程办公，需提前1天在OA系统中申请。远程期间需保持在线状态。",
    "技术架构：公司后端使用 Python + FastAPI，前端使用 React + TypeScript，数据库为 PostgreSQL，缓存用 Redis。",
    "新员工入职流程：入职当天需携带身份证、学历证书、离职证明。HR会安排工位和设备，导师会在第一周安排培训。",
    "薪资发放：每月15日发放上月薪资，如遇节假日则提前至最近工作日。工资条可在HR系统中查看。",
]

print(f"知识库: {len(knowledge_base)} 条文档")

# 索引
print("\n[索引阶段]")
doc_embeddings = embed(knowledge_base)
print(f"  向量化完成: {len(doc_embeddings)} 条, 维度: {len(doc_embeddings[0]) if doc_embeddings else 0}")

# 查询
def simple_rag(question: str, top_k: int = 2) -> str:
    """简单 RAG 流程"""
    # 1. Query Embedding
    query_emb = embed([question])[0]

    # 2. 向量检索
    scores = []
    for i, doc_emb in enumerate(doc_embeddings):
        a, b = np.array(query_emb), np.array(doc_emb)
        sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        scores.append((i, sim))
    scores.sort(key=lambda x: x[1], reverse=True)
    top_docs = scores[:top_k]

    # 3. 构建上下文
    context = "\n\n".join(f"[文档{i+1}] {knowledge_base[idx]}" for i, (idx, _) in enumerate(top_docs))

    # 4. 构建 Prompt
    system = """你是公司知识库问答助手。请根据以下检索到的文档回答问题。
规则：
1. 只基于提供的文档回答，不编造信息
2. 如果文档中没有相关信息，说"根据已有资料无法回答"
3. 回答简洁、准确"""

    prompt = f"检索到的文档：\n{context}\n\n问题：{question}"

    # 5. LLM 生成
    answer = chat(prompt, system)

    return answer, top_docs, context

print("\n[查询阶段]")
questions = [
    "年假有几天？怎么申请？",
    "报销超过5000元怎么办？",
    "公司用什么技术栈？",
]

for q in questions:
    answer, top_docs, context = simple_rag(q)
    print(f"\n  Q: {q}")
    print(f"  检索: {[(knowledge_base[idx][:20]+'...', f'{sim:.3f}') for idx, sim in top_docs]}")
    print(f"  A: {answer[:100]}...")

# ============================================================================
# 4. RAG vs 微调 vs Prompt Engineering
# ============================================================================
print("\n\n--- 4. 方案对比 ---")
print("""
┌──────────────┬─────────────────┬─────────────────┬─────────────────┐
│              │ Prompt Eng.      │     RAG          │    微调          │
├──────────────┼─────────────────┼─────────────────┼─────────────────┤
│  知识来源    │ Prompt 中传入    │ 外部知识库检索  │ 训练到模型参数  │
│  知识更新    │ 改 Prompt       │ 更新文档即可    │ 需重新训练      │
│  适合数据量  │ <10页           │ 10~10000+页     │ 100+条QA        │
│  幻觉控制    │ 中              │ 好（有出处）    │ 一般            │
│  实现成本    │ 低              │ 中              │ 高              │
│  推理成本    │ 高(长Prompt)    │ 中              │ 低              │
│  定制化      │ 低              │ 中              │ 高              │
│  实时性      │ 需手动更新      │ 实时            │ 需重新训练      │
└──────────────┴─────────────────┴─────────────────┴─────────────────┘

推荐组合：
  RAG + Prompt Engineering（最常见）
  RAG + 微调（最强，微调优化格式/风格，RAG提供知识）
""")

# ============================================================================
# 5. RAG 的挑战
# ============================================================================
print("\n--- 5. RAG 的挑战 ---")
print("""
┌──────────────────┬──────────────────────────────────────┐
│  挑战             │  应对策略                             │
├──────────────────┼──────────────────────────────────────┤
│  检索不到相关文档│  混合检索(向量+关键词)               │
│                  │  Query改写/扩展                      │
│                  │  优化分块策略                        │
├──────────────────┼──────────────────────────────────────┤
│  检索到不相关文档│  Reranking 重排序                    │
│                  │  相似度阈值过滤                      │
│                  │  元数据过滤                          │
├──────────────────┼──────────────────────────────────────┤
│  LLM 忽略检索内容│  优化 Prompt 设计                    │
│                  │  Lost-in-the-Middle 文档重排         │
│                  │  上下文压缩                          │
├──────────────────┼──────────────────────────────────────┤
│  回答有幻觉      │  引用来源标注                        │
│                  │  幻觉检测（事实核查）                │
│                  │  temperature=0                       │
├──────────────────┼──────────────────────────────────────┤
│  多轮对话上下文  │  对话历史摘要                        │
│                  │  历史消息作为检索上下文              │
└──────────────────┴──────────────────────────────────────┘
""")

# ============================================================================
# 6. 无 RAG vs 有 RAG
# ============================================================================
print("\n--- 6. 对比演示 ---")

question = "公司的远程办公政策是什么？每周能远程几天？"

# 无 RAG
no_rag = chat(question, "你是公司的HR助手")
print(f"无 RAG: {no_rag[:100]}...")

# 有 RAG
rag_answer, _, _ = simple_rag(question)
print(f"有 RAG: {rag_answer[:100]}...")

print("""
对比：
  无RAG → LLM 只能猜测或给通用回答，可能产生幻觉
  有RAG → LLM 基于真实文档回答，准确且可溯源
""")

print("=" * 60)
print("[完成] 第1课完成！你已经学会了：")
print("  [v] RAG 解决的三大问题（截止/幻觉/私域）")
print("  [v] RAG 两阶段架构（索引+查询）")
print("  [v] 简单 RAG 完整流程实现")
print("  [v] RAG vs 微调 vs Prompt Engineering")
print("  [v] RAG 的五大挑战及应对策略")
print("  [v] 有/无 RAG 的效果对比")
print("=" * 60)
print("\n下一课：02_document_loading.py - 文档加载")
