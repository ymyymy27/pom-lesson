# 第 07 节：自定义 Hooks

## 一、什么是自定义 Hook？

自定义 Hook 是一个 **以 `use` 开头的函数**，用来封装可复用的状态逻辑。

```
规则：
1. 函数名必须以 use 开头
2. 内部可以调用其他 Hooks
3. 可以返回任意值（状态、函数、对象等）
```

---

## 二、常用自定义 Hooks

### 2.1 useFetch — 数据请求

```tsx
import { useState, useEffect, useCallback } from 'react';

interface UseFetchResult<T> {
    data: T | null;
    loading: boolean;
    error: string | null;
    refetch: () => void;
}

function useFetch<T>(url: string, options?: RequestInit): UseFetchResult<T> {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    
    const fetchData = useCallback(async () => {
        const controller = new AbortController();
        
        try {
            setLoading(true);
            setError(null);
            
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            setData(result);
        } catch (err) {
            if (err instanceof Error && err.name !== 'AbortError') {
                setError(err.message);
            }
        } finally {
            setLoading(false);
        }
        
        return () => controller.abort();
    }, [url]);
    
    useEffect(() => {
        const cleanup = fetchData();
        return () => { cleanup.then(fn => fn?.()); };
    }, [fetchData]);
    
    return { data, loading, error, refetch: fetchData };
}

// 使用
function TaskListPage() {
    const { data, loading, error, refetch } = useFetch<PaginatedResponse<Task>>(
        '/api/v1/tasks/?page=1'
    );
    
    if (loading) return <Spinner />;
    if (error) return <ErrorMessage message={error} onRetry={refetch} />;
    
    return <TaskList tasks={data?.results ?? []} />;
}
```

### 2.2 useAuth — 认证状态

```tsx
import { useState, useEffect, useContext, createContext, useCallback } from 'react';

interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    loading: boolean;
}

interface AuthContextType extends AuthState {
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    register: (data: RegisterData) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [state, setState] = useState<AuthState>({
        user: null,
        token: localStorage.getItem('access_token'),
        isAuthenticated: false,
        loading: true,
    });
    
    // 初始化：验证 Token 并获取用户信息
    useEffect(() => {
        if (state.token) {
            fetch('/api/v1/auth/me/', {
                headers: { Authorization: `Bearer ${state.token}` },
            })
                .then(res => {
                    if (res.ok) return res.json();
                    throw new Error('Token 无效');
                })
                .then(user => setState(prev => ({ ...prev, user, isAuthenticated: true, loading: false })))
                .catch(() => {
                    localStorage.removeItem('access_token');
                    setState({ user: null, token: null, isAuthenticated: false, loading: false });
                });
        } else {
            setState(prev => ({ ...prev, loading: false }));
        }
    }, []);
    
    const login = useCallback(async (email: string, password: string) => {
        const res = await fetch('/api/v1/auth/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        if (!res.ok) throw new Error('登录失败');
        
        const data = await res.json();
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        setState({
            user: data.user,
            token: data.access,
            isAuthenticated: true,
            loading: false,
        });
    }, []);
    
    const logout = useCallback(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setState({ user: null, token: null, isAuthenticated: false, loading: false });
    }, []);
    
    const register = useCallback(async (data: RegisterData) => {
        const res = await fetch('/api/v1/auth/register/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error('注册失败');
        
        const result = await res.json();
        localStorage.setItem('access_token', result.tokens.access);
        localStorage.setItem('refresh_token', result.tokens.refresh);
        setState({
            user: result.user,
            token: result.tokens.access,
            isAuthenticated: true,
            loading: false,
        });
    }, []);
    
    return (
        <AuthContext.Provider value={{ ...state, login, logout, register }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth 必须在 AuthProvider 内使用');
    return context;
}

// 使用
function LoginPage() {
    const { login } = useAuth();
    const navigate = useNavigate();
    
    const handleSubmit = async (email: string, password: string) => {
        try {
            await login(email, password);
            navigate('/tasks');
        } catch {
            alert('登录失败');
        }
    };
}

function Navbar() {
    const { user, isAuthenticated, logout } = useAuth();
    
    return (
        <nav>
            {isAuthenticated ? (
                <>
                    <span>你好，{user?.username}</span>
                    <button onClick={logout}>登出</button>
                </>
            ) : (
                <Link to="/login">登录</Link>
            )}
        </nav>
    );
}
```

### 2.3 useDebounce — 防抖

```tsx
function useDebounce<T>(value: T, delay: number = 300): T {
    const [debouncedValue, setDebouncedValue] = useState(value);
    
    useEffect(() => {
        const timer = setTimeout(() => setDebouncedValue(value), delay);
        return () => clearTimeout(timer);
    }, [value, delay]);
    
    return debouncedValue;
}

// 使用
function TaskSearch() {
    const [search, setSearch] = useState('');
    const debouncedSearch = useDebounce(search, 300);
    
    useEffect(() => {
        if (debouncedSearch) {
            fetchTasks({ search: debouncedSearch });
        }
    }, [debouncedSearch]);
    
    return <input value={search} onChange={e => setSearch(e.target.value)} />;
}
```

