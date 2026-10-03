"""
==============================================================================
第1课：机器学习概述与 Scikit-learn 入门
==============================================================================

本课内容：
1. 机器学习三大类型（监督/无监督/强化学习）
2. sklearn 生态与核心 API
3. 内置数据集的加载与探索
4. 数据集划分（训练集/测试集）
5. 第一个模型：从数据到预测的完整流程

运行方式：python 01_ml_overview.py
==============================================================================
"""

import numpy as np
import pandas as pd
from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

print("=" * 60)
print("第1课：机器学习概述与 Scikit-learn 入门")
print("=" * 60)

# ============================================================================
# 1. 机器学习三大类型
# ============================================================================
print("\n--- 1. 机器学习三大类型 ---")

ml_types = {
    "监督学习 (Supervised)": {
        "特点": "有标签数据，已知正确答案",
        "任务": "分类（离散）、回归（连续）",
        "例子": "垃圾邮件检测、房价预测、图像分类",
        "算法": "线性回归、逻辑回归、决策树、SVM、随机森林",
    },
    "无监督学习 (Unsupervised)": {
        "特点": "无标签数据，自动发现结构",
        "任务": "聚类、降维、异常检测",
        "例子": "客户分群、数据压缩、异常交易检测",
        "算法": "K-Means、PCA、DBSCAN",
    },
    "强化学习 (Reinforcement)": {
        "特点": "智能体与环境交互，通过奖励学习",
        "任务": "决策、控制",
        "例子": "游戏AI、机器人控制、推荐系统",
        "算法": "Q-Learning、PPO、DQN",
    },
}

for name, info in ml_types.items():
    print(f"\n  【{name}】")
    for k, v in info.items():
        print(f"    {k}: {v}")

# ============================================================================
# 2. Scikit-learn 核心 API 设计
# ============================================================================
print("\n--- 2. Scikit-learn 核心 API ---")

print("""
  sklearn 所有模型都遵循统一接口：

  model = SomeModel(参数)      # 创建模型
  model.fit(X_train, y_train)  # 训练（学习）
  y_pred = model.predict(X_test)  # 预测
  score = model.score(X_test, y_test)  # 评估

  这个设计叫 Estimator API，学会一个，所有模型都会用！

  核心模块：
  ┌─────────────────────────────────────────────┐
  │ sklearn.datasets        内置数据集           │
  │ sklearn.model_selection  数据划分/交叉验证    │
  │ sklearn.preprocessing    数据预处理           │
  │ sklearn.linear_model     线性模型             │
  │ sklearn.tree             决策树               │
  │ sklearn.ensemble         集成方法             │
  │ sklearn.svm              支持向量机           │
  │ sklearn.neighbors        近邻算法             │
  │ sklearn.cluster          聚类                 │
  │ sklearn.decomposition    降维                 │
  │ sklearn.metrics          评估指标             │
  │ sklearn.pipeline         管道                 │
  └─────────────────────────────────────────────┘
""")

# ============================================================================
# 3. 内置数据集
# ============================================================================
print("--- 3. 内置数据集探索 ---")

# --- 3.1 Iris 鸢尾花数据集（分类） ---
print("\n  [Iris 鸢尾花数据集]")
iris = datasets.load_iris()
print(f"  特征名: {iris.feature_names}")
print(f"  类别名: {list(iris.target_names)}")
print(f"  数据形状: {iris.data.shape}  (150个样本, 4个特征)")
print(f"  标签分布: {np.bincount(iris.target)}  (每类50个)")

# 转成 DataFrame 方便查看
df_iris = pd.DataFrame(iris.data, columns=iris.feature_names)
df_iris["target"] = iris.target
print(f"\n  前5行数据:")
print(df_iris.head().to_string(index=False))

