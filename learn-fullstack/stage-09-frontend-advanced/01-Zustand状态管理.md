# 第 01 节：Zustand 状态管理

## 一、为什么需要全局状态管理？

组件间共享状态（如用户信息、主题、通知）如果都靠 Props 逐层传递（Prop Drilling），代码会变得混乱。全局状态管理让任何组件都能直接访问和修改共享状态。

### 1.1 方案对比

| 方案 | 复杂度 | 包大小 | 学习成本 | 推荐场景 |
|------|--------|--------|---------|---------|
| **Context + useReducer** | 中 | 0 | 低 | 简单场景（主题、语言） |
| **Zustand** | 低 | 1KB | 极低 | 中小型项目（推荐） |
| **Redux Toolkit** | 高 | 11KB | 中 | 大型企业项目 |
| **Jotai / Recoil** | 中 | 3KB | 中 | 原子化状态 |

---

## 二、安装与基础用法

```bash
npm install zustand
```

### 2.1 创建 Store

```typescript
// src/store/useTaskStore.ts
import { create } from 'zustand';

interface Task {
    id: number;
    title: string;
    status: string;
    priority: number;
}

interface TaskStore {
    tasks: Task[];
    loading: boolean;
    error: string | null;
    filter: string;
    
    // Actions
    setTasks: (tasks: Task[]) => void;
    addTask: (task: Task) => void;
    updateTask: (id: number, updates: Partial<Task>) => void;
    deleteTask: (id: number) => void;
    setFilter: (filter: string) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
}

const useTaskStore = create<TaskStore>((set) => ({
    tasks: [],
    loading: false,
    error: null,
    filter: 'all',
    
    setTasks: (tasks) => set({ tasks }),
    
    addTask: (task) => set((state) => ({
        tasks: [task, ...state.tasks],
    })),
    
    updateTask: (id, updates) => set((state) => ({
        tasks: state.tasks.map((t) =>
            t.id === id ? { ...t, ...updates } : t
        ),
    })),
    
    deleteTask: (id) => set((state) => ({
        tasks: state.tasks.filter((t) => t.id !== id),
    })),
    
    setFilter: (filter) => set({ filter }),
    setLoading: (loading) => set({ loading }),
    setError: (error) => set({ error }),
}));

export default useTaskStore;
```

### 2.2 在组件中使用

```tsx
// src/pages/TaskListPage.tsx
import useTaskStore from '@/store/useTaskStore';

function TaskListPage() {
    const { tasks, loading, filter, setFilter } = useTaskStore();
    
    const filteredTasks = tasks.filter((t) => {
        if (filter === 'all') return true;
        return t.status === filter;
    });
    
    return (
        <div>
            <StatusFilter value={filter} onChange={setFilter} />
            {loading ? <Spinner /> : <TaskList tasks={filteredTasks} />}
        </div>
    );
}

// 组件只订阅需要的状态（性能优化）
function TaskCount() {
    const count = useTaskStore((state) => state.tasks.length);
    return <span>共 {count} 个任务</span>;
}

function TaskActions() {
    const { addTask, deleteTask, updateTask } = useTaskStore();
    
    const handleComplete = (id: number) => {
        updateTask(id, { status: 'completed' });
    };
    
    return <div>...</div>;
}
```

---

## 三、异步 Action

