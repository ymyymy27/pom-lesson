# XGBoost 梯度提升

> stage-02 补充课  
> 前置：[`03-分类算法.md`](../03-分类算法.md)、[`learn-sklearn/`](../learn-sklearn/)

## 1. 为什么学 XGBoost？

XGBoost（eXtreme Gradient Boosting）是表格数据竞赛和工业界的**默认强基线**：

- Kaggle 表格赛常胜算法
- 训练速度快、可解释（特征重要性）
- 原生支持缺失值、正则化防过拟合

---

## 2. 核心概念

```
Boosting = 串行训练多个弱学习器，每个修正前一个的残差

XGBoost 优化：
  - 二阶泰勒展开加速收敛
  - 列采样（类似 Random Forest）
  - 并行化（特征级并行）
  - L1/L2 正则
```

---

## 3. 快速上手

```python
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd

# 示例：AI Hub 文本分类（传统 ML 基线）
df = pd.read_csv("data/text_labels.csv")
X = df["text"]  # 需先做 TF-IDF 或 CountVectorizer
y = df["label"]

from sklearn.feature_extraction.text import TfidfVectorizer
vectorizer = TfidfVectorizer(max_features=5000)
X_vec = vectorizer.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_vec, y, test_size=0.2, random_state=42
)

model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="mlogloss",
)
model.fit(X_train, y_train)

print(classification_report(y_test, model.predict(X_test)))
```

---

## 4. 关键超参数

| 参数 | 说明 | 典型范围 |
|------|------|----------|
| `n_estimators` | 树的数量 | 100–1000 |
| `max_depth` | 树深度 | 3–10 |
| `learning_rate` | 学习率 | 0.01–0.3 |
| `subsample` | 行采样 | 0.6–1.0 |
| `colsample_bytree` | 列采样 | 0.6–1.0 |
| `reg_alpha` / `reg_lambda` | L1/L2 正则 | 0–10 |

---

## 5. 与 sklearn 对比

| 场景 | 推荐 |
|------|------|
| 表格数据分类/回归 | **XGBoost** |
| 快速原型、小数据集 | Random Forest |
| 需要概率校准 | XGBoost + CalibratedClassifierCV |
| 文本/图像 | 深度学习（stage-03+） |

---

## 6. 动手练习

1. 用 XGBoost 完成 AI Hub 文本分类基线，记录 F1
2. 用 `model.feature_importances_` 分析 Top 10 特征
3. 用 `GridSearchCV` 调 `max_depth` 和 `learning_rate`

---

## 参考

- [XGBoost 官方文档](https://xgboost.readthedocs.io/)
- 安装：`pip install xgboost`