# --- 3.2 其他常用数据集 ---
print("\n  [其他常用内置数据集]")
builtin_datasets = {
    "load_iris()": "鸢尾花分类 (150样本, 4特征, 3类)",
    "load_digits()": "手写数字分类 (1797样本, 64特征, 10类)",
    "load_wine()": "葡萄酒分类 (178样本, 13特征, 3类)",
    "load_breast_cancer()": "乳腺癌分类 (569样本, 30特征, 2类)",
    "load_diabetes()": "糖尿病回归 (442样本, 10特征)",
    "fetch_california_housing()": "加州房价回归 (20640样本, 8特征)",
}
for name, desc in builtin_datasets.items():
    print(f"    {name:35s} → {desc}")

# --- 3.3 生成模拟数据 ---
print("\n  [生成模拟数据]")
from sklearn.datasets import make_classification, make_regression

# 生成分类数据
X_cls, y_cls = make_classification(
    n_samples=200, n_features=5, n_informative=3,
    n_classes=2, random_state=42
)
print(f"  make_classification: X={X_cls.shape}, y={y_cls.shape}")

# 生成回归数据
X_reg, y_reg = make_regression(
    n_samples=200, n_features=3, noise=10, random_state=42
)
print(f"  make_regression:     X={X_reg.shape}, y={y_reg.shape}")

# ============================================================================
# 4. 数据集划分
# ============================================================================
print("\n--- 4. 数据集划分 ---")

X, y = iris.data, iris.target

# 基本划分：80% 训练，20% 测试
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"  总数据: {X.shape[0]} 个样本")
print(f"  训练集: {X_train.shape[0]} 个样本 ({X_train.shape[0]/X.shape[0]:.0%})")
print(f"  测试集: {X_test.shape[0]} 个样本 ({X_test.shape[0]/X.shape[0]:.0%})")
print(f"  训练集标签分布: {np.bincount(y_train)}")
print(f"  测试集标签分布: {np.bincount(y_test)}")

print("""
  关键参数:
    test_size=0.2    测试集占 20%
    random_state=42  固定随机种子（结果可复现）
    stratify=y       分层抽样（保持各类别比例一致）

  为什么要划分？
    训练集：用来训练模型（"学习"）
    测试集：用来评估模型（"考试"）
    不能用训练数据考试，否则是"作弊"→ 过拟合
""")

# ============================================================================
# 5. 第一个完整模型
# ============================================================================
print("--- 5. 第一个完整模型 ---")

# 步骤1: 加载数据
print("\n  步骤1: 加载数据")
X, y = iris.data, iris.target
print(f"    数据: {X.shape}, 标签: {y.shape}")

# 步骤2: 划分数据
print("  步骤2: 划分数据")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"    训练: {X_train.shape}, 测试: {X_test.shape}")

# 步骤3: 数据预处理（标准化）
print("  步骤3: 数据预处理（标准化）")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)  # fit + transform
X_test_scaled = scaler.transform(X_test)          # 只 transform（用训练集的参数）
print(f"    标准化前均值: {X_train[:, 0].mean():.2f}, 标准差: {X_train[:, 0].std():.2f}")
print(f"    标准化后均值: {X_train_scaled[:, 0].mean():.2f}, 标准差: {X_train_scaled[:, 0].std():.2f}")

# 步骤4: 训练模型
print("  步骤4: 训练模型")
model = LogisticRegression(max_iter=200, random_state=42)
model.fit(X_train_scaled, y_train)
print(f"    模型已训练完成")

# 步骤5: 预测
print("  步骤5: 预测")
y_pred = model.predict(X_test_scaled)
print(f"    预测结果: {y_pred}")
print(f"    真实标签: {y_test}")

# 步骤6: 评估
print("  步骤6: 评估")
acc = accuracy_score(y_test, y_pred)
print(f"    准确率: {acc:.4f} ({acc:.0%})")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 60)
print("第1课总结:")
print("  [v] 机器学习三大类型: 监督/无监督/强化")
print("  [v] sklearn 统一API: fit() → predict() → score()")
print("  [v] 内置数据集: load_iris / load_digits / make_*")
print("  [v] 数据划分: train_test_split + stratify")
print("  [v] 完整流程: 加载→划分→预处理→训练→预测→评估")
print("=" * 60)
