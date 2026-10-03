# 第 01 节：Django 入门与项目结构

## 一、什么是 Django？

Django 是一个 **高级 Python Web 框架**，遵循"不要重复自己（DRY）"原则，提供了 Web 开发中常用的组件（ORM、认证、Admin、表单等），让你专注于业务逻辑。

### 1.1 Django 的设计哲学

- **快速开发** — 内置常用功能，减少重复代码
- **DRY 原则** — Don't Repeat Yourself
- **松耦合** — 各组件独立，可以替换
- **显式优于隐式** — 代码清晰明了
- **安全优先** — 内置防 XSS、CSRF、SQL 注入

### 1.2 MTV 架构

Django 使用 **MTV**（Model-Template-View）架构，对应经典 MVC 的变体：

```
客户端请求
    ↓
URL Router（urls.py）     → 路由分发
    ↓
View（views.py）          → 处理业务逻辑（对应 MVC 的 Controller）
    ↓
Model（models.py）        → 操作数据库
    ↓
Template（*.html）        → 渲染页面（前后端分离时不需要）
    ↓
Response 返回给客户端
```

| Django MTV | MVC 对应 | 职责 |
|-----------|---------|------|
| **Model** | Model | 数据模型，操作数据库 |
| **Template** | View | 模板渲染（前后端分离时用 JSON 替代） |
| **View** | Controller | 接收请求，处理逻辑，返回响应 |

> 💡 前后端分离架构中，Template 层被前端框架（React）替代，Django 只返回 JSON 数据。

---

## 二、安装 Django

### 2.1 创建项目虚拟环境

```bash
# 创建项目目录
mkdir taskflow-backend
cd taskflow-backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境（Windows PowerShell）
.venv\Scripts\Activate.ps1

# 激活虚拟环境（Mac/Linux）
source .venv/bin/activate
```

### 2.2 安装 Django

```bash
pip install django

# 验证安装
python -m django --version   # 5.x
```

### 2.3 使用 Poetry（推荐）

```bash
# 初始化项目
poetry init --name taskflow --python "^3.11"

# 安装 Django
poetry add django

# 安装开发依赖
poetry add --group dev pytest black ruff

# 激活环境
poetry shell
```

---

## 三、创建 Django 项目

### 3.1 创建项目

```bash
# 在当前目录创建项目（注意末尾的点 .）
django-admin startproject config .
```

> **为什么用 `config` 而不是项目名？** 因为这个目录存放的是项目配置，用 `config` 更语义化。

### 3.2 项目目录结构

```
taskflow-backend/
├── config/                 # 项目配置目录
│   ├── __init__.py        # 标识为 Python 包
│   ├── settings.py        # 项目设置（数据库、中间件、应用等）
│   ├── urls.py            # 根 URL 路由配置
│   ├── asgi.py            # ASGI 服务器入口（异步）
│   └── wsgi.py            # WSGI 服务器入口（同步，生产用）
├── manage.py              # Django 命令行管理工具
├── .venv/                 # 虚拟环境（不提交到 Git）
└── pyproject.toml         # 项目依赖配置
```

### 3.3 启动开发服务器

```bash
python manage.py runserver

# 输出：
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CTRL-BREAK.
```

浏览器打开 `http://127.0.0.1:8000/`，看到 Django 的欢迎页面就说明成功了。

---

## 四、settings.py 详解

`settings.py` 是 Django 的核心配置文件，控制项目的所有行为。

### 4.1 关键配置项

