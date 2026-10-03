> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 02 节：组件与 Props

## 一、函数组件

React 中一切皆组件。函数组件就是一个 **接收 Props、返回 JSX** 的函数。

```tsx
// 最简组件
function Greeting() {
    return <h1>你好，世界！</h1>;
}

// 带 Props 的组件
interface GreetingProps {
    name: string;
    role?: string;  // 可选
}

function Greeting({ name, role = '成员' }: GreetingProps) {
    return <h1>你好，{name}（{role}）！</h1>;
}

// 使用
<Greeting name="张三" />
<Greeting name="李四" role="管理员" />
```

---

## 二、Props 详解

### 2.1 基础类型

```tsx
interface TaskCardProps {
    id: number;
    title: string;
    description?: string;          // 可选
    priority: number;
    isCompleted: boolean;
    tags: string[];
    assignee: { id: number; name: string } | null;
    onComplete: (id: number) => void;  // 回调函数
    onDelete?: (id: number) => void;   // 可选回调
}

function TaskCard({
    id,
    title,
    description = '',
    priority,
    isCompleted,
    tags,
    assignee,
    onComplete,
    onDelete,
}: TaskCardProps) {
    return (
        <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold">{title}</h3>
            {description && <p className="text-gray-500 text-sm mt-1">{description}</p>}
            
            <div className="flex gap-1 mt-2">
                {tags.map((tag) => (
                    <span key={tag} className="px-2 py-0.5 bg-gray-100 text-xs rounded">{tag}</span>
                ))}
            </div>
            
            <div className="flex justify-between items-center mt-3">
                <span className="text-sm text-gray-400">
                    {assignee ? assignee.name : '未分配'}
                </span>
                <div className="flex gap-2">
                    <button
                        onClick={() => onComplete(id)}
                        className="text-sm text-green-600 hover:underline"
                    >
                        {isCompleted ? '已完成' : '完成'}
                    </button>
                    {onDelete && (
                        <button
                            onClick={() => onDelete(id)}
                            className="text-sm text-red-600 hover:underline"
                        >
                            删除
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
```

### 2.2 children Props

```tsx
// 容器组件
interface CardProps {
    title: string;
    children: React.ReactNode;  // 任意 JSX 内容
    footer?: React.ReactNode;
}

function Card({ title, children, footer }: CardProps) {
    return (
        <div className="bg-white rounded-lg shadow">
            <div className="px-4 py-3 border-b">
                <h3 className="font-semibold">{title}</h3>
            </div>
            <div className="p-4">{children}</div>
            {footer && <div className="px-4 py-3 border-t bg-gray-50">{footer}</div>}
        </div>
    );
}

// 使用
<Card title="任务详情" footer={<button>保存</button>}>
    <p>这里是任务的详细内容...</p>
    <TaskForm />
</Card>
```

### 2.3 组件组合

```tsx
// 布局组件
function PageLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />
            <main className="max-w-7xl mx-auto px-4 py-8">
                {children}
            </main>
            <Footer />
        </div>
    );
}

function Sidebar({ children }: { children: React.ReactNode }) {
    return (
        <aside className="w-64 bg-white shadow-sm p-4">
            {children}
        </aside>
    );
}

// 页面组合
function TaskPage() {
    return (
        <PageLayout>
            <div className="flex gap-6">
                <Sidebar>
                    <ProjectList />
                    <TagFilter />
                </Sidebar>
                <div className="flex-1">
                    <TaskList />
                </div>
            </div>
        </PageLayout>
    );
}
```

---

## 三、事件处理

```tsx
function TaskCard({ task }: { task: Task }) {
    // 事件处理函数
    const handleClick = () => {
        console.log('点击了任务:', task.title);
    };
    
    const handleComplete = (e: React.MouseEvent<HTMLButtonElement>) => {
        e.stopPropagation();  // 阻止冒泡
        console.log('完成任务:', task.id);
    };
    
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        console.log('输入值:', e.target.value);
    };
    
    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();  // 阻止默认提交行为
        console.log('表单提交');
    };
    
    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            console.log('按了回车');
        }
    };
    
    return (
        <div onClick={handleClick} className="cursor-pointer">
            <h3>{task.title}</h3>
            <button onClick={handleComplete}>完成</button>
            <input onChange={handleInputChange} onKeyDown={handleKeyDown} />
            <form onSubmit={handleSubmit}>
                <button type="submit">提交</button>
            </form>
        </div>
    );
}
```

### 3.1 向子组件传递回调

```tsx
// 父组件
function TaskPage() {
    const handleTaskComplete = (taskId: number) => {
        console.log('完成任务:', taskId);
        // 更新状态...
    };
    
    const handleTaskDelete = (taskId: number) => {
        console.log('删除任务:', taskId);
    };
    
    return (
        <div>
            {tasks.map((task) => (
                <TaskCard
                    key={task.id}
                    task={task}
                    onComplete={handleTaskComplete}
                    onDelete={handleTaskDelete}
                />
            ))}
        </div>
    );
}

// 子组件
interface TaskCardProps {
    task: Task;
    onComplete: (id: number) => void;
    onDelete: (id: number) => void;
}

function TaskCard({ task, onComplete, onDelete }: TaskCardProps) {
    return (
        <div>
            <h3>{task.title}</h3>
            <button onClick={() => onComplete(task.id)}>完成</button>
            <button onClick={() => onDelete(task.id)}>删除</button>
        </div>
    );
}
```

---

## 四、练习

1. 创建 `TaskCard` 组件，接收任务数据和回调函数作为 Props
2. 创建 `Card` 容器组件，使用 `children` 和可选的 `footer`
3. 创建 `PageLayout` 布局组件，包含 Navbar + main + Footer
4. 实现父子组件通信：父组件传递回调，子组件调用回调通知父组件
5. 为所有 Props 添加 TypeScript 接口定义
