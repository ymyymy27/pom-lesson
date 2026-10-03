"""
==============================================================================
第6课：模型调优
==============================================================================

本课内容：
1. 交叉验证详解（K-Fold / Stratified / Leave-One-Out）
2. 网格搜索（GridSearchCV）
3. 随机搜索（RandomizedSearchCV）
4. Pipeline（管道：预处理+模型一体化）
5. 过拟合与欠拟合诊断

运行方式：python 06_model_tuning.py
==============================================================================
"""

import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import (
    cross_val_score, KFold, StratifiedKFold,
    GridSearchCV, RandomizedSearchCV,
    learning_curve,
    train_test_split,
)
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, make_scorer
from scipy.stats import randint, uniform

print("=" * 60)
print("第6课：模型调优")
print("=" * 60)

# 准备数据
data = load_breast_cancer()
X, y = data.data, data.target
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ============================================================================
# 1. 交叉验证详解
# ============================================================================
print("\n--- 1. 交叉验证详解 ---")

print("""
  为什么不只用 train/test split？
    单次划分结果不稳定，换个随机种子结果就不一样

  K-Fold 交叉验证：
    将数据分成K份，轮流用1份做测试、K-1份做训练
    得到K个分数，取平均 → 更稳定、更可信

    ┌──────┬──────┬──────┬──────┬──────┐
    │ Test │Train │Train │Train │Train │  → Score 1
    │Train │ Test │Train │Train │Train │  → Score 2
    │Train │Train │ Test │Train │Train │  → Score 3
    │Train │Train │Train │ Test │Train │  → Score 4
    │Train │Train │Train │Train │ Test │  → Score 5
    └──────┴──────┴──────┴──────┴──────┘
                                     平均 → Final Score
""")

# 基本交叉验证
model = LogisticRegression(max_iter=5000, random_state=42)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

scores = cross_val_score(model, X_scaled, y, cv=5, scoring="accuracy")
print(f"  5-Fold CV 分数: {scores.round(4)}")
print(f"  均值: {scores.mean():.4f} ± {scores.std():.4f}")

# StratifiedKFold（分类任务推荐，保持各类别比例）
print("\n  [StratifiedKFold] 分类任务推荐")
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores_s = cross_val_score(model, X_scaled, y, cv=skf, scoring="accuracy")
print(f"  Stratified 5-Fold: {scores_s.mean():.4f} ± {scores_s.std():.4f}")

# 不同K值
print("\n  不同 K 值的影响:")
for k in [3, 5, 10]:
    s = cross_val_score(model, X_scaled, y, cv=k, scoring="accuracy")
    print(f"    {k:>2}-Fold: {s.mean():.4f} ± {s.std():.4f}")

# ============================================================================
# 2. GridSearchCV 网格搜索
# ============================================================================
print("\n--- 2. GridSearchCV 网格搜索 ---")

print("""
  超参数（Hyperparameter）：模型训练前需要人为设定的参数
    逻辑回归: C（正则化强度）
    随机森林: n_estimators（树数量）, max_depth（最大深度）
    SVM:      C, gamma, kernel

  网格搜索：穷举所有参数组合，找出最优
    优点：一定能找到最优（在给定范围内）
    缺点：参数多时非常慢
""")

# 随机森林网格搜索
param_grid = {
    "n_estimators": [50, 100, 200],
    "max_depth": [3, 5, 10, None],
    "min_samples_split": [2, 5, 10],
}

rf = RandomForestClassifier(random_state=42)
grid_search = GridSearchCV(
    rf, param_grid,
    cv=5,
    scoring="accuracy",
    n_jobs=-1,       # 使用所有CPU核心
    verbose=0,
)
grid_search.fit(X_train, y_train)

print(f"  搜索空间: {3*4*3} = 36 种组合")
print(f"  最佳参数: {grid_search.best_params_}")
print(f"  最佳CV分数: {grid_search.best_score_:.4f}")
print(f"  测试集分数: {grid_search.score(X_test, y_test):.4f}")

# 查看Top5结果
results = pd.DataFrame(grid_search.cv_results_)
top5 = results.nsmallest(5, "rank_test_score")[
    ["params", "mean_test_score", "std_test_score", "rank_test_score"]
]
print(f"\n  Top 5 参数组合:")
for _, row in top5.iterrows():
    print(f"    #{int(row['rank_test_score'])}: {row['mean_test_score']:.4f} ± {row['std_test_score']:.4f} {row['params']}")

# ============================================================================
# 3. RandomizedSearchCV 随机搜索
# ============================================================================
print("\n--- 3. RandomizedSearchCV 随机搜索 ---")

print("""
  随机搜索：从参数分布中随机采样 n 次
    优点：参数多时比网格搜索快得多
    缺点：不保证找到全局最优

  经验：n_iter=50~100 通常就够了
""")

