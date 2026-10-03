import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第4课：FAISS 高性能向量检索
==============================================================================

FAISS = Facebook AI Similarity Search
高性能向量检索库，支持十亿级向量搜索。

本课内容：
1. FAISS 核心概念
2. 索引类型详解
3. 索引构建与搜索
4. ID 映射与元数据
5. 保存与加载
6. 性能优化
==============================================================================
"""

import time
import numpy as np

print("=" * 60)
print("第4课：FAISS 高性能检索")
print("=" * 60)

# ============================================================================
# 1. 核心概念
# ============================================================================
print("\n--- 1. 核心概念 ---")
print("""
FAISS 是纯向量检索库（不是数据库）：
  ✅ 超高速向量搜索（十亿级）
  ✅ CPU 和 GPU 版本
  ✅ 多种索引算法
  ❌ 不存储原始文本
  ❌ 不支持元数据过滤
  ❌ 需要自己管理 ID→文本 映射

FAISS vs ChromaDB：
  ChromaDB: 简单易用，自带文本和元数据 → 原型/小项目
  FAISS:    极致性能，需要自己管理文本 → 大规模生产

三类索引：
  精确索引: IndexFlat  → 暴力搜索，100%召回率
  近似索引: IndexIVF   → 分区搜索，速度快，精度略降
  图索引:   IndexHNSW  → 图搜索，速度和精度平衡最优
""")

try:
    import faiss

    # ========================================================================
    # 2. 索引类型
    # ========================================================================
    print("\n--- 2. 索引类型 ---")

    dim = 128  # 向量维度
    n_vectors = 10000
    np.random.seed(42)
    vectors = np.random.randn(n_vectors, dim).astype('float32')
    queries = np.random.randn(5, dim).astype('float32')

    # --- Flat Index（精确搜索）---
    print("\n[Flat Index - 精确搜索]")
    index_flat = faiss.IndexFlatL2(dim)  # L2 距离
    index_flat.add(vectors)

    start = time.time()
    distances, indices = index_flat.search(queries, k=5)
    flat_time = time.time() - start

    print(f"  向量数: {index_flat.ntotal}")
    print(f"  搜索耗时: {flat_time*1000:.1f}ms")
    print(f"  Top-5 索引: {indices[0]}")
    print(f"  Top-5 距离: {[f'{d:.2f}' for d in distances[0]]}")

    # --- Flat IP（内积/余弦相似度）---
    print("\n[Flat IP - 余弦相似度（归一化后）]")
    vectors_norm = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    index_ip = faiss.IndexFlatIP(dim)
    index_ip.add(vectors_norm)

    q_norm = queries / np.linalg.norm(queries, axis=1, keepdims=True)
    distances_ip, indices_ip = index_ip.search(q_norm, k=5)
    print(f"  余弦相似度 Top-5: {[f'{d:.4f}' for d in distances_ip[0]]}")

    # --- IVF Index（倒排索引，近似搜索）---
    print("\n[IVF Index - 近似搜索]")
    nlist = 50  # 聚类中心数
    quantizer = faiss.IndexFlatL2(dim)
    index_ivf = faiss.IndexIVFFlat(quantizer, dim, nlist)

    index_ivf.train(vectors)  # 需要训练！
    index_ivf.add(vectors)
    index_ivf.nprobe = 10  # 搜索时检查的聚类数

    start = time.time()
    distances_ivf, indices_ivf = index_ivf.search(queries, k=5)
    ivf_time = time.time() - start

    print(f"  聚类数: {nlist}, nprobe: {index_ivf.nprobe}")
    print(f"  搜索耗时: {ivf_time*1000:.1f}ms")
    print(f"  Top-5 索引: {indices_ivf[0]}")

    # 计算召回率
    flat_set = set(indices[0].tolist())
    ivf_set = set(indices_ivf[0].tolist())
    recall = len(flat_set & ivf_set) / len(flat_set)
    print(f"  召回率: {recall:.0%}（vs Flat精确结果）")

    # --- HNSW Index（图搜索，推荐！）---
    print("\n[HNSW Index - 图搜索（推荐）]")
    M = 32  # 图的连接数
    index_hnsw = faiss.IndexHNSWFlat(dim, M)
    index_hnsw.hnsw.efConstruction = 200  # 构建时搜索深度
    index_hnsw.hnsw.efSearch = 64  # 搜索时搜索深度

    start = time.time()
    index_hnsw.add(vectors)
    build_time = time.time() - start

    start = time.time()
    distances_hnsw, indices_hnsw = index_hnsw.search(queries, k=5)
    hnsw_time = time.time() - start

    hnsw_set = set(indices_hnsw[0].tolist())
    recall_hnsw = len(flat_set & hnsw_set) / len(flat_set)

    print(f"  M={M}, efConstruction=200, efSearch=64")
    print(f"  构建耗时: {build_time*1000:.1f}ms")
    print(f"  搜索耗时: {hnsw_time*1000:.1f}ms")
    print(f"  召回率: {recall_hnsw:.0%}")

    # 对比总结
    print(f"""
