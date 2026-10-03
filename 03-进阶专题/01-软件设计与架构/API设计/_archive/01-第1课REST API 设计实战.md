> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第1课：REST API 设计实战

## 1. 统一响应格式

```json
// 成功
{
  "data": {
    "id": "task_abc123",
    "title": "Implement login",
    "status": "in_progress",
    "assignee": {"id": "user_42", "name": "Alice"},
    "created_at": "2026-07-30T10:00:00Z"
  },
  "meta": {
    "request_id": "req_xyz789"
  }
}

// 列表
{
  "data": [ ... ],
  "meta": {
    "cursor": "task_def456",
    "has_more": true,
    "total_count": 150
  }
}

// 错误
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Title is required",
    "details": [
      {"field": "title", "message": "must not be empty"}
    ]
  },
  "meta": {
    "request_id": "req_xyz789"
  }
}
```

---

## 2. 分页策略

### Offset 分页（简单但不推荐大规模）

```
GET /tasks?page=3&limit=20

问题：OFFSET 10000 时 DB 扫描 10000 行再返回 20 行
```

### Cursor 分页（推荐）

```
GET /tasks?cursor=task_abc123&limit=20

响应：
{
  "data": [...],
  "meta": {
    "next_cursor": "task_def456",
    "has_more": true
  }
}

实现：WHERE (created_at, id) < (cursor_created_at, cursor_id)
     ORDER BY created_at DESC, id DESC
     LIMIT 20
```

---

## 3. 版本策略

| 策略 | 示例 | 优点 | 缺点 |
|------|------|------|------|
| URL Path | `/api/v1/tasks` | 直观 | URL 变化 |
| Header | `Accept: application/vnd.api.v2+json` | URL 不变 | 不直观 |
| Query | `/api/tasks?version=2` | 简单 | 容易遗漏 |

**推荐：URL Path 版本 + 向后兼容**

```
兼容规则：
  ✅ 加新字段（旧客户端忽略）
  ✅ 加新 endpoint
  ❌ 删字段（需新版本）
  ❌ 改字段类型（需新版本）
  ❌ 改 URL 结构（需新版本）

废弃流程：
  1. v2 发布，v1 标记 deprecated
  2. 响应加 Header：Deprecation: true, Sunset: Sat, 01 Jan 2028
  3. 文档和 changelog 通知
  4. 6-12 个月后下线 v1
```

---

## 4. 资源建模示例（TaskFlow）

```yaml
# openapi.yaml 片段
paths:
  /api/v1/projects:
    get:
      summary: List projects
      parameters:
        - name: cursor
          in: query
        - name: limit
          in: query
          schema: { type: integer, default: 20, maximum: 100 }
      responses:
        200:
          description: Project list

  /api/v1/projects/{project_id}/tasks:
    post:
      summary: Create task
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [title]
              properties:
                title: { type: string, maxLength: 200 }
                description: { type: string }
                assignee_id: { type: string }
                priority: { type: string, enum: [low, medium, high] }
      responses:
        201:
          description: Task created
        422:
          description: Validation error
```

---

## 5. 动手练习

1. 为 TaskFlow 设计完整的 Tasks API（CRUD + 状态变更 + 分配）
2. 设计 cursor 分页的 API 和 DB 查询
3. 写一份 API 版本废弃通知模板

---

**下一课** → [02_api_patterns.md](<02-第2课API 高级模式.md>)
