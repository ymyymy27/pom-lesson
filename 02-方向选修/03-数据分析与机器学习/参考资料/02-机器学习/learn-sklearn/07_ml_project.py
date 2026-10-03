"""
==============================================================================
第7课：机器学习综合项目 — 从数据到模型的完整流程
==============================================================================

本课内容：
1. 问题定义与数据探索
2. 数据清洗与预处理
3. 特征工程
4. 模型训练与选择
5. 超参数调优
6. 最终评估与总结

项目：乳腺癌诊断分类（二分类，真实医疗场景）

运行方式：python 07_ml_project.py
==============================================================================
"""

import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report, confusion_matrix,
)

print("=" * 60)
print("综合项目：乳腺癌诊断分类")
print("=" * 60)

# ============================================================================
# 1. 问题定义与数据探索
# ============================================================================
print("\n" + "=" * 60)
print("阶段1：问题定义与数据探索")
print("=" * 60)

print("""
  问题: 根据肿瘤的细胞特征，判断是良性还是恶性
  类型: 二分类问题
  场景: 医疗诊断 → 漏诊(FN)代价远大于误诊(FP)
  关键指标: Recall（不能漏掉恶性肿瘤）+ AUC
""")

# 加载数据
data = load_breast_cancer()
X = pd.DataFrame(data.data, columns=data.feature_names)
y = pd.Series(data.target, name="target")

print(f"  数据形状: {X.shape} ({X.shape[0]}个样本, {X.shape[1]}个特征)")
print(f"  标签: 0=恶性(malignant), 1=良性(benign)")
print(f"  标签分布:")
print(f"    恶性: {(y==0).sum()} ({(y==0).mean():.1%})")
print(f"    良性: {(y==1).sum()} ({(y==1).mean():.1%})")

# 基本统计
print(f"\n  特征统计 (前5个特征):")
print(X.iloc[:, :5].describe().round(2).to_string())

# 缺失值检查
print(f"\n  缺失值: {X.isnull().sum().sum()} 个 ← 无缺失，数据质量好")

# ============================================================================
# 2. 数据划分
# ============================================================================
print("\n" + "=" * 60)
print("阶段2：数据划分")
print("=" * 60)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"  训练集: {X_train.shape[0]} 个样本")
print(f"  测试集: {X_test.shape[0]} 个样本")
print(f"  训练集标签分布: 恶性={sum(y_train==0)}, 良性={sum(y_train==1)}")
print(f"  测试集标签分布: 恶性={sum(y_test==0)}, 良性={sum(y_test==1)}")

# ============================================================================
# 3. 特征分析
# ============================================================================
print("\n" + "=" * 60)
print("阶段3：特征分析")
print("=" * 60)

# 特征与标签的相关性
correlations = X_train.corrwith(y_train).abs().sort_values(ascending=False)
print("  与标签相关性最高的10个特征:")
for feat, corr in correlations.head(10).items():
    bar = "█" * int(corr * 30)
    print(f"    {feat:>30s}: {corr:.4f} {bar}")

print(f"\n  与标签相关性最低的5个特征:")
for feat, corr in correlations.tail(5).items():
    print(f"    {feat:>30s}: {corr:.4f}")

# ============================================================================
# 4. 基线模型对比
# ============================================================================
print("\n" + "=" * 60)
print("阶段4：基线模型对比")
print("=" * 60)

pipelines = {
    "Logistic Regression": Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=5000, random_state=42)),
    ]),
    "Decision Tree": Pipeline([
        ("scaler", StandardScaler()),
        ("model", DecisionTreeClassifier(max_depth=5, random_state=42)),
    ]),
    "Random Forest": Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestClassifier(n_estimators=100, random_state=42)),
    ]),
    "Gradient Boosting": Pipeline([
        ("scaler", StandardScaler()),
        ("model", GradientBoostingClassifier(n_estimators=100, random_state=42)),
    ]),
    "SVM": Pipeline([
        ("scaler", StandardScaler()),
        ("model", SVC(probability=True, random_state=42)),
    ]),
    "KNN": Pipeline([
        ("scaler", StandardScaler()),
        ("model", KNeighborsClassifier(n_neighbors=5)),
    ]),
}

print(f"  {'模型':>25s}  {'Accuracy':>10s}  {'F1':>10s}  {'Recall':>10s}")
print(f"  {'-'*60}")

baseline_results = {}
for name, pipe in pipelines.items():
    acc_scores = cross_val_score(pipe, X_train, y_train, cv=5, scoring="accuracy")
    f1_scores = cross_val_score(pipe, X_train, y_train, cv=5, scoring="f1")
    rec_scores = cross_val_score(pipe, X_train, y_train, cv=5, scoring="recall")
    baseline_results[name] = {
        "accuracy": acc_scores.mean(),
        "f1": f1_scores.mean(),
        "recall": rec_scores.mean(),
    }
    print(f"  {name:>25s}  {acc_scores.mean():>10.4f}  {f1_scores.mean():>10.4f}  {rec_scores.mean():>10.4f}")

# 选出Top3
top3 = sorted(baseline_results.items(), key=lambda x: x[1]["f1"], reverse=True)[:3]
print(f"\n  Top 3 (按F1排序):")
for name, scores in top3:
    print(f"    {name}: F1={scores['f1']:.4f}")

# ============================================================================
# 5. 超参数调优（对Top模型）
# ============================================================================
print("\n" + "=" * 60)
print("阶段5：超参数调优")
print("=" * 60)

