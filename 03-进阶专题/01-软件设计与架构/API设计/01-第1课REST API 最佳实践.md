> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第1课：REST API 最佳实践

## 1. 资源命名规范

### 基本规则

```
✅ 复数名词：/users, /tasks, /projects
✅ 小写 + 连字符：/order-items（或 snake_case：/order_items）
✅ 层级表达从属：/projects/{id}/tasks
✅ 过滤/排序用 query：/tasks?status=done&sort=-created_at

❌ 动词：/createTask
❌ 单复混用：/user 和 /projects
❌ 文件扩展名：/users.json
❌ 大写：/Users
```

### 特殊操作：子资源 vs Action

```
状态流转（有副作用的业务动作）：

方案 A — 子资源（推荐）
POST /tasks/{id}/transitions
Body: { "to_status": "in_progress" }

方案 B — Action 动词（可接受，GitHub 风格）
POST /tasks/{id}/assign
Body: { "assignee_id": "user_123" }

避免：
POST /tasks/doAssign  ← 动词在 URL 根级
```

---

## 2. HTTP Method 语义

| Method | 幂等 | 安全 | 用途 |
|--------|------|------|------|
| GET | ✅ | ✅ | 查询，不改变状态 |
| POST | ❌ | ❌ | 创建资源、触发动作 |
| PUT | ✅ | ❌ | 全量替换 |
| PATCH | ❌* | ❌ | 部分更新 |
| DELETE | ✅ | ❌ | 删除 |

*PATCH 通常设计为幂等

### 示例：Task CRUD

```http
GET    /projects/{pid}/tasks           # 列表
GET    /tasks/{id}                     # 详情
POST   /projects/{pid}/tasks           # 创建
PATCH  /tasks/{id}                     # 更新部分字段
PUT    /tasks/{id}                     # 全量替换（少用）
DELETE /tasks/{id}                     # 删除（软删返回 204）
```

---

## 3. 查询：过滤、排序、分页

### 过滤

```
GET /tasks?status=in_progress
GET /tasks?assignee_id=user_123&priority=high
GET /tasks?created_after=2026-07-01
```

### 排序

```
GET /tasks?sort=created_at          # 升序
GET /tasks?sort=-created_at         # 降序（前缀 -）
GET /tasks?sort=priority,-created_at  # 多字段
```

### 分页

**Cursor 分页（推荐，大数据集）：**

```
GET /tasks?limit=20
GET /tasks?limit=20&cursor=eyJpZCI6MTIzfQ

Response:
{
  "data": [...],
  "pagination": {
    "cursor": "eyJpZCI6MTQ1fQ",
    "has_more": true
  }
}
```

**Offset 分页（简单场景）：**

```
GET /tasks?limit=20&offset=40

缺点：深分页性能差，数据漂移
适合：管理后台、数据量 < 10 万
```

### 字段选择（Sparse Fieldsets）

```
GET /tasks?fields=id,title,status
减少 payload，移动端友好
```

---

## 4. 请求体验设计

### 创建 Task

```http
POST /projects/proj_abc/tasks
Content-Type: application/json
Authorization: Bearer eyJ...

{
  "title": "完成 API 文档",
  "description": "REST 最佳实践章节",
  "assignee_id": "user_xyz",
  "priority": "high",
  "due_date": "2026-08-15",
  "tag_ids": ["tag_1", "tag_2"]
}
```

```http
HTTP/1.1 201 Created
Location: /tasks/task_new123

{
  "data": {
    "id": "task_new123",
    "title": "完成 API 文档",
    "status": "todo",
    "created_at": "2026-07-30T10:00:00Z",
    ...
  }
}
```

**要点：**
- 201 + `Location` header
- 返回完整创建后的资源
- 客户端不传 `id`、`status`（服务端生成）

### 部分更新

```http
PATCH /tasks/task_new123
{
  "priority": "low"
}

只更新指定字段，其他不变
```

---

## 5. 错误处理

### 校验错误（400）

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "title",
        "code": "REQUIRED",
        "message": "Title is required"
      },
      {
        "field": "due_date",
        "code": "INVALID_FORMAT",
        "message": "Expected ISO 8601 date"
      }
    ]
  }
}
```

### 业务冲突（409 / 422）

```json
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "Cannot transition from 'done' to 'in_progress'",
    "details": [
      {
        "field": "status",
        "current": "done",
        "requested": "in_progress",
        "allowed": []
      }
    ]
  }
}
```

### 错误码设计

```
格式：{DOMAIN}_{REASON}

TASK_NOT_FOUND
TASK_INVALID_STATE_TRANSITION
PROJECT_ACCESS_DENIED
USER_EMAIL_ALREADY_EXISTS
RATE_LIMIT_EXCEEDED
```

---

## 6. 批量操作

```
批量创建：
POST /tasks/batch
{ "tasks": [ {...}, {...} ] }

批量更新：
PATCH /tasks/batch
{ "ids": ["t1","t2"], "updates": { "status": "done" } }

异步批量（大量数据）：
POST /imports/tasks
→ 202 Accepted
{ "job_id": "job_abc", "status_url": "/jobs/job_abc" }
```

---

## 7. 关联资源与嵌入

```
# 默认：只返回 ID 引用
GET /tasks/task_123
{
  "id": "task_123",
  "assignee_id": "user_xyz",
  "project_id": "proj_abc"
}

# 嵌入关联（?include=）
GET /tasks/task_123?include=assignee,project
{
  "id": "task_123",
  "assignee": { "id": "user_xyz", "name": "Alice" },
  "project": { "id": "proj_abc", "name": "TaskFlow" }
}
```

**注意：** 控制嵌入深度，避免 N+1 和过大 payload。

---

## 8. Idempotency（幂等键）

```
POST 创建可能因网络重试重复执行

解决：客户端传 Idempotency-Key

POST /tasks
Idempotency-Key: uuid-generated-by-client

服务端：
  1. 查 key 是否已处理 → 返回之前结果
  2. 未处理 → 执行并存储 key + 结果
  3. key 有效期通常 24h
```

---

## 9. OpenAPI 快速入门

```yaml
openapi: 3.0.3
info:
  title: TaskFlow API
  version: 1.0.0

paths:
  /projects/{projectId}/tasks:
    post:
      summary: Create a task
      parameters:
        - name: projectId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateTaskRequest'
      responses:
        '201':
          description: Task created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Task'

components:
  schemas:
    CreateTaskRequest:
      type: object
      required: [title]
      properties:
        title:
          type: string
          maxLength: 200
        priority:
          type: string
          enum: [low, medium, high]
    Task:
      type: object
      properties:
        id:
          type: string
        title:
          type: string
        status:
          type: string
          enum: [todo, in_progress, review, done]
```

**工具：** Swagger UI、Redoc、Stoplight、FastAPI 自动生成

---

## 10. 动手练习

1. 为 TaskFlow 设计完整 endpoint 列表（至少 15 个）
2. 设计 Task 状态流转 API，含允许的状态转换矩阵
3. 写一份 OpenAPI spec（至少包含 Task CRUD + 分页）
4. 设计统一的错误响应格式，覆盖 5 种常见错误

---

## 11. 自检清单

- [ ] 资源命名符合 REST 规范
- [ ] 正确使用 HTTP Method 和状态码
- [ ] 能设计 cursor 分页和过滤参数
- [ ] 错误响应包含 code、message、details
- [ ] 了解幂等键的用途
- [ ] 能写基础 OpenAPI spec

---

**下一课** → [02_api_versioning_and_contracts.md](<02-第2课API 版本策略与契约管理.md>)
