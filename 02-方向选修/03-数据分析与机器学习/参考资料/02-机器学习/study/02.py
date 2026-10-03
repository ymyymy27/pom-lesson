import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge,Lasso,ElasticNet
from sklearn.metrics import r2_score
from sklearn.metrics import mean_absolute_error
np.random.seed(42)

# x = np.random.rand(100,1)
# y = 3 * x.squeeze() + 5 + np.random.randn(100) * 2

# x_train,x_test,y_train,y_test = train_test_split(x,y,test_size=0.2,random_state=42)

# model = LinearRegression()
# model.fit(x_train,y_train)

# y_pred = model.predict(x_test)
# mse = mean_squared_error(y_test,y_pred)

np.random.seed(42)
x_nl = np.random.rand(100,1) * 6 - 3
y_nl = 2 * x_nl.squeeze() ** 2 -3 * x_nl.squeeze() + 1 + np.random.randn(100) * 2

x_nl_train,x_nl_test,y_nl_train,y_nl_test = train_test_split(x_nl,y_nl,test_size=.3)

for degree in [1,2,3,5]:
    pipe = Pipeline(
        [(
            "poly",PolynomialFeatures(degree=degree,include_bias=False)
        ),
        (
            "model",LinearRegression()
        )]
    )
    pipe.fit(x_nl_train,y_nl_train)
    y_pred = pipe.predict(x_nl_test)
    r2 = r2_score(y_nl_test,y_pred)
    mse = mean_squared_error(y_nl_test,y_pred)

poly = PolynomialFeatures(degree=10,include_bias=False)
x_poly_train = poly.fit_transform(x_nl_train)
x_poly_test = poly.transform(x_nl_test)

models = {
    "LinearRegression (无正则)": LinearRegression(),
    "Ridge" : Ridge(alpha=1),
    "Lasso" : Lasso(alpha=0.1),
    "ElasticNet" : ElasticNet(alpha=0.1,l1_ratio=0.5),
}

for name,m in models.items():
    m.fit(x_poly_train,y_nl_train)
    train_score = r2_score(y_nl_train,m.predict(x_poly_train))
    test_score = r2_score(y_nl_test,m.predict(x_poly_test))
    n_nonzero = np.sum(np.abs(m.coef_) > 1e-6)
    print(f"  {name:35s} 训练R²={train_score:.4f}  测试R²={test_score:.4f}  非零系数={n_nonzero}")

x_train = x_poly_train
y_train = y_nl_train
x_test = x_poly_test
y_test = y_nl_test

model = LinearRegression()
model.fit(x_train, y_train)
y_pred = model.predict(x_test)

mse_val = mean_squared_error(y_test, y_pred)
rmse_val = np.sqrt(mse_val)
mae_val = mean_absolute_error(y_test, y_pred)
r2_val = r2_score(y_test, y_pred)


