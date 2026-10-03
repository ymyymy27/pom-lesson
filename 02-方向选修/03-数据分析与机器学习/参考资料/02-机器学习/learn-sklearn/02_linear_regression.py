"""
==============================================================================
第2课：线性回归与梯度下降
==============================================================================

本课内容：
1. 线性回归原理与 sklearn 实现
2. 损失函数（MSE）与梯度下降手动实现
3. 多项式回归（处理非线性关系）
4. 正则化（Ridge / Lasso / ElasticNet）
5. 回归评估指标（MSE / RMSE / MAE / R²）

运行方式：python 02_linear_regression.py
==============================================================================
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline

print("=" * 60)
print("第2课：线性回归与梯度下降")
print("=" * 60)

# ============================================================================
# 1. 线性回归原理
# ============================================================================
print("\n--- 1. 线性回归原理 ---")

print("""
  线性回归：找一条直线（或超平面）最好地拟合数据

  模型:  y = w₁x₁ + w₂x₂ + ... + wₙxₙ + b
         y = Xw + b

  目标:  找到最优的 w 和 b，使预测值尽量接近真实值
  方法:  最小化损失函数（均方误差 MSE）

  MSE = (1/n) Σ(yᵢ - ŷᵢ)²
""")

# --- sklearn 实现 ---
print("  [sklearn 线性回归]")

# 生成模拟数据：y = 3x + 5 + 噪声
np.random.seed(42)
X = np.random.rand(100, 1) * 10
y = 3 * X.squeeze() + 5 + np.random.randn(100) * 2

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 训练
model = LinearRegression()
model.fit(X_train, y_train)

print(f"  真实参数:  w=3, b=5")
print(f"  学到的参数: w={model.coef_[0]:.4f}, b={model.intercept_:.4f}")

# 预测
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"  MSE: {mse:.4f}")

# ============================================================================
# 2. 手动实现梯度下降
# ============================================================================
print("\n--- 2. 手动实现梯度下降 ---")

print("""
  梯度下降：沿着损失函数下降最快的方向更新参数

  重复:
    1. 计算预测值: ŷ = Xw + b
    2. 计算损失: L = MSE(y, ŷ)
    3. 计算梯度: ∂L/∂w, ∂L/∂b
    4. 更新参数: w = w - lr * ∂L/∂w
                 b = b - lr * ∂L/∂b
""")


class GradientDescentLinearRegression:
    """手动实现线性回归（梯度下降法）"""

    def __init__(self, learning_rate=0.01, n_iterations=1000):
        self.lr = learning_rate
        self.n_iter = n_iterations
        self.w = None
        self.b = None
        self.losses = []

    def fit(self, X, y):
        n_samples, n_features = X.shape
        self.w = np.zeros(n_features)
        self.b = 0.0

        for i in range(self.n_iter):
            # 前向：计算预测值
            y_pred = X @ self.w + self.b

            # 计算损失
            loss = np.mean((y - y_pred) ** 2)
            self.losses.append(loss)

            # 计算梯度
            dw = (-2 / n_samples) * (X.T @ (y - y_pred))
            db = (-2 / n_samples) * np.sum(y - y_pred)

            # 更新参数
            self.w -= self.lr * dw
            self.b -= self.lr * db

        return self

    def predict(self, X):
        return X @ self.w + self.b


# 标准化（梯度下降对尺度敏感）
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

gd_model = GradientDescentLinearRegression(learning_rate=0.1, n_iterations=500)
gd_model.fit(X_train_s, y_train)

y_pred_gd = gd_model.predict(X_test_s)
mse_gd = mean_squared_error(y_test, y_pred_gd)

print(f"  手动梯度下降 MSE: {mse_gd:.4f}")
print(f"  sklearn MSE:      {mse:.4f}")
print(f"  损失下降: {gd_model.losses[0]:.2f} → {gd_model.losses[-1]:.2f}")

# ============================================================================
# 3. 多项式回归
# ============================================================================
print("\n--- 3. 多项式回归（处理非线性关系）---")

print("""
  当数据是非线性的，直线拟合不好 → 用多项式特征

  原始特征: [x]
  degree=2: [x, x²]
  degree=3: [x, x², x³]

  本质还是线性模型，只是特征变了
