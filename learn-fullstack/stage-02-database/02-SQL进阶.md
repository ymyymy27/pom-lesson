# 第 02 节：SQL 进阶

## 一、JOIN — 多表联查

### 1.1 为什么需要 JOIN？

数据分散在多张表中（用户在 `users` 表，任务在 `tasks` 表），查询时需要把它们 **关联** 起来。

**示例数据：**

```
users 表:                          tasks 表:
id | name                          id | title        | assignee_id
1  | 张三                           1  | 修复Bug      | 1
2  | 李四                           2  | 写文档       | 2
3  | 王五                           3  | 部署上线     | 1
                                    4  | 设计UI       | NULL
```

### 1.2 INNER JOIN（内连接）

返回两张表中 **匹配** 的行。没有匹配的行会被排除。

```sql
-- 查询每个任务及其负责人
SELECT t.id, t.title, u.name AS assignee_name
FROM tasks t
INNER JOIN users u ON t.assignee_id = u.id;

-- 结果：（注意：assignee_id 为 NULL 的"设计UI"不出现）
-- id | title    | assignee_name
-- 1  | 修复Bug  | 张三
-- 2  | 写文档   | 李四
-- 3  | 部署上线 | 张三
```

### 1.3 LEFT JOIN（左连接）

返回左表的 **所有行**，右表没有匹配的用 NULL 填充。

```sql
-- 查询所有任务，包括未分配的
SELECT t.id, t.title, u.name AS assignee_name
FROM tasks t
LEFT JOIN users u ON t.assignee_id = u.id;

-- 结果：
-- id | title    | assignee_name
-- 1  | 修复Bug  | 张三
-- 2  | 写文档   | 李四
-- 3  | 部署上线 | 张三
-- 4  | 设计UI   | NULL          ← 未分配的任务也会出现
```

### 1.4 RIGHT JOIN（右连接）

返回右表的所有行，左表没有匹配的用 NULL 填充。

```sql
-- 查询所有用户及其任务（包括没有任务的用户）
SELECT u.name, t.title
FROM tasks t
RIGHT JOIN users u ON t.assignee_id = u.id;

-- 结果：
-- name | title
-- 张三 | 修复Bug
-- 张三 | 部署上线
-- 李四 | 写文档
-- 王五 | NULL        ← 王五没有任务
```

### 1.5 FULL OUTER JOIN（全外连接）

返回两张表的 **所有行**，无匹配的用 NULL 填充。

```sql
SELECT u.name, t.title
FROM tasks t
FULL OUTER JOIN users u ON t.assignee_id = u.id;

-- 结果：（两边都包含）
-- name | title
-- 张三 | 修复Bug
-- 张三 | 部署上线
-- 李四 | 写文档
-- 王五 | NULL       ← 没有任务的用户
-- NULL | 设计UI     ← 没有负责人的任务
```

### 1.6 JOIN 类型图示

```
INNER JOIN:        LEFT JOIN:         RIGHT JOIN:       FULL OUTER JOIN:
  ┌───┐             ┌───┐              ┌───┐             ┌───┐
  │ ██│             │███│              │ ██│             │███│
  │███│             │███│              │███│             │███│
  │██ │             │██ │              │███│             │███│
  └───┘             └───┘              └───┘             └───┘
  交集部分          左表全部+交集       右表全部+交集      两表全部
```

### 1.7 多表 JOIN

```sql
-- 查询任务详情：任务标题、负责人、项目名
SELECT
    t.title AS task_title,
    u.name AS assignee,
    p.name AS project_name
FROM tasks t
LEFT JOIN users u ON t.assignee_id = u.id
LEFT JOIN projects p ON t.project_id = p.id
WHERE t.status = 'in_progress'
ORDER BY t.priority DESC;
```

### 1.8 自连接

同一张表自己和自己 JOIN，用于有层级关系的数据。

```sql
-- 查询每个员工及其经理的名字
-- employees 表有 id, name, manager_id 字段
SELECT
    e.name AS employee,
    m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;
```

---

## 二、子查询

子查询是嵌套在其他 SQL 语句中的 SELECT 查询。

### 2.1 WHERE 中的子查询