### 2.4 useLocalStorage — 本地存储

```tsx
function useLocalStorage<T>(key: string, initialValue: T) {
    const [value, setValue] = useState<T>(() => {
        try {
            const stored = localStorage.getItem(key);
            return stored ? JSON.parse(stored) : initialValue;
        } catch {
            return initialValue;
        }
    });
    
    useEffect(() => {
        localStorage.setItem(key, JSON.stringify(value));
    }, [key, value]);
    
    const removeValue = useCallback(() => {
        localStorage.removeItem(key);
        setValue(initialValue);
    }, [key, initialValue]);
    
    return [value, setValue, removeValue] as const;
}

// 使用
function App() {
    const [theme, setTheme] = useLocalStorage('theme', 'light');
    const [pageSize, setPageSize] = useLocalStorage('page_size', 20);
}
```

### 2.5 useToggle — 开关状态

```tsx
function useToggle(initialValue: boolean = false) {
    const [value, setValue] = useState(initialValue);
    
    const toggle = useCallback(() => setValue(v => !v), []);
    const setTrue = useCallback(() => setValue(true), []);
    const setFalse = useCallback(() => setValue(false), []);
    
    return { value, toggle, setTrue, setFalse };
}

// 使用
function TaskCard() {
    const { value: isExpanded, toggle: toggleExpand } = useToggle(false);
    const { value: isModalOpen, setTrue: openModal, setFalse: closeModal } = useToggle(false);
    
    return (
        <div>
            <button onClick={toggleExpand}>{isExpanded ? '收起' : '展开'}</button>
            {isExpanded && <div>详细内容...</div>}
            
            <button onClick={openModal}>编辑</button>
            {isModalOpen && <Modal onClose={closeModal} />}
        </div>
    );
}
```

### 2.6 usePagination — 分页

```tsx
interface UsePaginationResult<T> {
    data: T[];
    total: number;
    page: number;
    pageSize: number;
    totalPages: number;
    loading: boolean;
    error: string | null;
    setPage: (page: number) => void;
    setPageSize: (size: number) => void;
    nextPage: () => void;
    prevPage: () => void;
    hasNext: boolean;
    hasPrev: boolean;
}

function usePagination<T>(
    fetchUrl: string,
    initialPageSize: number = 20,
): UsePaginationResult<T> {
    const [data, setData] = useState<T[]>([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(initialPageSize);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    
    const totalPages = Math.ceil(total / pageSize);
    
    useEffect(() => {
        const controller = new AbortController();
        setLoading(true);
        
        fetch(`${fetchUrl}?page=${page}&page_size=${pageSize}`, {
            signal: controller.signal,
        })
            .then(res => res.json())
            .then(result => {
                setData(result.results);
                setTotal(result.count);
                setError(null);
            })
            .catch(err => {
                if (err.name !== 'AbortError') setError(err.message);
            })
            .finally(() => setLoading(false));
        
        return () => controller.abort();
    }, [fetchUrl, page, pageSize]);
    
    return {
        data,
        total,
        page,
        pageSize,
        totalPages,
        loading,
        error,
        setPage,
        setPageSize: (size: number) => { setPageSize(size); setPage(1); },
        nextPage: () => setPage(p => Math.min(p + 1, totalPages)),
        prevPage: () => setPage(p => Math.max(p - 1, 1)),
        hasNext: page < totalPages,
        hasPrev: page > 1,
    };
}

// 使用
function TaskListPage() {
    const {
        data: tasks, loading, page, totalPages, setPage, hasNext, hasPrev, nextPage, prevPage,
    } = usePagination<Task>('/api/v1/tasks/');
    
    return (
        <div>
            {loading ? <Spinner /> : <TaskList tasks={tasks} />}
            <div className="flex gap-2 mt-4">
                <button onClick={prevPage} disabled={!hasPrev}>上一页</button>
                <span>{page} / {totalPages}</span>
                <button onClick={nextPage} disabled={!hasNext}>下一页</button>
            </div>
        </div>
    );
}
```

---

## 三、练习

1. 实现 `useFetch` Hook，支持加载状态、错误处理、重新请求
2. 实现 `useAuth` Hook + `AuthProvider`，管理登录状态
3. 实现 `useDebounce` Hook，用于搜索输入防抖
4. 实现 `useLocalStorage` Hook，持久化用户偏好设置
5. 实现 `usePagination` Hook，封装分页逻辑
6. 在 TaskFlow 前端项目中整合以上 Hooks

## 阶段总结

至此，第 08 阶段全部完成。你已经掌握：

- ✅ React 组件化思想和 JSX 语法
- ✅ 函数组件、Props、事件处理
- ✅ useState 状态管理和表单处理
- ✅ useEffect 副作用和数据获取
- ✅ useRef、useMemo、useCallback、useReducer
- ✅ React Router 路由、嵌套路由、路由守卫
- ✅ 自定义 Hooks 封装可复用逻辑

**下一阶段** → 第 09 阶段：前端进阶（状态管理/API 对接/UI 框架）
