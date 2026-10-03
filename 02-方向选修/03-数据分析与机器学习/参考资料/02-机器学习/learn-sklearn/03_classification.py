"""
==============================================================================
第3课：分类算法
==============================================================================

本课内容：
1. 逻辑回归（Logistic Regression）
2. 决策树（Decision Tree）
3. 随机森林（Random Forest）
4. 支持向量机（SVM）
5. K近邻（KNN）
6. 多模型对比

运行方式：python 03_classification.py
==============================================================================
"""

import numpy as np
import pandas as pd
from sklearn.datasets import load_iris, load_breast_cancer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, classification_report

print("=" * 60)
print("第3课：分类算法")
print("=" * 60)

# 准备数据
iris = load_iris()
X, y = iris.data, iris.target
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

# ============================================================================
# 1. 逻辑回归
# ============================================================================
print("\n--- 1. 逻辑回归 (Logistic Regression) ---")

print("""
  虽然叫"回归"，但它是分类算法！
  
  原理：
    线性回归: y = Xw + b        → 输出连续值
    逻辑回归: p = σ(Xw + b)     → 输出概率 [0, 1]
    
    σ(z) = 1 / (1 + e^(-z))     ← Sigmoid 函数
    
    p > 0.5 → 正类
    p ≤ 0.5 → 负类
    
  多分类策略：OvR（一对多）或 Multinomial
""")

lr = LogisticRegression(max_iter=200, random_state=42)
lr.fit(X_train_s, y_train)
y_pred = lr.predict(X_test_s)
print(f"  准确率: {accuracy_score(y_test, y_pred):.4f}")

# 概率输出
y_prob = lr.predict_proba(X_test_s)
print(f"  第一个样本的概率: {y_prob[0].round(4)}")
print(f"  对应类别: {iris.target_names}")

# ============================================================================
# 2. 决策树
# ============================================================================
print("\n--- 2. 决策树 (Decision Tree) ---")

print("""
  原理：通过一系列"是/否"问题将数据分开
  
  例如：
    花瓣长度 > 2.5?
      ├── 是 → 花瓣宽度 > 1.7?
      │         ├── 是 → virginica
      │         └── 否 → versicolor
      └── 否 → setosa
  
  关键参数：
    max_depth:      最大深度（防止过拟合）
    min_samples_split: 分裂所需最小样本数
    criterion:      分裂标准（gini / entropy）
""")

# 不同深度对比
print("  max_depth 对模型的影响:")
for depth in [1, 2, 3, 5, None]:
    dt = DecisionTreeClassifier(max_depth=depth, random_state=42)
    dt.fit(X_train, y_train)
    train_acc = dt.score(X_train, y_train)
    test_acc = dt.score(X_test, y_test)
    depth_str = str(depth) if depth else "无限"
    print(f"    depth={depth_str:>4}: 训练={train_acc:.4f}, 测试={test_acc:.4f}"
          f"{'  ← 可能过拟合' if train_acc - test_acc > 0.05 else ''}")

# 特征重要性
dt_best = DecisionTreeClassifier(max_depth=3, random_state=42)
dt_best.fit(X_train, y_train)
importance = pd.Series(dt_best.feature_importances_, index=iris.feature_names)
print(f"\n  特征重要性:")
for feat, imp in importance.sort_values(ascending=False).items():
    bar = "█" * int(imp * 30)
    print(f"    {feat:>25s}: {imp:.4f} {bar}")

# ============================================================================
# 3. 随机森林
# ============================================================================
print("\n--- 3. 随机森林 (Random Forest) ---")

print("""
  原理：多棵决策树的"投票"
  
  1. 随机抽样（Bootstrap）创建多个子数据集
  2. 每个子数据集训练一棵决策树（随机选特征子集）
  3. 预测时，所有树投票，少数服从多数
  
  优点：
    - 不容易过拟合（集成效应）
    - 能衡量特征重要性
    - 不需要特征缩放
  
  关键参数：
    n_estimators: 树的数量（越多越稳定，但更慢）
    max_depth:    每棵树的最大深度
""")

# 不同树数量对比
print("  n_estimators 对模型的影响:")
for n_trees in [1, 5, 10, 50, 100, 200]:
    rf = RandomForestClassifier(n_estimators=n_trees, max_depth=5, random_state=42)
    rf.fit(X_train, y_train)
    test_acc = rf.score(X_test, y_test)
    print(f"    n_estimators={n_trees:>3}: 测试准确率={test_acc:.4f}")

# 特征重要性
rf_best = RandomForestClassifier(n_estimators=100, random_state=42)
rf_best.fit(X_train, y_train)
importance_rf = pd.Series(rf_best.feature_importances_, index=iris.feature_names)
print(f"\n  随机森林特征重要性:")
for feat, imp in importance_rf.sort_values(ascending=False).items():
    bar = "█" * int(imp * 30)
    print(f"    {feat:>25s}: {imp:.4f} {bar}")

