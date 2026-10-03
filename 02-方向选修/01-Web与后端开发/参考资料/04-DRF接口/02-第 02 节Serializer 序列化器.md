> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 02 节：Serializer 序列化器

## 一、什么是序列化器？

序列化器负责 **数据格式转换** 和 **数据验证**：

```
序列化 (Serialization):    Python 对象 → JSON（给前端）
反序列化 (Deserialization): JSON → Python 对象（存数据库）
验证 (Validation):          检查数据是否合法
```

```
前端请求 JSON → 反序列化 → 验证 → 存入数据库
数据库查询 → Python 对象 → 序列化 → JSON 响应给前端
```

---

## 二、Serializer 基础类

### 2.1 手动定义字段

```python
from rest_framework import serializers

class TaskSerializer(serializers.Serializer):
    """手动定义每个字段"""
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    status = serializers.ChoiceField(
        choices=['pending', 'in_progress', 'completed', 'cancelled'],
        default='pending'
    )
    priority = serializers.IntegerField(min_value=0, max_value=10, default=0)
    due_date = serializers.DateField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    
    def create(self, validated_data):
        """反序列化 → 创建对象"""
        return Task.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """反序列化 → 更新对象"""
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.status = validated_data.get('status', instance.status)
        instance.priority = validated_data.get('priority', instance.priority)
        instance.due_date = validated_data.get('due_date', instance.due_date)
        instance.save()
        return instance
```

### 2.2 使用序列化器

```python
# ===== 序列化（对象 → JSON）=====
task = Task.objects.get(pk=1)
serializer = TaskSerializer(task)
print(serializer.data)
# {'id': 1, 'title': '学习DRF', 'status': 'pending', ...}

# 序列化多个对象
tasks = Task.objects.all()
serializer = TaskSerializer(tasks, many=True)
print(serializer.data)
# [{'id': 1, ...}, {'id': 2, ...}]

# ===== 反序列化（JSON → 对象）=====
data = {'title': '新任务', 'priority': 8}
serializer = TaskSerializer(data=data)

# 验证
if serializer.is_valid():
    task = serializer.save()     # 调用 create()
    print(serializer.data)       # 序列化后的数据
else:
    print(serializer.errors)     # 验证错误信息
    # {'title': ['This field is required.'], ...}

# raise_exception=True — 验证失败时自动返回 400 响应
serializer.is_valid(raise_exception=True)

# ===== 更新 =====
task = Task.objects.get(pk=1)
data = {'title': '修改后的标题', 'priority': 9}
serializer = TaskSerializer(task, data=data)       # 全量更新
serializer = TaskSerializer(task, data=data, partial=True)  # 部分更新
serializer.is_valid(raise_exception=True)
serializer.save()    # 调用 update()
```

---

## 三、ModelSerializer（最常用）

`ModelSerializer` 根据模型 **自动生成字段**，大幅减少代码。

### 3.1 基础用法

```python
# apps/tasks/serializers.py
from rest_framework import serializers
from .models import Task, Tag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'project', 'assignee', 'creator', 'tags',
            'due_date', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']
```

### 3.2 fields 选项

```python
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        
        # 方式1：显式列出（推荐！安全）
        fields = ['id', 'title', 'status', 'priority']
        
        # 方式2：所有字段（不推荐，可能暴露敏感数据）
        # fields = '__all__'
        
        # 方式3：排除指定字段
        # exclude = ['created_at', 'updated_at']
```

### 3.3 字段控制

```python
class TaskSerializer(serializers.ModelSerializer):
    # 自定义字段属性
    title = serializers.CharField(max_length=200, help_text='任务标题')
    
    # 只读字段
    created_at = serializers.DateTimeField(read_only=True)
    
    # 只写字段
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'status', 'priority', 'created_at']
        read_only_fields = ['id', 'created_at', 'updated_at']  # 批量设置只读
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True},
            'priority': {'min_value': 0, 'max_value': 10},
            'assignee': {'required': False},
        }
```

---

## 四、字段类型详解

### 4.1 常用字段

| Serializer 字段 | 对应 Model 字段 | 说明 |
|----------------|----------------|------|
| `CharField` | CharField, TextField | 字符串 |
| `IntegerField` | IntegerField | 整数 |
| `FloatField` | FloatField | 浮点数 |
| `DecimalField` | DecimalField | 精确小数 |
| `BooleanField` | BooleanField | 布尔值 |
| `DateField` | DateField | 日期 |
| `DateTimeField` | DateTimeField | 日期时间 |
| `EmailField` | EmailField | 邮箱 |
| `URLField` | URLField | URL |
| `UUIDField` | UUIDField | UUID |
| `ChoiceField` | CharField(choices=...) | 选择字段 |
| `FileField` | FileField | 文件 |
| `ImageField` | ImageField | 图片 |
| `JSONField` | JSONField | JSON |
| `SlugRelatedField` | ForeignKey | 关联字段（用 slug 表示） |
| `PrimaryKeyRelatedField` | ForeignKey | 关联字段（用主键表示） |
| `StringRelatedField` | ForeignKey | 关联字段（用 __str__ 表示） |

