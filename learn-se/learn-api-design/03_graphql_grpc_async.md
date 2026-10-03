# 第3课：GraphQL、gRPC 与 API 选型

## 1. 三种 API 风格对比

| 维度 | REST | GraphQL | gRPC |
|------|------|---------|------|
| 协议 | HTTP/JSON | HTTP/JSON | HTTP/2 + Protobuf |
| 数据获取 | 固定 endpoint | 客户端定制查询 | 强类型 RPC |
| 过度获取 | 常见 | 不存在 | 不存在 |
| 类型系统 | OpenAPI | Schema | .proto 文件 |
| 浏览器友好 | ✅ | ✅ | ❌（需 gRPC-Web） |
| 性能 | 中 | 中 | 高（二进制） |
| 学习曲线 | 低 | 中 | 中 |
| 适用 | 通用 CRUD | 复杂前端、BFF | 服务间通信 |

---

## 2. GraphQL

### 核心概念

```graphql
# Schema 定义
type Task {
  id: ID!
  title: String!
  status: TaskStatus!
  assignee: User
  comments: [Comment!]!
}

type Query {
  task(id: ID!): Task
  tasks(projectId: ID!, status: TaskStatus): [Task!]!
}

type Mutation {
  createTask(input: CreateTaskInput!): Task!
  updateTask(id: ID!, input: UpdateTaskInput!): Task!
}

# 客户端一次请求获取所需数据
query {
  task(id: "task_123") {
    title
    status
    assignee { name email }
    comments(last: 5) { text author { name } }
  }
}
```

### 何时选 GraphQL

```
✅ 前端需要灵活组合数据（移动端 vs Web 端需求不同）
✅ 多个 REST endpoint 经常一起调用（N+1 问题）
✅ 快速迭代的前端（字段自由添加）

❌ 简单 CRUD（REST 更简单）
❌ 文件上传（REST 更自然）
❌ 团队无 GraphQL 经验
❌ 需要 HTTP 缓存（GraphQL 都是 POST）
```

### GraphQL 陷阱

```
N+1 查询：comments 每个都查一次 DB
  → DataLoader 批量加载

深度限制：防止恶意嵌套查询
  → 限制 query 深度和复杂度

权限：每个 field 都需要授权检查
  → Field-level authorization
```

---

## 3. gRPC

### 核心概念

```protobuf
// task.proto
service TaskService {
  rpc GetTask(GetTaskRequest) returns (Task);
  rpc ListTasks(ListTasksRequest) returns (stream Task);
  rpc CreateTask(CreateTaskRequest) returns (Task);
}

message Task {
  string id = 1;
  string title = 2;
  TaskStatus status = 3;
}
```

### 何时选 gRPC

```
✅ 微服务间内部通信（高性能、强类型）
✅ 双向流（实时数据、聊天）
✅ 多语言服务（proto 生成各语言代码）

❌ 浏览器直接调用（需 gRPC-Web 代理）
❌ 公开 API（REST 更通用）
❌ 调试（二进制不如 JSON 直观）
```

---

## 4. 选型决策树

```
Q1: 谁调用？
  浏览器/移动端 → REST 或 GraphQL
  服务间内部   → gRPC 或 REST

Q2: 数据结构？
  固定、简单   → REST
  灵活组合     → GraphQL
  高性能二进制 → gRPC

Q3: 团队经验？
  无特殊经验   → REST（默认选择）
  有 GraphQL 经验 → 考虑 GraphQL
  微服务成熟   → 内部 gRPC + 外部 REST
```

### 常见组合

```
BFF 模式（Backend for Frontend）：
  Mobile App → GraphQL BFF → 内部 gRPC 服务
  Web App    → REST API   → 内部 gRPC 服务
  服务间      → gRPC

  对外 REST/GraphQL，对内 gRPC
```

---

## 5. 动手练习

1. 为 TaskFlow 选择 API 风格并写 ADR 说明理由
2. 用 GraphQL Schema 定义 Task + Project + Comment
3. 设计 BFF 模式下的 API 架构图

---

## 6. 自检清单

- [ ] 能对比 REST/GraphQL/gRPC 的适用场景
- [ ] 理解 GraphQL 的 N+1 问题和 DataLoader
- [ ] 知道 gRPC 适合服务间通信
- [ ] 会用决策树选择合适的 API 风格

---

**下一模块** → [learn-performance/](../learn-performance/)：性能工程
