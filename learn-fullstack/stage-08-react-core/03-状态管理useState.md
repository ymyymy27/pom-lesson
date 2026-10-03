# 第 03 节：状态管理 useState

## 一、什么是状态？

状态（State）是组件内部的 **可变数据**。当状态改变时，React 会自动 **重新渲染** 组件，更新 UI。

```
Props — 外部传入，组件不能修改（只读）
State — 组件内部管理，可以修改（触发重新渲染）
```

---

## 二、useState 基础

```tsx
import { useState } from 'react';

function Counter() {
    // useState 返回 [当前值, 设置函数]
    const [count, setCount] = useState(0);  // 初始值为 0
    
    return (
        <div>
            <p>计数：{count}</p>
            <button onClick={() => setCount(count + 1)}>+1</button>
            <button onClick={() => setCount(count - 1)}>-1</button>
            <button onClick={() => setCount(0)}>重置</button>
        </div>
    );
}
```

### 2.1 不同类型的状态

```tsx
function TaskForm() {
    // 字符串
    const [title, setTitle] = useState('');
    
    // 数字
    const [priority, setPriority] = useState(0);
    
    // 布尔值
    const [isUrgent, setIsUrgent] = useState(false);
    
    // 对象
    const [task, setTask] = useState<Task>({
        title: '',
        description: '',
        status: 'pending',
        priority: 0,
    });
    
    // 数组
    const [tags, setTags] = useState<string[]>([]);
    
    // null 联合类型
    const [selectedTask, setSelectedTask] = useState<Task | null>(null);
    
    return <div>...</div>;
}
```

---

## 三、状态更新规则

### 3.1 对象状态更新

```tsx
// ❌ 直接修改对象（不会触发重新渲染）
task.title = '新标题';
setTask(task);

// ✅ 创建新对象（展开运算符）
setTask({ ...task, title: '新标题' });
setTask({ ...task, priority: 8, status: 'in_progress' });

// ✅ 嵌套对象
const [user, setUser] = useState({
    name: '张三',
    profile: { bio: '', phone: '' },
});
setUser({
    ...user,
    profile: { ...user.profile, bio: '前端开发者' },
});
```

### 3.2 数组状态更新

```tsx
const [tasks, setTasks] = useState<Task[]>([]);

// 添加元素
setTasks([...tasks, newTask]);           // 末尾添加
setTasks([newTask, ...tasks]);           // 开头添加

// 删除元素
setTasks(tasks.filter(t => t.id !== taskId));

// 更新元素
setTasks(tasks.map(t => 
    t.id === taskId ? { ...t, status: 'completed' } : t
));

// 排序（创建新数组再排序）
setTasks([...tasks].sort((a, b) => b.priority - a.priority));
```

### 3.3 函数式更新

当新状态依赖旧状态时，使用函数式更新确保正确。

```tsx
// ❌ 可能有问题（闭包陈旧值）
setCount(count + 1);
setCount(count + 1); // 两次调用，但只 +1

// ✅ 函数式更新（总是基于最新值）
setCount(prev => prev + 1);
setCount(prev => prev + 1); // 正确 +2

// 数组
setTasks(prev => [...prev, newTask]);
setTasks(prev => prev.filter(t => t.id !== id));
```

---

## 四、表单处理

### 4.1 受控组件

```tsx
function CreateTaskForm({ onSubmit }: { onSubmit: (data: CreateTaskData) => void }) {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        priority: 0,
        status: 'pending' as const,
    });
    
    const handleChange = (
        e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
    ) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: name === 'priority' ? Number(value) : value,
        }));
    };
    
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.title.trim()) return;
        onSubmit(formData);
        // 重置表单
        setFormData({ title: '', description: '', priority: 0, status: 'pending' });
    };
    
    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="block text-sm font-medium">标题</label>
                <input
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    className="mt-1 block w-full rounded border-gray-300 shadow-sm"
                    placeholder="任务标题"
                    required
                />
            </div>
            
            <div>
                <label className="block text-sm font-medium">描述</label>
                <textarea
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    rows={3}
                    className="mt-1 block w-full rounded border-gray-300 shadow-sm"
                />
            </div>
            
            <div>
                <label className="block text-sm font-medium">优先级</label>
                <input
                    type="range"
                    name="priority"
                    value={formData.priority}
                    onChange={handleChange}
                    min={0}
                    max={10}
                    className="mt-1 w-full"
                />
                <span className="text-sm text-gray-500">{formData.priority}</span>
            </div>
            
            <div>
                <label className="block text-sm font-medium">状态</label>
                <select
                    name="status"
                    value={formData.status}
                    onChange={handleChange}
                    className="mt-1 block w-full rounded border-gray-300 shadow-sm"
                >
                    <option value="pending">待办</option>
                    <option value="in_progress">进行中</option>
                </select>
            </div>
            
            <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
                创建任务
            </button>
        </form>
    );
}
```

---

## 五、状态提升

当多个组件需要共享状态时，将状态 **提升到共同的父组件**。

```tsx
function TaskPage() {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [filter, setFilter] = useState<string>('all');
    
    const filteredTasks = tasks.filter(task => {
        if (filter === 'all') return true;
        return task.status === filter;
    });
    
    const handleCreate = (data: CreateTaskData) => {
        const newTask: Task = { id: Date.now(), ...data, createdAt: new Date().toISOString() };
        setTasks(prev => [newTask, ...prev]);
    };
    
    const handleComplete = (id: number) => {
        setTasks(prev => prev.map(t =>
            t.id === id ? { ...t, status: 'completed' } : t
        ));
    };
    
    const handleDelete = (id: number) => {
        setTasks(prev => prev.filter(t => t.id !== id));
    };
    
    return (
        <div className="flex gap-6">
            <div className="w-64">
                {/* 过滤器更新父组件状态 */}
                <StatusFilter value={filter} onChange={setFilter} />
                <TaskStats tasks={tasks} />
            </div>
            <div className="flex-1 space-y-4">
                <CreateTaskForm onSubmit={handleCreate} />
                <TaskList
                    tasks={filteredTasks}
                    onComplete={handleComplete}
                    onDelete={handleDelete}
                />
            </div>
        </div>
    );
}
```

---

## 六、练习

1. 创建 `Counter` 组件，实现 +1、-1、重置功能
2. 创建 `CreateTaskForm` 受控表单组件，包含标题、描述、优先级、状态
3. 实现任务列表：添加任务、完成任务、删除任务
4. 实现状态过滤器：按 all / pending / completed 过滤
5. 练习状态提升：将任务列表状态提升到父组件
