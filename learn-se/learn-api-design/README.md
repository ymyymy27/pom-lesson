# API 设计

RESTful API 的设计原则、版本策略、高级模式与契约管理。

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 参考 | `00_api_design_overview.md` | API 设计全景、REST 约束、设计流程 |
| 参考 | `00_api_design_principles.md` | 设计原则速查 |
| 第1课 | `01_rest_api_best_practices.md` | 资源建模、HTTP 语义、分页、幂等键、OpenAPI |
| 第2课 | `02_api_versioning_and_contracts.md` | 版本策略、OpenAPI 契约、Webhook、批量操作 |
| 第3课 | `03_graphql_grpc_async.md` | GraphQL/gRPC 选型、异步 API |

> 已合并的重复文件见 [`_archive/`](_archive/README.md)

## 学习目标

- 能用资源导向思维设计 REST API，而非 RPC 风格堆砌
- 掌握统一的错误响应、分页、过滤规范
- 理解 API 版本策略及 Breaking Change 管理

## 关联课程

- `learn-architecture/01_monolith_and_layered.md` — 整洁架构中的接口层
- `learn-domain-design/03_tactical_patterns.md` — 应用服务与 API 映射
- `learn-security/02_auth_and_identity.md` — 认证授权在 API 层的实现
- `projects/capstone_taskflow.md` — TaskFlow API 设计练习
