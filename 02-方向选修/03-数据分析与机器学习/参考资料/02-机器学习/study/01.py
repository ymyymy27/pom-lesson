'''
# 机器学习分类

# 监督学习
有标签数据，已知正确答案
1.分类
2.回归

# 无监督学习
无标签数据，自动发现结构
聚类

# 强化学习
环境交互学习


机器学习工作流程：

需求分析->数据集采集->数据处理->特征设计->模型选择->模型训练->模型评估->部署上线
'''

'''
scikit-learn环境搭建
'''

from sklearn.linear_model import LinearRegression
# # 挑选模型
# model = LinearRegression()

# # 训练模型
# model.fit(x_train, y_train)

# # 预测
# result = model.predict(x_test)

# # 评估
# score = model.score(x_test, y_test)

#---------

from sklearn.model_selection import train_test_split

# x_train, x_test, y_train, y_test = train_test_split(x,y,test_size=0.2,random_state=42)
import numpy as np
import pandas as pd
from sklearn import datasets
from sklearn.model_selection import train_test_split

iris = datasets.load_iris()
print(f"  特征名: {iris.feature_names}")
print(f"  类别名: {list(iris.target_names)}")
print(f"  数据形状: {iris.data.shape}  (150个样本, 4个特征)")
print(f"  标签分布: {np.bincount(iris.target)}  (每类50个)")

df_iris = pd.DataFrame(iris.data, columns=iris.feature_names)
# df_iris["target"] = iris.target
print(df_iris.head().to_string(index=False))

from sklearn.datasets import make_classification, make_regression

x_cls,y_cls = make_classification(n_samples=200,n_features=5,n_informative=3)