# 第 04 节：副作用 useEffect

## 一、什么是副作用？

副作用（Side Effect）是指组件渲染之外的操作：
- **数据获取** — 调用 API
- **订阅** — WebSocket、事件监听
- **DOM 操作** — 修改 document.title
- **定时器** — setTimeout、setInterval

`useEffect` 让你在函数组件中执行副作用。

---

## 二、useEffect 基础

```tsx
import { useState, useEffect } from 'react';

function TaskPage() {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    
    useEffect(() => {
        // 副作用函数（组件渲染后执行）
        fetchTasks();
    }, []); // 依赖数组为空 → 只在组件挂载时执行一次
    
    async function fetchTasks() {
        try {
            setLoading(true);
            const response = await fetch('/api/v1/tasks/');
            if (!response.ok) throw new Error('请求失败');
            const data = await response.json();
            setTasks(data.results);
        } catch (err) {
            setError(err instanceof Error ? err.message : '未知错误');
        } finally {
            setLoading(false);
        }
    }
    
    if (loading) return <p>加载中...</p>;
    if (error) return <p className="text-red-500">错误：{error}</p>;
    
    return (
        <ul>
            {tasks.map(task => (
                <li key={task.id}>{task.title}</li>
            ))}
        </ul>
    );
}
```

---

## 三、依赖数组

```tsx
// 1. 无依赖数组 → 每次渲染后都执行（通常不需要）
useEffect(() => {
    console.log('每次渲染后执行');
});

// 2. 空依赖数组 → 只在挂载时执行一次
useEffect(() => {
    console.log('只执行一次（组件挂载）');
}, []);

// 3. 有依赖 → 依赖变化时执行
useEffect(() => {
    console.log('status 变化时执行');
    fetchTasks(status);
}, [status]);  // status 变了才重新执行

// 4. 多个依赖
useEffect(() => {
    fetchTasks({ status, page, search });
}, [status, page, search]); // 任何一个变了都重新执行
```

### 3.1 常见模式：搜索防抖

```tsx
function TaskSearch() {
    const [search, setSearch] = useState('');
    const [results, setResults] = useState<Task[]>([]);
    
    useEffect(() => {
        // 防抖：用户停止输入 300ms 后才搜索
        const timer = setTimeout(() => {
            if (search.trim()) {
                fetch(`/api/v1/tasks/?search=${search}`)
                    .then(res => res.json())
                    .then(data => setResults(data.results));
            } else {
                setResults([]);
            }
        }, 300);
        
        // 清理函数：组件卸载或下次 effect 执行前调用
        return () => clearTimeout(timer);
    }, [search]);
    
    return (
        <div>
            <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="搜索任务..."
            />
            <ul>
                {results.map(task => <li key={task.id}>{task.title}</li>)}
            </ul>
        </div>
    );
}
```

---

## 四、清理函数

清理函数用于 **取消订阅、清除定时器、中止请求** 等。

```tsx
// 定时器
useEffect(() => {
    const interval = setInterval(() => {
        console.log('每秒执行');
    }, 1000);
    
    return () => clearInterval(interval); // 组件卸载时清除
}, []);

// 事件监听
useEffect(() => {
    const handleResize = () => {
        console.log('窗口大小:', window.innerWidth);
    };
    window.addEventListener('resize', handleResize);
    
    return () => window.removeEventListener('resize', handleResize);
}, []);

// 中止 API 请求（AbortController）
useEffect(() => {
    const controller = new AbortController();
    
    fetch('/api/v1/tasks/', { signal: controller.signal })
        .then(res => res.json())
        .then(data => setTasks(data.results))
        .catch(err => {
            if (err.name !== 'AbortError') {
                setError(err.message);
            }
        });
    
    return () => controller.abort(); // 组件卸载时中止请求
}, []);
```

---

## 五、常见场景

### 5.1 修改页面标题

```tsx
function TaskDetail({ task }: { task: Task }) {
    useEffect(() => {
        document.title = `${task.title} - TaskFlow`;
        
        return () => {
            document.title = 'TaskFlow';
        };
    }, [task.title]);
    
    return <div>...</div>;
}
```

### 5.2 依赖变化时重新获取数据

```tsx
function TaskList() {
    const [status, setStatus] = useState<string>('all');
    const [page, setPage] = useState(1);
    const [tasks, setTasks] = useState<Task[]>([]);
    const [total, setTotal] = useState(0);
    
    useEffect(() => {
        const controller = new AbortController();
        
        const params = new URLSearchParams({ page: String(page), page_size: '20' });
        if (status !== 'all') params.set('status', status);
        
        fetch(`/api/v1/tasks/?${params}`, { signal: controller.signal })
            .then(res => res.json())
            .then(data => {
                setTasks(data.results);
                setTotal(data.count);
            })
            .catch(err => {
                if (err.name !== 'AbortError') console.error(err);
            });
        
        return () => controller.abort();
    }, [status, page]); // status 或 page 变化时重新请求
    
    // 切换过滤时重置页码
    const handleStatusChange = (newStatus: string) => {
        setStatus(newStatus);
        setPage(1);
    };
    
    return <div>...</div>;
}
```

### 5.3 localStorage 持久化

```tsx
function useLocalStorage<T>(key: string, initialValue: T) {
    const [value, setValue] = useState<T>(() => {
        const stored = localStorage.getItem(key);
        return stored ? JSON.parse(stored) : initialValue;
    });
    
    useEffect(() => {
        localStorage.setItem(key, JSON.stringify(value));
    }, [key, value]);
    
    return [value, setValue] as const;
}

// 使用
function App() {
    const [theme, setTheme] = useLocalStorage('theme', 'light');
}
```

---

## 六、useEffect 注意事项

```tsx
// ❌ 不要在 useEffect 中直接使用 async
useEffect(async () => {  // 错误！useEffect 不能返回 Promise
    const data = await fetchData();
}, []);

// ✅ 在 useEffect 内部定义 async 函数
useEffect(() => {
    async function loadData() {
        const data = await fetchData();
        setData(data);
    }
    loadData();
}, []);

// ❌ 遗漏依赖
const [userId, setUserId] = useState(1);
useEffect(() => {
    fetchUser(userId); // 用了 userId 但没放入依赖数组
}, []); // ESLint 会警告

// ✅ 正确包含依赖
useEffect(() => {
    fetchUser(userId);
}, [userId]);
```

---

## 七、练习

1. 使用 useEffect 在组件挂载时获取任务列表
2. 实现加载状态和错误处理（loading / error / data 三种状态）
3. 实现搜索防抖：输入停止 300ms 后发起搜索请求
4. 实现依赖变化触发请求：状态过滤器变化时重新获取数据
5. 使用 AbortController 在组件卸载时中止进行中的请求
6. 实现 `useLocalStorage` 自定义 Hook
