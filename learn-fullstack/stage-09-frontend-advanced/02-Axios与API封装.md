# 第 02 节：Axios 与 API 封装

## 一、为什么用 Axios？

Axios 相比原生 `fetch` 提供了更多便利：

| 特性 | fetch | Axios |
|------|-------|-------|
| 自动 JSON 转换 | 需要手动 `.json()` | 自动解析 |
| 请求/响应拦截器 | ❌ | ✅ |
| 超时设置 | 需要 AbortController | `timeout` 参数 |
| HTTP 错误处理 | 不抛异常（需检查 ok） | 自动抛异常 |
| 请求取消 | AbortController | CancelToken / AbortController |
| 上传进度 | ❌ | `onUploadProgress` |

---

## 二、安装与基础配置

```bash
npm install axios
```

```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
    baseURL: '/api/v1',
    timeout: 15000,
    headers: {
        'Content-Type': 'application/json',
    },
});

export default api;
```

---

## 三、拦截器

### 3.1 请求拦截器 — 自动附加 Token

```typescript
// src/services/api.ts
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);
```

### 3.2 响应拦截器 — Token 自动刷新

```typescript
let isRefreshing = false;
let failedQueue: Array<{
    resolve: (token: string) => void;
    reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null) => {
    failedQueue.forEach(({ resolve, reject }) => {
        if (token) resolve(token);
        else reject(error);
    });
    failedQueue = [];
};

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        
        // 401 且不是刷新 Token 请求本身
        if (error.response?.status === 401 && !originalRequest._retry) {
            if (isRefreshing) {
                // 已经在刷新了，加入等待队列
                return new Promise((resolve, reject) => {
                    failedQueue.push({
                        resolve: (token) => {
                            originalRequest.headers.Authorization = `Bearer ${token}`;
                            resolve(api(originalRequest));
                        },
                        reject,
                    });
                });
            }
            
            originalRequest._retry = true;
            isRefreshing = true;
            
            try {
                const refreshToken = localStorage.getItem('refresh_token');
                if (!refreshToken) throw new Error('No refresh token');
                
                const { data } = await axios.post('/api/v1/auth/refresh/', {
                    refresh: refreshToken,
                });
                
                const newToken = data.access;
                localStorage.setItem('access_token', newToken);
                
                processQueue(null, newToken);
                
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                return api(originalRequest);
            } catch (refreshError) {
                processQueue(refreshError, null);
                // 刷新失败，清除认证状态并跳转登录
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        }
        
        return Promise.reject(error);
    }
);
```

---

## 四、API 服务层封装

```typescript
// src/services/taskService.ts
import api from './api';
import type { Task, PaginatedResponse, CreateTaskRequest, UpdateTaskRequest } from '@/types';

interface TaskQueryParams {
    page?: number;
    page_size?: number;
    status?: string;
    search?: string;
    ordering?: string;
    project?: number;
}

export const taskService = {
    getList: (params?: TaskQueryParams) =>
        api.get<PaginatedResponse<Task>>('/tasks/', { params }),
    
    getById: (id: number) =>
        api.get<Task>(`/tasks/${id}/`),
    
    create: (data: CreateTaskRequest) =>
        api.post<Task>('/tasks/', data),
    
    update: (id: number, data: UpdateTaskRequest) =>
        api.patch<Task>(`/tasks/${id}/`, data),
    
    delete: (id: number) =>
        api.delete(`/tasks/${id}/`),
    
    complete: (id: number) =>
        api.post<Task>(`/tasks/${id}/complete/`),
    
    assign: (id: number, userId: number) =>
        api.post<Task>(`/tasks/${id}/assign/`, { user_id: userId }),
    
    getStatistics: (params?: { project?: number }) =>
        api.get('/tasks/statistics/', { params }),
    
    getMyTasks: () =>
        api.get<PaginatedResponse<Task>>('/tasks/my_tasks/'),
};

// src/services/authService.ts
export const authService = {
    login: (email: string, password: string) =>
        api.post('/auth/login/', { email, password }),
    
    register: (data: { username: string; email: string; password: string; password_confirm: string }) =>
        api.post('/auth/register/', data),
    
    getMe: () =>
        api.get('/auth/me/'),
    
    updateMe: (data: Partial<{ username: string; bio: string; phone: string }>) =>
        api.patch('/auth/me/', data),
    
    changePassword: (data: { old_password: string; new_password: string; new_password_confirm: string }) =>
        api.post('/auth/change-password/', data),
};

// src/services/projectService.ts
export const projectService = {
    getList: (params?: { page?: number }) =>
        api.get<PaginatedResponse<Project>>('/projects/', { params }),
    
    getById: (id: number) =>
        api.get<Project>(`/projects/${id}/`),
    
    create: (data: { name: string; description?: string }) =>
        api.post<Project>('/projects/', data),
    
    update: (id: number, data: Partial<Project>) =>
        api.patch<Project>(`/projects/${id}/`, data),
    
    delete: (id: number) =>
        api.delete(`/projects/${id}/`),
};
```

### 在组件中使用

```tsx
import { taskService } from '@/services/taskService';

function TaskListPage() {
    const [tasks, setTasks] = useState<Task[]>([]);
    
    useEffect(() => {
        taskService.getList({ status: 'pending', page: 1 })
            .then(({ data }) => setTasks(data.results))
            .catch((err) => console.error(err));
    }, []);
    
    const handleCreate = async (formData: CreateTaskRequest) => {
        try {
            const { data: newTask } = await taskService.create(formData);
            setTasks((prev) => [newTask, ...prev]);
        } catch (err) {
            if (axios.isAxiosError(err)) {
                console.error('验证错误:', err.response?.data);
            }
        }
    };
}
```

---

## 五、错误处理工具

```typescript
// src/utils/errorHandler.ts
import axios from 'axios';

export function getErrorMessage(error: unknown): string {
    if (axios.isAxiosError(error)) {
        const data = error.response?.data;
        if (typeof data === 'string') return data;
        if (data?.message) return data.message;
        if (data?.detail) return data.detail;
        
        // 字段级错误
        if (typeof data === 'object') {
            const messages = Object.entries(data)
                .map(([key, value]) => `${key}: ${(value as string[]).join(', ')}`)
                .join('; ');
            if (messages) return messages;
        }
        
        return `请求失败 (${error.response?.status})`;
    }
    
    if (error instanceof Error) return error.message;
    return '未知错误';
}
```

---

## 六、练习

1. 创建 Axios 实例，配置 baseURL 和超时
2. 实现请求拦截器：自动附加 JWT Token
3. 实现响应拦截器：401 时自动刷新 Token
4. 封装 `taskService`、`authService`、`projectService`
5. 实现统一错误提取工具 `getErrorMessage`
6. 在组件中使用 Service 层发起请求
