> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 03 节：视图与 ViewSet

## 一、DRF 视图层级

DRF 提供了从底层到高层的多种视图抽象，越往上封装越多、代码越少：

```
层级从低到高：

@api_view          函数视图，最灵活，代码最多
    ↓
APIView            类视图基类，手动处理每个 HTTP 方法
    ↓
GenericAPIView     通用视图基类 + Mixin 组合
    ↓
Concrete Views     具体视图（ListAPIView、CreateAPIView 等）
    ↓
ViewSet            视图集，自动路由
    ↓
ModelViewSet       模型视图集，一行搞定 CRUD
```

---

## 二、APIView（类视图基类）

手动处理每个 HTTP 方法，完全控制逻辑。

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Task
from .serializers import TaskReadSerializer, TaskWriteSerializer

class TaskListView(APIView):
    """任务列表：GET 获取列表 / POST 创建"""
    
    def get(self, request):
        tasks = Task.objects.select_related('assignee', 'project').all()
        serializer = TaskReadSerializer(tasks, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = TaskWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        # 返回时用 ReadSerializer 展开关联对象
        output = TaskReadSerializer(task).data
        return Response(output, status=status.HTTP_201_CREATED)

class TaskDetailView(APIView):
    """任务详情：GET / PUT / PATCH / DELETE"""
    
    def get_object(self, pk):
        return get_object_or_404(Task, pk=pk)
    
    def get(self, request, pk):
        task = self.get_object(pk)
        serializer = TaskReadSerializer(task)
        return Response(serializer.data)
    
    def put(self, request, pk):
        task = self.get_object(pk)
        serializer = TaskWriteSerializer(task, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response(TaskReadSerializer(task).data)
    
    def patch(self, request, pk):
        task = self.get_object(pk)
        serializer = TaskWriteSerializer(task, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response(TaskReadSerializer(task).data)
    
    def delete(self, request, pk):
        task = self.get_object(pk)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

```python
# urls.py
urlpatterns = [
    path('tasks/', TaskListView.as_view()),
    path('tasks/<int:pk>/', TaskDetailView.as_view()),
]
```

---

## 三、GenericAPIView + Mixins

`GenericAPIView` 提供了 `queryset`、`serializer_class` 等通用属性。  
`Mixin` 提供了 `list()`、`create()`、`retrieve()`、`update()`、`destroy()` 等方法。

### 3.1 Mixin 说明

| Mixin | 提供的方法 | 对应操作 |
|-------|----------|---------|
| `ListModelMixin` | `list()` | GET 列表 |
| `CreateModelMixin` | `create()` | POST 创建 |
| `RetrieveModelMixin` | `retrieve()` | GET 详情 |
| `UpdateModelMixin` | `update()`, `partial_update()` | PUT / PATCH 更新 |
| `DestroyModelMixin` | `destroy()` | DELETE 删除 |

### 3.2 组合 Mixin

```python
from rest_framework import generics, mixins

class TaskListCreateView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    generics.GenericAPIView,
):
    queryset = Task.objects.select_related('assignee', 'project').all()
    serializer_class = TaskWriteSerializer
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TaskReadSerializer
        return TaskWriteSerializer
    
    def perform_create(self, serializer):
        """create() 保存时的钩子"""
        serializer.save(creator=self.request.user)

class TaskDetailView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    queryset = Task.objects.all()
    serializer_class = TaskWriteSerializer
    
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
```

---

## 四、Concrete Views（具体视图）

DRF 已经组合好了 Mixin + GenericAPIView，直接用：

| 视图 | 组合 | 支持的方法 |
|------|------|-----------|
| `ListAPIView` | List | GET |
| `CreateAPIView` | Create | POST |
| `RetrieveAPIView` | Retrieve | GET |
| `UpdateAPIView` | Update | PUT, PATCH |
| `DestroyAPIView` | Destroy | DELETE |
| `ListCreateAPIView` | List + Create | GET, POST |
| `RetrieveUpdateAPIView` | Retrieve + Update | GET, PUT, PATCH |
| `RetrieveDestroyAPIView` | Retrieve + Destroy | GET, DELETE |
| `RetrieveUpdateDestroyAPIView` | Retrieve + Update + Destroy | GET, PUT, PATCH, DELETE |

```python
from rest_framework import generics

class TaskListCreateView(generics.ListCreateAPIView):
    queryset = Task.objects.select_related('assignee', 'project').all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TaskReadSerializer
        return TaskWriteSerializer
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.select_related('assignee', 'project').all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TaskReadSerializer
        return TaskWriteSerializer
```

代码量比 APIView 少了一半以上。

---

## 五、ViewSet（视图集）

ViewSet 把列表和详情 **合并到一个类** 中，配合 Router 自动生成 URL。

### 5.1 ViewSet 动作映射

```
ViewSet 方法    →    HTTP 方法 + URL
─────────────────────────────────────
list()          →    GET    /tasks/
create()        →    POST   /tasks/
retrieve()      →    GET    /tasks/{pk}/
update()        →    PUT    /tasks/{pk}/
partial_update()→    PATCH  /tasks/{pk}/
destroy()       →    DELETE /tasks/{pk}/
```

### 5.2 ModelViewSet（最常用）

```python
from rest_framework import viewsets

class TaskViewSet(viewsets.ModelViewSet):
    """
    任务 CRUD — 一个类搞定所有操作
    自动提供：list / create / retrieve / update / partial_update / destroy
    """
    queryset = Task.objects.select_related(
        'assignee', 'project', 'creator'
    ).prefetch_related('tags').all()
    
    def get_serializer_class(self):
        """读写分离"""
        if self.action in ['list', 'retrieve']:
            return TaskReadSerializer
        return TaskWriteSerializer
    
    def perform_create(self, serializer):
        """创建时自动设置 creator"""
        serializer.save(creator=self.request.user)
    
    def perform_update(self, serializer):
        """更新钩子"""
        serializer.save()
```

### 5.3 其他 ViewSet 类型

```python
# ViewSet — 最基础，需要手动实现所有方法
class TaskViewSet(viewsets.ViewSet):
    def list(self, request):
        tasks = Task.objects.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        task = get_object_or_404(Task, pk=pk)
        serializer = TaskSerializer(task)
        return Response(serializer.data)

# GenericViewSet — 带 queryset 和 serializer_class
class TaskViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    """只读的 ViewSet — 只有 list 和 retrieve"""
    queryset = Task.objects.all()
    serializer_class = TaskReadSerializer

# ReadOnlyModelViewSet — 只读 ViewSet 的快捷方式
class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    """等价于 GenericViewSet + ListModelMixin + RetrieveModelMixin"""
    queryset = Task.objects.all()
    serializer_class = TaskReadSerializer
```

### 5.4 perform_xxx 钩子方法

| 钩子方法 | 调用时机 | 常见用途 |
|---------|---------|---------|
| `perform_create(serializer)` | `create()` 中保存前 | 设置 creator、发送通知 |
| `perform_update(serializer)` | `update()` 中保存前 | 记录变更日志 |
| `perform_destroy(instance)` | `destroy()` 中删除前 | 软删除、权限检查 |

```python
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskWriteSerializer
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
    
    def perform_update(self, serializer):
        # 可以在保存前做额外操作
        instance = serializer.save()
        # 记录日志、发送通知等
    
    def perform_destroy(self, instance):
        # 软删除而非真删除
        instance.status = 'cancelled'
        instance.save()
        # 或者真删除：instance.delete()
```

### 5.5 自定义 Action

除了标准 CRUD，还可以添加额外的自定义操作。

```python
from rest_framework.decorators import action

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskWriteSerializer
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """POST /api/v1/tasks/{pk}/complete/ — 完成任务"""
        task = self.get_object()
        task.status = 'completed'
        task.save()
        return Response(TaskReadSerializer(task).data)
    
    @action(detail=True, methods=['post'], url_path='assign')
    def assign_to(self, request, pk=None):
        """POST /api/v1/tasks/{pk}/assign/ — 分配任务"""
        task = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': '请提供 user_id'}, status=400)
        task.assignee_id = user_id
        task.status = 'in_progress'
        task.save()
        return Response(TaskReadSerializer(task).data)
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """GET /api/v1/tasks/my_tasks/ — 获取我的任务"""
        tasks = self.get_queryset().filter(assignee=request.user)
        serializer = TaskReadSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """GET /api/v1/tasks/statistics/ — 任务统计"""
        from django.db.models import Count, Q
        stats = Task.objects.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            completed=Count('id', filter=Q(status='completed')),
        )
        return Response(stats)
```

`@action` 参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| `detail` | True=详情级（需要 pk），False=列表级 | `detail=True` |
| `methods` | 支持的 HTTP 方法 | `['post']` |
| `url_path` | 自定义 URL 路径 | `'assign'` |
| `url_name` | 自定义 URL 名称 | `'task-assign'` |
| `serializer_class` | 自定义序列化器 | `AssignSerializer` |
| `permission_classes` | 自定义权限 | `[IsAuthenticated]` |

---

## 六、重写 get_queryset()

```python
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskWriteSerializer
    
    def get_queryset(self):
        """动态过滤查询集"""
        qs = Task.objects.select_related('assignee', 'project').prefetch_related('tags')
        
        # 根据 URL 参数过滤（嵌套路由场景）
        project_id = self.kwargs.get('project_pk')
        if project_id:
            qs = qs.filter(project_id=project_id)
        
        # 非管理员只能看到自己的任务
        user = self.request.user
        if not user.is_staff:
            qs = qs.filter(
                models.Q(assignee=user) | models.Q(creator=user)
            )
        
        return qs
```

---

## 七、视图选择指南

| 场景 | 推荐视图 | 原因 |
|------|---------|------|
| 标准 CRUD | `ModelViewSet` | 代码最少，自动路由 |
| 只读 API | `ReadOnlyModelViewSet` | 只提供 list + retrieve |
| 列表+创建 | `ListCreateAPIView` | 不需要 ViewSet 时 |
| 自定义逻辑多 | `APIView` | 完全控制 |
| 函数式简单接口 | `@api_view` | 如 health_check |
| 需要额外 Action | `ModelViewSet` + `@action` | 如 complete、assign |

---

## 八、练习

### 基础练习

1. 用 `APIView` 为 Tag 实现列表和详情视图
2. 用 `ListCreateAPIView` + `RetrieveUpdateDestroyAPIView` 改写
3. 用 `ModelViewSet` 再次改写，对比代码量

### 进阶练习

4. 为 `TaskViewSet` 添加 `@action`：`complete`、`my_tasks`、`statistics`
5. 重写 `get_queryset()`：非管理员只能看到自己创建或被分配的任务
6. 实现读写分离：`get_serializer_class()` 根据 action 返回不同的序列化器
7. 重写 `perform_destroy()`：实现软删除（设为 cancelled 而非真删除）
