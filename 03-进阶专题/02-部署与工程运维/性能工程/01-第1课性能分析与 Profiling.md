> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第1课：性能分析与 Profiling

## 1. 分析流程

```
1. 定义目标：p99 延迟从 800ms 降到 200ms
2. 建立基准：当前 p99 = 800ms
3. Profiling：找到热点（占时间最多的部分）
4. 优化热点
5. 验证：p99 是否降到 200ms？
6. 重复 3-5 直到达标
```

---

## 2. Python Profiling 工具

### cProfile（CPU 热点）

```python
import cProfile
import pstats

cProfile.run("main()", "output.prof")
stats = pstats.Stats("output.prof")
stats.sort_stats("cumulative").print_stats(20)
# 显示累计时间最多的 20 个函数
```

```bash
# 命令行
python -m cProfile -s cumulative app.py
```

### py-spy（生产环境，无需改代码）

```bash
pip install py-spy
py-spy top --pid 12345        # 实时看 CPU 热点
py-spy record -o profile.svg --pid 12345  # 生成火焰图
```

### memory_profiler（内存）

```python
from memory_profiler import profile

@profile
def load_large_dataset():
    data = [i for i in range(10_000_000)]
    return sum(data)
```

### 火焰图（Flame Graph）

```
阅读方法：
  - 横轴：函数占样本的比例（越宽 = 越热点）
  - 纵轴：调用栈深度
  - 找「宽的平台」= 优化目标

  [====main====]
  [==handler==][=db=]
  [query][parse]  ← query 很宽 → 优化 DB 查询
```

---

## 3. 常见瓶颈模式

| 模式 | 表现 | 定位 | 解决 |
|------|------|------|------|
| N+1 查询 | 列表页慢 | SQL 日志大量相似查询 | select_related / prefetch |
| 无索引 | 特定查询慢 | EXPLAIN ANALYZE | 加索引 |
| 同步阻塞 | 等外部 API | Profile 卡在 HTTP | 异步/并行 |
| 内存泄漏 | 运行越久越慢 | memory_profiler | 修复引用 |
| 大对象 | GC 频繁 | 内存快照 | 流式处理 |
| 锁竞争 | CPU 不高但慢 | py-spy 卡在 lock | 减少共享状态 |

### N+1 示例

```python
# ❌ N+1：1 + N 次查询
tasks = Task.objects.all()          # 1 次
for task in tasks:
    print(task.assignee.name)       # N 次

# ✅ 预加载：2 次查询
tasks = Task.objects.select_related("assignee").all()
for task in tasks:
    print(task.assignee.name)
```

---

## 4. 数据库慢查询分析

```sql
-- PostgreSQL：查看慢查询
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- 分析执行计划
EXPLAIN ANALYZE
SELECT * FROM tasks WHERE project_id = 123 AND status = 'todo'
ORDER BY created_at DESC LIMIT 20;
```

```
关注：
  Seq Scan → 可能需要索引
  Nested Loop + 大表 → 可能需要 JOIN 优化
  Sort + 大数据集 → 可能需要索引覆盖排序
  Rows Removed by Filter → 索引选择性差
```

---

## 5. 动手练习

1. 用 cProfile 分析一个 Python 脚本，找出 Top 3 热点
2. 修复一个 N+1 查询（Django ORM 或 SQLAlchemy）
3. 对一条慢 SQL 运行 EXPLAIN ANALYZE 并解读结果

---

**下一课** → [02_optimization_patterns.md](02-第2课优化模式.md)
