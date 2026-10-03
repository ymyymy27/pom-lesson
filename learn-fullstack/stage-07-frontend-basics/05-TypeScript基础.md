# 第 05 节：TypeScript 基础

## 一、什么是 TypeScript？

TypeScript 是 JavaScript 的 **超集**，添加了 **静态类型系统**。代码在编译时检查类型错误，而不是在运行时才发现。

```typescript
// JavaScript — 运行时才发现错误
function add(a, b) {
    return a + b;
}
add('1', 2); // '12' — 字符串拼接，不是数学加法

// TypeScript — 编译时就报错
function add(a: number, b: number): number {
    return a + b;
}
add('1', 2); // ❌ 编译错误：类型 "string" 不能赋值给类型 "number"
```

### 1.1 为什么用 TypeScript？

- **编译时类型检查** — 减少运行时错误
- **IDE 智能提示** — 自动补全、跳转定义
- **代码即文档** — 类型定义说明了数据结构
- **重构安全** — 修改类型后，所有用到的地方都会报错
- **React 生态标配** — 大多数 React 项目都用 TypeScript

---

## 二、基础类型

```typescript
// 基本类型
let name: string = '张三';
let age: number = 25;
let isActive: boolean = true;
let nothing: null = null;
let notDefined: undefined = undefined;

// 数组
let numbers: number[] = [1, 2, 3];
let names: Array<string> = ['张三', '李四'];

// 元组（固定长度和类型的数组）
let pair: [string, number] = ['张三', 25];

// 枚举
enum TaskStatus {
    Pending = 'pending',
    InProgress = 'in_progress',
    Completed = 'completed',
    Cancelled = 'cancelled',
}
let status: TaskStatus = TaskStatus.Pending;

// any（尽量避免）
let data: any = 'hello';
data = 123; // 不报错，失去类型检查

// unknown（比 any 安全）
let input: unknown = 'hello';
// input.toUpperCase(); // ❌ 不能直接使用
if (typeof input === 'string') {
    input.toUpperCase(); // ✅ 类型收窄后可以使用
}

// void（函数无返回值）
function log(message: string): void {
    console.log(message);
}

// never（永远不会返回）
function throwError(message: string): never {
    throw new Error(message);
}
```

---

## 三、接口（Interface）

接口定义对象的 **形状**（有哪些属性、每个属性什么类型）。

```typescript
// 定义接口
interface User {
    id: number;
    username: string;
    email: string;
    avatar?: string;          // 可选属性
    readonly createdAt: string; // 只读属性
}

// 使用接口
const user: User = {
    id: 1,
    username: '张三',
    email: 'zs@example.com',
    createdAt: '2025-01-01',
};

// user.createdAt = '2025-06-01'; // ❌ 只读属性不能修改

// 函数参数和返回值
function getUser(id: number): User {
    return { id, username: '张三', email: 'zs@example.com', createdAt: '' };
}

// 接口继承
interface UserWithProfile extends User {
    bio: string;
    phone: string;
}
```

### 3.1 TaskFlow 接口定义

```typescript
// types/index.ts

interface Tag {
    id: number;
    name: string;
    color: string;
}

interface UserBrief {
    id: number;
    username: string;
    email: string;
    avatar?: string;
}

interface Project {
    id: number;
    name: string;
    description: string;
    owner: UserBrief;
    isArchived: boolean;
    createdAt: string;
}

interface Task {
    id: number;
    title: string;
    description: string;
    status: TaskStatus;
    priority: number;
    project: Project;
    assignee: UserBrief | null;
    creator: UserBrief;
    tags: Tag[];
    dueDate: string | null;
    createdAt: string;
    updatedAt: string;
}

// API 响应类型
interface PaginatedResponse<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}

interface ApiError {
    code: number;
    message: string;
    errors: Record<string, string[]>;
}

// 创建/更新请求类型
interface CreateTaskRequest {
    title: string;
    description?: string;
    priority?: number;
    project: number;
    assignee?: number;
    tags?: number[];
    dueDate?: string;
}

interface UpdateTaskRequest {
    title?: string;
    description?: string;
    status?: TaskStatus;
    priority?: number;
    assignee?: number | null;
    tags?: number[];
    dueDate?: string | null;
}
```

---

## 四、类型别名（Type）

```typescript
// type 关键字
type ID = number;
type StatusType = 'pending' | 'in_progress' | 'completed' | 'cancelled';

// 联合类型
type StringOrNumber = string | number;
let value: StringOrNumber = 'hello';
value = 42; // ✅

// 交叉类型
type Timestamped = {
    createdAt: string;
    updatedAt: string;
};

type TaskWithTimestamp = Task & Timestamped;

// 字面量类型
type Direction = 'up' | 'down' | 'left' | 'right';
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
```