```sql
-- 查询分配了任务的用户
SELECT * FROM users
WHERE id IN (
    SELECT DISTINCT assignee_id FROM tasks WHERE assignee_id IS NOT NULL
);

-- 查询年龄大于平均年龄的用户
SELECT * FROM users
WHERE age > (SELECT AVG(age) FROM users);

-- EXISTS — 判断子查询是否有结果
SELECT * FROM users u
WHERE EXISTS (
    SELECT 1 FROM tasks t WHERE t.assignee_id = u.id
);
```

### 2.2 FROM 中的子查询（派生表）

```sql
-- 查询每个用户的任务数，筛选任务数大于 3 的
SELECT user_tasks.name, user_tasks.task_count
FROM (
    SELECT u.name, COUNT(t.id) AS task_count
    FROM users u
    LEFT JOIN tasks t ON t.assignee_id = u.id
    GROUP BY u.name
) AS user_tasks
WHERE user_tasks.task_count > 3;
```

### 2.3 SELECT 中的子查询（标量子查询）

```sql
-- 每个用户及其任务数
SELECT
    u.name,
    u.email,
    (SELECT COUNT(*) FROM tasks t WHERE t.assignee_id = u.id) AS task_count
FROM users u;
```

### 2.4 CTE — Common Table Expression（推荐，比子查询更清晰）

```sql
-- WITH 子句定义临时结果集
WITH user_task_counts AS (
    SELECT
        u.id,
        u.name,
        COUNT(t.id) AS task_count
    FROM users u
    LEFT JOIN tasks t ON t.assignee_id = u.id
    GROUP BY u.id, u.name
)
SELECT name, task_count
FROM user_task_counts
WHERE task_count > 3
ORDER BY task_count DESC;

-- 多个 CTE
WITH
active_users AS (
    SELECT * FROM users WHERE is_active = TRUE
),
pending_tasks AS (
    SELECT * FROM tasks WHERE status = 'pending'
)
SELECT au.name, COUNT(pt.id) AS pending_count
FROM active_users au
LEFT JOIN pending_tasks pt ON pt.assignee_id = au.id
GROUP BY au.name;
```

---

## 三、聚合与分组进阶

### 3.1 GROUP BY + 聚合

```sql
-- 按状态和优先级统计任务数
SELECT
    status,
    CASE
        WHEN priority >= 8 THEN '高'
        WHEN priority >= 4 THEN '中'
        ELSE '低'
    END AS priority_level,
    COUNT(*) AS task_count
FROM tasks
GROUP BY status, priority_level
ORDER BY status, task_count DESC;
```

### 3.2 CASE WHEN — 条件表达式

```sql
-- 类似 if-else，在 SQL 中做条件判断
SELECT
    name,
    age,
    CASE
        WHEN age < 18 THEN '未成年'
        WHEN age < 30 THEN '青年'
        WHEN age < 50 THEN '中年'
        ELSE '老年'
    END AS age_group
FROM users;

-- 用 CASE 做条件聚合
SELECT
    COUNT(*) AS total_tasks,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) AS completed,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) AS pending,
    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) AS in_progress
FROM tasks;
```

### 3.3 窗口函数（PostgreSQL 强项）

窗口函数在一组"窗口"行上计算值，但 **不会像 GROUP BY 那样合并行**。

```sql
-- ROW_NUMBER() — 给每行加序号
SELECT
    name,
    age,
    ROW_NUMBER() OVER (ORDER BY age DESC) AS rank
FROM users;

-- 按状态分组编号
SELECT
    title,
    status,
    ROW_NUMBER() OVER (PARTITION BY status ORDER BY priority DESC) AS rank_in_status
FROM tasks;

-- 累计求和
SELECT
    created_at::date AS date,
    COUNT(*) AS daily_count,
    SUM(COUNT(*)) OVER (ORDER BY created_at::date) AS cumulative_total
FROM tasks
GROUP BY created_at::date
ORDER BY date;

-- RANK() vs DENSE_RANK()
-- RANK:       1, 2, 2, 4（跳过）
-- DENSE_RANK: 1, 2, 2, 3（不跳过）
SELECT
    name,
    age,
    RANK() OVER (ORDER BY age DESC) AS rank,
    DENSE_RANK() OVER (ORDER BY age DESC) AS dense_rank
FROM users;
```

---

## 四、字符串与日期函数

### 4.1 字符串函数

