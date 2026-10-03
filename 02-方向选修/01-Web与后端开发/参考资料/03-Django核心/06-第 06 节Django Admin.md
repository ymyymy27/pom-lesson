> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 06 节：Django Admin

## 一、什么是 Django Admin？

Django Admin 是 **内置的自动化管理后台**，基于你定义的模型自动生成管理界面，支持数据的增删改查。

- 开发阶段：快速管理数据，不用写前端页面
- 生产阶段：给运营/管理员使用的后台工具
- 零额外代码即可使用，但高度可定制

---

## 二、快速启用

### 2.1 创建超级用户

```bash
python manage.py createsuperuser
# 输入用户名、邮箱、密码
```

### 2.2 访问 Admin

启动开发服务器后访问：`http://127.0.0.1:8000/admin/`

### 2.3 注册模型

```python
# apps/tasks/admin.py
from django.contrib import admin
from .models import Task, Tag

# 最简注册 — 一行代码
admin.site.register(Task)
admin.site.register(Tag)
```

注册后刷新 Admin 页面，就能看到模型并管理数据了。

---

## 三、自定义 ModelAdmin

### 3.1 基础自定义

```python
# apps/tasks/admin.py
from django.contrib import admin
from .models import Task, Tag

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # ===== 列表页配置 =====
    list_display = ['id', 'title', 'status', 'priority', 'assignee', 'project', 'created_at']
    list_display_links = ['id', 'title']          # 可点击进入详情的列
    list_filter = ['status', 'priority', 'project', 'tags']  # 右侧过滤器
    search_fields = ['title', 'description']       # 搜索框搜索的字段
    list_per_page = 20                             # 每页显示条数
    list_editable = ['status', 'priority']         # 列表页直接编辑
    ordering = ['-priority', '-created_at']        # 默认排序
    date_hierarchy = 'created_at'                  # 日期层级导航

    # ===== 详情页配置 =====
    readonly_fields = ['created_at', 'updated_at'] # 只读字段
    
    # 字段分组
    fieldsets = [
        ('基本信息', {
            'fields': ['title', 'description', 'status', 'priority']
        }),
        ('关联信息', {
            'fields': ['project', 'assignee', 'creator', 'tags']
        }),
        ('日期', {
            'fields': ['due_date', 'created_at', 'updated_at'],
            'classes': ['collapse'],  # 可折叠
        }),
    ]
    
    # 多对多字段使用水平过滤器（更好的选择体验）
    filter_horizontal = ['tags']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'color', 'task_count']
    search_fields = ['name']
    
    def task_count(self, obj):
        """自定义列：显示标签关联的任务数"""
        return obj.tasks.count()
    task_count.short_description = '任务数'
```

### 3.2 配置项速查

| 配置项 | 作用 | 示例 |
|--------|------|------|
| `list_display` | 列表显示的列 | `['title', 'status']` |
| `list_display_links` | 点击进入详情的列 | `['title']` |
| `list_filter` | 右侧过滤器 | `['status', 'project']` |
| `search_fields` | 搜索字段 | `['title', 'description']` |
| `list_per_page` | 每页行数 | `20` |
| `list_editable` | 列表页可编辑的列 | `['status', 'priority']` |
| `ordering` | 默认排序 | `['-created_at']` |
| `date_hierarchy` | 日期层级导航 | `'created_at'` |
| `readonly_fields` | 只读字段 | `['created_at']` |
| `fieldsets` | 详情页字段分组 | 见上面示例 |
| `fields` | 详情页显示的字段 | `['title', 'status']` |
| `exclude` | 详情页排除的字段 | `['updated_at']` |
| `filter_horizontal` | 多对多水平过滤器 | `['tags']` |
| `filter_vertical` | 多对多垂直过滤器 | `['tags']` |
| `raw_id_fields` | 外键用 ID 输入替代下拉 | `['assignee']` |
| `autocomplete_fields` | 外键自动补全 | `['assignee']` |
| `prepopulated_fields` | 自动填充字段 | `{'slug': ('title',)}` |
| `save_on_top` | 顶部显示保存按钮 | `True` |

---

## 四、自定义显示

### 4.1 自定义列

```python
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'colored_status', 'priority_display', 'assignee_name', 'is_overdue']
    
    @admin.display(description='状态', ordering='status')
    def colored_status(self, obj):
        """带颜色的状态标签"""
        colors = {
            'pending': '#FFA500',
            'in_progress': '#1E90FF',
            'completed': '#32CD32',
            'cancelled': '#FF4444',
        }
        color = colors.get(obj.status, '#666')
        label = obj.get_status_display()
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, label
        )
    
    @admin.display(description='优先级', ordering='priority')
    def priority_display(self, obj):
        """优先级星级显示"""
        if obj.priority >= 8:
            return format_html('<span style="color: red;">⚡ {} (紧急)</span>', obj.priority)
        return str(obj.priority)
    
    @admin.display(description='负责人')
    def assignee_name(self, obj):
        return obj.assignee.username if obj.assignee else '—'
    
    @admin.display(description='是否过期', boolean=True)
    def is_overdue(self, obj):
        """布尔值显示为图标"""
        return obj.is_overdue
```