### Interface vs Type

| 特性 | Interface | Type |
|------|-----------|------|
| 对象形状 | ✅ | ✅ |
| 继承/扩展 | `extends` | `&`（交叉类型） |
| 联合类型 | ❌ | ✅ `string \| number` |
| 声明合并 | ✅ | ❌ |
| 推荐场景 | 定义对象/类 | 联合类型、工具类型 |

---

## 五、泛型

泛型让类型 **参数化**，编写可复用的类型安全代码。

```typescript
// 泛型函数
function getFirst<T>(arr: T[]): T | undefined {
    return arr[0];
}

const firstNum = getFirst([1, 2, 3]);        // 推断为 number
const firstStr = getFirst(['a', 'b', 'c']);  // 推断为 string

// 泛型接口
interface ApiResponse<T> {
    code: number;
    message: string;
    data: T;
}

// 使用
type TaskListResponse = ApiResponse<Task[]>;
type TaskDetailResponse = ApiResponse<Task>;
type StatsResponse = ApiResponse<{
    total: number;
    pending: number;
    completed: number;
}>;

// 泛型约束
interface HasId {
    id: number;
}

function findById<T extends HasId>(items: T[], id: number): T | undefined {
    return items.find(item => item.id === id);
}

// 多个泛型参数
function mapArray<T, U>(arr: T[], fn: (item: T) => U): U[] {
    return arr.map(fn);
}

const titles = mapArray(tasks, task => task.title); // string[]
```

---

## 六、函数类型

```typescript
// 参数和返回值类型
function createTask(title: string, priority: number = 0): Task {
    // ...
}

// 箭头函数类型
const formatDate = (date: string): string => {
    return new Date(date).toLocaleDateString('zh-CN');
};

// 函数类型别名
type TaskFilter = (task: Task) => boolean;

const isUrgent: TaskFilter = (task) => task.priority >= 8;
const isPending: TaskFilter = (task) => task.status === TaskStatus.Pending;

// 可选参数和默认值
function getTasks(
    status?: TaskStatus,
    page: number = 1,
    pageSize: number = 20,
): Promise<PaginatedResponse<Task>> {
    // ...
}

// 回调函数类型
function fetchData(
    url: string,
    onSuccess: (data: unknown) => void,
    onError?: (error: Error) => void,
): void {
    // ...
}
```

---

## 七、类型工具

```typescript
// Partial<T> — 所有属性变为可选
type UpdateTask = Partial<Task>;

// Required<T> — 所有属性变为必填
type RequiredTask = Required<Task>;

// Pick<T, K> — 选取部分属性
type TaskBrief = Pick<Task, 'id' | 'title' | 'status' | 'priority'>;

// Omit<T, K> — 排除部分属性
type TaskWithoutTimestamps = Omit<Task, 'createdAt' | 'updatedAt'>;

// Record<K, V> — 键值对类型
type TaskStatusCount = Record<TaskStatus, number>;
// { pending: number, in_progress: number, completed: number, cancelled: number }

// Readonly<T> — 所有属性变为只读
type ReadonlyTask = Readonly<Task>;

// 实际使用
type CreateTaskDTO = Omit<Task, 'id' | 'createdAt' | 'updatedAt' | 'creator'>;
type UpdateTaskDTO = Partial<Pick<Task, 'title' | 'description' | 'status' | 'priority'>>;
```

---

## 八、类型收窄

```typescript
// typeof 收窄
function formatValue(value: string | number): string {
    if (typeof value === 'string') {
        return value.toUpperCase();    // 这里 value 是 string
    }
    return value.toFixed(2);           // 这里 value 是 number
}

// in 操作符收窄
interface Task { title: string; status: string; }
interface Project { name: string; isArchived: boolean; }

function getName(item: Task | Project): string {
    if ('title' in item) {
        return item.title;   // Task
    }
    return item.name;        // Project
}

// 自定义类型守卫
function isTask(item: Task | Project): item is Task {
    return 'title' in item;
}

if (isTask(item)) {
    console.log(item.title);   // TypeScript 知道这是 Task
}
```

---

## 九、练习

1. 为 TaskFlow 定义完整的 TypeScript 接口：`User`、`Task`、`Project`、`Tag`
2. 定义 API 响应泛型：`ApiResponse<T>` 和 `PaginatedResponse<T>`
3. 使用枚举定义 `TaskStatus`，使用联合类型定义 `HttpMethod`
4. 使用 `Partial`、`Pick`、`Omit` 创建 `CreateTaskRequest` 和 `UpdateTaskRequest`
5. 编写泛型函数 `findById<T extends HasId>(items: T[], id: number): T | undefined`
6. 为上一节的 `TaskFlowAPI` 类添加 TypeScript 类型注解
