# 第 03 节：PostgreSQL 实战

## 一、为什么选 PostgreSQL？

| 特性 | PostgreSQL | MySQL | SQLite |
|------|-----------|-------|--------|
| **功能完整性** | 最强（JSON、数组、全文搜索、窗口函数） | 够用 | 基础 |
| **数据完整性** | 严格 | 宽松 | 基础 |
| **并发性能** | MVCC，读写不互锁 | 看引擎 | 单写锁 |
| **扩展性** | 丰富（插件、自定义类型） | 一般 | 无 |
| **适用场景** | 生产环境首选 | Web 应用广泛 | 开发/嵌入式 |
| **Django 支持** | 最佳 | 良好 | 开发用 |

> Django 官方推荐 PostgreSQL 作为生产数据库。

---

## 二、安装 PostgreSQL

### 2.1 Windows 安装

1. 下载：https://www.postgresql.org/download/windows/
2. 运行安装程序，勾选以下组件：
   - PostgreSQL Server
   - pgAdmin 4（图形化管理工具）
   - Command Line Tools
3. 设置超级用户 `postgres` 的密码（**请记住！**）
4. 默认端口：`5432`

### 2.2 验证安装

```bash
# 进入 PostgreSQL 命令行
psql -U postgres

# 查看版本
SELECT version();

# 退出
\q
```

### 2.3 Docker 安装（推荐，后续课程使用）

```bash
# 拉取并启动 PostgreSQL 容器
docker run -d \
    --name postgres \
    -e POSTGRES_USER=taskflow \
    -e POSTGRES_PASSWORD=taskflow123 \
    -e POSTGRES_DB=taskflow_db \
    -p 5432:5432 \
    postgres:16

# 进入容器的 psql
docker exec -it postgres psql -U taskflow -d taskflow_db
```

---

## 三、psql 命令行工具

### 3.1 连接数据库

```bash
# 连接格式
psql -h 主机 -p 端口 -U 用户名 -d 数据库名

# 本地连接
psql -U postgres

# 连接指定数据库
psql -U postgres -d taskflow_db

# 连接字符串格式
psql "postgresql://taskflow:taskflow123@localhost:5432/taskflow_db"
```

### 3.2 常用 psql 命令

```
\l          -- 列出所有数据库
\c dbname   -- 切换数据库
\dt         -- 列出当前数据库的所有表
\d tablename -- 查看表结构
\di         -- 列出所有索引
\du         -- 列出所有用户/角色
\df         -- 列出所有函数
\dn         -- 列出所有 schema

\x          -- 开启/关闭扩展显示模式（竖向显示）
\timing     -- 开启/关闭显示查询耗时
\i file.sql -- 执行 SQL 文件
\o file.txt -- 将输出重定向到文件

\q          -- 退出 psql
\?          -- 查看所有 psql 命令
\h SELECT   -- 查看 SQL 语句帮助
```

---

## 四、数据库与用户管理

### 4.1 创建数据库和用户

```sql
-- 创建用户（角色）
CREATE USER taskflow_user WITH PASSWORD 'secure_password';

-- 创建数据库
CREATE DATABASE taskflow_db
    OWNER taskflow_user
    ENCODING 'UTF8'
    LC_COLLATE 'en_US.UTF-8'
    LC_CTYPE 'en_US.UTF-8';

-- 授权
GRANT ALL PRIVILEGES ON DATABASE taskflow_db TO taskflow_user;

-- 连接到新数据库后，授权 schema
\c taskflow_db
GRANT ALL ON SCHEMA public TO taskflow_user;
```

### 4.2 删除数据库和用户

```sql
-- 删除数据库（必须先断开所有连接）
DROP DATABASE IF EXISTS taskflow_db;

-- 删除用户
DROP USER IF EXISTS taskflow_user;
```

---

## 五、PostgreSQL 特有数据类型

### 5.1 数组类型

```sql
-- 定义数组列
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200),
    tags TEXT[]              -- 文本数组
);

-- 插入数组数据
INSERT INTO articles (title, tags)
VALUES ('学习PostgreSQL', ARRAY['数据库', 'SQL', 'PostgreSQL']);

INSERT INTO articles (title, tags)
VALUES ('Django入门', '{Django,Python,Web}');   -- 另一种语法

-- 查询数组
SELECT * FROM articles WHERE 'Python' = ANY(tags);          -- 包含 Python
SELECT * FROM articles WHERE tags @> ARRAY['Django'];       -- 包含 Django
SELECT * FROM articles WHERE array_length(tags, 1) > 2;     -- 标签数 > 2

-- 数组操作
SELECT unnest(tags) AS tag FROM articles;                    -- 展开数组
SELECT tags[1] FROM articles;                                -- 访问第一个元素
SELECT array_append(tags, '新标签') FROM articles;            -- 追加元素
```