索引类型对比:
  {'类型':<12} {'搜索(ms)':>10} {'召回率':>8} {'需训练':>8}
  {'-'*42}
  {'Flat':<12} {flat_time*1000:>9.1f} {'100%':>8} {'否':>8}
  {'IVF':<12} {ivf_time*1000:>9.1f} {f'{recall:.0%}':>8} {'是':>8}
  {'HNSW':<12} {hnsw_time*1000:>9.1f} {f'{recall_hnsw:.0%}':>8} {'否':>8}
""")

    # ========================================================================
    # 3. ID 映射
    # ========================================================================
    print("--- 3. ID 映射 ---")
    print("""
FAISS 默认用顺序整数 ID (0, 1, 2, ...)
需要自定义 ID 时用 IndexIDMap。
""")

    index_base = faiss.IndexFlatL2(dim)
    index_idmap = faiss.IndexIDMap(index_base)

    # 自定义 ID
    custom_ids = np.array([1001, 1002, 1003, 1004, 1005], dtype=np.int64)
    small_vecs = vectors[:5]
    index_idmap.add_with_ids(small_vecs, custom_ids)

    distances, indices = index_idmap.search(queries[:1], k=3)
    print(f"自定义 ID 搜索:")
    print(f"  返回的 ID: {indices[0]}（而非 0,1,2）")

    # 实际应用：ID → 文本 映射
    id_to_text = {
        1001: "机器学习入门",
        1002: "深度学习教程",
        1003: "Python编程指南",
        1004: "数据分析实战",
        1005: "自然语言处理",
    }
    print(f"  对应文本: {[id_to_text.get(int(i), '?') for i in indices[0]]}")

    # ========================================================================
    # 4. 保存与加载
    # ========================================================================
    print("\n--- 4. 保存加载 ---")

    import tempfile, os

    temp = tempfile.mkdtemp()
    index_path = os.path.join(temp, "test.index")

    # 保存
    faiss.write_index(index_flat, index_path)
    file_size = os.path.getsize(index_path) / 1024 / 1024
    print(f"保存: {index_path}")
    print(f"  文件大小: {file_size:.1f}MB ({n_vectors}条 × {dim}维)")

    # 加载
    loaded_index = faiss.read_index(index_path)
    print(f"加载: {loaded_index.ntotal} 条向量")

    # 验证
    d1, i1 = index_flat.search(queries[:1], k=3)
    d2, i2 = loaded_index.search(queries[:1], k=3)
    assert np.array_equal(i1, i2), "加载后结果不一致！"
    print(f"验证: 搜索结果一致 ✓")

    # 清理
    import shutil
    shutil.rmtree(temp, ignore_errors=True)

    # ========================================================================
    # 5. 性能优化
    # ========================================================================
    print("\n--- 5. 性能优化 ---")
    print("""
┌──────────────────┬──────────────────────────────────────┐
│  优化策略         │  说明                                 │
├──────────────────┼──────────────────────────────────────┤
│  选对索引类型    │  <10K: Flat, <1M: HNSW, >1M: IVF   │
│  向量归一化      │  用 IP 代替 L2（更快）              │
│  降维            │  PCA 降维 + OPQ                      │
│  量化            │  PQ/SQ 压缩向量（省内存）           │
│  批量搜索        │  多条 query 一起搜索                 │
│  GPU 加速        │  faiss-gpu，大规模数据显著提速      │
│  nprobe 调节     │  IVF: nprobe↑ → 精度↑速度↓         │
│  efSearch 调节   │  HNSW: efSearch↑ → 精度↑速度↓      │
└──────────────────┴──────────────────────────────────────┘
""")

    # 批量搜索性能
    print("批量搜索性能:")
    for batch_size in [1, 10, 100]:
        batch_queries = np.random.randn(batch_size, dim).astype('float32')
        start = time.time()
        index_flat.search(batch_queries, k=5)
        elapsed = time.time() - start
        per_query = elapsed / batch_size * 1000
        print(f"  batch={batch_size}: 总{elapsed*1000:.1f}ms, "
              f"每条{per_query:.2f}ms")

    # IVF nprobe 对比
    print(f"\nIVF nprobe 对比:")
    print(f"  {'nprobe':>8} {'耗时(ms)':>10} {'召回率':>8}")
    print(f"  {'-'*30}")
    for nprobe in [1, 5, 10, 20, 50]:
        index_ivf.nprobe = nprobe
        start = time.time()
        d_ivf, i_ivf = index_ivf.search(queries, k=5)
        t = time.time() - start
        rec = len(set(indices[0].tolist()) & set(i_ivf[0].tolist())) / 5
        print(f"  {nprobe:>8} {t*1000:>9.1f} {rec:>7.0%}")

except ImportError:
    print("\nfaiss-cpu 未安装，跳过实践演示")
    print("安装: pip install faiss-cpu")

print("\n" + "=" * 60)
print("[完成] 第4课完成！你已经学会了：")
print("  [v] FAISS vs ChromaDB 定位区别")
print("  [v] 三种索引（Flat/IVF/HNSW）对比")
print("  [v] L2 距离 vs 余弦相似度（IP）")
print("  [v] ID 映射（IndexIDMap）")
print("  [v] 索引保存与加载")
print("  [v] 性能优化（批量/nprobe/efSearch）")
print("=" * 60)
print("\n下一课：05_text_splitting.py - 文本分块")
