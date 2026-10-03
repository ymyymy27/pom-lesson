from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import numpy as np

from sklearn.tree import DecisionTreeClassifier

iris = load_iris()
x,y = iris.data, iris.target
x_train,x_test,y_train,y_test = train_test_split(x,y,test_size=0.2,random_state=42)
scaler = StandardScaler()
x_train_s = scaler.fit_transform(x_train)
x_test_s = scaler.transform(x_test)


model = LogisticRegression(max_iter=200)
model.fit(x_train,y_train)

y_pred = model.predict(x_test)
acc = accuracy_score(y_test,y_pred)
# print(f"准确率: {acc:.4f}")

y_prob = model.predict_proba(x_test)
# for i in range(len(y_prob)):
#     print(f"第{i+1}个样本的概率: {y_prob[i].round(4)}")
#     print(f"对应类别: {iris.target_names[np.argmax(y_prob[i])]}")

for depth in [1,2,3,5,None]:
    dt = DecisionTreeClassifier(max_depth=depth,random_state=42)
    dt.fit(x_train,y_train)
    train_acc = dt.score(x_train,y_train)
    test_acc = dt.score(x_test,y_test)
    depth_str = str(depth) if depth else "无限"
    print(f"  depth={depth_str:>4}: 训练={train_acc:.4f}, 测试={test_acc:.4f}"
        f"{'  ← 可能过拟合' if train_acc - test_acc > 0.05 else ''}")

dt_best = DecisionTreeClassifier(max_depth=3,random_state=42)
dt_best.fit(x_train,y_train)
importance = pd.Series(dt_best.feature_importances_,index=iris.feature_names)