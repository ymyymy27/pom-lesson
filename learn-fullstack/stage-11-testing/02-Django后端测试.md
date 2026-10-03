# 第 02 节：Django 后端测试

## 一、Factory Boy 测试数据工厂

手动创建测试数据繁琐且难维护，Factory Boy 自动生成。

```bash
pip install factory-boy faker
```

```python
# tests/factories.py
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from apps.projects.models import Project
from apps.tasks.models import Task

User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')

class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project
    
    name = factory.Faker('company', locale='zh_CN')
    description = factory.Faker('text', max_nb_chars=200, locale='zh_CN')
    owner = factory.SubFactory(UserFactory)

class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task
    
    title = factory.Faker('sentence', nb_words=4, locale='zh_CN')
    description = factory.Faker('paragraph', locale='zh_CN')
    status = 'pending'
    priority = factory.Faker('random_int', min=0, max=10)
    project = factory.SubFactory(ProjectFactory)
    creator = factory.SubFactory(UserFactory)
    assignee = None
```

```python
# tests/conftest.py
import pytest
from rest_framework.test import APIClient
from tests.factories import UserFactory, ProjectFactory, TaskFactory

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return UserFactory()

@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def project(user):
    return ProjectFactory(owner=user)

@pytest.fixture
def task(user, project):
    return TaskFactory(project=project, creator=user)
```

---

## 二、模型测试

```python
# tests/test_models.py
import pytest
from tests.factories import UserFactory, TaskFactory, ProjectFactory

@pytest.mark.django_db
class TestTaskModel:
    
    def test_create_task(self, project, user):
        task = TaskFactory(
            title='测试任务',
            project=project,
            creator=user,
            priority=8,
        )
        assert task.title == '测试任务'
        assert task.status == 'pending'
        assert task.priority == 8
        assert task.creator == user
        assert task.project == project
    
    def test_task_str(self, task):
        assert str(task) == task.title
    
    def test_default_status(self, task):
        assert task.status == 'pending'
    
    def test_task_assignment(self, task):
        assignee = UserFactory()
        task.assignee = assignee
        task.save()
        task.refresh_from_db()
        assert task.assignee == assignee

@pytest.mark.django_db
class TestProjectModel:
    
    def test_create_project(self, user):
        project = ProjectFactory(name='TaskFlow', owner=user)
        assert project.name == 'TaskFlow'
        assert project.owner == user
    
    def test_project_member_count(self, project, user):
        project.members.add(user)
        assert project.members.count() == 1
```

---

## 三、API 测试

### 3.1 认证 API 测试

```python
# tests/test_auth_api.py
import pytest
from django.urls import reverse
from tests.factories import UserFactory

@pytest.mark.django_db
class TestAuthAPI:
    
    def test_register(self, api_client):
        url = reverse('register')  # 或直接用路径
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 201
        assert 'tokens' in response.data
        assert response.data['user']['email'] == 'new@example.com'
    
    def test_register_duplicate_email(self, api_client, user):
        url = reverse('register')
        data = {
            'username': 'another',
            'email': user.email,
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == 400
    
    def test_login(self, api_client, user):
        url = '/api/v1/auth/login/'
        response = api_client.post(url, {
            'email': user.email,
            'password': 'testpass123',
        }, format='json')
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_login_wrong_password(self, api_client, user):
        url = '/api/v1/auth/login/'
        response = api_client.post(url, {
            'email': user.email,
            'password': 'wrongpassword',
        }, format='json')
        assert response.status_code == 401
    
    def test_me(self, auth_client, user):
        response = auth_client.get('/api/v1/auth/me/')
        assert response.status_code == 200
        assert response.data['email'] == user.email
    
    def test_me_unauthenticated(self, api_client):
        response = api_client.get('/api/v1/auth/me/')
        assert response.status_code == 401
```

### 3.2 任务 CRUD 测试

```python
# tests/test_task_api.py
import pytest
from tests.factories import UserFactory, TaskFactory, ProjectFactory

@pytest.mark.django_db
class TestTaskAPI:
    
    def test_list_tasks(self, auth_client, project, user):
        TaskFactory.create_batch(5, project=project, creator=user)
        response = auth_client.get('/api/v1/tasks/')
        assert response.status_code == 200
        assert response.data['count'] == 5
        assert len(response.data['results']) == 5
    
    def test_create_task(self, auth_client, project):
        data = {
            'title': '新任务',
            'description': '任务描述',
            'priority': 8,
            'project': project.id,
        }
        response = auth_client.post('/api/v1/tasks/', data, format='json')
        assert response.status_code == 201
        assert response.data['title'] == '新任务'
        assert response.data['priority'] == 8
    
    def test_create_task_without_title(self, auth_client, project):
        data = {'project': project.id}
        response = auth_client.post('/api/v1/tasks/', data, format='json')
        assert response.status_code == 400
        assert 'title' in response.data
    
    def test_retrieve_task(self, auth_client, task):
        response = auth_client.get(f'/api/v1/tasks/{task.id}/')
        assert response.status_code == 200
        assert response.data['id'] == task.id
    
    def test_update_task(self, auth_client, task):
        response = auth_client.patch(f'/api/v1/tasks/{task.id}/', {
            'status': 'in_progress',
        }, format='json')
        assert response.status_code == 200
        assert response.data['status'] == 'in_progress'
    
    def test_delete_task(self, auth_client, task):
        response = auth_client.delete(f'/api/v1/tasks/{task.id}/')
        assert response.status_code == 204
    
    def test_filter_by_status(self, auth_client, project, user):
        TaskFactory.create_batch(3, project=project, creator=user, status='pending')
        TaskFactory.create_batch(2, project=project, creator=user, status='completed')
        
        response = auth_client.get('/api/v1/tasks/?status=pending')
        assert response.data['count'] == 3
        
        response = auth_client.get('/api/v1/tasks/?status=completed')
        assert response.data['count'] == 2
    
    def test_search_tasks(self, auth_client, project, user):
        TaskFactory(title='修复登录Bug', project=project, creator=user)
        TaskFactory(title='添加搜索功能', project=project, creator=user)
        
        response = auth_client.get('/api/v1/tasks/?search=Bug')
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == '修复登录Bug'

@pytest.mark.django_db
class TestTaskPermissions:
    
    def test_unauthenticated_cannot_create(self, api_client, project):
        response = api_client.post('/api/v1/tasks/', {
            'title': '测试',
            'project': project.id,
        }, format='json')
        assert response.status_code == 401
    
    def test_non_owner_cannot_delete(self, auth_client, project):
        other_user = UserFactory()
        task = TaskFactory(project=project, creator=other_user)
        response = auth_client.delete(f'/api/v1/tasks/{task.id}/')
        # 根据你的权限设置，可能是 403 或 404
        assert response.status_code in [403, 404]
```

---

## 四、练习

1. 创建 Factory Boy 工厂：`UserFactory`、`ProjectFactory`、`TaskFactory`
2. 在 `conftest.py` 中定义公共 fixture
3. 编写模型测试：创建、默认值、关联关系
4. 编写 API 测试：注册、登录、任务 CRUD
5. 编写权限测试：未认证访问、非所有者操作
6. 运行 `pytest -v --cov=apps` 查看覆盖率
