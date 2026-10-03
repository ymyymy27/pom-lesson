> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# API 设计原则

## 1. API First 设计

```
传统：写代码 → 自动生成 API 文档（代码驱动）
API First：先设计 API 规范 → Review → 再写代码（契约驱动）

工具：OpenAPI (Swagger) / AsyncAPI

流程：
  1. 写 openapi.yaml 定义所有 endpoint
  2. 前后端/客户端 Review 达成一致
  3. 用工具生成 Server Stub / Client SDK
  4. 并行开发（Mock Server 让前端不阻塞）
```

---

## 2. RESTful 核心原则

```
1. 资源导向（Resources）
   URL 表示资源（名词），不是动作（动词）
   ✅ GET /tasks/123
   ❌ GET /getTask?id=123

2. HTTP 动词语义
   GET    — 读取（安全、幂等）
   POST   — 创建（非幂等）
   PUT    — 全量更新（幂等）
   PATCH  — 部分更新
   DELETE — 删除（幂等）

3. 状态码语义
   200 OK          — 成功
   201 Created     — 创建成功
   204 No Content  — 删除成功
   400 Bad Request — 客户端参数错误
   401 Unauthorized — 未认证
   403 Forbidden   — 无权限
   404 Not Found   — 资源不存在
   409 Conflict    — 冲突（重复创建）
   422 Unprocessable — 验证失败
   429 Too Many Requests — 限流
   500 Internal Server Error — 服务端错误

4. 无状态（Stateless）
   每个请求包含完整上下文（Token），服务端不存 Session
```

---

## 3. URL 设计规范

```
# 资源集合
GET    /api/v1/projects              # 列表
POST   /api/v1/projects              # 创建
GET    /api/v1/projects/{id}         # 详情
PUT    /api/v1/projects/{id}         # 更新
DELETE /api/v1/projects/{id}         # 删除

# 嵌套资源（浅层嵌套，最多 2 层）
GET    /api/v1/projects/{id}/tasks   # 项目下的任务
POST   /api/v1/projects/{id}/tasks   # 在项目下创建任务

# 过滤、排序、分页（Query Parameter）
GET /api/v1/tasks?status=todo&sort=-created_at&page=2&limit=20

# 动作（非 CRUD 时用子资源）
POST /api/v1/tasks/{id}/assign       # 分配任务
POST /api/v1/orders/{id}/cancel      # 取消订单
```

---

## 4. API 设计 Checklist

```
命名：
  □ URL 用复数名词（/tasks 不是 /task）
  □ 小写 + 连字符（/task-comments）
  □ 版本在 URL 或 Header 中（/api/v1/）

请求/响应：
  □ 统一响应格式（data + meta + errors）
  □ 分页用 cursor 而非 offset
  □ 日期用 ISO 8601（2026-07-30T10:00:00Z）
  □ ID 用 string 或 UUID（不用自增 int 暴露业务量）

安全：
  □ HTTPS
  □ 认证（Bearer Token）
  □ Rate Limiting
  □ 输入验证

文档：
  □ OpenAPI 规范
  □ 每个 endpoint 有示例
  □ 错误码说明

演进：
  □ 版本策略明确
  □ 向后兼容（加字段 OK，删/改字段需新版本）
  □ 废弃通知（Deprecation Header）
```

---

**下一课** → [01_rest_design.md](<01-第1课REST API 最佳实践.md>)