# ============================================================================
# 4. 支持向量机（SVM）
# ============================================================================
print("\n--- 4. 支持向量机 (SVM) ---")

print("""
  原理：找一个超平面，使两类数据之间的"间隔"最大化
  
  核函数（处理非线性）：
    linear:  线性核（适合线性可分）
    poly:    多项式核
    rbf:     高斯核（最常用，能处理复杂边界）
    sigmoid: Sigmoid核
  
  关键参数：
    C:     惩罚系数（C越大越严格，可能过拟合）
    gamma: RBF核的参数（gamma越大边界越复杂）
""")

# 不同核函数对比
print("  不同核函数:")
for kernel in ["linear", "poly", "rbf", "sigmoid"]:
    svm = SVC(kernel=kernel, random_state=42)
    svm.fit(X_train_s, y_train)
    acc = svm.score(X_test_s, y_test)
    print(f"    {kernel:>8}: 准确率={acc:.4f}")

# ============================================================================
# 5. K近邻（KNN）
# ============================================================================
print("\n--- 5. K近邻 (KNN) ---")

print("""
  原理：看新样本周围最近的K个邻居，投票决定类别
  
  "物以类聚" — 和你最像的K个数据是什么类，你就是什么类
  
  关键参数：
    n_neighbors: K值（邻居数量）
    weights:     uniform（等权）/ distance（距离加权）
  
  注意：KNN 对特征缩放敏感，需要先标准化！
""")

# 不同K值对比
print("  不同K值:")
k_scores = []
for k in range(1, 16):
    knn = KNeighborsClassifier(n_neighbors=k)
    knn.fit(X_train_s, y_train)
    acc = knn.score(X_test_s, y_test)
    k_scores.append(acc)
    if k <= 10 or k == 15:
        print(f"    K={k:>2}: 准确率={acc:.4f}")

best_k = np.argmax(k_scores) + 1
print(f"  最佳K值: {best_k} (准确率={max(k_scores):.4f})")

# ============================================================================
# 6. 多模型对比（交叉验证）
# ============================================================================
print("\n--- 6. 多模型交叉验证对比 ---")

print("""
  交叉验证（Cross Validation）：
    将数据分成K份，轮流用每份做测试，其余做训练
    结果更稳定、更可信
""")

models = {
    "Logistic Regression": LogisticRegression(max_iter=200),
    "Decision Tree (d=3)": DecisionTreeClassifier(max_depth=3),
    "Random Forest (100)": RandomForestClassifier(n_estimators=100),
    "SVM (rbf)": SVC(kernel="rbf"),
    "KNN (k=5)": KNeighborsClassifier(n_neighbors=5),
}

# 用标准化数据
print(f"\n  {'模型':>25s}    均值 ± 标准差")
print(f"  {'-'*50}")
results = {}
for name, m in models.items():
    scores = cross_val_score(m, scaler.fit_transform(X), y, cv=5, scoring="accuracy")
    results[name] = scores.mean()
    print(f"  {name:>25s}:  {scores.mean():.4f} ± {scores.std():.4f}")

best = max(results, key=results.get)
print(f"\n  最佳模型: {best} (准确率={results[best]:.4f})")

# ============================================================================
# 7. 算法选择指南
# ============================================================================
print("\n--- 7. 算法选择指南 ---")

print("""
  ┌─────────────────┬──────────────────────────────────────┐
  │ 算法            │ 适用场景                              │
  ├─────────────────┼──────────────────────────────────────┤
  │ 逻辑回归        │ 线性可分、需要概率输出、可解释性强     │
  │ 决策树          │ 需要可解释性、数据有明确的分界条件     │
  │ 随机森林        │ 通用首选、不容易过拟合、大数据集       │
  │ SVM             │ 中小数据集、高维数据、复杂边界         │
  │ KNN             │ 小数据集、快速原型、基线模型           │
  └─────────────────┴──────────────────────────────────────┘
  
  实际工作中的建议：
    1. 先用逻辑回归做基线（简单、快速）
    2. 再试随机森林（通常效果好）
    3. 如果需要高精度，尝试SVM或集成方法
    4. 最终通过交叉验证选出最佳模型
""")

# ============================================================================
# 总结
# ============================================================================
print("=" * 60)
print("第3课总结:")
print("  [v] 逻辑回归: Sigmoid + 概率输出，分类基线")
print("  [v] 决策树: 可解释性强，注意控制深度")
print("  [v] 随机森林: 多树投票，通用首选")
print("  [v] SVM: 最大间隔，核函数处理非线性")
print("  [v] KNN: 近邻投票，需要标准化")
print("  [v] 交叉验证: 更可靠的模型评估方式")
print("=" * 60)
