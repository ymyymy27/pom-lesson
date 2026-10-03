> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# API 设计全景

## 1. API 设计是什么？

### 一句话解释

**API 是系统对外的「契约」** —— 定义客户端能做什么、数据长什么样、出错时怎么反馈。

### API 在架构中的位置

```
┌─────────────┐
│   Client    │  Web / Mobile / 第三方
└──────┬──────┘
       │ HTTP / gRPC / WebSocket
       ▼
┌─────────────┐
│  API Layer  │  ← 本模块关注点：接口设计
│ (Controller)│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Application │  用例编排
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Domain    │  业务规则
└─────────────┘
```

**好 API 的特征：** 一致、可预测、自描述、向后兼容。

---

## 2. API 风格对比

| 风格 | 特点 | 适用 |
|------|------|------|
| REST | 资源 + HTTP 动词 | 大多数 CRUD 业务 API |
| GraphQL | 客户端定制查询 | 复杂前端、多端差异大 |
| gRPC | 二进制、强类型、流 | 微服务内部通信 |
| WebSocket | 双向实时 | 聊天、通知、协作 |
| Webhook | 事件回调 | 集成第三方 |

**本模块侧重 REST**，因为最通用；GraphQL/gRPC 在架构课中按需引入。

---

## 3. REST 核心约束（Richardson 成熟度）

```
Level 0：单一 URL + POST（RPC 风格）
Level 1：多资源 URL
Level 2：HTTP 动词（GET/POST/PUT/PATCH/DELETE）
Level 3：HATEOAS（链接驱动，实际较少用）

目标：至少 Level 2
```

### 资源 vs 动作

```
❌ RPC 风格
POST /createTask
POST /deleteUser
GET  /getOrderById?id=123

✅ REST 风格
POST   /tasks          创建任务
DELETE /users/{id}     删除用户
GET    /orders/{id}    获取订单
```

**规则：** URL 是名词（资源），动词由 HTTP Method 表达。

---

## 4. API 设计流程

```
1. 识别资源（从领域模型出发）
   Task, Project, User, Comment, Notification

2. 定义关系
   Project has many Tasks
   Task has many Comments

3. 设计 CRUD + 特殊操作
   特殊操作用子资源或 Action：
   POST /tasks/{id}/assign
   POST /tasks/{id}/transitions  （状态流转）

4. 定义请求/响应 Schema
   用 OpenAPI / JSON Schema

5. 统一错误格式、分页、认证

6. Review：一致性、安全性、扩展性
```

---

## 5. TaskFlow 资源模型示例

```
/users
/users/{id}
/users/{id}/projects          # 用户参与的项目

/projects
/projects/{id}
/projects/{id}/members         # 项目成员
/projects/{id}/tasks           # 项目下的任务

/tasks
/tasks/{id}
/tasks/{id}/comments
/tasks/{id}/attachments
/tasks/{id}/transitions        # 状态变更

/notifications                 # 当前用户的通知
/notifications/{id}/read
```

---

## 6. HTTP 状态码速查

| 码 | 含义 | 何时用 |
|----|------|--------|
| 200 | OK | GET/PUT/PATCH 成功 |
| 201 | Created | POST 创建成功 |
| 204 | No Content | DELETE 成功 |
| 400 | Bad Request | 参数校验失败 |
| 401 | Unauthorized | 未登录 / Token 无效 |
| 403 | Forbidden | 已登录但无权限 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 业务冲突（重复创建） |
| 422 | Unprocessable | 语义错误（状态不允许） |
| 429 | Too Many Requests | 限流 |
| 500 | Internal Error | 服务端 bug |
| 503 | Unavailable | 服务降级/维护 |

**原则：** 精确使用状态码，不要一切 200 或一切 500。

---

## 7. 统一响应格式

### 成功

```json
{
  "data": {
    "id": "task_abc123",
    "title": "完成 API 设计文档",
    "status": "in_progress"
  },
  "meta": {
    "request_id": "req_xyz789"
  }
}
```

### 错误

```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with id task_abc123 not found",
    "details": []
  },
  "meta": {
    "request_id": "req_xyz789"
  }
}
```

### 列表 + 分页

```json
{
  "data": [ ... ],
  "pagination": {
    "cursor": "eyJpZCI6MTIzfQ",
    "has_more": true,
    "total": 156
  }
}
```

**规则：**
- `code` 机器可读，前端/i18n 映射
- `message` 人类可读，可展示
- 始终带 `request_id` 便于排查

---

## 8. API 设计坏味道

| 坏味道 | 表现 | 改进 |
|--------|------|------|
| 动词 URL | `/getUserList` | `/users` |
| 不一致命名 | `/users` + `/project-list` | 统一复数 snake/camel |
| 泄露实现 | `/tables/orders/rows/1` | `/orders/1` |
| 过度嵌套 | `/a/b/c/d/e/f` | 最多 2-3 层，其余用 query |
| 无版本 | 改字段 break 客户端 | `/v1/` 或 Header |
| 无文档 | 口口相传 | OpenAPI spec |

---

## 9. 学习路线

```
00_api_design_overview.md（本文）
        ↓
01_rest_api_best_practices.md — REST 最佳实践
        ↓
02_api_versioning_and_contracts.md — 版本与契约
        ↓
learn-security/01_auth_and_access_control.md — API 安全
```

---

## 10. 自检清单

- [ ] 能区分 REST 与 RPC 风格 API
- [ ] 知道 Richardson 成熟度 Level 0-2
- [ ] 能从领域模型识别 API 资源
- [ ] 掌握常用 HTTP 状态码
- [ ] 能设计统一的成功/错误响应格式

---

**下一课** → [01_rest_api_best_practices.md](<01-第1课REST API 最佳实践.md>)
