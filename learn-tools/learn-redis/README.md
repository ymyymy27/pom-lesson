# Redis 缓存与数据存储 从零开始学习教程

独立工具课，与 [`learn-docker`](../learn-docker/) 并列。Markdown 文档 + 终端动手练习，不依赖全栈课程进度。

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 参考 | `00_redis_syntax.md` | Redis 语法结构参考（CLI / 数据结构 / redis-py） |
| 第1课 | `01_redis_basics.md` | Redis 是什么、安装、核心概念（KV / 内存 / 持久化） |
| 第2课 | `02_data_structures.md` | 五大数据结构：String / Hash / List / Set / Sorted Set |
| 第3课 | `03_python_redis.md` | redis-py 连接、连接池、Pipeline、错误处理 |
| 第4课 | `04_caching_patterns.md` | 缓存模式、穿透/击穿/雪崩、Key 设计、TTL 策略 |
| 第5课 | `05_advanced_patterns.md` | Session、限流、分布式锁、Pub/Sub、Celery 消息队列 |
| 第6课 | `06_practical_web_app.md` | 实战：FastAPI + Redis（缓存 / 限流 / 会话 / 健康检查） |
| 第7课 | `07_logical_databases_and_isolation.md` | **逻辑库 db0–db15、隔离策略、实例规划** |
| 第8课 | `08_deployment_and_environments.md` | **部署架构、多环境配置、安全与持久化** |
| 第9课 | `09_team_collaboration.md` | **团队协作、Key 治理、框架共存** |
| 第10课 | `10_production_operations.md` | **生产运维、高可用、监控与故障处理** |

## 学习方式

- Markdown 文档 + 终端动手练习
- 需要先完成 [`learn-docker`](../learn-docker/) 第 1–3 课（用 Docker 运行 Redis）
- 每课都有可运行的示例命令或 Python 脚本
- 按顺序学习；第 1–6 课打基础与实战，**第 7–10 课为部署与协作必修**

## 环境准备

```bash
cd practice
docker compose up -d
docker exec -it learn-redis redis-cli PING   # 应返回 PONG（Windows 无需本机安装 redis-cli）
```

- **Python**: 3.11+
- **依赖**: `pip install redis fastapi uvicorn`

## 学习顺序建议

```
learn-docker (容器基础)  →  learn-redis (本课程)  →  按需选学
                              │                      ├─ learn-fullstack stage-06 (Django + Celery 集成)
                              │                      └─ learn-se (系统设计中的 Redis 案例)
```

## 与全栈课程的关系

| 主题 | 权威来源（本课） | 全栈课程 |
|------|------------------|----------|
| Redis 命令与数据结构 | `learn-redis` | stage-02 仅保留链接 |
| 缓存模式与 Key 设计 | `learn-redis` 第 4 课 | stage-06/14 聚焦 Django 集成 |
| Celery + Redis Broker | `learn-redis` 第 5 课概览 | stage-06 深入 Celery API |
| 架构级案例（秒杀/Feed） | — | `learn-se/learn-system-design` |
