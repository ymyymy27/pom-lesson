> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 05 节：ORM 查询 API

## 一、QuerySet 基础

### 1.1 什么是 QuerySet？

QuerySet 是 Django ORM 的查询结果集，具有两个重要特性：
- **惰性求值（Lazy）** — 创建 QuerySet 不会立即查询数据库，只有在 **使用数据** 时才执行 SQL
- **链式调用** — 每个过滤方法返回新的 QuerySet，可以连续调用

```python
# 惰性求值示例
qs = Task.objects.filter(status='pending')   # 还没查询数据库！
qs = qs.filter(priority__gte=5)              # 还没查询！
qs = qs.order_by('-priority')                # 还没查询！

# 以下操作才会触发数据库查询：
tasks = list(qs)            # 转为列表
for task in qs:             # 迭代
    print(task.title)
task = qs[0]                # 切片/索引
count = qs.count()          # 聚合
exists = qs.exists()        # 判断是否存在
print(qs)                   # 打印
```

---

## 二、创建数据

```python
from apps.tasks.models import Task, Tag
from apps.projects.models import Project
from django.contrib.auth import get_user_model

User = get_user_model()

# ===== 方式1：create() — 创建并保存 =====
task = Task.objects.create(
    title='学习Django ORM',
    description='深入学习查询API',
    status='pending',
    priority=8,
    project=project,
    assignee=user,
    creator=user,
)

# ===== 方式2：实例化 + save() =====
task = Task(
    title='搭建API',
    status='pending',
    priority=5,
)
task.project = project
task.save()    # 此时才写入数据库

# ===== 方式3：get_or_create() — 存在则获取，不存在则创建 =====
tag, created = Tag.objects.get_or_create(
    name='Python',
    defaults={'color': '#3776AB'}   # 只在创建时使用的字段
)
# created=True 表示新创建，created=False 表示已存在

# ===== 方式4：update_or_create() — 存在则更新，不存在则创建 =====
tag, created = Tag.objects.update_or_create(
    name='Python',
    defaults={'color': '#FFD43B'}   # 创建或更新时使用的字段
)

# ===== 方式5：bulk_create() — 批量创建（性能最好） =====
tasks = Task.objects.bulk_create([
    Task(title='任务1', priority=1, project=project, creator=user),
    Task(title='任务2', priority=2, project=project, creator=user),
    Task(title='任务3', priority=3, project=project, creator=user),
])
# 一条 INSERT 语句插入多行
```

---

## 三、查询数据

### 3.1 基础查询

```python
# 所有记录
Task.objects.all()

# 获取单个对象
task = Task.objects.get(pk=1)           # 找不到或找到多个会抛异常
task = Task.objects.get(title='学习Django ORM')

# get() 的异常处理
from django.core.exceptions import ObjectDoesNotExist
try:
    task = Task.objects.get(pk=999)
except Task.DoesNotExist:               # 推荐用法
    print("任务不存在")
except Task.MultipleObjectsReturned:
    print("找到多个匹配记录")

# 获取第一条/最后一条（找不到返回 None，不抛异常）
task = Task.objects.first()
task = Task.objects.last()
task = Task.objects.filter(status='pending').first()
```

### 3.2 filter() — 过滤

```python
# 等值过滤
Task.objects.filter(status='pending')
Task.objects.filter(priority=8)

# 链式过滤（AND 关系）
Task.objects.filter(status='pending').filter(priority__gte=5)
# 等价于
Task.objects.filter(status='pending', priority__gte=5)
```

### 3.3 字段查找（Field Lookups）

通过 **双下划线** `__` 语法实现丰富的查询条件。

