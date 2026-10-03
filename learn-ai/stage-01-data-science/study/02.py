import pandas as pd
import numpy as np

# s = pd.Series([10,20,30],index=['a','b','c'])
# print(s['b'])

# df = pd.DataFrame({
#     'name':['Alice','Bob','Charlie'],
#     'age':[25,30,35],
#     'salary':[50000,60000,70000]
# })
# print(df)
# df = pd.read_csv( 
#     'students.csv'
#     )
# print(df)

# df.to_csv('output.csv', index=False)

# print("\n数据已保存到 output.csv")
# df.head(5)
# df.tail(3)
# df.shape
# df.dtypes
# df.info
# df.decribe
# print(df.shape)

# df.columns
# df['age']
# df[['name','age']]

# c = df.loc[0:2,'name':'age']
# d = df['name'].isin(['Alice','Bob'])


df = pd.read_csv(
    'student.csv'
)
print(df)

df[da['age']>30]

print(df.loc[0:2,'name':'age'])
df.iloc[0:2,0:2]
df.query('age > 30 and salary > 60000')

df[df['name'].isin(['Alice','Bob'])]


