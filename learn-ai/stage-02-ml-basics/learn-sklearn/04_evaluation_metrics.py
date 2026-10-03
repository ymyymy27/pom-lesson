"""
==============================================================================
第4课：分类评估指标详解
==============================================================================

本课内容：
1. 混淆矩阵（Confusion Matrix）
2. 准确率、精确率、召回率、F1
3. ROC 曲线与 AUC
4. 多分类评估
5. 不均衡数据集的评估策略
6. AI产品经理必知：指标选择指南

运行方式：python 04_evaluation_metrics.py
==============================================================================
"""

import numpy as np
from sklearn.datasets import load_breast_cancer, make_classification
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report,
    roc_auc_score, roc_curve, precision_recall_curve,
    average_precision_score,
)
from sklearn.preprocessing import StandardScaler

print("=" * 60)
print("第4课：分类评估指标详解")
print("=" * 60)

# 准备二分类数据（乳腺癌数据集）
data = load_breast_cancer()
X, y = data.data, data.target
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

model = LogisticRegression(max_iter=5000, random_state=42)
model.fit(X_train_s, y_train)
y_pred = model.predict(X_test_s)
y_prob = model.predict_proba(X_test_s)[:, 1]

# ============================================================================
# 1. 混淆矩阵
# ============================================================================
print("\n--- 1. 混淆矩阵 (Confusion Matrix) ---")

print("""
  混淆矩阵：展示预测与真实的对应关系

                    预测为正    预测为负
  实际为正          TP          FN        ← FN=漏报（该抓没抓到）
  实际为负          FP          TN        ← FP=误报（冤枉好人）

  TP (True Positive):   预测正确的正例 ✓
  TN (True Negative):   预测正确的负例 ✓
  FP (False Positive):  把负例错判为正例 ✗（误报/虚警）
  FN (False Negative):  把正例错判为负例 ✗（漏报/遗漏）
""")

cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()
print(f"  混淆矩阵:")
print(f"    TP={tp}  FN={fn}")
print(f"    FP={fp}  TN={tn}")
print(f"    总计: {tp+tn+fp+fn} 个样本")

# ============================================================================
# 2. 准确率、精确率、召回率、F1
# ============================================================================
print("\n--- 2. 四大核心指标 ---")

acc = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred)
rec = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print(f"""
  准确率 Accuracy  = (TP+TN) / 总数 = ({tp}+{tn}) / {tp+tn+fp+fn} = {acc:.4f}
    → 所有预测中，正确的比例
    → 数据均衡时好用，不均衡时有陷阱

  精确率 Precision = TP / (TP+FP) = {tp} / ({tp}+{fp}) = {prec:.4f}
    → 预测为正的里面，真正是正的比例
    → "查准率"：抓到的人里，有多少是真犯人？
    → 高精确率 = 少冤枉人

  召回率 Recall    = TP / (TP+FN) = {tp} / ({tp}+{fn}) = {rec:.4f}
    → 真正为正的里面，被正确预测的比例
    → "查全率"：所有犯人中，抓到了多少？
    → 高召回率 = 少漏人

  F1 Score         = 2 × (P×R) / (P+R) = {f1:.4f}
    → 精确率和召回率的调和平均
    → 两者的综合平衡指标
""")

# ============================================================================
# 3. 精确率 vs 召回率的取舍
# ============================================================================
print("--- 3. 精确率 vs 召回率：不可兼得 ---")

print("""
  精确率和召回率通常此消彼长：
    提高阈值 → 精确率↑ 但 召回率↓（宁缺毋滥）
    降低阈值 → 召回率↑ 但 精确率↓（宁滥勿缺）

  ┌──────────────────┬──────────┬──────────────────────────┐
  │ 场景             │ 优先指标  │ 原因                      │
  ├──────────────────┼──────────┼──────────────────────────┤
  │ 垃圾邮件过滤     │ Precision │ 不能把正常邮件误删         │
  │ 疾病筛查         │ Recall    │ 不能漏掉任何患者           │
  │ 搜索引擎         │ Precision │ 结果要相关                 │
  │ 欺诈检测         │ Recall    │ 不能放过任何欺诈           │
  │ 推荐系统         │ Precision │ 推荐要准，不能骚扰用户     │
  │ 安全审计         │ Recall    │ 不能遗漏安全隐患           │
  └──────────────────┴──────────┴──────────────────────────┘
""")

# 不同阈值下的精确率/召回率
print("  不同阈值下的 Precision/Recall:")
for threshold in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    y_pred_t = (y_prob >= threshold).astype(int)
    p = precision_score(y_test, y_pred_t, zero_division=0)
    r = recall_score(y_test, y_pred_t, zero_division=0)
    f = f1_score(y_test, y_pred_t, zero_division=0)
    print(f"    阈值={threshold:.1f}: Precision={p:.4f}  Recall={r:.4f}  F1={f:.4f}")

# ============================================================================
# 4. ROC 曲线与 AUC
# ============================================================================
print("\n--- 4. ROC 曲线与 AUC ---")

