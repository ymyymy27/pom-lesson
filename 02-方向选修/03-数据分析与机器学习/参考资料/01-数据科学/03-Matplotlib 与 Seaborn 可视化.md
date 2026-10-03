> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Matplotlib 与 Seaborn 可视化

## 学习目标

- 掌握 Matplotlib 基础绑图（折线图、柱状图、散点图、直方图）
- 学会 Seaborn 高级统计可视化
- 能为数据分析和模型评估制作专业图表

## 1. Matplotlib 基础

```bash
pip install matplotlib seaborn
```

```python
import matplotlib.pyplot as plt
import numpy as np

# 最简单的折线图
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.plot(x, y)
plt.title('Sine Wave')
plt.xlabel('x')
plt.ylabel('sin(x)')
plt.grid(True)
plt.show()
```

## 2. 常用图表类型

```python
fig, axes = plt.subplots(2, 2, figsize=(10, 8))

# 折线图
axes[0, 0].plot(x, np.sin(x), label='sin')
axes[0, 0].plot(x, np.cos(x), label='cos')
axes[0, 0].legend()
axes[0, 0].set_title('Line Plot')

# 柱状图
categories = ['A', 'B', 'C', 'D']
values = [23, 45, 56, 78]
axes[0, 1].bar(categories, values, color='steelblue')
axes[0, 1].set_title('Bar Chart')

# 散点图
x_scatter = np.random.randn(100)
y_scatter = x_scatter + np.random.randn(100) * 0.5
axes[1, 0].scatter(x_scatter, y_scatter, alpha=0.6)
axes[1, 0].set_title('Scatter Plot')

# 直方图
data = np.random.randn(1000)
axes[1, 1].hist(data, bins=30, edgecolor='black')
axes[1, 1].set_title('Histogram')

plt.tight_layout()
plt.show()
```

## 3. 图表美化

```python
# 设置全局样式
plt.style.use('seaborn-v0_8-whitegrid')

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(x, np.sin(x), linewidth=2, color='#2196F3', label='sin(x)')
ax.fill_between(x, np.sin(x), alpha=0.2, color='#2196F3')
ax.set_title('Styled Plot', fontsize=16, fontweight='bold')
ax.set_xlabel('X axis', fontsize=12)
ax.set_ylabel('Y axis', fontsize=12)
ax.legend(fontsize=12)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.savefig('plot.png', dpi=150, bbox_inches='tight')
plt.show()
```

## 4. Seaborn 统计可视化

```python
import seaborn as sns
import pandas as pd

# 加载示例数据集
tips = sns.load_dataset('tips')
iris = sns.load_dataset('iris')

# 分布图
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
sns.histplot(data=tips, x='total_bill', kde=True, ax=axes[0])
sns.boxplot(data=tips, x='day', y='total_bill', ax=axes[1])
sns.violinplot(data=tips, x='day', y='total_bill', ax=axes[2])
plt.tight_layout()
plt.show()
```

## 5. Seaborn 关系图

```python
# 散点图 + 回归线
sns.lmplot(data=tips, x='total_bill', y='tip', hue='smoker')
plt.show()

# 热力图（相关矩阵）
corr = iris.drop('species', axis=1).corr()
plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap='coolwarm', center=0)
plt.title('Correlation Matrix')
plt.show()

# 配对图（特征间关系总览）
sns.pairplot(iris, hue='species', diag_kind='kde')
plt.show()
```

## 6. 机器学习常用图表

```python
# 混淆矩阵
from sklearn.metrics import confusion_matrix
y_true = [0, 1, 1, 0, 1, 0, 1, 1]
y_pred = [0, 1, 0, 0, 1, 1, 1, 1]
cm = confusion_matrix(y_true, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Neg', 'Pos'],
            yticklabels=['Neg', 'Pos'])
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

# 学习曲线（后续在 ML 阶段详解）
# ROC 曲线
# 特征重要性柱状图
```

## 练习

1. 用 Matplotlib 绘制多条折线图，展示不同函数的对比
2. 用 Seaborn 加载 `tips` 数据集，绘制分类对比箱线图
3. 对 `iris` 数据集绘制配对图和相关矩阵热力图
4. 创建一个 2x3 的子图布局，展示 6 种不同的图表类型

## 下一节

→ [04-Jupyter与数据分析实战](<04-Jupyter 与数据分析实战.md>)
