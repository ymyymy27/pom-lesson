> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 03 节：JavaScript ES6+

## 一、变量声明

```javascript
// let — 块级作用域，可重新赋值
let count = 0;
count = 1;

// const — 块级作用域，不可重新赋值（推荐优先使用）
const API_URL = 'http://localhost:8000/api/v1';
const user = { name: '张三' };
user.name = '李四';  // ✅ 对象属性可以修改
// user = {};         // ❌ 不能重新赋值

// var — 函数作用域（不推荐，有变量提升问题）
```

**规则：** 优先用 `const`，需要重新赋值时用 `let`，不用 `var`。

---

## 二、数据类型

```javascript
// 基本类型
const str = 'hello';           // string
const num = 42;                // number
const bool = true;             // boolean
const nothing = null;          // null
const notDefined = undefined;  // undefined
const big = 9007199254740991n; // bigint
const sym = Symbol('id');      // symbol

// 引用类型
const arr = [1, 2, 3];
const obj = { name: '张三', age: 25 };
const fn = () => console.log('hi');

// 类型检查
typeof str    // 'string'
typeof num    // 'number'
typeof bool   // 'boolean'
typeof obj    // 'object'
typeof arr    // 'object' — 数组也是对象
Array.isArray(arr)  // true
```

---

## 三、模板字符串

```javascript
const name = '张三';
const task = { id: 1, title: '学习React' };

// 模板字符串（反引号 ``）
const greeting = `你好，${name}！`;
const message = `任务 #${task.id}: ${task.title}`;

// 多行字符串
const html = `
  <div class="task-card">
    <h3>${task.title}</h3>
    <span>ID: ${task.id}</span>
  </div>
`;

// 表达式
const status = `状态: ${task.completed ? '已完成' : '待办'}`;
```

---

## 四、解构赋值

```javascript
// ===== 数组解构 =====
const [first, second, ...rest] = [1, 2, 3, 4, 5];
// first=1, second=2, rest=[3,4,5]

const [a, , c] = [1, 2, 3]; // 跳过第二个: a=1, c=3

// 默认值
const [x = 0, y = 0] = [10]; // x=10, y=0

// 交换变量
let p = 1, q = 2;
[p, q] = [q, p]; // p=2, q=1

// ===== 对象解构 =====
const user = { name: '张三', email: 'zs@example.com', age: 25 };

const { name, email } = user;
// name='张三', email='zs@example.com'

// 重命名
const { name: userName, email: userEmail } = user;

// 默认值
const { phone = '未填写' } = user;

// 嵌套解构
const response = {
    data: {
        user: { id: 1, name: '张三' },
        token: 'abc123',
    },
    status: 200,
};
const { data: { user: { id }, token }, status } = response;
// id=1, token='abc123', status=200

// ===== 函数参数解构 =====
function createTask({ title, priority = 0, tags = [] }) {
    console.log(title, priority, tags);
}
createTask({ title: '新任务', priority: 8 });
```

---

## 五、展开运算符与剩余参数

```javascript
// ===== 展开运算符 (...) =====

// 数组展开
const arr1 = [1, 2, 3];
const arr2 = [4, 5, 6];
const merged = [...arr1, ...arr2];  // [1,2,3,4,5,6]
const copy = [...arr1];             // 浅拷贝

// 对象展开
const defaults = { priority: 0, status: 'pending' };
const task = { ...defaults, title: '新任务', priority: 8 };
// { priority: 8, status: 'pending', title: '新任务' }

// 对象浅拷贝 + 修改
const updatedUser = { ...user, name: '李四' };

// ===== 剩余参数 (...) =====
function sum(...numbers) {
    return numbers.reduce((acc, n) => acc + n, 0);
}
sum(1, 2, 3, 4); // 10

function logTask(id, ...tags) {
    console.log(`Task #${id}, Tags: ${tags.join(', ')}`);
}
logTask(1, 'Bug', 'Urgent'); // Task #1, Tags: Bug, Urgent
```

---

## 六、箭头函数

```javascript
// 传统函数
function add(a, b) {
    return a + b;
}

// 箭头函数
const add = (a, b) => a + b;

// 单参数可省略括号
const double = n => n * 2;

// 多行需要花括号和 return
const createTask = (title, priority) => {
    const task = { title, priority, status: 'pending' };
    return task;
};