""")

# 生成非线性数据：y = 2x² - 3x + 1 + 噪声
np.random.seed(42)
X_nl = np.random.rand(100, 1) * 6 - 3
y_nl = 2 * X_nl.squeeze() ** 2 - 3 * X_nl.squeeze() + 1 + np.random.randn(100) * 2

X_nl_train, X_nl_test, y_nl_train, y_nl_test = train_test_split(
    X_nl, y_nl, test_size=0.2, random_state=42
)

# 不同 degree 对比
for degree in [1, 2, 3, 5]:
    pipe = Pipeline([
        ("poly", PolynomialFeatures(degree=degree, include_bias=False)),
        ("model", LinearRegression()),
    ])
    pipe.fit(X_nl_train, y_nl_train)
    y_pred = pipe.predict(X_nl_test)
    r2 = r2_score(y_nl_test, y_pred)
    mse = mean_squared_error(y_nl_test, y_pred)
    print(f"  degree={degree}: R²={r2:.4f}, MSE={mse:.4f}")

print("\n  degree=2 效果最好（真实关系就是二次），degree过高会过拟合")

# ============================================================================
# 4. 正则化
# ============================================================================
print("\n--- 4. 正则化（防止过拟合）---")

print("""
  正则化：在损失函数中加入惩罚项，限制参数大小

  Ridge (L2):    Loss = MSE + α × Σwᵢ²    （参数整体缩小）
  Lasso (L1):    Loss = MSE + α × Σ|wᵢ|   （部分参数变为0，特征选择）
  ElasticNet:    Loss = MSE + α₁ × Σ|wᵢ| + α₂ × Σwᵢ²  （两者结合）

  α 越大 → 惩罚越强 → 参数越小 → 模型越简单
""")

# 用多项式 degree=10 制造过拟合场景
poly = PolynomialFeatures(degree=10, include_bias=False)
X_poly_train = poly.fit_transform(X_nl_train)
X_poly_test = poly.transform(X_nl_test)

models = {
    "LinearRegression (无正则)": LinearRegression(),
    "Ridge (L2, α=1.0)": Ridge(alpha=1.0),
    "Lasso (L1, α=1.0)": Lasso(alpha=1.0),
    "ElasticNet (L1+L2)": ElasticNet(alpha=1.0, l1_ratio=0.5),
}

for name, m in models.items():
    m.fit(X_poly_train, y_nl_train)
    train_score = r2_score(y_nl_train, m.predict(X_poly_train))
    test_score = r2_score(y_nl_test, m.predict(X_poly_test))
    n_nonzero = np.sum(np.abs(m.coef_) > 1e-6)
    print(f"  {name:35s} 训练R²={train_score:.4f}  测试R²={test_score:.4f}  非零系数={n_nonzero}")

# ============================================================================
# 5. 回归评估指标
# ============================================================================
print("\n--- 5. 回归评估指标 ---")

# 用简单线性回归的预测结果
model = LinearRegression()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

mse_val = mean_squared_error(y_test, y_pred)
rmse_val = np.sqrt(mse_val)
mae_val = mean_absolute_error(y_test, y_pred)
r2_val = r2_score(y_test, y_pred)

print(f"  MSE  (均方误差):     {mse_val:.4f}  — 越小越好，对大误差敏感")
print(f"  RMSE (均方根误差):   {rmse_val:.4f}  — 和y同单位，直觉好理解")
print(f"  MAE  (平均绝对误差): {mae_val:.4f}  — 越小越好，对异常值鲁棒")
print(f"  R²   (决定系数):     {r2_val:.4f}   — 1.0完美，0.0等于瞎猜")

print("""
  指标选择指南:
    日常汇报 → RMSE（直觉好理解："平均误差约X元"）
    有异常值 → MAE（比MSE鲁棒）
    模型对比 → R²（不同数据集也能比较）
""")

# ============================================================================
# 总结
# ============================================================================
print("=" * 60)
print("第2课总结:")
print("  [v] 线性回归: y = Xw + b, 最小化MSE")
print("  [v] 梯度下降: 计算梯度 → 更新参数 → 重复")
print("  [v] 多项式回归: 增加特征维度处理非线性")
print("  [v] 正则化: Ridge(L2)/Lasso(L1)/ElasticNet")
print("  [v] 评估指标: MSE/RMSE/MAE/R²")
print("=" * 60)
