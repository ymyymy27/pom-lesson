# TaskFlow — 任务协作平台

贯穿全栈课程的实战项目。随各阶段学习进度，逐步构建用户系统、项目管理、任务分配、实时通知等完整功能。

## 项目结构

```
taskflow/
├── backend/          # Django + DRF 后端
├── frontend/         # React + TypeScript 前端
└── docker-compose.yml
```

## 里程碑

| 阶段 | 能力 |
|------|------|
| 02 | 数据库表结构设计 |
| 03–04 | Django 模型与 REST API |
| 05 | JWT 认证与用户系统 |
| 06 | Celery 异步任务与 Redis 缓存 |
| 07–09 | React 前端界面 |
| 10 | 前后端联调 |
| 11–14 | 测试、容器化、CI/CD、监控 |

## 快速启动

```bash
# 启动基础设施（PostgreSQL + Redis）
docker compose up -d

# 后端（阶段 03 起逐步完善）
cd backend

# 前端（阶段 07 起逐步完善）
cd frontend
```

详见各阶段 README 中的实战说明。
