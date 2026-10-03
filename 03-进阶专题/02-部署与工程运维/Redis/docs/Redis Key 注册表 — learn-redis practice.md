> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# Redis Key 注册表 — learn-redis practice

> 模板文档，团队协作规范见 [`09_team_collaboration.md`](<../09-第9课团队协作规范与 Key 治理.md>)

## 实例

| 环境 | REDIS_URL | 说明 |
|------|-----------|------|
| local | `redis://localhost:6379/0` | `practice/docker-compose.yml` → 容器 `learn-redis` |

## DB 分配

| DB | 用途 |
|----|------|
| 0 | 业务：cache、session、ratelimit、health |
| 1 | Celery broker（若启用） |
| 2 | Celery result（若启用） |

## Key 清单

| Pattern | 类型 | TTL | 写入方 | 说明 |
|---------|------|-----|--------|------|
| `{p}:cache:article:{id}` | String (JSON) | 300s | GET/POST /articles | 文章详情缓存 |
| `{p}:session:{session_id}` | String (JSON) | 86400s | POST /auth/login | 登录 Session |
| `{p}:ratelimit:{ip}:{path}` | ZSet | 60s | 中间件 | 滑动窗口限流 |
| `_health` | String | 5s | GET /health | 健康检查探针 |

`{p}` = `REDIS_KEY_PREFIX`，默认 `myapp` 或 `dev:yourname:myapp`。

## 变更流程

1. 新增 key → 更新本表 → PR review
2. 禁止未文档化的 `FLUSHALL` / 生产 `FLUSHDB`
