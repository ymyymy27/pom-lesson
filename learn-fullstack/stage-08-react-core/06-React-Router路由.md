# 第 06 节：React Router 路由

## 一、什么是前端路由？

前后端分离架构中，页面切换由 **前端路由** 控制，不需要刷新页面：

```
传统 Web：点击链接 → 浏览器请求服务器 → 返回新页面（整页刷新）
SPA 路由：点击链接 → JS 拦截 → 切换组件（不刷新页面）
```

---

## 二、安装与配置

```bash
npm install react-router-dom
```

### 2.1 基础路由

```tsx
// src/main.tsx
import { BrowserRouter } from 'react-router-dom';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
    <BrowserRouter>
        <App />
    </BrowserRouter>
);
```

```tsx
// src/App.tsx
import { Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import TaskListPage from './pages/TaskListPage';
import TaskDetailPage from './pages/TaskDetailPage';
import ProjectListPage from './pages/ProjectListPage';
import LoginPage from './pages/LoginPage';
import NotFoundPage from './pages/NotFoundPage';

function App() {
    return (
        <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/tasks" element={<TaskListPage />} />
            <Route path="/tasks/:id" element={<TaskDetailPage />} />
            <Route path="/projects" element={<ProjectListPage />} />
            <Route path="*" element={<NotFoundPage />} />
        </Routes>
    );
}
```

---

## 三、嵌套路由与布局

```tsx
// src/App.tsx
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import AuthLayout from './layouts/AuthLayout';

function App() {
    return (
        <Routes>
            {/* 需要登录的页面 — 共享 MainLayout */}
            <Route element={<MainLayout />}>
                <Route path="/" element={<Navigate to="/tasks" replace />} />
                <Route path="/tasks" element={<TaskListPage />} />
                <Route path="/tasks/:id" element={<TaskDetailPage />} />
                <Route path="/projects" element={<ProjectListPage />} />
                <Route path="/projects/:id" element={<ProjectDetailPage />} />
                <Route path="/settings" element={<SettingsPage />} />
            </Route>
            
            {/* 不需要登录的页面 — 共享 AuthLayout */}
            <Route element={<AuthLayout />}>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
            </Route>
            
            <Route path="*" element={<NotFoundPage />} />
        </Routes>
    );
}
```

```tsx
// src/layouts/MainLayout.tsx
import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';

function MainLayout() {
    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />
            <div className="flex">
                <Sidebar />
                <main className="flex-1 p-6">
                    <Outlet />  {/* 子路由在这里渲染 */}
                </main>
            </div>
        </div>
    );
}

export default MainLayout;
```

---

## 四、导航

### 4.1 Link 和 NavLink

```tsx
import { Link, NavLink } from 'react-router-dom';

function Navbar() {
    return (
        <nav className="flex gap-4">
            {/* Link — 普通链接 */}
            <Link to="/">首页</Link>
            
            {/* NavLink — 自动添加 active 样式 */}
            <NavLink
                to="/tasks"
                className={({ isActive }) =>
                    isActive ? 'text-blue-600 font-bold' : 'text-gray-600'
                }
            >
                任务
            </NavLink>
            
            <NavLink
                to="/projects"
                className={({ isActive }) =>
                    isActive ? 'text-blue-600 font-bold' : 'text-gray-600'
                }
            >
                项目
            </NavLink>
        </nav>
    );
}
```

### 4.2 编程式导航

```tsx
import { useNavigate } from 'react-router-dom';

function LoginPage() {
    const navigate = useNavigate();
    
    const handleLogin = async () => {
        const success = await login(email, password);
        if (success) {
            navigate('/tasks');           // 跳转到任务页
            // navigate('/tasks', { replace: true }); // 替换历史记录（不能后退）
            // navigate(-1);              // 后退
        }
    };
    
    return <button onClick={handleLogin}>登录</button>;
}

// 创建任务后跳转到详情页
function CreateTaskForm() {
    const navigate = useNavigate();
    
    const handleSubmit = async (data: CreateTaskData) => {
        const task = await createTask(data);
        navigate(`/tasks/${task.id}`);
    };
    
    return <form>...</form>;
}
```

---

## 五、路由参数

### 5.1 URL 参数

```tsx
// 路由定义：<Route path="/tasks/:id" element={<TaskDetailPage />} />
import { useParams } from 'react-router-dom';

function TaskDetailPage() {
    const { id } = useParams<{ id: string }>();
    const [task, setTask] = useState<Task | null>(null);
    
    useEffect(() => {
        fetch(`/api/v1/tasks/${id}/`)
            .then(res => res.json())
            .then(data => setTask(data));
    }, [id]);
    
    if (!task) return <p>加载中...</p>;
    
    return (
        <div>
            <h1>{task.title}</h1>
            <p>{task.description}</p>
        </div>
    );
}
```

### 5.2 查询参数

```tsx
import { useSearchParams } from 'react-router-dom';

function TaskListPage() {
    const [searchParams, setSearchParams] = useSearchParams();
    
    // 读取查询参数
    const status = searchParams.get('status') || 'all';
    const page = Number(searchParams.get('page') || '1');
    const search = searchParams.get('search') || '';
    
    // 更新查询参数
    const handleFilterChange = (newStatus: string) => {
        setSearchParams({
            status: newStatus,
            page: '1',  // 切换过滤器时重置页码
            ...(search && { search }),
        });
    };
    
    const handlePageChange = (newPage: number) => {
        setSearchParams(prev => {
            prev.set('page', String(newPage));
            return prev;
        });
    };
    
    // URL: /tasks?status=pending&page=2&search=bug
    
    useEffect(() => {
        fetchTasks({ status, page, search });
    }, [status, page, search]);
    
    return <div>...</div>;
}
```

---

## 六、路由守卫（受保护路由）

```tsx
// src/components/ProtectedRoute.tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
    const { isAuthenticated, loading } = useAuth();
    const location = useLocation();
    
    if (loading) {
        return <div className="flex justify-center items-center h-screen">加载中...</div>;
    }
    
    if (!isAuthenticated) {
        // 未登录，跳转到登录页，记录当前路径以便登录后跳回
        return <Navigate to="/login" state={{ from: location }} replace />;
    }
    
    return <>{children}</>;
}

// 在 App.tsx 中使用
function App() {
    return (
        <Routes>
            <Route element={
                <ProtectedRoute>
                    <MainLayout />
                </ProtectedRoute>
            }>
                <Route path="/tasks" element={<TaskListPage />} />
                <Route path="/projects" element={<ProjectListPage />} />
            </Route>
            
            <Route path="/login" element={<LoginPage />} />
        </Routes>
    );
}

// 登录后跳回
function LoginPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const from = (location.state as any)?.from?.pathname || '/tasks';
    
    const handleLogin = async () => {
        await login(email, password);
        navigate(from, { replace: true });
    };
}
```

---

## 七、练习

1. 配置基础路由：首页、任务列表、任务详情、登录、404
2. 实现嵌套路由：`MainLayout` 包裹需要导航栏的页面
3. 使用 `NavLink` 创建导航栏，当前页面高亮
4. 使用 `useParams` 在任务详情页获取任务 ID 并请求数据
5. 使用 `useSearchParams` 实现任务列表的状态过滤和分页
6. 实现 `ProtectedRoute`，未登录时跳转到登录页
