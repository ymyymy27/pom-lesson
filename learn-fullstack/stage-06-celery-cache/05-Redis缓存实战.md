# 第 05 节：Redis 缓存实战

## 一、缓存策略

### 1.1 常见缓存模式

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| **Cache Aside** | 先查缓存，没有再查 DB，写入缓存 | 通用（最常用） |
| **Read Through** | 缓存层自动从 DB 加载 | 读多写少 |
| **Write Through** | 写数据时同时更新缓存和 DB | 数据一致性要求高 |
| **Write Behind** | 写数据时只更新缓存，异步更新 DB | 写入量大 |

### 1.2 Cache Aside 模式（推荐）

```python
from django.core.cache import cache

def get_task(task_id):
    """Cache Aside 模式"""
    cache_key = f"task:{task_id}"
    
    # 1. 先查缓存
    task_data = cache.get(cache_key)
    if task_data is not None:
        return task_data  # 缓存命中
    
    # 2. 缓存未命中，查数据库
    from apps.tasks.models import Task
    try:
        task = Task.objects.select_related('assignee', 'project').get(pk=task_id)
    except Task.DoesNotExist:
        # 缓存空值防止缓存穿透
        cache.set(cache_key, None, timeout=60)
        return None
    
    # 3. 序列化并写入缓存
    from apps.tasks.serializers import TaskReadSerializer
    task_data = TaskReadSerializer(task).data
    cache.set(cache_key, task_data, timeout=300)
    
    return task_data

def update_task(task_id, data):
    """更新时先更新 DB，再删除缓存"""
    from apps.tasks.models import Task
    Task.objects.filter(pk=task_id).update(**data)
    
    # 删除缓存（而非更新缓存，避免并发问题）
    cache.delete(f"task:{task_id}")
```

---

## 二、缓存常见问题与对策

### 2.1 缓存穿透

**问题：** 请求不存在的数据，每次都穿透到数据库。

```python
# 解决方案：缓存空值
def get_task_safe(task_id):
    cache_key = f"task:{task_id}"
    
    # 使用特殊标记区分 "缓存中无此键" 和 "值为 None"
    CACHE_MISS = object()
    result = cache.get(cache_key, CACHE_MISS)
    
    if result is not CACHE_MISS:
        return result  # 可能是数据，也可能是 None（空值缓存）
    
    from apps.tasks.models import Task
    try:
        task = Task.objects.get(pk=task_id)
        data = TaskReadSerializer(task).data
        cache.set(cache_key, data, timeout=300)
        return data
    except Task.DoesNotExist:
        cache.set(cache_key, None, timeout=60)  # 缓存空值，短过期
        return None
```

### 2.2 缓存雪崩

**问题：** 大量缓存同时过期，导致数据库压力暴增。

```python
import random

# 解决方案：过期时间加随机偏移
def cache_with_jitter(key, data, base_timeout=300):
    jitter = random.randint(0, 60)  # 随机 0-60 秒偏移
    cache.set(key, data, timeout=base_timeout + jitter)
```

### 2.3 缓存击穿

**问题：** 热点数据过期瞬间，大量请求同时穿透。

```python
import time

def get_hot_data(key, fetch_func, timeout=300):
    """带锁的缓存获取（防止缓存击穿）"""
    data = cache.get(key)
    if data is not None:
        return data
    
    lock_key = f"lock:{key}"
    # 尝试获取锁
    if cache.add(lock_key, '1', timeout=10):
        try:
            # 获得锁，查数据库
            data = fetch_func()
            cache.set(key, data, timeout=timeout)
            return data
        finally:
            cache.delete(lock_key)
    else:
        # 未获得锁，等待后重试
        time.sleep(0.1)
        return cache.get(key)  # 其他线程可能已经填充了缓存
```

---

## 三、缓存服务封装

