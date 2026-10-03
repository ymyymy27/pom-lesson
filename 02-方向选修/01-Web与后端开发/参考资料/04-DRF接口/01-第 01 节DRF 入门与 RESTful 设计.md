> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 01 节：DRF 入门与 RESTful 设计

## 一、什么是 RESTful API？

REST（Representational State Transfer）是一种 **API 设计风格**，核心思想是：用 **URL 标识资源**，用 **HTTP 方法表示操作**。

### 1.1 核心原则

```
资源 (Resource)    = URL 表示的实体（任务、用户、项目）
表示 (Representation) = 数据格式（JSON）
状态转移 (State Transfer) = 通过 HTTP 方法改变资源状态
```

### 1.2 HTTP 方法对应 CRUD

| HTTP 方法 | 操作 | URL 示例 | 含义 |
|-----------|------|---------|------|
| **GET** | 读取 | `GET /api/tasks/` | 获取任务列表 |
| **GET** | 读取 | `GET /api/tasks/5/` | 获取任务 #5 详情 |
| **POST** | 创建 | `POST /api/tasks/` | 创建新任务 |
| **PUT** | 全量更新 | `PUT /api/tasks/5/` | 更新任务 #5 所有字段 |
| **PATCH** | 部分更新 | `PATCH /api/tasks/5/` | 更新任务 #5 部分字段 |
| **DELETE** | 删除 | `DELETE /api/tasks/5/` | 删除任务 #5 |

### 1.3 HTTP 状态码规范

| 状态码 | 含义 | 使用场景 |
|--------|------|---------|
| `200 OK` | 成功 | GET、PUT、PATCH 成功 |
| `201 Created` | 创建成功 | POST 成功 |
| `204 No Content` | 无内容 | DELETE 成功 |
| `400 Bad Request` | 请求错误 | 参数校验失败 |
| `401 Unauthorized` | 未认证 | 未提供或 Token 无效 |
| `403 Forbidden` | 无权限 | 已认证但权限不足 |
| `404 Not Found` | 不存在 | 资源未找到 |
| `405 Method Not Allowed` | 方法不允许 | 不支持的 HTTP 方法 |
| `500 Internal Server Error` | 服务器错误 | 后端异常 |

### 1.4 RESTful URL 设计规范

```
✅ 推荐
GET    /api/v1/tasks/              获取任务列表
POST   /api/v1/tasks/              创建任务
GET    /api/v1/tasks/5/            获取任务详情
PUT    /api/v1/tasks/5/            更新任务
DELETE /api/v1/tasks/5/            删除任务
GET    /api/v1/projects/1/tasks/   获取项目1下的任务
POST   /api/v1/tasks/5/comments/   给任务5添加评论

❌ 不推荐
GET    /api/getTaskList
POST   /api/createTask
GET    /api/getTaskById?id=5
POST   /api/deleteTask
```

### 1.5 请求与响应格式

```json
// 请求：POST /api/v1/tasks/
// Content-Type: application/json
{
    "title": "学习 DRF",
    "description": "完成序列化器章节",
    "priority": 8,
    "project": 1,
    "tags": [1, 2]
}

// 响应：201 Created
{
    "id": 42,
    "title": "学习 DRF",
    "description": "完成序列化器章节",
    "status": "pending",
    "priority": 8,
    "project": {
        "id": 1,
        "name": "TaskFlow"
    },
    "tags": [
        {"id": 1, "name": "Feature"},
        {"id": 2, "name": "Enhancement"}
    ],
    "assignee": null,
    "created_at": "2025-06-01T10:30:00Z"
}
```

---

## 二、Django REST Framework 简介

DRF 是 Django 生态中 **构建 RESTful API 的标准库**，提供了：

- **Serializer** — 数据序列化/反序列化/验证
- **APIView / ViewSet** — 视图处理
- **Router** — 自动 URL 路由
- **Authentication** — 认证（Token、JWT、Session）
- **Permission** — 权限控制
- **Pagination** — 分页
- **Filtering** — 过滤
- **Throttling** — 限流
- **Browsable API** — 可浏览的 Web API 界面

---

## 三、安装与配置

### 3.1 安装

```bash
pip install djangorestframework
pip install django-cors-headers    # 跨域支持（前后端分离必须）
pip install django-filter          # 过滤支持
pip install drf-spectacular        # API 文档
```

### 3.2 配置 settings.py