param_distributions = {
    "n_estimators": randint(50, 300),       # 50~300 均匀分布
    "max_depth": [3, 5, 10, 15, None],
    "min_samples_split": randint(2, 20),
    "min_samples_leaf": randint(1, 10),
}

random_search = RandomizedSearchCV(
    RandomForestClassifier(random_state=42),
    param_distributions,
    n_iter=30,       # 随机尝试30次
    cv=5,
    scoring="accuracy",
    random_state=42,
    n_jobs=-1,
)
random_search.fit(X_train, y_train)

print(f"  随机搜索 30 次")
print(f"  最佳参数: {random_search.best_params_}")
print(f"  最佳CV分数: {random_search.best_score_:.4f}")
print(f"  测试集分数: {random_search.score(X_test, y_test):.4f}")

# ============================================================================
# 4. Pipeline 管道
# ============================================================================
print("\n--- 4. Pipeline 管道 ---")

print("""
  Pipeline 把预处理和模型封装在一起：
    1. 避免数据泄露（标准化和交叉验证正确结合）
    2. 代码更简洁
    3. 可以直接做 GridSearchCV

  pipeline.fit(X_train, y_train)  自动执行:
    scaler.fit_transform(X_train)
    model.fit(X_train_scaled, y_train)

  pipeline.predict(X_test)  自动执行:
    scaler.transform(X_test)
    model.predict(X_test_scaled)
""")

# 创建 Pipeline
pipe = Pipeline([
    ("scaler", StandardScaler()),           # 步骤1: 标准化
    ("model", LogisticRegression(max_iter=5000)),  # 步骤2: 模型
])

# 交叉验证（Pipeline 内部自动处理标准化）
scores = cross_val_score(pipe, X, y, cv=5, scoring="accuracy")
print(f"  Pipeline CV 分数: {scores.mean():.4f} ± {scores.std():.4f}")

# Pipeline + GridSearchCV
pipe_rf = Pipeline([
    ("scaler", StandardScaler()),
    ("model", RandomForestClassifier(random_state=42)),
])

# 注意参数名格式: "步骤名__参数名"
param_grid_pipe = {
    "model__n_estimators": [50, 100],
    "model__max_depth": [5, 10, None],
}

grid_pipe = GridSearchCV(pipe_rf, param_grid_pipe, cv=5, scoring="accuracy", n_jobs=-1)
grid_pipe.fit(X_train, y_train)
print(f"\n  Pipeline + GridSearch:")
print(f"  最佳参数: {grid_pipe.best_params_}")
print(f"  测试集分数: {grid_pipe.score(X_test, y_test):.4f}")

# 多模型对比 Pipeline
print("\n  [多模型 Pipeline 对比]")
pipelines = {
    "Logistic Regression": Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=5000)),
    ]),
    "Random Forest": Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestClassifier(n_estimators=100, random_state=42)),
    ]),
    "SVM": Pipeline([
        ("scaler", StandardScaler()),
        ("model", SVC(kernel="rbf")),
    ]),
}

for name, pipe in pipelines.items():
    scores = cross_val_score(pipe, X, y, cv=5, scoring="accuracy")
    print(f"    {name:>25s}: {scores.mean():.4f} ± {scores.std():.4f}")

# ============================================================================
# 5. 过拟合与欠拟合诊断
# ============================================================================
print("\n--- 5. 过拟合与欠拟合诊断 ---")

print("""
  欠拟合 (Underfitting):
    训练分数低，测试分数低
    → 模型太简单，学不到数据规律
    → 解决：增加特征、增加模型复杂度

  过拟合 (Overfitting):
    训练分数高，测试分数低（差距大）
    → 模型太复杂，记住了噪声
    → 解决：正则化、减少特征、增加数据

  刚刚好 (Just Right):
    训练分数高，测试分数也高（差距小）
""")

# 用学习曲线诊断
print("  [学习曲线] 随机森林不同深度:")
X_s = StandardScaler().fit_transform(X)
for depth in [1, 3, 5, None]:
    rf = RandomForestClassifier(n_estimators=50, max_depth=depth, random_state=42)
    rf.fit(X_train, y_train)
    train_score = rf.score(X_train, y_train)
    test_score = rf.score(X_test, y_test)
    gap = train_score - test_score
    depth_str = str(depth) if depth else "无限"
    status = "欠拟合" if test_score < 0.92 else ("过拟合" if gap > 0.05 else "良好")
    print(f"    depth={depth_str:>4}: 训练={train_score:.4f} 测试={test_score:.4f} 差距={gap:.4f} → {status}")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 60)
print("第6课总结:")
print("  [v] 交叉验证: K-Fold, StratifiedKFold, 更稳定的评估")
print("  [v] 网格搜索: 穷举参数组合，小空间用")
print("  [v] 随机搜索: 随机采样，大空间用")
print("  [v] Pipeline: 预处理+模型一体化，防数据泄露")
print("  [v] 过拟合诊断: 比较训练/测试分数差距")
print("=" * 60)