```python
# config/settings.py

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全密钥（生产环境必须从环境变量读取！）
SECRET_KEY = 'django-insecure-xxxxxxx'  # 开发用，生产环境要改

# 调试模式（生产环境必须设为 False）
DEBUG = True

# 允许访问的主机
ALLOWED_HOSTS = []  # 开发环境为空即可，生产环境填域名

# ==================== 已安装的应用 ====================
INSTALLED_APPS = [
    # Django 内置应用
    'django.contrib.admin',          # Admin 后台
    'django.contrib.auth',           # 认证系统
    'django.contrib.contenttypes',   # 内容类型框架
    'django.contrib.sessions',       # Session 框架
    'django.contrib.messages',       # 消息框架
    'django.contrib.staticfiles',    # 静态文件服务
    
    # 第三方应用（后续添加）
    # 'rest_framework',
    # 'corsheaders',
    
    # 自己的应用（后续添加）
    # 'apps.users',
    # 'apps.projects',
    # 'apps.tasks',
]

# ==================== 中间件 ====================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 根 URL 配置
ROOT_URLCONF = 'config.urls'

# ==================== 数据库 ====================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',      # 开发用 SQLite
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 后续改为 PostgreSQL：
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'taskflow_db',
#         'USER': 'taskflow_user',
#         'PASSWORD': 'secure_password',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

# ==================== 国际化 ====================
LANGUAGE_CODE = 'zh-hans'    # 中文
TIME_ZONE = 'Asia/Shanghai'  # 上海时区
USE_I18N = True
USE_TZ = True

# ==================== 静态文件 ====================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# 默认主键类型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

---

## 五、创建应用（App）

Django 项目由多个 **应用（App）** 组成。每个应用负责一个独立的功能模块。

### 5.1 创建应用

```bash
# 先创建 apps 目录统一管理
mkdir apps
python manage.py startapp users apps/users
python manage.py startapp projects apps/projects
python manage.py startapp tasks apps/tasks
```

### 5.2 应用目录结构

```
apps/
├── users/
│   ├── __init__.py
│   ├── admin.py         # Admin 后台配置
│   ├── apps.py          # 应用配置
│   ├── models.py        # 数据模型
│   ├── views.py         # 视图函数/类
│   ├── tests.py         # 测试
│   └── migrations/      # 数据库迁移文件
│       └── __init__.py
├── projects/
│   └── ...（同上）
└── tasks/
    └── ...（同上）
```

### 5.3 注册应用

每个应用需要修改 `apps.py` 并注册到 `settings.py`。

```python
# apps/users/apps.py
from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'      # 注意这里要用完整路径
    verbose_name = '用户管理'
```

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
    
    # 自己的应用
    'apps.users',
    'apps.projects',
    'apps.tasks',
]
```

---

## 六、Django 请求生命周期

一个 HTTP 请求在 Django 中的完整流程：

```
客户端发送 HTTP 请求
        ↓
1. WSGI/ASGI 服务器接收请求
        ↓
2. 中间件处理请求（按顺序，从上到下）
   SecurityMiddleware → SessionMiddleware → CommonMiddleware → ...
        ↓
3. URL 路由匹配（urls.py）
   /api/tasks/ → tasks.views.TaskListView
        ↓
4. 视图函数/类处理请求（views.py）
   - 从 Model 获取数据
   - 处理业务逻辑
   - 构造响应
        ↓
5. 中间件处理响应（按顺序，从下到上）
   ... → CommonMiddleware → SessionMiddleware → SecurityMiddleware
        ↓
6. 返回 HTTP 响应给客户端
```

---

## 七、manage.py 常用命令

```bash
# 开发服务器
python manage.py runserver                    # 默认 8000 端口
python manage.py runserver 0.0.0.0:8080       # 指定 IP 和端口

# 数据库迁移
python manage.py makemigrations               # 生成迁移文件
python manage.py migrate                      # 执行迁移
python manage.py showmigrations               # 查看迁移状态

# 创建超级用户
python manage.py createsuperuser

# Django Shell（交互式环境）
python manage.py shell

# 创建应用
python manage.py startapp app_name

# 收集静态文件（部署用）
python manage.py collectstatic

# 查看所有可用命令
python manage.py help
```

---

## 八、项目初始化实战

完整的初始化步骤：

```bash
# 1. 创建项目目录
mkdir taskflow-backend && cd taskflow-backend

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. 安装 Django
pip install django

# 4. 创建项目
django-admin startproject config .

# 5. 创建应用
mkdir apps
python manage.py startapp users apps/users
python manage.py startapp projects apps/projects
python manage.py startapp tasks apps/tasks

# 6. 修改 apps.py 中的 name（每个应用都要改）
# 7. 在 settings.py 中注册应用
# 8. 修改语言和时区

# 9. 初始数据库迁移
python manage.py migrate

# 10. 创建超级用户
python manage.py createsuperuser

# 11. 启动服务器
python manage.py runserver
```

---

## 九、练习

1. 按照上面的步骤，从零创建 `taskflow-backend` 项目
2. 创建 `users`、`projects`、`tasks` 三个应用并注册
3. 修改 `settings.py`：语言改中文、时区改上海
4. 运行 `migrate`，创建超级用户，访问 `http://127.0.0.1:8000/admin/`
5. 理解项目目录中每个文件的作用，用自己的话描述 Django 请求生命周期
