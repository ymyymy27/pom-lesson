"""
==============================================================================
第5课：特征工程
==============================================================================

本课内容：
1. 特征缩放（标准化/归一化）
2. 类别特征编码（Label/OneHot/Ordinal）
3. 缺失值处理
4. 特征选择（方差/相关性/模型重要性）
5. 降维（PCA）

运行方式：python 05_feature_engineering.py
==============================================================================
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler,
    LabelEncoder, OneHotEncoder, OrdinalEncoder,
)
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import (
    VarianceThreshold, SelectKBest, f_classif, mutual_info_classif,
)
from sklearn.decomposition import PCA
from sklearn.datasets import load_iris, load_breast_cancer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

print("=" * 60)
print("第5课：特征工程")
print("=" * 60)

# ============================================================================
# 1. 特征缩放
# ============================================================================
print("\n--- 1. 特征缩放 ---")

print("""
  为什么要缩放？
    不同特征的量纲不同（身高cm vs 体重kg vs 收入万元）
    很多算法对尺度敏感：逻辑回归、SVM、KNN、PCA
    不敏感的算法：决策树、随机森林

  三种常用方法：
    StandardScaler: 均值=0, 标准差=1  ← 最常用
    MinMaxScaler:   缩放到 [0, 1]
    RobustScaler:   对异常值鲁棒（用中位数和四分位数）
""")

# 模拟不同量纲的数据
data = pd.DataFrame({
    "身高(cm)": [170, 165, 180, 175, 160],
    "体重(kg)": [65, 55, 80, 70, 50],
    "收入(万)": [15, 8, 30, 20, 5],
})
print("  原始数据:")
print(f"  {data.to_string(index=False)}")

# StandardScaler
ss = StandardScaler()
data_std = pd.DataFrame(ss.fit_transform(data), columns=data.columns)
print(f"\n  StandardScaler (均值=0, 标准差=1):")
print(f"  {data_std.round(3).to_string(index=False)}")

# MinMaxScaler
mm = MinMaxScaler()
data_mm = pd.DataFrame(mm.fit_transform(data), columns=data.columns)
print(f"\n  MinMaxScaler (缩放到[0,1]):")
print(f"  {data_mm.round(3).to_string(index=False)}")

print("""
  ⚠️ 重要原则：
    1. 先 split 再 fit_transform（防止数据泄露）
    2. 训练集 fit_transform，测试集只 transform
    
    scaler.fit_transform(X_train)   ← 用训练集计算均值/标准差
    scaler.transform(X_test)        ← 用训练集的参数转换测试集
""")

# ============================================================================
# 2. 类别特征编码
# ============================================================================
print("\n--- 2. 类别特征编码 ---")

print("""
  机器学习模型只能处理数字，文字类别需要编码

  三种方法：
    LabelEncoder:   类别 → 整数（有序类别）
    OneHotEncoder:  类别 → 独热向量（无序类别，推荐）
    OrdinalEncoder: 类别 → 有序整数（多列同时编码）
""")

# LabelEncoder（单列）
print("  [LabelEncoder] 适合有序类别")
le = LabelEncoder()
sizes = ["S", "M", "L", "XL", "M", "S"]
encoded = le.fit_transform(sizes)
print(f"    原始: {sizes}")
print(f"    编码: {encoded}")
print(f"    解码: {list(le.inverse_transform(encoded))}")

# OneHotEncoder（无序类别，推荐）
print("\n  [OneHotEncoder] 适合无序类别")
colors = np.array(["红", "蓝", "绿", "红", "蓝"]).reshape(-1, 1)
ohe = OneHotEncoder(sparse_output=False)
encoded_oh = ohe.fit_transform(colors)
print(f"    原始: {colors.ravel()}")
print(f"    编码:")
for i, cat in enumerate(ohe.categories_[0]):
    print(f"      {cat}: {encoded_oh[:, i].astype(int)}")

print("""
  ⚠️ 注意：
    - 无序类别（颜色/城市/品牌）→ 用 OneHot
    - 有序类别（低/中/高）→ 用 Ordinal / Label
    - 高基数类别（上千种）→ 考虑 Target Encoding 或降维
""")

# ============================================================================
# 3. 缺失值处理
# ============================================================================
print("\n--- 3. 缺失值处理 ---")

# 模拟缺失数据
df_miss = pd.DataFrame({
    "年龄": [25, np.nan, 35, 40, np.nan, 30],
    "收入": [5000, 8000, np.nan, 12000, 6000, np.nan],
    "城市": ["北京", "上海", None, "北京", "深圳", "上海"],
})
print("  含缺失值的数据:")
print(f"  {df_miss.to_string(index=False)}")
print(f"  缺失统计: {df_miss.isnull().sum().to_dict()}")

# 数值列：用均值填充
num_imputer = SimpleImputer(strategy="mean")
df_num = df_miss[["年龄", "收入"]].copy()
df_num_filled = pd.DataFrame(
    num_imputer.fit_transform(df_num),
    columns=df_num.columns
)
print(f"\n  均值填充后:")
print(f"  {df_num_filled.to_string(index=False)}")

# 类别列：用众数填充
cat_imputer = SimpleImputer(strategy="most_frequent")
df_cat = df_miss[["城市"]].copy()
df_cat_filled = pd.DataFrame(
    cat_imputer.fit_transform(df_cat),
    columns=["城市"]
)
print(f"\n  众数填充后: {df_cat_filled['城市'].tolist()}")

print("""
  填充策略选择：
    mean:           均值（数值型，正态分布）
    median:         中位数（数值型，有异常值）
    most_frequent:  众数（类别型）
    constant:       固定值（如 "Unknown"）