```sql
-- 拼接
SELECT CONCAT(first_name, ' ', last_name) AS full_name FROM users;
SELECT first_name || ' ' || last_name AS full_name FROM users;  -- PostgreSQL

-- 大小写
SELECT UPPER(name), LOWER(email) FROM users;

-- 截取
SELECT SUBSTRING(email FROM 1 FOR 5) FROM users;  -- 前5个字符

-- 替换
SELECT REPLACE(email, '@example.com', '@new.com') FROM users;

-- 长度
SELECT LENGTH(name) FROM users;

-- 去空格
SELECT TRIM('  hello  ');      -- 'hello'
SELECT LTRIM('  hello');       -- 'hello'
SELECT RTRIM('hello  ');       -- 'hello'
```

### 4.2 日期函数

```sql
-- 当前时间
SELECT NOW();                          -- 2025-01-01 12:30:00+08
SELECT CURRENT_DATE;                   -- 2025-01-01
SELECT CURRENT_TIMESTAMP;              -- 同 NOW()

-- 提取部分
SELECT EXTRACT(YEAR FROM created_at) FROM tasks;
SELECT EXTRACT(MONTH FROM created_at) FROM tasks;
SELECT EXTRACT(DOW FROM created_at) FROM tasks;    -- 星期几（0=周日）

-- 日期运算
SELECT NOW() + INTERVAL '7 days';      -- 7天后
SELECT NOW() - INTERVAL '1 month';     -- 1月前
SELECT created_at + INTERVAL '30 days' AS deadline FROM tasks;

-- 日期差
SELECT AGE(NOW(), created_at) FROM tasks;  -- 返回 interval

-- 格式化
SELECT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS');  -- '2025-01-01 12:30:00'

-- 按日统计
SELECT
    created_at::date AS date,
    COUNT(*) AS count
FROM tasks
GROUP BY date
ORDER BY date;
```

---

## 五、UNION — 合并查询结果

```sql
-- UNION — 合并并去重
SELECT name, email FROM users WHERE is_active = TRUE
UNION
SELECT name, email FROM archived_users;

-- UNION ALL — 合并但不去重（性能更好）
SELECT 'active' AS source, name FROM users WHERE is_active = TRUE
UNION ALL
SELECT 'inactive' AS source, name FROM users WHERE is_active = FALSE;
```

---

## 六、实用查询模板

### 6.1 分页查询

```sql
-- 第 N 页，每页 page_size 条
SELECT *
FROM tasks
ORDER BY created_at DESC
LIMIT 20 OFFSET (3 - 1) * 20;  -- 第3页，每页20条
```

### 6.2 统计报表

```sql
-- 任务看板统计
WITH task_stats AS (
    SELECT
        u.name AS assignee,
        COUNT(*) AS total,
        COUNT(CASE WHEN t.status = 'completed' THEN 1 END) AS completed,
        COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) AS in_progress,
        COUNT(CASE WHEN t.status = 'pending' THEN 1 END) AS pending
    FROM users u
    LEFT JOIN tasks t ON t.assignee_id = u.id
    GROUP BY u.name
)
SELECT
    assignee,
    total,
    completed,
    in_progress,
    pending,
    ROUND(completed * 100.0 / NULLIF(total, 0), 1) AS completion_rate
FROM task_stats
ORDER BY completion_rate DESC;
```

### 6.3 最近 7 天每天的新增任务数

```sql
SELECT
    d.date,
    COALESCE(COUNT(t.id), 0) AS task_count
FROM generate_series(
    CURRENT_DATE - INTERVAL '6 days',
    CURRENT_DATE,
    '1 day'
) AS d(date)
LEFT JOIN tasks t ON t.created_at::date = d.date
GROUP BY d.date
ORDER BY d.date;
```

---

## 七、练习

### 基础练习

1. 用 INNER JOIN 查询所有任务及其负责人的姓名和邮箱
2. 用 LEFT JOIN 查询所有用户及其任务数（包含没有任务的用户）
3. 查询被分配了最多任务的前 3 个用户

### 进阶练习

4. 用 CTE 查询每个用户的任务完成率，按完成率降序排列
5. 用窗口函数给任务按优先级排名，同一用户内部排名
6. 写一个查询，统计每个月的新增用户数和新增任务数（用 UNION 或 JOIN）
7. 查询"有未完成任务且注册时间超过 30 天"的用户