### 5.2 JSONB 类型（重要！）

JSONB 是 PostgreSQL 存储 JSON 数据的二进制格式，支持索引和高效查询。

```sql
-- 定义 JSONB 列
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 插入 JSON 数据
INSERT INTO user_profiles (user_id, metadata) VALUES
(1, '{"theme": "dark", "language": "zh", "notifications": {"email": true, "sms": false}}'),
(2, '{"theme": "light", "language": "en", "notifications": {"email": true, "sms": true}}');

-- 查询 JSON 字段
SELECT metadata->>'theme' AS theme FROM user_profiles;              -- 获取文本值
SELECT metadata->'notifications'->>'email' FROM user_profiles;      -- 嵌套访问
SELECT * FROM user_profiles WHERE metadata->>'theme' = 'dark';      -- 条件查询

-- JSON 路径查询
SELECT * FROM user_profiles
WHERE metadata @> '{"notifications": {"email": true}}';  -- 包含指定 JSON

-- 更新 JSON 字段
UPDATE user_profiles
SET metadata = jsonb_set(metadata, '{theme}', '"blue"')
WHERE user_id = 1;

-- 添加新键
UPDATE user_profiles
SET metadata = metadata || '{"avatar": "default.png"}'::jsonb
WHERE user_id = 1;

-- 删除键
UPDATE user_profiles
SET metadata = metadata - 'avatar'
WHERE user_id = 1;

-- 为 JSONB 创建索引
CREATE INDEX idx_profiles_metadata ON user_profiles USING GIN (metadata);
```

### 5.3 UUID 类型

```sql
-- 启用 uuid 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 使用 UUID 作为主键
CREATE TABLE api_tokens (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.4 枚举类型

```sql
-- 创建枚举类型
CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'completed', 'cancelled');

CREATE TABLE tasks_v2 (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200),
    status task_status DEFAULT 'pending'
);

-- 只能插入枚举中定义的值
INSERT INTO tasks_v2 (title, status) VALUES ('任务1', 'in_progress');  -- OK
INSERT INTO tasks_v2 (title, status) VALUES ('任务2', 'invalid');       -- 报错！
```

---

## 六、Python 连接 PostgreSQL

### 6.1 psycopg2（最常用的驱动）

```bash
pip install psycopg2-binary
```

```python
import psycopg2
from psycopg2.extras import RealDictCursor

# 连接数据库
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="taskflow_db",
    user="taskflow_user",
    password="secure_password",
)

# 使用游标执行 SQL
with conn.cursor(cursor_factory=RealDictCursor) as cur:
    # 查询
    cur.execute("SELECT * FROM users WHERE age > %s", (25,))
    users = cur.fetchall()
    for user in users:
        print(user["name"], user["email"])
    
    # 插入
    cur.execute(
        "INSERT INTO users (name, email, age) VALUES (%s, %s, %s) RETURNING id",
        ("新用户", "new@example.com", 22)
    )
    new_id = cur.fetchone()["id"]
    
    # 提交事务
    conn.commit()

# 关闭连接
conn.close()
```

### 6.2 使用上下文管理器

```python
import psycopg2
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        dbname="taskflow_db",
        user="taskflow_user",
        password="secure_password",
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# 使用
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        print(f"用户总数: {count}")
```

> 💡 实际项目中不会直接写 SQL，而是使用 Django ORM（第 03 阶段学习）。但 **理解 SQL 是使用 ORM 的基础**。

---

## 七、pgAdmin 图形化工具

pgAdmin 是 PostgreSQL 的官方图形化管理工具。

### 主要功能

1. **连接管理** — 管理多个数据库连接
2. **查询工具** — 可视化 SQL 编辑器，支持自动补全
3. **表管理** — 图形化创建/修改表结构
4. **数据查看** — 浏览和编辑表数据
5. **备份恢复** — 数据库备份和还原

### 连接步骤

1. 打开 pgAdmin → 右键 "Servers" → "Register" → "Server"
2. General 标签：Name 填 `TaskFlow`
3. Connection 标签：
   - Host: `localhost`
   - Port: `5432`
   - Database: `taskflow_db`
   - Username: `taskflow_user`
   - Password: `secure_password`
4. 点击 Save

---

## 八、练习

### 基础练习

1. 安装 PostgreSQL（本地或 Docker），创建 `taskflow_db` 数据库和 `taskflow_user` 用户
2. 用 psql 连接数据库，创建 `users` 和 `tasks` 表，插入测试数据
3. 用 pgAdmin 连接数据库，浏览数据

### 进阶练习

4. 创建一个包含 JSONB 列的 `user_settings` 表，练习 JSON 数据的增删改查
5. 用 psycopg2 写一个 Python 脚本，实现用户的 CRUD 操作
6. 创建一个包含数组列的表，查询"标签包含 Python"的所有记录