# 对 Logistic Regression 调优
print("  [调优 Logistic Regression]")
pipe_lr = Pipeline([
    ("scaler", StandardScaler()),
    ("model", LogisticRegression(max_iter=5000, random_state=42)),
])

param_grid_lr = {
    "model__C": [0.01, 0.1, 1, 10, 100],
    "model__penalty": ["l1", "l2"],
    "model__solver": ["liblinear"],
}

grid_lr = GridSearchCV(pipe_lr, param_grid_lr, cv=5, scoring="f1", n_jobs=-1)
grid_lr.fit(X_train, y_train)
print(f"  最佳参数: {grid_lr.best_params_}")
print(f"  最佳CV F1: {grid_lr.best_score_:.4f}")

# 对 Random Forest 调优
print("\n  [调优 Random Forest]")
pipe_rf = Pipeline([
    ("scaler", StandardScaler()),
    ("model", RandomForestClassifier(random_state=42)),
])

param_grid_rf = {
    "model__n_estimators": [100, 200],
    "model__max_depth": [5, 10, None],
    "model__min_samples_split": [2, 5],
}

grid_rf = GridSearchCV(pipe_rf, param_grid_rf, cv=5, scoring="f1", n_jobs=-1)
grid_rf.fit(X_train, y_train)
print(f"  最佳参数: {grid_rf.best_params_}")
print(f"  最佳CV F1: {grid_rf.best_score_:.4f}")

# 对 SVM 调优
print("\n  [调优 SVM]")
pipe_svm = Pipeline([
    ("scaler", StandardScaler()),
    ("model", SVC(probability=True, random_state=42)),
])

param_grid_svm = {
    "model__C": [0.1, 1, 10],
    "model__kernel": ["rbf", "linear"],
    "model__gamma": ["scale", "auto"],
}

grid_svm = GridSearchCV(pipe_svm, param_grid_svm, cv=5, scoring="f1", n_jobs=-1)
grid_svm.fit(X_train, y_train)
print(f"  最佳参数: {grid_svm.best_params_}")
print(f"  最佳CV F1: {grid_svm.best_score_:.4f}")

# 选出最佳模型
best_models = {
    "Logistic Regression": grid_lr,
    "Random Forest": grid_rf,
    "SVM": grid_svm,
}
best_name = max(best_models, key=lambda k: best_models[k].best_score_)
best_model = best_models[best_name]
print(f"\n  最终选择: {best_name} (CV F1={best_model.best_score_:.4f})")

# ============================================================================
# 6. 最终评估
# ============================================================================
print("\n" + "=" * 60)
print("阶段6：最终评估（在测试集上）")
print("=" * 60)

y_pred = best_model.predict(X_test)
y_prob = best_model.predict_proba(X_test)[:, 1]

print(f"\n  使用模型: {best_name}")
print(f"  测试集结果:")
print(f"    Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
print(f"    Precision: {precision_score(y_test, y_pred):.4f}")
print(f"    Recall:    {recall_score(y_test, y_pred):.4f}")
print(f"    F1 Score:  {f1_score(y_test, y_pred):.4f}")
print(f"    AUC:       {roc_auc_score(y_test, y_prob):.4f}")

# 混淆矩阵
cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()
print(f"\n  混淆矩阵:")
print(f"    {'':>15s} 预测恶性  预测良性")
print(f"    {'实际恶性':>12s}   {cm[0,0]:>4d}     {cm[0,1]:>4d}")
print(f"    {'实际良性':>12s}   {cm[1,0]:>4d}     {cm[1,1]:>4d}")

# 详细分类报告
print(f"\n  详细分类报告:")
print(classification_report(y_test, y_pred, target_names=["恶性", "良性"]))

# 业务解读
print(f"  业务解读:")
print(f"    漏诊(FN): {fn} 例 — 恶性肿瘤被误判为良性 ⚠️")
print(f"    误诊(FP): {fp} 例 — 良性肿瘤被误判为恶性")
if fn == 0:
    print(f"    → 零漏诊！非常好！")
elif fn <= 2:
    print(f"    → 漏诊较少，但在医疗场景中仍需关注")
else:
    print(f"    → 漏诊较多，需要调低阈值提高Recall")

# ============================================================================
# 7. 项目总结
# ============================================================================
print("\n" + "=" * 60)
print("项目总结")
print("=" * 60)

print("""
  完整的 ML 项目流程:

  ┌─────────────────────────────────────────────┐
  │ 1. 问题定义     定义任务类型、业务目标       │
  │                 确定关键评估指标              │
  ├─────────────────────────────────────────────┤
  │ 2. 数据探索     查看数据形状、分布、缺失值   │
  │                 理解特征含义                  │
  ├─────────────────────────────────────────────┤
  │ 3. 数据预处理   缺失值处理、编码、缩放       │
  │                 特征选择与工程                │
  ├─────────────────────────────────────────────┤
  │ 4. 基线模型     多个算法快速对比             │
  │                 交叉验证评估                  │
  ├─────────────────────────────────────────────┤
  │ 5. 模型调优     GridSearch / RandomSearch    │
  │                 Pipeline 封装                │
  ├─────────────────────────────────────────────┤
  │ 6. 最终评估     在测试集上全面评估           │
  │                 业务解读与决策建议            │
  └─────────────────────────────────────────────┘

  AI产品经理需要理解：
    - 数据质量决定模型上限
    - 评估指标要与业务目标对齐
    - 模型选择要考虑可解释性和部署成本
    - 模型性能不是唯一考量（延迟、成本、公平性）
""")

print("=" * 60)
print("[完成] learn-sklearn 课程全部完成！")
print("=" * 60)
