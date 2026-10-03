# 第 05 节：常用 Hooks

## 一、useRef

`useRef` 创建一个 **可变的引用对象**，在整个组件生命周期内保持不变，修改时 **不触发重新渲染**。

### 1.1 访问 DOM 元素

```tsx
import { useRef, useEffect } from 'react';

function SearchInput() {
    const inputRef = useRef<HTMLInputElement>(null);
    
    useEffect(() => {
        // 组件挂载后自动聚焦
        inputRef.current?.focus();
    }, []);
    
    return <input ref={inputRef} placeholder="搜索任务..." />;
}
```

### 1.2 存储不需要触发渲染的值

```tsx
function Timer() {
    const [count, setCount] = useState(0);
    const intervalRef = useRef<number | null>(null);
    
    const start = () => {
        if (intervalRef.current !== null) return;
        intervalRef.current = window.setInterval(() => {
            setCount(prev => prev + 1);
        }, 1000);
    };
    
    const stop = () => {
        if (intervalRef.current !== null) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
    };
    
    useEffect(() => {
        return () => stop(); // 组件卸载时清除
    }, []);
    
    return (
        <div>
            <p>计时：{count}s</p>
            <button onClick={start}>开始</button>
            <button onClick={stop}>停止</button>
        </div>
    );
}
```

### 1.3 记录前一个值

```tsx
function usePrevious<T>(value: T): T | undefined {
    const ref = useRef<T>();
    useEffect(() => {
        ref.current = value;
    });
    return ref.current;
}

function TaskDetail({ task }: { task: Task }) {
    const prevStatus = usePrevious(task.status);
    
    useEffect(() => {
        if (prevStatus && prevStatus !== task.status) {
            console.log(`状态变化: ${prevStatus} → ${task.status}`);
        }
    }, [task.status, prevStatus]);
    
    return <div>{task.title}</div>;
}
```

---

## 二、useMemo

`useMemo` 缓存 **计算结果**，只在依赖变化时重新计算，避免昂贵计算在每次渲染时重复执行。

```tsx
import { useMemo } from 'react';

function TaskDashboard({ tasks }: { tasks: Task[] }) {
    // ✅ 只在 tasks 变化时重新计算
    const statistics = useMemo(() => {
        return {
            total: tasks.length,
            pending: tasks.filter(t => t.status === 'pending').length,
            inProgress: tasks.filter(t => t.status === 'in_progress').length,
            completed: tasks.filter(t => t.status === 'completed').length,
            avgPriority: tasks.length > 0
                ? (tasks.reduce((sum, t) => sum + t.priority, 0) / tasks.length).toFixed(1)
                : '0',
        };
    }, [tasks]);
    
    return (
        <div className="grid grid-cols-4 gap-4">
            <StatCard label="总计" value={statistics.total} />
            <StatCard label="待办" value={statistics.pending} />
            <StatCard label="进行中" value={statistics.inProgress} />
            <StatCard label="已完成" value={statistics.completed} />
        </div>
    );
}

// 排序+过滤也适合 useMemo
function TaskList({ tasks, filter, sortBy }: Props) {
    const processedTasks = useMemo(() => {
        let result = [...tasks];
        
        if (filter !== 'all') {
            result = result.filter(t => t.status === filter);
        }
        
        result.sort((a, b) => {
            if (sortBy === 'priority') return b.priority - a.priority;
            if (sortBy === 'date') return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
            return 0;
        });
        
        return result;
    }, [tasks, filter, sortBy]);
    
    return (
        <ul>
            {processedTasks.map(task => <TaskCard key={task.id} task={task} />)}
        </ul>
    );
}
```

---

## 三、useCallback

`useCallback` 缓存 **函数引用**，避免父组件重新渲染时创建新的回调函数，导致子组件不必要的重新渲染。