### 4.2 字段通用参数

```python
serializers.CharField(
    required=True,            # 是否必填（默认 True）
    allow_null=False,         # 是否允许 None
    allow_blank=False,        # 是否允许空字符串
    default='',               # 默认值
    read_only=False,          # 只读（序列化时输出，反序列化时忽略）
    write_only=False,         # 只写（反序列化时接收，序列化时不输出）
    source='field_name',      # 数据来源字段
    validators=[],            # 验证器列表
    help_text='描述',          # 帮助文本（用于 API 文档）
    label='标题',              # 显示标签
)
```

### 4.3 SerializerMethodField（计算字段）

```python
class TaskSerializer(serializers.ModelSerializer):
    # 自定义计算字段
    is_overdue = serializers.SerializerMethodField()
    assignee_name = serializers.SerializerMethodField()
    tag_names = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'priority',
            'is_overdue', 'assignee_name', 'tag_names', 'comment_count',
        ]
    
    def get_is_overdue(self, obj):
        """以 get_<field_name> 命名"""
        return obj.is_overdue
    
    def get_assignee_name(self, obj):
        if obj.assignee:
            return obj.assignee.username
        return None
    
    def get_tag_names(self, obj):
        return list(obj.tags.values_list('name', flat=True))
    
    def get_comment_count(self, obj):
        return obj.comments.count()
```

---

## 五、关联字段与嵌套序列化

### 5.1 关联字段表示方式

```python
# 假设 Task 有 ForeignKey 到 Project 和 User

# 方式1：主键表示（默认）
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'project', 'assignee']
# 输出: {"project": 1, "assignee": 5}

# 方式2：字符串表示（用 __str__）
class TaskSerializer(serializers.ModelSerializer):
    project = serializers.StringRelatedField()
    assignee = serializers.StringRelatedField()
    class Meta:
        model = Task
        fields = ['id', 'title', 'project', 'assignee']
# 输出: {"project": "TaskFlow", "assignee": "张三"}

# 方式3：Slug 表示（用指定字段）
class TaskSerializer(serializers.ModelSerializer):
    assignee = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = Task
        fields = ['id', 'title', 'assignee']
# 输出: {"assignee": "zhangsan"}
# 输入: {"assignee": "zhangsan"}（通过 username 查找用户）
```

### 5.2 嵌套序列化（读取时展开详情）

```python
class ProjectBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name']

class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class TaskDetailSerializer(serializers.ModelSerializer):
    """读取时使用 — 嵌套展开关联对象"""
    project = ProjectBriefSerializer(read_only=True)
    assignee = UserBriefSerializer(read_only=True)
    creator = UserBriefSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'project', 'assignee', 'creator', 'tags',
            'due_date', 'created_at', 'updated_at',
        ]

# 输出:
# {
#   "id": 1,
#   "title": "学习DRF",
#   "project": {"id": 1, "name": "TaskFlow"},
#   "assignee": {"id": 5, "username": "张三", "email": "zs@example.com"},
#   "tags": [{"id": 1, "name": "Feature", "color": "#00FF00"}],
#   ...
# }
```

### 5.3 读写分离（常用模式）

读取时展开嵌套对象，写入时接收 ID。

```python
class TaskWriteSerializer(serializers.ModelSerializer):
    """写入时使用 — 接收 ID"""
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority',
            'project', 'assignee', 'tags', 'due_date',
        ]
    
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        task = Task.objects.create(**validated_data)
        task.tags.set(tags)
        return task
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance

class TaskReadSerializer(serializers.ModelSerializer):
    """读取时使用 — 嵌套展开"""
    project = ProjectBriefSerializer(read_only=True)
    assignee = UserBriefSerializer(read_only=True)
    creator = UserBriefSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'project', 'assignee', 'creator', 'tags',
            'due_date', 'created_at', 'updated_at',
        ]
```

### 5.4 反向关联（一对多）

```python
# 项目序列化器中嵌套任务列表
class ProjectDetailSerializer(serializers.ModelSerializer):
    tasks = TaskReadSerializer(many=True, read_only=True)  # related_name='tasks'
    owner = UserBriefSerializer(read_only=True)
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'owner', 'tasks', 'task_count', 'created_at']
    
    def get_task_count(self, obj):
        return obj.tasks.count()
```

---

## 六、数据验证

