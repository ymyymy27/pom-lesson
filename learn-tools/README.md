# 开发工具课程

日常开发中必备的工具型知识，按优先级排列。

## 课程目录

| 课程 | 目录 | 内容 | 课时 |
|------|------|------|------|
| pip 包管理 | `learn-pip/` | pip 命令、版本管理、虚拟环境、镜像源、**uv 现代工具链** | 6课 |
| Git 版本控制 | `learn-git/` | 基础操作、分支、合并冲突、远程协作、高级技巧 | 5课 |
| Shell 命令行 | `learn-shell/` | 文件操作、管道重定向、文本处理、脚本编写 | 5课 |
| 正则表达式 | `learn-regex/` | 语法基础、分组引用、实战模式、Python re 模块 | 5课 |
| Docker 容器 | `learn-docker/` | 核心概念、镜像容器、Compose、网络存储、实战 | 6课 |
| Redis 缓存 | `learn-redis/` | 数据结构、缓存模式、限流锁、Pub/Sub、FastAPI 实战 | 6课 |
| SQL 数据分析 | `learn-sql/` | SELECT/WHERE、聚合分组、JOIN子查询、窗口函数、PM实战 | 5课 |
| pytest 测试 | `learn-pytest/` | 断言/fixture、参数化、Mock、插件、集成测试、实战 | 7课 |
| 网络与组网 | `learn-network/` | IP/子网、NAT、SSH 隧道、VPN/Mesh、内网穿透、异地协作 | 8课 |

## 学习顺序建议

```
learn-pip → learn-pytest → learn-shell → learn-git → learn-network → learn-regex → learn-docker → learn-redis → learn-sql
  包管理      单元测试       命令行基础     版本控制       组网协作      文本处理       容器化部署      缓存/队列      数据分析
```

## 学习方式

- 工具课程以 **Markdown 文档** 为主，因为这些工具主要在终端/命令行中操作
- 边读文档边在终端中动手练习
- 每门课程最后一课包含实战练习或可运行脚本
