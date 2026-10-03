> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 04 节：Django ORM 模型

## 一、什么是 ORM？

ORM（Object-Relational Mapping，对象关系映射）让你 **用 Python 类和对象操作数据库**，而不需要写 SQL。

```
Python 代码                          SQL
─────────────────────────────────────────────────
Task.objects.all()            →    SELECT * FROM tasks;
Task.objects.filter(status='pending')  →  SELECT * FROM tasks WHERE status='pending';
Task.objects.create(title='新任务')    →  INSERT INTO tasks (title) VALUES ('新任务');
task.delete()                 →    DELETE FROM tasks WHERE id=1;
```

### ORM 的优势

- **不用写 SQL** — 用 Python 语法操作数据库
- **数据库无关** — 切换数据库（SQLite → PostgreSQL）无需改代码
- **防 SQL 注入** — ORM 自动参数化查询
- **迁移管理** — 自动生成数据库表结构变更

---

## 二、定义模型

### 2.1 基础模型

```python
# apps/tasks/models.py
from django.db import models
from django.conf import settings

class Task(models.Model):
    """任务模型"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', '待办'
        IN_PROGRESS = 'in_progress', '进行中'
        COMPLETED = 'completed', '已完成'
        CANCELLED = 'cancelled', '已取消'
    
    title = models.CharField('标题', max_length=200)
    description = models.TextField('描述', blank=True, default='')
    status = models.CharField(
        '状态',
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    priority = models.IntegerField('优先级', default=0)
    due_date = models.DateField('截止日期', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'
        ordering = ['-created_at']      # 默认按创建时间倒序
        db_table = 'tasks'              # 自定义表名（可选）
    
    def __str__(self):
        return self.title
    
    @property
    def is_overdue(self):
        """是否过期"""
        from datetime import date
        if self.due_date and self.status != self.Status.COMPLETED:
            return self.due_date < date.today()
        return False
```

### 2.2 字段类型速查

| 字段类型 | 说明 | 对应 SQL | 示例 |
|---------|------|---------|------|
| `CharField` | 短文本（必须指定 max_length） | VARCHAR | 标题、姓名 |
| `TextField` | 长文本 | TEXT | 描述、内容 |
| `IntegerField` | 整数 | INTEGER | 年龄、优先级 |
| `BigIntegerField` | 大整数 | BIGINT | 大范围 ID |
| `FloatField` | 浮点数 | FLOAT | 评分 |
| `DecimalField` | 精确小数 | NUMERIC | 金额 |
| `BooleanField` | 布尔值 | BOOLEAN | 是否激活 |
| `DateField` | 日期 | DATE | 截止日期 |
| `DateTimeField` | 日期时间 | TIMESTAMP | 创建时间 |
| `EmailField` | 邮箱（带验证） | VARCHAR(254) | 邮箱 |
| `URLField` | URL（带验证） | VARCHAR(200) | 链接 |
| `UUIDField` | UUID | UUID | 唯一标识 |
| `SlugField` | Slug | VARCHAR(50) | URL 友好标识 |
| `FileField` | 文件 | VARCHAR(100) | 上传文件 |
| `ImageField` | 图片 | VARCHAR(100) | 头像 |
| `JSONField` | JSON 数据 | JSONB | 扩展数据 |

### 2.3 字段通用参数

```python
models.CharField(
    verbose_name='标题',     # 字段的可读名称
    max_length=200,          # 最大长度（CharField 必填）
    null=True,               # 数据库层面允许 NULL（默认 False）
    blank=True,              # 表单/序列化层面允许为空（默认 False）
    default='',              # 默认值
    unique=True,             # 唯一约束
    db_index=True,           # 创建数据库索引
    choices=Status.choices,  # 可选值列表
    help_text='请输入标题',   # 帮助文本
    editable=False,          # 是否可编辑（False 时不出现在表单中）
)

# null vs blank
# null=True  → 数据库允许存 NULL（针对数据库）
# blank=True → 表单验证时允许为空（针对验证）
# 字符串字段推荐用 blank=True + default='' 而非 null=True

# auto_now vs auto_now_add
# auto_now_add=True → 创建时自动设置（只在创建时）
# auto_now=True      → 每次保存时自动更新
```

---

## 三、关联关系

### 3.1 一对多（ForeignKey）

一个项目有多个任务，一个任务只属于一个项目。