""")

# ============================================================================
# 4. 特征选择
# ============================================================================
print("\n--- 4. 特征选择 ---")

iris = load_iris()
X, y = iris.data, iris.target

print(f"  原始特征: {iris.feature_names}")

# 方法1: 方差过滤
print("\n  [方法1: 方差过滤]")
print(f"  各特征方差: {np.var(X, axis=0).round(4)}")
selector = VarianceThreshold(threshold=0.5)
X_var = selector.fit_transform(X)
selected = [f for f, s in zip(iris.feature_names, selector.get_support()) if s]
print(f"  方差>0.5 的特征: {selected} ({X_var.shape[1]}个)")

# 方法2: 统计检验（SelectKBest）
print("\n  [方法2: SelectKBest (F统计量)]")
selector_k = SelectKBest(f_classif, k=2)
X_k = selector_k.fit_transform(X, y)
scores = selector_k.scores_
for feat, score in zip(iris.feature_names, scores):
    bar = "█" * int(score / 20)
    print(f"    {feat:>25s}: {score:>8.2f} {bar}")
selected_k = [f for f, s in zip(iris.feature_names, selector_k.get_support()) if s]
print(f"  选择的Top2: {selected_k}")

# 方法3: 模型重要性
print("\n  [方法3: 随机森林特征重要性]")
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X, y)
for feat, imp in sorted(zip(iris.feature_names, rf.feature_importances_), key=lambda x: -x[1]):
    bar = "█" * int(imp * 40)
    print(f"    {feat:>25s}: {imp:.4f} {bar}")

# ============================================================================
# 5. PCA 降维
# ============================================================================
print("\n--- 5. PCA 降维 ---")

print("""
  PCA (主成分分析)：
    将高维数据投影到低维空间，尽量保留信息（方差最大化）
    
  用途：
    1. 降维 → 减少计算量
    2. 可视化 → 高维数据投影到2D/3D
    3. 去噪 → 去除低方差成分
""")

# 30维数据 → 2维可视化
data_bc = load_breast_cancer()
X_bc = StandardScaler().fit_transform(data_bc.data)

pca = PCA(n_components=2)
X_2d = pca.fit_transform(X_bc)

print(f"  原始维度: {data_bc.data.shape[1]}维")
print(f"  降维后:   {X_2d.shape[1]}维")
print(f"  保留方差: {pca.explained_variance_ratio_.sum():.4f} ({pca.explained_variance_ratio_.sum():.1%})")
print(f"  各成分方差: {pca.explained_variance_ratio_.round(4)}")

# 选择最优维度
print(f"\n  不同维度保留的方差:")
pca_full = PCA().fit(X_bc)
cumvar = np.cumsum(pca_full.explained_variance_ratio_)
for n in [2, 5, 10, 15, 20, 25, 30]:
    if n <= len(cumvar):
        print(f"    {n:>2}维: 保留方差={cumvar[n-1]:.4f} ({cumvar[n-1]:.1%})")

# 降维后的分类效果对比
print(f"\n  降维后分类效果对比:")
X_tr, X_te, y_tr, y_te = train_test_split(X_bc, data_bc.target, test_size=0.2, random_state=42)
for n_comp in [2, 5, 10, 30]:
    if n_comp <= X_bc.shape[1]:
        pca_n = PCA(n_components=n_comp)
        X_tr_pca = pca_n.fit_transform(X_tr)
        X_te_pca = pca_n.transform(X_te)
        lr = LogisticRegression(max_iter=5000, random_state=42)
        lr.fit(X_tr_pca, y_tr)
        acc = lr.score(X_te_pca, y_te)
        var = pca_n.explained_variance_ratio_.sum()
        print(f"    {n_comp:>2}维 (方差{var:.1%}): 准确率={acc:.4f}")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 60)
print("第5课总结:")
print("  [v] 特征缩放: StandardScaler最常用，先split再fit")
print("  [v] 类别编码: 无序→OneHot, 有序→Ordinal")
print("  [v] 缺失值: 数值用均值/中位数，类别用众数")
print("  [v] 特征选择: 方差过滤/统计检验/模型重要性")
print("  [v] PCA降维: 保留主要方差，减少维度")
print("=" * 60)
