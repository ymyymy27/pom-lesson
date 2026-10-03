> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 01 节：React 入门与 JSX

## 一、什么是 React？

React 是 Facebook 开源的 **UI 构建库**，核心理念：

- **组件化** — 将 UI 拆分为独立、可复用的组件
- **声明式** — 描述"UI 应该是什么样"，React 负责更新 DOM
- **单向数据流** — 数据从父组件流向子组件（Props）

```
声明式 vs 命令式：

命令式（jQuery 风格）：
document.getElementById('count').innerHTML = count + 1;

声明式（React 风格）：
<span>{count}</span>  // 数据变了，UI 自动更新
```

---

## 二、JSX 语法

JSX 是 JavaScript 的语法扩展，在 JS 中写类似 HTML 的代码。

### 2.1 基础语法

```tsx
// JSX 会被编译为 React.createElement() 调用
const element = <h1>Hello, TaskFlow!</h1>;

// 等价于：
const element = React.createElement('h1', null, 'Hello, TaskFlow!');
```

### 2.2 表达式嵌入

```tsx
const name = '张三';
const task = { title: '学习React', priority: 8 };

function App() {
    return (
        <div>
            {/* 变量 */}
            <h1>你好，{name}！</h1>
            
            {/* 表达式 */}
            <p>优先级：{task.priority >= 8 ? '紧急' : '普通'}</p>
            
            {/* 函数调用 */}
            <p>当前时间：{new Date().toLocaleString()}</p>
            
            {/* 计算 */}
            <p>{2 + 3}</p>
        </div>
    );
}
```

### 2.3 JSX 规则

```tsx
function App() {
    const isLoggedIn = true;
    const tasks = ['任务1', '任务2', '任务3'];
    
    return (
        // 规则1：必须有一个根元素（或用 Fragment）
        <>
            {/* 规则2：HTML 属性用 camelCase */}
            <div className="container" tabIndex={0} onClick={handleClick}>
                {/* 规则3：style 用对象 */}
                <h1 style={{ color: 'red', fontSize: '24px' }}>标题</h1>
                
                {/* 规则4：所有标签必须闭合 */}
                <img src="logo.png" alt="logo" />
                <br />
                <input type="text" />
                
                {/* 规则5：条件渲染 */}
                {isLoggedIn && <p>欢迎回来！</p>}
                {isLoggedIn ? <UserMenu /> : <LoginButton />}
                
                {/* 规则6：列表渲染必须有 key */}
                <ul>
                    {tasks.map((task, index) => (
                        <li key={index}>{task}</li>
                    ))}
                </ul>
            </div>
        </>
    );
}
```

### 2.4 条件渲染

```tsx
function TaskStatus({ status }: { status: string }) {
    // 方式1：三元表达式
    return <span>{status === 'completed' ? '✅ 已完成' : '⏳ 进行中'}</span>;
    
    // 方式2：&& 短路
    // return <>{status === 'completed' && <span>✅ 已完成</span>}</>;
    
    // 方式3：提前 return
    // if (status === 'completed') return <span>✅ 已完成</span>;
    // return <span>⏳ 进行中</span>;
}

// 多条件
function StatusBadge({ status }: { status: string }) {
    const config: Record<string, { label: string; color: string }> = {
        pending: { label: '待办', color: 'bg-yellow-100 text-yellow-800' },
        in_progress: { label: '进行中', color: 'bg-blue-100 text-blue-800' },
        completed: { label: '已完成', color: 'bg-green-100 text-green-800' },
        cancelled: { label: '已取消', color: 'bg-red-100 text-red-800' },
    };
    
    const { label, color } = config[status] ?? { label: '未知', color: 'bg-gray-100' };
    
    return <span className={`px-2 py-1 rounded-full text-xs ${color}`}>{label}</span>;
}
```

### 2.5 列表渲染

```tsx
interface Task {
    id: number;
    title: string;
    status: string;
}

function TaskList({ tasks }: { tasks: Task[] }) {
    if (tasks.length === 0) {
        return <p className="text-gray-500">暂无任务</p>;
    }
    
    return (
        <ul className="space-y-2">
            {tasks.map((task) => (
                // key 必须是唯一且稳定的值，不要用 index
                <li key={task.id} className="p-3 bg-white rounded shadow">
                    <span>{task.title}</span>
                    <StatusBadge status={task.status} />
                </li>
            ))}
        </ul>
    );
}
```

---

## 三、第一个组件

```tsx
// src/App.tsx
function App() {
    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <h1 className="text-2xl font-bold text-gray-900">TaskFlow</h1>
                </div>
            </header>
            
            <main className="max-w-7xl mx-auto px-4 py-8">
                <h2 className="text-xl font-semibold mb-4">我的任务</h2>
                <TaskList tasks={[
                    { id: 1, title: '学习 React', status: 'in_progress' },
                    { id: 2, title: '搭建 API', status: 'completed' },
                    { id: 3, title: '编写测试', status: 'pending' },
                ]} />
            </main>
        </div>
    );
}

export default App;
```

---

## 四、练习

1. 创建一个 React 项目，修改 `App.tsx`，显示 "Hello, TaskFlow!"
2. 使用 JSX 表达式显示当前日期和一段动态文字
3. 创建 `StatusBadge` 组件，根据 status 显示不同颜色的标签
4. 创建 `TaskList` 组件，接收任务数组并渲染列表
5. 练习条件渲染：任务为空时显示"暂无任务"
6. 练习列表渲染：使用 `map` + `key` 渲染任务列表
