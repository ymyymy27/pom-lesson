# Pandas 数据处理

## 学习目标

- 掌握 Series 和 DataFrame 两大核心数据结构
- 学会数据读写、清洗、筛选、聚合操作
- 能用 Pandas 完成实际数据分析任务

## 1. Pandas 简介

Pandas 是基于 NumPy 的数据分析库，提供灵活的表格型数据结构。

```bash
pip install pandas
```

## 2. Series 与 DataFrame

```python
import pandas as pd
import numpy as np

# Series - 一维带标签数组
s = pd.Series([10, 20, 30], index=['a', 'b', 'c'])
print(s['b'])       # 20

# DataFrame - 二维表格
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'salary': [50000, 60000, 70000]
})
print(df)
```

## 3. 数据读写

```python
# CSV
df = pd.read_csv('data.csv')
df.to_csv('output.csv', index=False)

# Excel
df = pd.read_excel('data.xlsx', sheet_name='Sheet1')
df.to_excel('output.xlsx', index=False)

# JSON
df = pd.read_json('data.json')
df.to_json('output.json', orient='records')

# SQL（需要 SQLAlchemy）
from sqlalchemy import create_engine
engine = create_engine('sqlite:///mydb.db')
df = pd.read_sql('SELECT * FROM users', engine)
df.to_sql('users', engine, if_exists='replace')
```

## 4. 数据探索

```python
df = pd.read_csv('data.csv')

# 基本信息
df.head(5)         # 前 5 行
df.tail(3)         # 后 3 行
df.shape           # (行数, 列数)
df.dtypes          # 各列数据类型
df.info()          # 综合信息
df.describe()      # 统计摘要

# 列操作
df.columns         # 列名
df['age']          # 选取单列 → Series
df[['name', 'age']]  # 选取多列 → DataFrame
```

## 5. 数据筛选

```python
# 布尔索引
df[df['age'] > 30]
df[(df['age'] > 25) & (df['salary'] > 55000)]

# loc - 基于标签
df.loc[0:2, 'name':'age']      # 行标签 0-2，列 name 到 age

# iloc - 基于位置
df.iloc[0:2, 0:2]              # 前 2 行，前 2 列

# query 方法
df.query('age > 30 and salary > 60000')

# isin
df[df['name'].isin(['Alice', 'Bob'])]
```

## 6. 数据清洗

```python
# 缺失值
df.isnull().sum()              # 各列缺失数
df.dropna()                    # 删除含缺失的行
df.dropna(subset=['age'])      # 仅看 age 列
df.fillna(0)                   # 用 0 填充
df['age'].fillna(df['age'].mean(), inplace=True)  # 均值填充

# 重复值
df.duplicated().sum()          # 重复行数
df.drop_duplicates()           # 删除重复行

# 类型转换
df['age'] = df['age'].astype(int)
df['date'] = pd.to_datetime(df['date'])

# 字符串处理
df['name'] = df['name'].str.lower()
df['name'] = df['name'].str.strip()
df['email_domain'] = df['email'].str.split('@').str[1]

# 重命名
df.rename(columns={'name': '姓名', 'age': '年龄'}, inplace=True)
```

## 7. 数据聚合与分组

```python
# 基本聚合
df['salary'].mean()
df['salary'].sum()
df['age'].value_counts()

# groupby
grouped = df.groupby('department')
grouped['salary'].mean()                     # 各部门平均薪资
grouped.agg({'salary': 'mean', 'age': 'max'})  # 多列多聚合

# 自定义聚合
grouped.agg(
    avg_salary=('salary', 'mean'),
    max_age=('age', 'max'),
    count=('name', 'count')
)

# 透视表
pd.pivot_table(df, values='salary', index='department',
               columns='gender', aggfunc='mean')
```

## 8. 数据合并

```python
# merge（类似 SQL JOIN）
df1 = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})
df2 = pd.DataFrame({'id': [2, 3, 4], 'score': [80, 90, 70]})

pd.merge(df1, df2, on='id', how='inner')   # 内连接
pd.merge(df1, df2, on='id', how='left')    # 左连接
pd.merge(df1, df2, on='id', how='outer')   # 外连接

# concat（拼接）
pd.concat([df1, df2], axis=0)   # 纵向拼接
pd.concat([df1, df2], axis=1)   # 横向拼接
```

## 9. 数据变换

```python
# apply - 对列或行应用函数
df['salary_level'] = df['salary'].apply(
    lambda x: 'high' if x > 60000 else 'low'
)

# map - Series 映射
df['gender_cn'] = df['gender'].map({'M': '男', 'F': '女'})

# 排序
df.sort_values('salary', ascending=False)
df.sort_values(['department', 'salary'], ascending=[True, False])

# 新增列
df['bonus'] = df['salary'] * 0.1
df['full_name'] = df['first_name'] + ' ' + df['last_name']
```

## 练习

1. 读取一个 CSV 文件，查看基本统计信息，处理缺失值
2. 对数据按某一列分组，计算各组的均值、中位数、标准差
3. 合并两张表（模拟订单表和用户表的 JOIN）
4. 用 `apply` 实现一个自定义的分类函数
5. 创建一个透视表，分析不同维度下的数据分布

## 下一节

→ [03-Matplotlib与Seaborn可视化](03-Matplotlib与Seaborn可视化.md)
