# 第 01 节：自定义 User 模型

## 一、为什么要自定义 User？

Django 内置的 User 模型只有 `username`、`email`、`password` 等基础字段。实际项目中通常需要：
- 用邮箱登录而不是用户名
- 添加头像、手机号等字段
- 使用自定义的验证逻辑

> ⚠️ **必须在项目初始化时就自定义 User 模型**，后期修改会非常麻烦。

---

## 二、继承 AbstractUser

### 2.1 定义自定义 User

```python
# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """自定义用户模型"""
    
    email = models.EmailField('邮箱', unique=True)  # 邮箱唯一
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True)
    bio = models.TextField('简介', blank=True, default='')
    phone = models.CharField('手机号', max_length=20, blank=True, default='')
    
    # 用邮箱作为登录字段
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # createsuperuser 时额外要求的字段
    
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        db_table = 'users'
    
    def __str__(self):
        return self.username
```

### 2.2 注册自定义 User

```python
# config/settings.py
AUTH_USER_MODEL = 'users.User'  # 必须在第一次 migrate 之前设置！
```

### 2.3 迁移

```bash
# 如果之前已经 migrate 过，需要删除数据库重来
# 删除所有 migrations 文件（保留 __init__.py）
# 删除 db.sqlite3

python manage.py makemigrations users
python manage.py migrate
python manage.py createsuperuser
```

---

## 三、引用 User 模型的正确方式

```python
# ✅ 在 models.py 中引用（用字符串，避免循环导入）
from django.conf import settings

class Task(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,       # 'users.User'
        on_delete=models.SET_NULL,
        null=True,
    )

# ✅ 在视图/序列化器中获取 User 模型
from django.contrib.auth import get_user_model
User = get_user_model()

# ❌ 不要直接导入
# from django.contrib.auth.models import User  # 不要这样！
```

---

## 四、User Profile（一对一扩展）

如果需要更多可选信息，可以用一对一关联。

```python
# apps/users/models.py
class UserSettings(models.Model):
    """用户设置"""
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='settings',
    )
    theme = models.CharField('主题', max_length=20, default='light')
    language = models.CharField('语言', max_length=10, default='zh')
    notification_email = models.BooleanField('邮件通知', default=True)
    notification_push = models.BooleanField('推送通知', default=True)
    
    class Meta:
        verbose_name = '用户设置'
        verbose_name_plural = '用户设置'
```

### 4.1 信号自动创建

```python
# apps/users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserSettings

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        UserSettings.objects.create(user=instance)
```

```python
# apps/users/apps.py
from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = '用户管理'
    
    def ready(self):
        import apps.users.signals  # noqa
```

---

## 五、User Admin 配置

```python
# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserSettings

class UserSettingsInline(admin.StackedInline):
    model = UserSettings
    can_delete = False

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['id', 'username', 'email', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email']
    ordering = ['-date_joined']
    inlines = [UserSettingsInline]
    
    # 添加自定义字段到详情页
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('avatar', 'bio', 'phone')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('扩展信息', {'fields': ('email', 'avatar', 'bio', 'phone')}),
    )
```

---

## 六、User 序列化器

```python
# apps/users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserSettings

User = get_user_model()

class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ['theme', 'language', 'notification_email', 'notification_push']

class UserSerializer(serializers.ModelSerializer):
    settings = UserSettingsSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'avatar', 'bio', 'phone',
            'is_active', 'date_joined', 'settings',
        ]
        read_only_fields = ['id', 'email', 'is_active', 'date_joined']

class UserBriefSerializer(serializers.ModelSerializer):
    """简要用户信息（用于嵌套在其他序列化器中）"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar']
```

---

## 七、练习

1. 定义自定义 User 模型，添加 `avatar`、`bio`、`phone` 字段
2. 设置 `AUTH_USER_MODEL`，运行迁移，创建超级用户
3. 创建 `UserSettings` 模型，用信号自动创建
4. 配置 User Admin，显示自定义字段
5. 创建 `UserSerializer` 和 `UserBriefSerializer`