```python
# apps/projects/models.py
class Project(models.Model):
    name = models.CharField('项目名', max_length=200)
    description = models.TextField('描述', blank=True, default='')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_projects',
        verbose_name='拥有者',
    )
    is_archived = models.BooleanField('已归档', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '项目'
        verbose_name_plural = '项目'
    
    def __str__(self):
        return self.name

# apps/tasks/models.py
class Task(models.Model):
    title = models.CharField('标题', max_length=200)
    
    # 外键 — 多对一关系
    project = models.ForeignKey(
        'projects.Project',              # 关联的模型（可以用字符串引用）
        on_delete=models.CASCADE,        # 项目删除时，任务也删除
        related_name='tasks',            # 反向查询名：project.tasks.all()
        verbose_name='所属项目',
    )
    
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,       # 用户删除时，设为 NULL
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name='负责人',
    )
    
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name='创建者',
    )
```

**on_delete 选项：**

| 选项 | 行为 | 适用场景 |
|------|------|---------|
| `CASCADE` | 级联删除 | 项目删除 → 任务也删除 |
| `SET_NULL` | 设为 NULL（需 null=True） | 用户删除 → 任务保留，负责人置空 |
| `SET_DEFAULT` | 设为默认值 | 少用 |
| `PROTECT` | 阻止删除（抛异常） | 有关联数据时不允许删除 |
| `DO_NOTHING` | 什么都不做 | 需自行处理 |

### 3.2 多对多（ManyToManyField）

一个任务可以有多个标签，一个标签可以属于多个任务。

```python
# apps/tasks/models.py
class Tag(models.Model):
    name = models.CharField('标签名', max_length=50, unique=True)
    color = models.CharField('颜色', max_length=7, default='#666666')
    
    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'
    
    def __str__(self):
        return self.name

class Task(models.Model):
    title = models.CharField('标题', max_length=200)
    
    # 多对多关系 — Django 自动创建中间表
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='tasks',
        verbose_name='标签',
    )
```

**多对多操作：**

```python
task = Task.objects.get(pk=1)
tag_python = Tag.objects.get(name='Python')
tag_django = Tag.objects.get(name='Django')

# 添加标签
task.tags.add(tag_python)
task.tags.add(tag_python, tag_django)    # 一次添加多个

# 移除标签
task.tags.remove(tag_python)

# 清空所有标签
task.tags.clear()

# 设置标签（替换所有）
task.tags.set([tag_python, tag_django])

# 查询任务的所有标签
task.tags.all()

# 反向查询：查询标签关联的所有任务
tag_python.tasks.all()
```

### 3.3 一对一（OneToOneField）

一个用户只有一份详细资料。

```python
# apps/users/models.py
class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='用户',
    )
    bio = models.TextField('简介', blank=True, default='')
    phone = models.CharField('电话', max_length=20, blank=True, default='')
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True)
    settings = models.JSONField('设置', default=dict, blank=True)
    
    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'
    
    def __str__(self):
        return f"{self.user.username}的资料"

# 使用
user.profile              # 正向访问
user.profile.bio          # 获取简介
```

### 3.4 带额外字段的多对多（through）

项目成员关系需要额外字段（角色、加入时间）。

```python
class Project(models.Model):
    name = models.CharField(max_length=200)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ProjectMember',         # 指定中间表
        related_name='joined_projects',
    )

class ProjectMember(models.Model):
    class Role(models.TextChoices):
        OWNER = 'owner', '拥有者'
        ADMIN = 'admin', '管理员'
        MEMBER = 'member', '成员'
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField('角色', max_length=20, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField('加入时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '项目成员'
        verbose_name_plural = '项目成员'
        unique_together = ['project', 'user']  # 同一项目中用户不重复
    
    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.role})"
```

---

## 四、数据库迁移

迁移（Migration）是 Django 管理数据库 schema 变更的方式。

### 4.1 迁移工作流

```bash
# 1. 修改 models.py（定义/修改模型）

# 2. 生成迁移文件
python manage.py makemigrations
# 输出：
# Migrations for 'tasks':
#   apps/tasks/migrations/0001_initial.py
#     - Create model Tag
#     - Create model Task

# 3. 查看迁移 SQL（可选，用于审查）
python manage.py sqlmigrate tasks 0001

# 4. 执行迁移
python manage.py migrate

# 5. 查看迁移状态
python manage.py showmigrations
```

### 4.2 迁移常见操作

```bash
# 回滚到指定迁移
python manage.py migrate tasks 0002     # 回滚到 0002

# 回滚到初始状态
python manage.py migrate tasks zero

# 生成空迁移（用于数据迁移）
python manage.py makemigrations tasks --empty -n "populate_default_tags"

# 合并迁移冲突
python manage.py makemigrations --merge
```

### 4.3 数据迁移

