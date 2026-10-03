> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 04 节：Django 缓存框架

## 一、为什么需要缓存？

数据库查询是 Web 应用最大的性能瓶颈之一。对于 **频繁读取但不常变化** 的数据，缓存可以极大提升响应速度。

```
无缓存：
请求 → 查询数据库（10ms）→ 序列化（5ms）→ 响应
每次请求都查数据库

有缓存：
请求 → 查缓存（0.1ms）→ 命中 → 直接返回
请求 → 查缓存 → 未命中 → 查数据库 → 写入缓存 → 返回
```

---

## 二、Django 缓存配置

### 2.1 Redis 缓存后端

```bash
pip install django-redis
```

```python
# config/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',    # Redis 数据库 1（Broker 用 0）
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'taskflow',                    # 键前缀
        'TIMEOUT': 300,                              # 默认过期时间 5 分钟
    }
}

# Session 也用 Redis 存储
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

---

## 三、低级缓存 API

直接在代码中操作缓存，最灵活。

```python
from django.core.cache import cache

# ===== 基础操作 =====
cache.set('key', 'value', timeout=300)       # 设置缓存，5 分钟过期
value = cache.get('key')                      # 获取缓存
value = cache.get('key', default='默认值')    # 获取，不存在返回默认值
cache.delete('key')                           # 删除缓存
cache.clear()                                 # 清空所有缓存

# ===== 高级操作 =====
cache.get_or_set('key', 'value', timeout=300) # 不存在则设置并返回
cache.set_many({'k1': 'v1', 'k2': 'v2'}, timeout=300)  # 批量设置
cache.get_many(['k1', 'k2'])                  # 批量获取
cache.delete_many(['k1', 'k2'])               # 批量删除

# 原子递增/递减
cache.set('counter', 0)
cache.incr('counter')        # 1
cache.incr('counter', 5)     # 6
cache.decr('counter')        # 5

# 键不存在时才设置（分布式锁）
cache.add('lock_key', 'locked', timeout=60)   # 返回 True/False

# 检查键是否存在
cache.has_key('key')
```

### 3.1 在视图中使用缓存

```python
from django.core.cache import cache
from rest_framework.response import Response

class TaskViewSet(viewsets.ModelViewSet):
    
    def list(self, request, *args, **kwargs):
        # 构造缓存键
        cache_key = f"task_list:{request.query_params.urlencode()}"
        
        # 尝试从缓存获取
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        # 缓存未命中，查询数据库
        response = super().list(request, *args, **kwargs)
        
        # 写入缓存
        cache.set(cache_key, response.data, timeout=60)
        
        return response
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
        # 创建后清除列表缓存
        self._invalidate_list_cache()
    
    def perform_update(self, serializer):
        serializer.save()
        self._invalidate_list_cache()
        cache.delete(f"task_detail:{serializer.instance.pk}")
    
    def perform_destroy(self, instance):
        instance.delete()
        self._invalidate_list_cache()
        cache.delete(f"task_detail:{instance.pk}")
    
    def _invalidate_list_cache(self):
        """清除所有列表缓存（简单方案：使用模式匹配删除）"""
        from django_redis import get_redis_connection
        conn = get_redis_connection('default')
        keys = conn.keys('taskflow:task_list:*')
        if keys:
            conn.delete(*keys)
```

---

## 四、DRF 缓存装饰器

### 4.1 使用 drf-extensions

```bash
pip install drf-extensions
```

```python
from rest_framework_extensions.cache.decorators import cache_response

class TaskViewSet(viewsets.ModelViewSet):
    
    @cache_response(timeout=60, key_func=None)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @cache_response(timeout=300)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
```

### 4.2 自定义缓存 Mixin

```python
# apps/core/mixins.py
from django.core.cache import cache
from rest_framework.response import Response

class CacheListMixin:
    """列表缓存 Mixin"""
    cache_timeout = 60  # 默认 60 秒
    
    def get_cache_key(self, request):
        """生成缓存键"""
        params = request.query_params.urlencode()
        model_name = self.queryset.model.__name__.lower()
        user_id = request.user.id if request.user.is_authenticated else 'anon'
        return f"api:{model_name}:list:{user_id}:{params}"
    
    def list(self, request, *args, **kwargs):
        cache_key = self.get_cache_key(request)
        cached = cache.get(cache_key)
        
        if cached is not None:
            return Response(cached)
        
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=self.cache_timeout)
        return response

class TaskViewSet(CacheListMixin, viewsets.ModelViewSet):
    cache_timeout = 120  # 2 分钟
    queryset = Task.objects.all()
    serializer_class = TaskReadSerializer
```

---

## 五、任务统计缓存示例

```python
from django.core.cache import cache
from django.db.models import Count, Q

class TaskViewSet(viewsets.ModelViewSet):
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """任务统计（缓存 5 分钟）"""
        project_id = request.query_params.get('project')
        cache_key = f"task_stats:{project_id or 'all'}"
        
        stats = cache.get(cache_key)
        if stats is None:
            qs = self.filter_queryset(self.get_queryset())
            stats = qs.aggregate(
                total=Count('id'),
                pending=Count('id', filter=Q(status='pending')),
                in_progress=Count('id', filter=Q(status='in_progress')),
                completed=Count('id', filter=Q(status='completed')),
                cancelled=Count('id', filter=Q(status='cancelled')),
            )
            cache.set(cache_key, stats, timeout=300)
        
        return Response(stats)
```

---

## 六、练习

1. 配置 Django Redis 缓存后端
2. 在 `TaskViewSet.list()` 中实现缓存：命中时直接返回，未命中时查库并缓存
3. 实现缓存失效：创建/更新/删除任务时清除相关缓存
4. 实现任务统计 API 的缓存（5 分钟过期）
5. 使用 `redis-cli` 查看缓存键，验证缓存是否生效