// 返回对象需要加括号
const getUser = () => ({ name: '张三', age: 25 });

// 数组方法中最常用
const tasks = [
    { id: 1, title: '任务1', priority: 8 },
    { id: 2, title: '任务2', priority: 3 },
    { id: 3, title: '任务3', priority: 6 },
];

// filter — 过滤
const urgent = tasks.filter(t => t.priority >= 5);

// map — 转换
const titles = tasks.map(t => t.title);

// find — 查找
const task = tasks.find(t => t.id === 2);

// sort — 排序
const sorted = [...tasks].sort((a, b) => b.priority - a.priority);

// reduce — 累计
const totalPriority = tasks.reduce((sum, t) => sum + t.priority, 0);

// some / every
const hasUrgent = tasks.some(t => t.priority >= 8);    // true
const allUrgent = tasks.every(t => t.priority >= 8);   // false

// forEach — 遍历
tasks.forEach(t => console.log(t.title));
```

---

## 七、对象简写与计算属性

```javascript
// 属性简写
const name = '张三';
const age = 25;
const user = { name, age };  // 等价于 { name: name, age: age }

// 方法简写
const task = {
    title: '学习JS',
    complete() {                // 等价于 complete: function() {}
        this.status = 'done';
    },
};

// 计算属性名
const field = 'status';
const update = {
    [field]: 'completed',       // { status: 'completed' }
    [`${field}_time`]: new Date(), // { status_time: ... }
};
```

---

## 八、可选链与空值合并

```javascript
// ===== 可选链 (?.) =====
const user = { profile: { avatar: 'url' } };
const avatar = user?.profile?.avatar;    // 'url'
const phone = user?.profile?.phone;      // undefined（不会报错）
const city = user?.address?.city;        // undefined

// 方法调用
user.getProfile?.();  // 如果方法存在则调用

// 数组访问
const first = arr?.[0];

// ===== 空值合并 (??) =====
// 只在值为 null 或 undefined 时使用默认值
const priority = task.priority ?? 0;     // 0 如果 priority 是 null/undefined
const name = user.name ?? '匿名';

// 对比 ||（会把 0、''、false 也当作假值）
const count = 0;
count || 10;   // 10 ← 不是我们想要的
count ?? 10;   // 0  ← 正确
```

---

## 九、模块系统

```javascript
// ===== 导出 =====
// utils.js
export const API_URL = 'http://localhost:8000/api/v1';

export function formatDate(date) {
    return new Date(date).toLocaleDateString('zh-CN');
}

export class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
}

// 默认导出（每个文件只能有一个）
export default function fetchTasks() { ... }

// ===== 导入 =====
// app.js
import fetchTasks from './utils.js';                    // 默认导出
import { API_URL, formatDate, ApiClient } from './utils.js'; // 命名导出
import fetchTasks, { API_URL } from './utils.js';       // 混合导入
import * as utils from './utils.js';                     // 全部导入
import { formatDate as fmt } from './utils.js';          // 重命名
```

---

## 十、类

```javascript
class Task {
    // 私有字段
    #id;
    
    constructor(title, priority = 0) {
        this.#id = Date.now();
        this.title = title;
        this.priority = priority;
        this.status = 'pending';
    }
    
    get id() {
        return this.#id;
    }
    
    complete() {
        this.status = 'completed';
    }
    
    toString() {
        return `[${this.status}] ${this.title} (P${this.priority})`;
    }
    
    // 静态方法
    static createUrgent(title) {
        return new Task(title, 10);
    }
}

// 继承
class BugTask extends Task {
    constructor(title, severity) {
        super(title, 10);  // 调用父类构造函数
        this.severity = severity;
        this.type = 'bug';
    }
}

const task = new Task('学习JS', 8);
const bug = BugTask.createUrgent('登录页崩溃');
```

---

## 十一、练习

1. 使用解构赋值从 API 响应中提取数据
2. 使用 `map`、`filter`、`sort` 处理任务列表：过滤高优先级、按优先级排序、提取标题
3. 使用展开运算符实现对象的浅拷贝和合并
4. 使用可选链和空值合并安全访问嵌套对象
5. 创建 `Task` 类，包含 `complete()`、`assign(user)` 方法
6. 使用 ES 模块导入导出，组织多个工具函数