```python
# ===== 比较 =====
Task.objects.filter(priority__gt=5)         # > 5
Task.objects.filter(priority__gte=5)        # >= 5
Task.objects.filter(priority__lt=5)         # < 5
Task.objects.filter(priority__lte=5)        # <= 5

# ===== 包含 =====
Task.objects.filter(status__in=['pending', 'in_progress'])

# ===== 范围 =====
Task.objects.filter(priority__range=(3, 8))    # 3 <= priority <= 8

# ===== NULL 判断 =====
Task.objects.filter(assignee__isnull=True)     # 未分配的任务
Task.objects.filter(due_date__isnull=False)    # 有截止日期的任务

# ===== 字符串匹配 =====
Task.objects.filter(title__exact='学习Django')         # 精确匹配
Task.objects.filter(title__iexact='学习django')        # 忽略大小写
Task.objects.filter(title__contains='Django')          # 包含
Task.objects.filter(title__icontains='django')         # 包含（忽略大小写）
Task.objects.filter(title__startswith='学习')           # 以...开头
Task.objects.filter(title__endswith='ORM')              # 以...结尾

# ===== 日期查找 =====
from datetime import date, datetime
Task.objects.filter(created_at__date=date.today())         # 今天创建的
Task.objects.filter(created_at__year=2025)                 # 2025年
Task.objects.filter(created_at__month=6)                   # 6月
Task.objects.filter(due_date__gt=date.today())             # 截止日期在今天之后
Task.objects.filter(created_at__date__gte=date(2025,1,1))  # 2025年1月1日之后

# ===== 跨关联查询（用双下划线跨表） =====
# 查询张三负责的任务
Task.objects.filter(assignee__username='zhangsan')

# 查询某项目下的任务
Task.objects.filter(project__name='TaskFlow')

# 查询有"Bug"标签的任务
Task.objects.filter(tags__name='Bug')

# 多层跨表
Task.objects.filter(project__owner__email='admin@example.com')
```

### 3.4 exclude() — 排除

```python
# 排除已完成的任务
Task.objects.exclude(status='completed')

# 组合使用
Task.objects.filter(priority__gte=5).exclude(status='cancelled')
```

### 3.5 Q 对象 — 复杂条件（OR / NOT）

`filter()` 的多个条件默认是 AND 关系。要用 OR 或 NOT，需要 Q 对象。

```python
from django.db.models import Q

# OR 条件
Task.objects.filter(
    Q(status='pending') | Q(status='in_progress')
)
# SQL: WHERE status='pending' OR status='in_progress'

# AND 条件
Task.objects.filter(
    Q(status='pending') & Q(priority__gte=5)
)

# NOT 条件
Task.objects.filter(
    ~Q(status='completed')
)
# SQL: WHERE NOT status='completed'

# 复杂组合
Task.objects.filter(
    (Q(status='pending') | Q(status='in_progress')) &
    Q(priority__gte=5) &
    ~Q(assignee__isnull=True)
)
# SQL: WHERE (status='pending' OR status='in_progress')
#        AND priority >= 5
#        AND assignee_id IS NOT NULL
```

### 3.6 F 对象 — 字段间比较和运算

F 对象引用模型字段的值，允许在查询中 **用字段和字段比较**，或进行 **字段级别的更新**。

```python
from django.db.models import F

# 字段间比较：查询截止日期早于创建日期的任务（不合理数据）
Task.objects.filter(due_date__lt=F('created_at'))

# 字段运算
Task.objects.filter(priority__gt=F('project__default_priority'))

# 字段级别更新（避免竞态条件）
# ❌ 有并发问题
task = Task.objects.get(pk=1)
task.priority = task.priority + 1
task.save()

# ✅ 原子操作
Task.objects.filter(pk=1).update(priority=F('priority') + 1)
```

---

## 四、排序、切片、去重