print("""
  ROC 曲线：以 FPR 为横轴、TPR 为纵轴的曲线
    TPR (True Positive Rate) = Recall = TP/(TP+FN)
    FPR (False Positive Rate) = FP/(FP+TN)

  AUC (Area Under ROC Curve)：ROC 曲线下面积
    AUC = 1.0  完美模型
    AUC = 0.5  随机猜测（等于没用）
    AUC > 0.8  通常认为是好模型

  AUC 的优点：
    - 不受阈值选择影响
    - 不受类别不均衡影响（比 Accuracy 更可靠）
    - 方便模型间对比
""")

fpr, tpr, thresholds = roc_curve(y_test, y_prob)
auc_val = roc_auc_score(y_test, y_prob)
print(f"  AUC = {auc_val:.4f}")

# 展示几个关键点
print(f"\n  ROC 曲线关键点:")
indices = [0, len(fpr)//4, len(fpr)//2, 3*len(fpr)//4, -1]
for i in indices:
    print(f"    阈值={thresholds[i]:.3f}: FPR={fpr[i]:.3f}, TPR={tpr[i]:.3f}")

# ============================================================================
# 5. 多分类评估
# ============================================================================
print("\n--- 5. 多分类评估 ---")

from sklearn.datasets import load_iris
iris = load_iris()
X_iris, y_iris = iris.data, iris.target
X_tr, X_te, y_tr, y_te = train_test_split(X_iris, y_iris, test_size=0.2, random_state=42)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_tr, y_tr)
y_p = clf.predict(X_te)

# classification_report 一目了然
print("  分类报告 (classification_report):")
print(classification_report(y_te, y_p, target_names=iris.target_names))

print("""
  多分类平均策略:
    macro:    每个类别的指标简单平均（不考虑样本数）
    weighted: 按各类别样本数加权平均（常用）
    micro:    全局计算（等于 Accuracy）
""")

# ============================================================================
# 6. 不均衡数据集
# ============================================================================
print("--- 6. 不均衡数据集评估 ---")

print("""
  准确率的陷阱：
    如果 95% 是负例、5% 是正例
    模型全部预测为"负" → 准确率 = 95%！看起来很高但毫无用处

  解决方案：
    1. 不看 Accuracy，看 F1 / AUC
    2. 看 classification_report 每个类别的指标
    3. 使用 balanced accuracy
""")

# 生成不均衡数据
X_imb, y_imb = make_classification(
    n_samples=1000, n_features=10, n_classes=2,
    weights=[0.95, 0.05],  # 95% vs 5%
    random_state=42
)
X_tr_i, X_te_i, y_tr_i, y_te_i = train_test_split(X_imb, y_imb, test_size=0.2, random_state=42)

print(f"\n  标签分布: 类0={sum(y_te_i==0)}, 类1={sum(y_te_i==1)}")

# "全猜0"的模型
y_all_zero = np.zeros_like(y_te_i)
print(f"\n  [全猜负例]")
print(f"    Accuracy = {accuracy_score(y_te_i, y_all_zero):.4f}  ← 看起来很高！")
print(f"    F1       = {f1_score(y_te_i, y_all_zero, zero_division=0):.4f}  ← 实际为0")

# 正常模型
lr_imb = LogisticRegression(max_iter=1000, random_state=42)
lr_imb.fit(X_tr_i, y_tr_i)
y_pred_imb = lr_imb.predict(X_te_i)

print(f"\n  [逻辑回归]")
print(f"    Accuracy  = {accuracy_score(y_te_i, y_pred_imb):.4f}")
print(f"    Precision = {precision_score(y_te_i, y_pred_imb, zero_division=0):.4f}")
print(f"    Recall    = {recall_score(y_te_i, y_pred_imb, zero_division=0):.4f}")
print(f"    F1        = {f1_score(y_te_i, y_pred_imb, zero_division=0):.4f}")

# ============================================================================
# 7. AI产品经理面试必知
# ============================================================================
print("\n--- 7. AI产品经理面试必知 ---")

print("""
  面试题: "为什么不能只看准确率？"
  答: 在数据不均衡时，准确率会被多数类主导。比如 95%/5% 的数据，
      全猜多数类就有 95% 准确率，但完全没有识别少数类的能力。
      应该结合 Precision/Recall/F1/AUC 综合评判。

  面试题: "模型准确率80%，能上线吗？"
  答: 不一定。需要看:
      1. 业务场景对准确率的要求（医疗>推荐）
      2. 各类别的 Precision 和 Recall 是否达标
      3. AUC 值是否合理
      4. 与基线模型（规则/旧模型）相比是否有提升
      5. 错误预测的代价（FP和FN哪个更严重）

  面试题: "如何选择评估指标？"
  答: 取决于业务场景中 FP 和 FN 的代价:
      - FP代价高（误报严重）→ 看 Precision
      - FN代价高（漏报严重）→ 看 Recall
      - 两者都重要 → 看 F1
      - 不确定阈值 → 看 AUC
""")

# ============================================================================
# 总结
# ============================================================================
print("=" * 60)
print("第4课总结:")
print("  [v] 混淆矩阵: TP/TN/FP/FN 四格")
print("  [v] 准确率: 总正确率，不均衡时有陷阱")
print("  [v] 精确率: 查准率，少冤枉（FP代价高时优先）")
print("  [v] 召回率: 查全率，少遗漏（FN代价高时优先）")
print("  [v] F1: 精确率和召回率的平衡")
print("  [v] AUC: 不受阈值影响，最推荐的综合指标")
print("=" * 60)
