# 第1课：SQL 基础 — SELECT 查询入门

## 1. SQL 是什么？

### 一句话解释
**SQL (Structured Query Language) 就是"和数据库对话的语言"** —— 用固定的语法告诉数据库你要查什么数据。

### 类比理解
```
你对数据库说:  "给我所有年龄大于25岁的用户，按注册时间排序"
SQL 翻译成:    SELECT * FROM users WHERE age > 25 ORDER BY created_at
```

### 为什么产品经理要学 SQL？

- ✅ **自主取数**：不用每次都找数据分析师
- ✅ **验证假设**：快速验证产品想法（"注册3天内未活跃的用户有多少？"）
- ✅ **数据驱动**：A/B测试分析、用户行为分析、漏斗分析
- ✅ **面试必考**：AI产品经理面试中 SQL 是高频技能考察点

---

## 2. 基础概念

### 数据库结构

```
数据库 (Database)
  └── 表 (Table)
        ├── 列/字段 (Column)    ← 数据的属性（姓名、年龄、邮箱）
        └── 行/记录 (Row)       ← 一条数据

示例 users 表:
┌────┬────────┬─────┬──────────────────┬────────────┐
│ id │ name   │ age │ email            │ created_at │
├────┼────────┼─────┼──────────────────┼────────────┤
│  1 │ 张三   │  25 │ zhang@gmail.com  │ 2024-01-15 │
│  2 │ 李四   │  30 │ li@qq.com        │ 2024-02-20 │
│  3 │ 王五   │  22 │ wang@outlook.com │ 2024-03-10 │
└────┴────────┴─────┴──────────────────┴────────────┘
```

### 常见数据类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `INT` / `INTEGER` | 整数 | 1, 100, -5 |
| `FLOAT` / `DECIMAL` | 小数 | 3.14, 99.9 |
| `VARCHAR(n)` / `TEXT` | 字符串 | 'hello', '张三' |
| `DATE` | 日期 | '2024-01-15' |
| `DATETIME` / `TIMESTAMP` | 日期时间 | '2024-01-15 14:30:00' |
| `BOOLEAN` | 布尔 | TRUE, FALSE |

---

## 3. SELECT — 查询数据

### 3.1 查询所有列

```sql
-- 查询 users 表的所有数据
SELECT * FROM users;

-- * 表示所有列
```

### 3.2 查询指定列

```sql
-- 只查姓名和年龄
SELECT name, age FROM users;

-- 给列起别名（AS）
SELECT name AS 姓名, age AS 年龄 FROM users;
```

### 3.3 去重（DISTINCT）

```sql
-- 查看有哪些不同的城市
SELECT DISTINCT city FROM users;

-- 组合去重
SELECT DISTINCT city, gender FROM users;
```

---

## 4. WHERE — 条件过滤

### 4.1 比较运算符

```sql
-- 等于
SELECT * FROM users WHERE age = 25;

-- 不等于
SELECT * FROM users WHERE age != 25;
SELECT * FROM users WHERE age <> 25;

-- 大于/小于
SELECT * FROM users WHERE age > 25;
SELECT * FROM users WHERE age >= 25;
SELECT * FROM users WHERE age < 30;
```

### 4.2 逻辑运算符

```sql
-- AND（同时满足）
SELECT * FROM users WHERE age > 25 AND city = '北京';

-- OR（满足其一）
SELECT * FROM users WHERE city = '北京' OR city = '上海';

-- NOT（取反）
SELECT * FROM users WHERE NOT age > 30;
```

### 4.3 范围与集合

```sql
-- BETWEEN（范围，包含两端）
SELECT * FROM users WHERE age BETWEEN 20 AND 30;

-- IN（在集合中）
SELECT * FROM users WHERE city IN ('北京', '上海', '深圳');

-- NOT IN（不在集合中）
SELECT * FROM users WHERE city NOT IN ('北京', '上海');
```

### 4.4 模糊匹配（LIKE）

```sql
-- % 匹配任意多个字符
SELECT * FROM users WHERE name LIKE '张%';     -- 以"张"开头
SELECT * FROM users WHERE email LIKE '%@gmail%'; -- 包含"@gmail"

-- _ 匹配单个字符
SELECT * FROM users WHERE name LIKE '张_';      -- "张"后面一个字
```