### 4.2 自定义过滤器

```python
class PriorityFilter(admin.SimpleListFilter):
    title = '优先级等级'
    parameter_name = 'priority_level'
    
    def lookups(self, request, model_admin):
        return [
            ('high', '高（8-10）'),
            ('medium', '中（4-7）'),
            ('low', '低（0-3）'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'high':
            return queryset.filter(priority__gte=8)
        elif self.value() == 'medium':
            return queryset.filter(priority__gte=4, priority__lte=7)
        elif self.value() == 'low':
            return queryset.filter(priority__lte=3)

class OverdueFilter(admin.SimpleListFilter):
    title = '是否过期'
    parameter_name = 'overdue'
    
    def lookups(self, request, model_admin):
        return [
            ('yes', '已过期'),
            ('no', '未过期'),
        ]
    
    def queryset(self, request, queryset):
        from datetime import date
        if self.value() == 'yes':
            return queryset.filter(
                due_date__lt=date.today()
            ).exclude(status='completed')
        elif self.value() == 'no':
            return queryset.exclude(
                due_date__lt=date.today()
            )

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_filter = ['status', PriorityFilter, OverdueFilter, 'project']
```

---

## 五、Admin Actions

批量操作：在列表页选中多条记录，执行自定义操作。

```python
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    actions = ['mark_completed', 'mark_pending', 'increase_priority']
    
    @admin.action(description='标记为已完成')
    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'成功将 {updated} 个任务标记为已完成')
    
    @admin.action(description='标记为待办')
    def mark_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f'成功将 {updated} 个任务标记为待办')
    
    @admin.action(description='优先级 +1')
    def increase_priority(self, request, queryset):
        from django.db.models import F
        updated = queryset.filter(priority__lt=10).update(priority=F('priority') + 1)
        self.message_user(request, f'成功提升 {updated} 个任务的优先级')
```

---

## 六、内联编辑（Inline）

在父模型的详情页中直接编辑子模型。

```python
# 在项目详情页中直接管理任务
class TaskInline(admin.TabularInline):        # 表格形式
    model = Task
    extra = 1                                  # 额外显示的空行数
    fields = ['title', 'status', 'priority', 'assignee']
    readonly_fields = ['created_at']
    show_change_link = True                    # 显示编辑链接

class CommentInline(admin.StackedInline):      # 堆叠形式（每条记录一个块）
    model = Comment
    extra = 0
    readonly_fields = ['user', 'created_at']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'owner', 'is_archived', 'created_at']
    inlines = [TaskInline]                     # 内联显示任务

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    inlines = [CommentInline]                  # 内联显示评论
```

---

## 七、重写 Admin 方法

### 7.1 自定义保存逻辑

```python
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    
    def save_model(self, request, obj, form, change):
        """保存时自动设置创建者"""
        if not change:  # 新建时
            obj.creator = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """自定义查询集（如：只显示当前用户的任务）"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(assignee=request.user)
    
    def get_readonly_fields(self, request, obj=None):
        """非超级管理员不能修改状态"""
        if not request.user.is_superuser:
            return self.readonly_fields + ['status']
        return self.readonly_fields
    
    def has_delete_permission(self, request, obj=None):
        """只有超级管理员可以删除"""
        return request.user.is_superuser
```

### 7.2 自定义列表查询优化

```python
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'assignee', 'project']
    list_select_related = ['assignee', 'project']  # 自动 JOIN 优化
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('assignee', 'project').prefetch_related('tags')
```

---

## 八、Admin 站点自定义

```python
# config/admin.py 或 config/urls.py 中
from django.contrib import admin

# 自定义标题
admin.site.site_header = 'TaskFlow 管理后台'
admin.site.site_title = 'TaskFlow Admin'
admin.site.index_title = '数据管理'
```

---

## 九、练习

### 基础练习

1. 为 `Task`、`Tag`、`Project` 注册 Admin，配置 `list_display`、`list_filter`、`search_fields`
2. 为 `Task` 添加自定义列：显示带颜色的状态、是否过期
3. 在 `Project` 详情页中内联显示任务（TabularInline）

### 进阶练习

4. 创建自定义过滤器 `PriorityFilter`（高/中/低）
5. 创建 Admin Action：批量将选中的任务标记为已完成
6. 重写 `save_model`：新建任务时自动设置 `creator` 为当前登录用户
7. 自定义 Admin 站点标题为"TaskFlow 管理后台"