```python
# 排序
Task.objects.order_by('priority')             # 升序
Task.objects.order_by('-priority')            # 降序
Task.objects.order_by('-priority', 'title')   # 多字段排序
Task.objects.order_by('?')                    # 随机排序（性能差）

# 切片（对应 SQL 的 LIMIT/OFFSET）
Task.objects.all()[:10]                       # 前 10 条
Task.objects.all()[10:20]                     # 第 11-20 条（第 2 页）
Task.objects.order_by('-priority')[0]         # 优先级最高的 1 条

# 去重
Task.objects.filter(tags__name__in=['Bug', 'Feature']).distinct()

# 指定返回的字段（减少数据传输）
Task.objects.values('id', 'title', 'status')
# 返回字典列表: [{'id': 1, 'title': '...', 'status': '...'}, ...]

Task.objects.values_list('id', 'title')
# 返回元组列表: [(1, '...'), (2, '...')]

Task.objects.values_list('title', flat=True)
# 返回扁平列表: ['任务1', '任务2', '任务3']
```

---

## 五、聚合与注解

### 5.1 aggregate() — 整体聚合

```python
from django.db.models import Count, Sum, Avg, Max, Min

# 聚合计算（返回字典）
result = Task.objects.aggregate(
    total=Count('id'),
    avg_priority=Avg('priority'),
    max_priority=Max('priority'),
    min_priority=Min('priority'),
)
# {'total': 50, 'avg_priority': 4.5, 'max_priority': 10, 'min_priority': 0}

# 条件聚合
from django.db.models import Count, Q
result = Task.objects.aggregate(
    total=Count('id'),
    pending=Count('id', filter=Q(status='pending')),
    completed=Count('id', filter=Q(status='completed')),
)
```

### 5.2 annotate() — 分组注解

```python
# 每个项目的任务数
from django.db.models import Count
projects = Project.objects.annotate(
    task_count=Count('tasks')
).order_by('-task_count')

for p in projects:
    print(f"{p.name}: {p.task_count}个任务")

# 每个用户的待办任务数
users = User.objects.annotate(
    pending_count=Count('assigned_tasks', filter=Q(assigned_tasks__status='pending'))
).filter(pending_count__gt=0)

# 每个项目的完成率
projects = Project.objects.annotate(
    total=Count('tasks'),
    completed=Count('tasks', filter=Q(tasks__status='completed')),
).annotate(
    completion_rate=Case(
        When(total=0, then=Value(0.0)),
        default=100.0 * F('completed') / F('total'),
        output_field=FloatField(),
    )
)

# 每个标签被使用的次数
tags = Tag.objects.annotate(
    usage_count=Count('tasks')
).order_by('-usage_count')
```

### 5.3 分组统计

```python
# 按状态分组统计
stats = Task.objects.values('status').annotate(
    count=Count('id'),
    avg_priority=Avg('priority'),
).order_by('status')
# [
#   {'status': 'completed', 'count': 20, 'avg_priority': 5.2},
#   {'status': 'in_progress', 'count': 15, 'avg_priority': 6.8},
#   {'status': 'pending', 'count': 30, 'avg_priority': 4.1},
# ]

# 按日期分组统计
from django.db.models.functions import TruncDate
daily_stats = Task.objects.annotate(
    date=TruncDate('created_at')
).values('date').annotate(
    count=Count('id')
).order_by('date')
```

---

## 六、更新与删除

```python
# ===== 更新 =====

# 方式1：修改实例并保存
task = Task.objects.get(pk=1)
task.status = 'completed'
task.save()
# save() 会更新所有字段

# 指定更新的字段（性能更好）
task.status = 'completed'
task.save(update_fields=['status', 'updated_at'])

# 方式2：批量更新（不会触发 save() 方法和信号）
Task.objects.filter(status='pending').update(status='cancelled')

# 使用 F 对象更新
Task.objects.filter(status='pending').update(priority=F('priority') + 1)

# 方式3：bulk_update() — 批量更新多个对象的不同值
tasks = Task.objects.filter(status='pending')[:10]
for task in tasks:
    task.status = 'in_progress'
Task.objects.bulk_update(tasks, ['status'])

# ===== 删除 =====

# 删除单个
task = Task.objects.get(pk=1)
task.delete()    # 返回 (1, {'tasks.Task': 1})

# 批量删除
Task.objects.filter(status='cancelled').delete()

# 注意：CASCADE 会级联删除关联数据
project.delete()  # 项目下的所有任务也会被删除
```