```python
# apps/core/cache.py
from django.core.cache import cache
import json
import random
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """统一缓存服务"""
    
    @staticmethod
    def get(key, default=None):
        return cache.get(key, default)
    
    @staticmethod
    def set(key, value, timeout=300, jitter=True):
        if jitter:
            timeout += random.randint(0, 60)
        cache.set(key, value, timeout=timeout)
    
    @staticmethod
    def delete(key):
        cache.delete(key)
    
    @staticmethod
    def delete_pattern(pattern):
        """删除匹配模式的所有键"""
        from django_redis import get_redis_connection
        conn = get_redis_connection('default')
        keys = conn.keys(f"taskflow:{pattern}")
        if keys:
            conn.delete(*keys)
            logger.debug(f"删除缓存键: {len(keys)} 个匹配 {pattern}")
    
    @staticmethod
    def get_or_set(key, fetch_func, timeout=300):
        """缓存不存在时调用 fetch_func 获取并缓存"""
        data = cache.get(key)
        if data is not None:
            return data
        
        data = fetch_func()
        if data is not None:
            CacheService.set(key, data, timeout=timeout)
        return data
```

---

## 四、TaskFlow 缓存方案总结

```python
# apps/tasks/cache_keys.py
"""TaskFlow 缓存键规范"""

class TaskCacheKeys:
    # 任务详情: task:detail:{task_id}
    DETAIL = "task:detail:{task_id}"
    
    # 任务列表: task:list:{query_hash}
    LIST = "task:list:{query_hash}"
    
    # 任务统计: task:stats:{project_id}
    STATS = "task:stats:{project_id}"
    
    # 项目任务数: project:task_count:{project_id}
    PROJECT_TASK_COUNT = "project:task_count:{project_id}"
    
    @classmethod
    def detail_key(cls, task_id):
        return cls.DETAIL.format(task_id=task_id)
    
    @classmethod
    def stats_key(cls, project_id='all'):
        return cls.STATS.format(project_id=project_id)
    
    @classmethod
    def invalidate_task(cls, task_id, project_id=None):
        """任务变更时清除相关缓存"""
        from apps.core.cache import CacheService
        CacheService.delete(cls.detail_key(task_id))
        CacheService.delete_pattern("task:list:*")
        if project_id:
            CacheService.delete(cls.stats_key(project_id))
            CacheService.delete(cls.stats_key('all'))
```

```
TaskFlow 缓存规划：

┌─────────────────┬───────────────┬──────────┬──────────┐
│ 数据             │ 缓存键模式     │ 过期时间  │ 失效策略  │
├─────────────────┼───────────────┼──────────┼──────────┤
│ 任务详情         │ task:detail:* │ 5 分钟   │ 更新/删除 │
│ 任务列表         │ task:list:*   │ 1 分钟   │ 增删改   │
│ 任务统计         │ task:stats:*  │ 5 分钟   │ 增删改   │
│ 项目列表         │ project:list  │ 2 分钟   │ 增删改   │
│ 用户信息         │ user:info:*   │ 10 分钟  │ 修改资料 │
│ 标签列表         │ tag:list      │ 30 分钟  │ 增删     │
└─────────────────┴───────────────┴──────────┴──────────┘
```

---

## 五、练习

1. 实现 Cache Aside 模式的任务详情缓存
2. 实现缓存空值防止缓存穿透
3. 封装 `CacheService` 工具类
4. 设计 TaskFlow 的缓存键规范
5. 在 `TaskViewSet` 中实现完整的缓存逻辑：读取缓存 + 变更时失效

## 阶段总结

至此，第 06 阶段全部完成。你已经掌握：

- ✅ Celery 异步任务架构和配置
- ✅ 任务编写、重试、链式调用
- ✅ Celery Beat 定时任务
- ✅ Django 缓存框架 + Redis
- ✅ 缓存策略（穿透、雪崩、击穿防护）

**下一阶段** → 第 07 阶段：前端基础（HTML/CSS/JavaScript/TypeScript）