### 4.5 NULL 判断

```sql
-- 判断是否为空（不能用 = NULL）
SELECT * FROM users WHERE phone IS NULL;
SELECT * FROM users WHERE phone IS NOT NULL;
```

---

## 5. ORDER BY — 排序

```sql
-- 升序（默认）
SELECT * FROM users ORDER BY age;
SELECT * FROM users ORDER BY age ASC;

-- 降序
SELECT * FROM users ORDER BY age DESC;

-- 多列排序
SELECT * FROM users ORDER BY city, age DESC;
-- 先按城市升序，同城市内按年龄降序
```

---

## 6. LIMIT — 限制行数

```sql
-- 取前10条
SELECT * FROM users LIMIT 10;

-- 跳过前20条，取10条（分页）
SELECT * FROM users LIMIT 10 OFFSET 20;
-- MySQL 简写: LIMIT 20, 10
```

---

## 7. 计算列与常用函数

### 算术运算

```sql
-- 计算列
SELECT name, age, age + 5 AS 五年后年龄 FROM users;
SELECT name, price, quantity, price * quantity AS 总价 FROM orders;
```

### 字符串函数

```sql
SELECT LENGTH(name) AS 名字长度 FROM users;              -- 字符串长度
SELECT UPPER(email) FROM users;                           -- 转大写
SELECT LOWER(email) FROM users;                           -- 转小写
SELECT CONCAT(name, '(', city, ')') AS 显示名 FROM users; -- 拼接
SELECT SUBSTRING(email, 1, 5) FROM users;                 -- 截取
```

### 日期函数

```sql
-- 当前日期
SELECT CURRENT_DATE;
SELECT NOW();

-- 日期提取
SELECT YEAR(created_at) AS 年 FROM users;
SELECT MONTH(created_at) AS 月 FROM users;

-- 日期差
SELECT DATEDIFF(NOW(), created_at) AS 注册天数 FROM users;
```

### CASE WHEN（条件表达式）

```sql
-- 类似 if-else
SELECT name, age,
  CASE
    WHEN age < 18 THEN '未成年'
    WHEN age < 30 THEN '青年'
    WHEN age < 50 THEN '中年'
    ELSE '老年'
  END AS 年龄段
FROM users;
```

---

## 8. SQL 执行顺序

```
书写顺序:  SELECT → FROM → WHERE → GROUP BY → HAVING → ORDER BY → LIMIT

实际执行:  FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
           ①       ②        ③          ④        ⑤        ⑥         ⑦

理解这个顺序很重要：
  - WHERE 在 SELECT 之前，所以 WHERE 中不能用 SELECT 的别名
  - ORDER BY 在 SELECT 之后，可以用别名
```

---

## 9. 动手练习

假设有如下表：

```
users 表: id, name, age, city, gender, created_at
orders 表: id, user_id, product, amount, order_date
```

1. 查询所有北京的用户
2. 查询年龄在 20-30 之间的女性用户
3. 查询邮箱包含 "gmail" 的用户
4. 查询所有用户，按年龄从大到小排序
5. 查询最近注册的 5 个用户
6. 用 CASE WHEN 把用户按年龄分成"青年/中年/老年"

---

## 10. 小结

| 语法 | 作用 | 示例 |
|------|------|------|
| `SELECT` | 查询列 | `SELECT name, age` |
| `FROM` | 指定表 | `FROM users` |
| `WHERE` | 条件过滤 | `WHERE age > 25` |
| `ORDER BY` | 排序 | `ORDER BY age DESC` |
| `LIMIT` | 限制行数 | `LIMIT 10` |
| `DISTINCT` | 去重 | `SELECT DISTINCT city` |
| `LIKE` | 模糊匹配 | `WHERE name LIKE '张%'` |
| `IN` | 集合匹配 | `WHERE city IN (...)` |
| `BETWEEN` | 范围 | `WHERE age BETWEEN 20 AND 30` |
| `CASE WHEN` | 条件表达式 | `CASE WHEN ... THEN ... END` |

---

**下一课：** `02_aggregation.md` - 聚合函数与分组