---

## 七、查询优化

### 7.1 N+1 问题

```python
# ❌ N+1 问题：每次访问外键都会额外查询一次
tasks = Task.objects.all()
for task in tasks:
    print(task.assignee.username)  # 每次循环查询一次 users 表！
# 如果有 100 个任务 → 1（查任务）+ 100（查用户）= 101 条 SQL

# ✅ select_related — 一对一/多对一（JOIN 查询）
tasks = Task.objects.select_related('assignee', 'project').all()
for task in tasks:
    print(task.assignee.username)  # 不会额外查询！
# 只有 1 条 SQL（JOIN 查询）

# ✅ prefetch_related — 多对多/一对多（额外查询但合并）
tasks = Task.objects.prefetch_related('tags').all()
for task in tasks:
    print([tag.name for tag in task.tags.all()])  # 不会额外查询！
# 只有 2 条 SQL：查任务 + 查标签
```

### 7.2 select_related vs prefetch_related

| 方法 | 适用关系 | SQL 方式 | 示例 |
|------|---------|---------|------|
| `select_related` | ForeignKey, OneToOneField | JOIN | `task.assignee` |
| `prefetch_related` | ManyToManyField, 反向 FK | 额外查询 | `task.tags.all()` |

### 7.3 其他优化技巧

```python
# only() — 只加载指定字段
tasks = Task.objects.only('id', 'title', 'status')

# defer() — 延迟加载指定字段
tasks = Task.objects.defer('description')  # description 较大，访问时才加载

# exists() — 判断是否存在（比 count() > 0 更高效）
if Task.objects.filter(status='pending').exists():
    print("有待办任务")

# count() — 用 SQL COUNT 而非 len()
count = Task.objects.filter(status='pending').count()  # ✅
count = len(Task.objects.filter(status='pending'))     # ❌ 加载所有数据再计数

# 批量操作代替循环
Task.objects.filter(status='pending').update(status='cancelled')  # ✅ 一条 SQL
for task in Task.objects.filter(status='pending'):                # ❌ N 条 SQL
    task.status = 'cancelled'
    task.save()

# iterator() — 大数据集逐条处理，节省内存
for task in Task.objects.all().iterator(chunk_size=100):
    process(task)
```

---

## 八、原始 SQL

有些极端复杂的查询 ORM 难以表达时，可以退回原始 SQL。

```python
# 方式1：raw() — 返回模型实例
tasks = Task.objects.raw('SELECT * FROM tasks WHERE priority > %s', [5])
for task in tasks:
    print(task.title)  # 返回的是 Task 对象

# 方式2：直接执行 SQL（返回原始数据）
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(
        "SELECT status, COUNT(*) FROM tasks GROUP BY status"
    )
    rows = cursor.fetchall()
    # [('pending', 10), ('completed', 20)]
```

> ⚠️ 尽量使用 ORM，只在 ORM 无法表达时才用原始 SQL。

---

## 九、练习

### 基础练习

1. 用 Django Shell（`python manage.py shell`）创建 5 个 Tag 和 10 个 Task
2. 练习 `filter()`：查询优先级 >= 5 的待办任务
3. 练习 `exclude()`：查询所有非已完成的任务
4. 练习关联查询：查询"张三"负责的所有任务

### 进阶练习

5. 用 `Q` 对象查询：状态为 pending 或 in_progress 且优先级 >= 5 的任务
6. 用 `annotate` 统计每个项目的任务数和完成率
7. 用 `select_related` 和 `prefetch_related` 优化查询，对比 SQL 条数
8. 用 `aggregate` 计算所有任务的平均优先级、最高优先级
