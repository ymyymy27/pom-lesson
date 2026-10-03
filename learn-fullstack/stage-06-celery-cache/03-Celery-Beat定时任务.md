# 第 03 节：Celery Beat 定时任务

## 一、什么是定时任务？

定时任务是按 **固定时间间隔** 或 **特定时间点** 自动执行的任务：
- 每天凌晨统计昨日数据
- 每小时清理过期 Token
- 每周一生成周报
- 每 5 分钟检查过期任务

Celery Beat 是 Celery 的定时任务调度器。

---

## 二、配置方式

### 2.1 在 settings.py 中配置（静态）

```python
# config/settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # 每 5 分钟检查过期任务
    'check-overdue-tasks': {
        'task': 'apps.tasks.tasks.check_overdue_tasks',
        'schedule': 300.0,  # 每 300 秒
    },
    
    # 每天凌晨 2 点生成日报
    'daily-report': {
        'task': 'apps.tasks.tasks.generate_daily_report',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # 每周一早上 9 点生成周报
    'weekly-report': {
        'task': 'apps.tasks.tasks.generate_weekly_report',
        'schedule': crontab(hour=9, minute=0, day_of_week='monday'),
    },
    
    # 每小时清理过期 Token
    'cleanup-expired-tokens': {
        'task': 'apps.users.tasks.cleanup_expired_tokens',
        'schedule': crontab(minute=0),  # 每小时整点
    },
    
    # 每天清理 30 天前的已读通知
    'cleanup-notifications': {
        'task': 'apps.tasks.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=3, minute=0),
        'kwargs': {'days': 30},
    },
}
```

### 2.2 Crontab 时间表达式

```python
from celery.schedules import crontab

crontab()                                    # 每分钟
crontab(minute=0)                            # 每小时整点
crontab(minute=0, hour=0)                    # 每天午夜
crontab(minute=0, hour='*/3')                # 每 3 小时
crontab(minute=30, hour=9)                   # 每天 9:30
crontab(minute=0, hour=9, day_of_week='mon-fri')  # 工作日 9:00
crontab(minute=0, hour=2, day_of_month=1)    # 每月 1 号凌晨 2 点
crontab(minute=0, hour=0, day_of_month=1, month_of_year='1,7')  # 1月和7月1号
```

### 2.3 使用 django-celery-beat（动态，推荐）

可以在 Admin 后台动态管理定时任务。

```python
# config/settings.py
INSTALLED_APPS = [
    ...
    'django_celery_beat',
]

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

```bash
python manage.py migrate
```

在 Admin 后台（`/admin/`）可以看到：
- **Periodic Tasks** — 定时任务列表
- **Intervals** — 时间间隔（如每 5 分钟）
- **Crontabs** — Crontab 表达式
- **Clocked** — 一次性定时任务

---

## 三、编写定时任务

```python
# apps/tasks/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta, date
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_overdue_tasks():
    """检查过期任务并发送提醒"""
    from apps.tasks.models import Task
    
    overdue_tasks = Task.objects.filter(
        due_date__lt=date.today(),
        status__in=['pending', 'in_progress'],
    ).select_related('assignee')
    
    count = overdue_tasks.count()
    
    for task in overdue_tasks:
        if task.assignee:
            logger.warning(f"任务过期提醒: '{task.title}' 负责人: {task.assignee.username}")
            # send_task_overdue_notification.delay(task.id)
    
    logger.info(f"检查过期任务完成: 发现 {count} 个过期任务")
    return {'overdue_count': count}

@shared_task
def generate_daily_report():
    """生成每日任务统计"""
    from apps.tasks.models import Task
    from django.db.models import Count, Q
    
    yesterday = date.today() - timedelta(days=1)
    
    stats = Task.objects.filter(
        updated_at__date=yesterday
    ).aggregate(
        created=Count('id', filter=Q(created_at__date=yesterday)),
        completed=Count('id', filter=Q(status='completed')),
        updated=Count('id'),
    )
    
    logger.info(f"每日报告 ({yesterday}): 新建 {stats['created']}, 完成 {stats['completed']}, 更新 {stats['updated']}")
    return stats

@shared_task
def generate_weekly_report():
    """生成每周项目报告"""
    from apps.projects.models import Project
    from apps.tasks.models import Task
    from django.db.models import Count, Q
    
    week_ago = date.today() - timedelta(days=7)
    
    projects = Project.objects.annotate(
        week_created=Count('tasks', filter=Q(tasks__created_at__date__gte=week_ago)),
        week_completed=Count('tasks', filter=Q(
            tasks__status='completed',
            tasks__updated_at__date__gte=week_ago,
        )),
    ).filter(is_archived=False)
    
    report = []
    for p in projects:
        report.append({
            'project': p.name,
            'new_tasks': p.week_created,
            'completed_tasks': p.week_completed,
        })
    
    logger.info(f"周报生成完成: {len(report)} 个活跃项目")
    return report
```

---

## 四、启动 Beat

```bash
# 启动 Worker（执行任务）
celery -A config worker --loglevel=info --pool=solo

# 启动 Beat（调度定时任务）— 另一个终端
celery -A config beat --loglevel=info

# 合并启动（开发用）
celery -A config worker --beat --loglevel=info --pool=solo
```

---

## 五、练习

1. 配置 `CELERY_BEAT_SCHEDULE`，添加每 5 分钟检查过期任务的定时任务
2. 编写 `check_overdue_tasks` 任务，查找过期任务并记录日志
3. 编写 `generate_daily_report` 任务，统计昨日数据
4. 安装 django-celery-beat，在 Admin 后台动态添加定时任务
5. 同时启动 Worker 和 Beat，验证定时任务是否按时执行