```typescript
// src/store/useTaskStore.ts
import { create } from 'zustand';

interface TaskStore {
    tasks: Task[];
    loading: boolean;
    error: string | null;
    
    fetchTasks: (params?: Record<string, string>) => Promise<void>;
    createTask: (data: CreateTaskData) => Promise<Task>;
    completeTask: (id: number) => Promise<void>;
    removeTask: (id: number) => Promise<void>;
}

const useTaskStore = create<TaskStore>((set, get) => ({
    tasks: [],
    loading: false,
    error: null,
    
    fetchTasks: async (params) => {
        set({ loading: true, error: null });
        try {
            const query = new URLSearchParams(params).toString();
            const res = await fetch(`/api/v1/tasks/?${query}`);
            if (!res.ok) throw new Error('获取任务失败');
            const data = await res.json();
            set({ tasks: data.results, loading: false });
        } catch (err) {
            set({ error: (err as Error).message, loading: false });
        }
    },
    
    createTask: async (data) => {
        const res = await fetch('/api/v1/tasks/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error('创建失败');
        const task = await res.json();
        set((state) => ({ tasks: [task, ...state.tasks] }));
        return task;
    },
    
    completeTask: async (id) => {
        await fetch(`/api/v1/tasks/${id}/complete/`, { method: 'POST' });
        set((state) => ({
            tasks: state.tasks.map((t) =>
                t.id === id ? { ...t, status: 'completed' } : t
            ),
        }));
    },
    
    removeTask: async (id) => {
        await fetch(`/api/v1/tasks/${id}/`, { method: 'DELETE' });
        set((state) => ({
            tasks: state.tasks.filter((t) => t.id !== id),
        }));
    },
}));
```

---

## 四、中间件

### 4.1 persist — 持久化

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SettingsStore {
    theme: 'light' | 'dark';
    language: string;
    pageSize: number;
    sidebarCollapsed: boolean;
    setTheme: (theme: 'light' | 'dark') => void;
    setLanguage: (lang: string) => void;
    setPageSize: (size: number) => void;
    toggleSidebar: () => void;
}

const useSettingsStore = create<SettingsStore>()(
    persist(
        (set) => ({
            theme: 'light',
            language: 'zh',
            pageSize: 20,
            sidebarCollapsed: false,
            setTheme: (theme) => set({ theme }),
            setLanguage: (language) => set({ language }),
            setPageSize: (pageSize) => set({ pageSize }),
            toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
        }),
        {
            name: 'taskflow-settings', // localStorage key
        }
    )
);
```

### 4.2 devtools — 开发调试

```typescript
import { devtools } from 'zustand/middleware';

const useTaskStore = create<TaskStore>()(
    devtools(
        (set) => ({
            // ... store 定义
        }),
        { name: 'TaskStore' }
    )
);
```

---

## 五、认证 Store

```typescript
// src/store/useAuthStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthStore {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    setUser: (user: User) => void;
    initialize: () => Promise<void>;
}

const useAuthStore = create<AuthStore>()(
    persist(
        (set, get) => ({
            user: null,
            token: null,
            isAuthenticated: false,
            
            login: async (email, password) => {
                const res = await fetch('/api/v1/auth/login/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password }),
                });
                if (!res.ok) throw new Error('登录失败');
                
                const data = await res.json();
                set({
                    user: data.user,
                    token: data.access,
                    isAuthenticated: true,
                });
                localStorage.setItem('refresh_token', data.refresh);
            },
            
            logout: () => {
                set({ user: null, token: null, isAuthenticated: false });
                localStorage.removeItem('refresh_token');
            },
            
            setUser: (user) => set({ user }),
            
            initialize: async () => {
                const { token } = get();
                if (!token) return;
                
                try {
                    const res = await fetch('/api/v1/auth/me/', {
                        headers: { Authorization: `Bearer ${token}` },
                    });
                    if (res.ok) {
                        const user = await res.json();
                        set({ user, isAuthenticated: true });
                    } else {
                        get().logout();
                    }
                } catch {
                    get().logout();
                }
            },
        }),
        {
            name: 'taskflow-auth',
            partialize: (state) => ({ token: state.token }), // 只持久化 token
        }
    )
);

export default useAuthStore;
```

---

## 六、练习

1. 创建 `useTaskStore`，包含任务 CRUD 和异步请求
2. 创建 `useAuthStore`，管理登录/登出/Token
3. 创建 `useSettingsStore`，使用 persist 持久化主题和偏好
4. 在组件中按需订阅状态，避免不必要的重新渲染
5. 使用 devtools 中间件，在浏览器 Redux DevTools 中查看状态