```python
# apps/tasks/migrations/0002_populate_default_tags.py
from django.db import migrations

def create_default_tags(apps, schema_editor):
    Tag = apps.get_model('tasks', 'Tag')
    default_tags = [
        {'name': 'Bug', 'color': '#FF0000'},
        {'name': 'Feature', 'color': '#00FF00'},
        {'name': 'Enhancement', 'color': '#0000FF'},
        {'name': 'Documentation', 'color': '#FFA500'},
    ]
    for tag_data in default_tags:
        Tag.objects.get_or_create(**tag_data)

def remove_default_tags(apps, schema_editor):
    Tag = apps.get_model('tasks', 'Tag')
    Tag.objects.filter(name__in=['Bug', 'Feature', 'Enhancement', 'Documentation']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('tasks', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(create_default_tags, remove_default_tags),
    ]
```

---

## 五、Meta 选项

```python
class Task(models.Model):
    # ... 字段 ...
    
    class Meta:
        # 基础设置
        verbose_name = '任务'              # 单数名称
        verbose_name_plural = '任务'       # 复数名称
        db_table = 'tasks'                 # 自定义表名
        
        # 排序
        ordering = ['-priority', '-created_at']  # 默认排序（负号=倒序）
        
        # 约束
        unique_together = [['project', 'title']]  # 联合唯一
        # 新写法（Django 4.0+）
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'title'],
                name='unique_task_title_per_project'
            ),
            models.CheckConstraint(
                check=models.Q(priority__gte=0, priority__lte=10),
                name='valid_priority_range'
            ),
        ]
        
        # 索引
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_at']),
            models.Index(
                fields=['status'],
                condition=models.Q(status='pending'),
                name='idx_pending_tasks'      # 部分索引
            ),
        ]
        
        # 权限
        permissions = [
            ('can_assign_task', '可以分配任务'),
            ('can_close_task', '可以关闭任务'),
        ]
```

---

## 六、模型方法

```python
class Task(models.Model):
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, default='pending')
    priority = models.IntegerField(default=0)
    
    def __str__(self):
        """字符串表示"""
        return f"[{self.get_status_display()}] {self.title}"
    
    @property
    def is_urgent(self):
        """属性方法：是否紧急"""
        return self.priority >= 8
    
    def complete(self):
        """完成任务"""
        self.status = 'completed'
        self.save(update_fields=['status', 'updated_at'])
    
    def assign_to(self, user):
        """分配给某用户"""
        self.assignee = user
        self.status = 'in_progress'
        self.save(update_fields=['assignee', 'status', 'updated_at'])
    
    def save(self, *args, **kwargs):
        """重写 save 方法（添加自定义逻辑）"""
        # 标题首字母大写
        if self.title:
            self.title = self.title.strip()
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """返回对象的 URL"""
        from django.urls import reverse
        return reverse('tasks:task-detail', kwargs={'pk': self.pk})
```

---

## 七、自定义 Manager

Manager 是模型与数据库交互的接口（默认是 `objects`）。

```python
class TaskQuerySet(models.QuerySet):
    """自定义 QuerySet — 链式调用"""
    
    def pending(self):
        return self.filter(status='pending')
    
    def in_progress(self):
        return self.filter(status='in_progress')
    
    def completed(self):
        return self.filter(status='completed')
    
    def urgent(self):
        return self.filter(priority__gte=8)
    
    def for_user(self, user):
        return self.filter(assignee=user)
    
    def overdue(self):
        from datetime import date
        return self.filter(due_date__lt=date.today()).exclude(status='completed')

class TaskManager(models.Manager):
    def get_queryset(self):
        return TaskQuerySet(self.model, using=self._db)
    
    def pending(self):
        return self.get_queryset().pending()
    
    def urgent(self):
        return self.get_queryset().urgent()

class Task(models.Model):
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, default='pending')
    priority = models.IntegerField(default=0)
    
    # 使用自定义 Manager
    objects = TaskManager()
    
# 使用
Task.objects.pending()                          # 所有待办任务
Task.objects.urgent()                           # 所有紧急任务
Task.objects.pending().urgent()                 # 紧急的待办任务
Task.objects.filter(project_id=1).pending()     # 项目1的待办任务
```

---

## 八、练习

### 基础练习

1. 在 `apps/tasks/models.py` 中定义 `Tag` 和 `Task` 模型，包含上面讲到的字段
2. 在 `apps/projects/models.py` 中定义 `Project` 和 `ProjectMember` 模型
3. 运行 `makemigrations` 和 `migrate`，查看生成的 SQL

### 进阶练习

4. 为 `Task` 添加 `Meta` 约束：优先级范围 0-10、同一项目下标题不重复
5. 为 `Task` 编写自定义 QuerySet 方法：`pending()`、`urgent()`、`overdue()`
6. 创建一个数据迁移，预填充默认标签（Bug、Feature、Enhancement、Documentation）
