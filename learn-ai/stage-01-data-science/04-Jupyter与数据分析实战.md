# Jupyter 与数据分析实战

## 学习目标

- 掌握 Jupyter Notebook / Lab 的使用技巧
- 学会完整的数据分析流程（EDA）
- 完成一个端到端的数据分析项目

## 1. Jupyter 环境搭建

```bash
pip install jupyterlab notebook

# 启动 Jupyter Lab
jupyter lab

# 启动传统 Notebook
jupyter notebook
```

## 2. Jupyter 快捷键与技巧

```
常用快捷键（命令模式，按 Esc 进入）：
- A / B        → 上方/下方插入新 cell
- DD           → 删除当前 cell
- M / Y        → 切换 Markdown / Code 模式
- Shift+Enter  → 运行当前 cell 并跳到下一个
- Ctrl+Enter   → 运行当前 cell（不跳转）

Magic Commands：
- %timeit      → 计时
- %%time       → cell 计时
- %matplotlib inline  → 内嵌图表
- !pip install xxx    → 安装包
- %who         → 查看已定义变量
```

## 3. 数据分析流程（EDA）

完整的探索性数据分析流程：

```
1. 加载数据 → 2. 初步探索 → 3. 数据清洗 → 4. 特征分析
     ↓              ↓             ↓              ↓
  read_csv      info/describe   缺失值/异常值   可视化/统计
     ↓              ↓             ↓              ↓
5. 相关性分析 → 6. 洞察总结 → 7. 可视化报告
```

## 4. 实战：泰坦尼克号生存分析

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 1. 加载数据
df = pd.read_csv('titanic.csv')

# 2. 初步探索
print(f"数据集形状: {df.shape}")
print(f"\n数据类型:\n{df.dtypes}")
print(f"\n基本统计:\n{df.describe()}")
print(f"\n缺失值:\n{df.isnull().sum()}")

# 3. 数据清洗
df['Age'].fillna(df['Age'].median(), inplace=True)
df['Embarked'].fillna(df['Embarked'].mode()[0], inplace=True)
df.drop('Cabin', axis=1, inplace=True)  # 缺失太多，直接删除

# 4. 特征分析
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# 生存率总览
df['Survived'].value_counts().plot.pie(
    autopct='%1.1f%%', ax=axes[0, 0],
    labels=['Dead', 'Survived']
)
axes[0, 0].set_title('Survival Rate')

# 性别与生存
sns.barplot(data=df, x='Sex', y='Survived', ax=axes[0, 1])
axes[0, 1].set_title('Survival by Gender')

# 舱位等级与生存
sns.barplot(data=df, x='Pclass', y='Survived', ax=axes[0, 2])
axes[0, 2].set_title('Survival by Class')

# 年龄分布
sns.histplot(data=df, x='Age', hue='Survived', kde=True, ax=axes[1, 0])
axes[1, 0].set_title('Age Distribution')

# 票价分布
sns.boxplot(data=df, x='Survived', y='Fare', ax=axes[1, 1])
axes[1, 1].set_title('Fare by Survival')

# 登船港口
sns.countplot(data=df, x='Embarked', hue='Survived', ax=axes[1, 2])
axes[1, 2].set_title('Embarked Distribution')

plt.tight_layout()
plt.show()

# 5. 相关性
numeric_df = df.select_dtypes(include=[np.number])
plt.figure(figsize=(8, 6))
sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm')
plt.title('Feature Correlation')
plt.show()

# 6. 关键洞察
print("""
关键发现：
1. 女性生存率远高于男性（~74% vs ~19%）
2. 一等舱生存率最高（~63%），三等舱最低（~24%）
3. 年龄较小的乘客生存率更高
4. 票价越高，生存率越高
""")
```

## 5. 数据分析最佳实践

- **先全局后细节**：先看整体分布，再深入具体特征
- **假设驱动**：带着问题去探索，而非漫无目的
- **可视化优先**：一图胜千数，善用可视化发现规律
- **记录过程**：用 Markdown cell 记录分析思路和发现
- **可复现**：确保 Notebook 从上到下可完整运行

## 练习

1. 使用 Jupyter Notebook 对一个真实数据集进行完整的 EDA
2. 生成至少 6 张不同类型的可视化图表
3. 总结 3-5 个数据洞察
4. 确保 Notebook 可从头到尾顺序执行

## 阶段总结

本阶段你已掌握：
- ✅ NumPy 数值计算
- ✅ Pandas 数据处理
- ✅ Matplotlib/Seaborn 可视化
- ✅ Jupyter 数据分析流程

→ 下一阶段：[stage-02 机器学习基础](../stage-02-ml-basics/)