```tsx
import { useCallback, memo } from 'react';

// 子组件使用 memo 包裹，只在 props 变化时重新渲染
const TaskCard = memo(function TaskCard({
    task,
    onComplete,
    onDelete,
}: {
    task: Task;
    onComplete: (id: number) => void;
    onDelete: (id: number) => void;
}) {
    console.log('TaskCard 渲染:', task.id);
    return (
        <div>
            <span>{task.title}</span>
            <button onClick={() => onComplete(task.id)}>完成</button>
            <button onClick={() => onDelete(task.id)}>删除</button>
        </div>
    );
});

// 父组件
function TaskList() {
    const [tasks, setTasks] = useState<Task[]>([]);
    
    // ✅ useCallback 缓存函数，tasks 变化时才创建新函数
    const handleComplete = useCallback((id: number) => {
        setTasks(prev => prev.map(t =>
            t.id === id ? { ...t, status: 'completed' } : t
        ));
    }, []); // 使用函数式更新，不依赖 tasks
    
    const handleDelete = useCallback((id: number) => {
        setTasks(prev => prev.filter(t => t.id !== id));
    }, []);
    
    return (
        <div>
            {tasks.map(task => (
                <TaskCard
                    key={task.id}
                    task={task}
                    onComplete={handleComplete}
                    onDelete={handleDelete}
                />
            ))}
        </div>
    );
}
```

### useMemo vs useCallback

```tsx
// useMemo — 缓存值
const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);

// useCallback — 缓存函数（是 useMemo 的语法糖）
const memoizedFn = useCallback((id: number) => { ... }, [deps]);
// 等价于
const memoizedFn = useMemo(() => (id: number) => { ... }, [deps]);
```

---

## 四、useReducer

适合 **复杂状态逻辑**，类似 Redux 的 reducer 模式。

```tsx
import { useReducer } from 'react';

// 状态类型
interface TaskState {
    tasks: Task[];
    loading: boolean;
    error: string | null;
    filter: string;
}

// Action 类型
type TaskAction =
    | { type: 'FETCH_START' }
    | { type: 'FETCH_SUCCESS'; payload: Task[] }
    | { type: 'FETCH_ERROR'; payload: string }
    | { type: 'ADD_TASK'; payload: Task }
    | { type: 'UPDATE_TASK'; payload: { id: number; updates: Partial<Task> } }
    | { type: 'DELETE_TASK'; payload: number }
    | { type: 'SET_FILTER'; payload: string };

// Reducer 函数
function taskReducer(state: TaskState, action: TaskAction): TaskState {
    switch (action.type) {
        case 'FETCH_START':
            return { ...state, loading: true, error: null };
        
        case 'FETCH_SUCCESS':
            return { ...state, loading: false, tasks: action.payload };
        
        case 'FETCH_ERROR':
            return { ...state, loading: false, error: action.payload };
        
        case 'ADD_TASK':
            return { ...state, tasks: [action.payload, ...state.tasks] };
        
        case 'UPDATE_TASK':
            return {
                ...state,
                tasks: state.tasks.map(t =>
                    t.id === action.payload.id ? { ...t, ...action.payload.updates } : t
                ),
            };
        
        case 'DELETE_TASK':
            return { ...state, tasks: state.tasks.filter(t => t.id !== action.payload) };
        
        case 'SET_FILTER':
            return { ...state, filter: action.payload };
        
        default:
            return state;
    }
}

// 使用
function TaskPage() {
    const [state, dispatch] = useReducer(taskReducer, {
        tasks: [],
        loading: false,
        error: null,
        filter: 'all',
    });
    
    useEffect(() => {
        dispatch({ type: 'FETCH_START' });
        fetch('/api/v1/tasks/')
            .then(res => res.json())
            .then(data => dispatch({ type: 'FETCH_SUCCESS', payload: data.results }))
            .catch(err => dispatch({ type: 'FETCH_ERROR', payload: err.message }));
    }, []);
    
    const handleComplete = (id: number) => {
        dispatch({ type: 'UPDATE_TASK', payload: { id, updates: { status: 'completed' } } });
    };
    
    const handleDelete = (id: number) => {
        dispatch({ type: 'DELETE_TASK', payload: id });
    };
    
    return <div>...</div>;
}
```

### useState vs useReducer

| 场景 | 推荐 |
|------|------|
| 简单状态（字符串、数字、布尔） | `useState` |
| 独立的状态值 | `useState` |
| 复杂状态逻辑（多个相关联的值） | `useReducer` |
| 下一个状态依赖前一个状态 | `useReducer` |
| 多种更新操作（增删改查） | `useReducer` |

---

## 五、练习

1. 使用 `useRef` 实现输入框自动聚焦
2. 使用 `useRef` 实现一个计时器（开始/停止/重置）
3. 使用 `useMemo` 缓存任务统计数据和排序结果
4. 使用 `useCallback` + `memo` 优化任务列表渲染
5. 使用 `useReducer` 重构任务管理状态（加载/成功/失败/增删改查）
