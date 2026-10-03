# Redis DB 分配表 — 模板

> 深度说明见 [`07_logical_databases_and_isolation.md`](../07_logical_databases_and_isolation.md)

## 实例

| 环境 | Host | 端口 | 密码 | 备注 |
|------|------|------|------|------|
| dev | localhost | 6379 | 无 | Docker `learn-redis` |
| staging | — | — | — | 独立实例 |
| prod | — | — | — | 独立实例 + ACL |

## 逻辑库分配

| DB | 用途 | 负责方 | Key 前缀 | 禁止操作 |
|----|------|--------|----------|----------|
| 0 | 业务 cache / session / ratelimit | Backend | `{p}:*` | — |
| 1 | Celery broker | Platform | Celery 内部 | FLUSHDB |
| 2 | Celery result | Platform | Celery 内部 | FLUSHDB |
| 3–15 | 预留 | — | — | 未分配前禁止使用 |

## 禁止事项

- 禁止 `FLUSHALL`
- 禁止在生产执行 `KEYS *`
- 禁止未文档化占用新 db
- 禁止在连接池中动态 `SELECT`