### 6.1 字段级验证

```python
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'priority', 'due_date']
    
    def validate_title(self, value):
        """验证单个字段：validate_<field_name>"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("标题至少需要 2 个字符")
        if Task.objects.filter(title=value).exists():
            raise serializers.ValidationError("标题已存在")
        return value.strip()
    
    def validate_priority(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError("优先级必须在 0-10 之间")
        return value
    
    def validate_due_date(self, value):
        from datetime import date
        if value and value < date.today():
            raise serializers.ValidationError("截止日期不能早于今天")
        return value
```

### 6.2 对象级验证

```python
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
    
    def validate(self, attrs):
        """跨字段验证"""
        # 已完成的任务不能设置截止日期
        if attrs.get('status') == 'completed' and attrs.get('due_date'):
            raise serializers.ValidationError({
                'due_date': '已完成的任务不需要截止日期'
            })
        
        # 高优先级任务必须有负责人
        if attrs.get('priority', 0) >= 8 and not attrs.get('assignee'):
            raise serializers.ValidationError({
                'assignee': '高优先级任务必须指定负责人'
            })
        
        return attrs
```

### 6.3 自定义验证器

```python
# 可复用的验证器
def no_profanity(value):
    """检查是否包含不当词汇"""
    bad_words = ['spam', 'xxx']
    for word in bad_words:
        if word in value.lower():
            raise serializers.ValidationError(f"内容不能包含 '{word}'")

class TaskSerializer(serializers.ModelSerializer):
    title = serializers.CharField(validators=[no_profanity])
    description = serializers.CharField(validators=[no_profanity], required=False)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description']

# UniqueValidator
from rest_framework.validators import UniqueValidator

class TagSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        validators=[UniqueValidator(queryset=Tag.objects.all(), message='标签名已存在')]
    )
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color']

# UniqueTogetherValidator
from rest_framework.validators import UniqueTogetherValidator

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Task.objects.all(),
                fields=['project', 'title'],
                message='同一项目下任务标题不能重复'
            )
        ]
```

### 6.4 验证错误响应格式

```json
// 验证失败时自动返回 400 响应
{
    "title": ["标题至少需要 2 个字符"],
    "priority": ["优先级必须在 0-10 之间"],
    "non_field_errors": ["高优先级任务必须指定负责人"]
}
```

---

## 七、重写 create() 和 update()

```python
class TaskSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'project', 'assignee', 'tags', 'due_date',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """自定义创建逻辑"""
        tags = validated_data.pop('tags', [])
        # 自动设置创建者为当前用户
        validated_data['creator'] = self.context['request'].user
        task = Task.objects.create(**validated_data)
        if tags:
            task.tags.set(tags)
        return task
    
    def update(self, instance, validated_data):
        """自定义更新逻辑"""
        tags = validated_data.pop('tags', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tags is not None:
            instance.tags.set(tags)
        
        return instance
    
    def to_representation(self, instance):
        """自定义序列化输出（读取时展开关联对象）"""
        data = super().to_representation(instance)
        # 将外键 ID 替换为嵌套对象
        data['tags'] = TagSerializer(instance.tags.all(), many=True).data
        if instance.assignee:
            data['assignee'] = {
                'id': instance.assignee.id,
                'username': instance.assignee.username,
            }
        if instance.project:
            data['project'] = {
                'id': instance.project.id,
                'name': instance.project.name,
            }
        return data
```

---

## 八、context（上下文）

序列化器可以通过 `context` 接收额外数据（如当前请求）。

```python
# 视图中传递 context
serializer = TaskSerializer(data=request.data, context={'request': request})

# ViewSet 和 GenericView 会自动传递 context，包含：
# - request: 当前请求
# - view: 当前视图
# - format: 请求的格式

# 在序列化器中使用 context
class TaskSerializer(serializers.ModelSerializer):
    is_mine = serializers.SerializerMethodField()
    
    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.assignee == request.user
        return False
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)
```

---

## 九、练习

### 基础练习

1. 为 `Tag` 创建 `TagSerializer`，包含字段验证（name 不为空、color 为合法颜色码）
2. 为 `Task` 创建 `TaskSerializer`，使用 `ModelSerializer`
3. 在 Django Shell 中测试序列化和反序列化

### 进阶练习

4. 创建 `TaskReadSerializer` 和 `TaskWriteSerializer`，实现读写分离
5. 为 `Task` 添加字段级验证：标题不少于 2 字符、截止日期不早于今天
6. 为 `Task` 添加对象级验证：高优先级任务必须有负责人
7. 重写 `create()` 方法，自动设置 `creator` 为当前登录用户
8. 使用 `SerializerMethodField` 添加 `is_overdue`、`comment_count` 计算字段