```python
# config/settings.py

INSTALLED_APPS = [
    # Django 内置
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 第三方
    'rest_framework',              # DRF
    'corsheaders',                 # CORS 跨域
    'django_filters',              # 过滤
    'drf_spectacular',             # API 文档
    
    # 自己的应用
    'apps.users',
    'apps.projects',
    'apps.tasks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',              # CORS 中间件（放在 CommonMiddleware 之前）
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==================== DRF 全局配置 ====================
REST_FRAMEWORK = {
    # 默认渲染器
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # 开发时可浏览
    ],
    
    # 默认解析器
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    
    # 默认认证（后续配置 JWT）
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    
    # 默认权限
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # 开发阶段先允许所有
    ],
    
    # 默认分页
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    
    # 默认过滤后端
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    
    # API 文档
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    
    # 日期时间格式
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
}

# ==================== CORS 配置 ====================
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',        # React 开发服务器
    'http://localhost:5173',        # Vite 开发服务器
]
# 开发阶段可以允许所有
# CORS_ALLOW_ALL_ORIGINS = True

# ==================== API 文档配置 ====================
SPECTACULAR_SETTINGS = {
    'TITLE': 'TaskFlow API',
    'DESCRIPTION': '任务协作平台 API 文档',
    'VERSION': '1.0.0',
}
```

---

## 四、第一个 DRF API

### 4.1 最简示例

```python
# apps/tasks/serializers.py
from rest_framework import serializers
from .models import Tag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color']
```

```python
# apps/tasks/views.py
from rest_framework import viewsets
from .models import Tag
from .serializers import TagSerializer

class TagViewSet(viewsets.ModelViewSet):
    """标签的增删改查 API — 只需 3 行代码"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
```

```python
# apps/tasks/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('tags', views.TagViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

```python
# config/urls.py
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.tasks.urls')),
]
```

### 4.2 自动获得的 API

仅上面几行代码，你就自动获得了：

```
GET    /api/v1/tags/        获取标签列表（带分页）
POST   /api/v1/tags/        创建标签
GET    /api/v1/tags/1/      获取标签详情
PUT    /api/v1/tags/1/      全量更新标签
PATCH  /api/v1/tags/1/      部分更新标签
DELETE /api/v1/tags/1/      删除标签
```

### 4.3 测试 API

```bash
# 使用 curl 测试
curl http://127.0.0.1:8000/api/v1/tags/
curl -X POST http://127.0.0.1:8000/api/v1/tags/ \
     -H "Content-Type: application/json" \
     -d '{"name": "Python", "color": "#3776AB"}'

# 或者直接在浏览器打开（DRF 提供可浏览的 API 界面）
# http://127.0.0.1:8000/api/v1/tags/
```

---

## 五、Request 与 Response

DRF 扩展了 Django 的 Request 和 Response。

### 5.1 DRF Request

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET', 'POST'])
def task_list(request):
    # DRF 的 request 扩展了 Django 的 HttpRequest
    
    # 自动解析请求体（不需要手动 json.loads）
    request.data          # POST/PUT/PATCH 的数据（自动解析 JSON/Form）
    request.query_params  # GET 参数（等价于 request.GET，但名字更清晰）
    request.user          # 当前用户
    request.auth          # 认证信息（Token 等）
    request.method        # HTTP 方法
    
    if request.method == 'GET':
        # request.query_params 获取查询参数
        status = request.query_params.get('status', None)
        return Response({"data": []})
    
    elif request.method == 'POST':
        # request.data 自动解析 JSON
        title = request.data.get('title')
        return Response({"title": title}, status=201)
```

### 5.2 DRF Response

```python
from rest_framework.response import Response
from rest_framework import status

# Response 会根据客户端的 Accept 头自动选择渲染格式（JSON / HTML）
return Response(data={'id': 1, 'title': '任务1'})
return Response(data={'id': 1}, status=status.HTTP_201_CREATED)
return Response(status=status.HTTP_204_NO_CONTENT)
return Response({'error': '未找到'}, status=status.HTTP_404_NOT_FOUND)

# 常用状态码常量
status.HTTP_200_OK
status.HTTP_201_CREATED
status.HTTP_204_NO_CONTENT
status.HTTP_400_BAD_REQUEST
status.HTTP_401_UNAUTHORIZED
status.HTTP_403_FORBIDDEN
status.HTTP_404_NOT_FOUND
```

---

## 六、@api_view 装饰器（函数视图）

DRF 的函数视图用 `@api_view` 装饰器。

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET', 'POST'])
def task_list(request):
    if request.method == 'GET':
        tasks = Task.objects.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(creator=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def task_detail(request, pk):
    try:
        task = Task.objects.get(pk=pk)
    except Task.DoesNotExist:
        return Response({'error': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = TaskSerializer(task)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = TaskSerializer(task, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

---

## 七、API Root

```python
# config/urls.py
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API 路由
    path('api/v1/', include('apps.tasks.urls')),
    path('api/v1/', include('apps.projects.urls')),
    
    # API 文档
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # DRF 登录（开发时使用可浏览 API）
    path('api-auth/', include('rest_framework.urls')),
]
```

---

## 八、练习

1. 安装 DRF 及相关包，在 `settings.py` 中完成配置
2. 为 `Tag` 模型创建 Serializer、ViewSet、Router，实现完整 CRUD
3. 在浏览器中打开 DRF 的可浏览 API 界面，测试增删改查
4. 用 `@api_view` 装饰器写一个 `health_check` 函数视图
5. 配置 CORS，确保 `http://localhost:3000` 可以访问 API
6. 配置 drf-spectacular，访问 Swagger 文档页面
