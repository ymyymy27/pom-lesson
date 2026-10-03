# 认证授权与多租户系统

面向后端开发者与架构师的权限系统专题：认证、授权模型、组织模型、数据权限、多租户隔离、越权防护与权限中台设计。学完本模块，你能独立设计并实现一个生产可用的多租户权限体系。

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 第0课 | `00_permission_overview.md` | 权限系统全景：五大支柱、课程地图、与现有课程分工 |
| 第1课 | `01_auth_engineering.md` | 认证工程：凭据、Session/JWT、刷新、SSO/OIDC、常见坑 |
| 第2课 | `02_permission_models.md` | 授权模型：ACL、RBAC（RBAC0-3）、ABAC、ReBAC、选型 |
| 第3课 | `03_org_model.md` | 组织模型：租户/用户/成员/部门/岗位/角色建模 |
| 第4课 | `04_data_permission.md` | 数据权限：行级范围、字段权限、实现方案与防绕过 |
| 第5课 | `05_multitenancy_models.md` | 多租户隔离模型：独立库/独立 Schema/共享表选型 |
| 第6课 | `06_multitenancy_implementation.md` | 多租户实现：租户上下文、ORM/RLS 过滤、缓存与异步 |
| 第7课 | `07_privilege_escalation_and_audit.md` | 越权防护与审计：IDOR、水平/垂直越权、审计与合规 |
| 第8课 | `08_permission_center_design.md` | 权限中台设计：边界、架构、API、缓存失效、微服务集成 |
| 第9课 | `09_capstone_multitask.md` | 综合大作业：MultiTask 多租户权限系统 |
| 实战 | `practice/` | 3 个可运行 Python 示例：RBAC、数据范围、租户隔离 |

## 学习目标

- 能画出权限系统的完整组成（认证/授权/组织/数据权限/审计）并说明各自职责
- 能根据业务场景选择 RBAC / ABAC / ReBAC 及多租户隔离模型
- 能设计用户-租户-成员-部门-角色-权限点的数据模型
- 能实现数据权限（本人/部门/全部）并防止绕过
- 能在请求、缓存、异步任务全链路贯彻租户隔离
- 能设计权限中台 API 与缓存失效策略，防范水平/垂直越权

## 与现有课程的关系

- `learn-security/02_auth_and_identity.md`：安全视角的认证授权原理与 OWASP 基线，本模块专注工程实现与系统设计
- `learn-api-design/`：接口契约设计，第 8 课会复用其原则
- `learn-fullstack/stage-05-auth/`：Django 认证实战，可与本模块对照
- `learn-architecture/`：微服务/模块化架构，第 8 课涉及服务间集成

## 学习方式

- 每课 30-45 分钟：概念 → 类比 → 图表/代码 → 动手练习 → 自检清单
- 第 2、4、6 课建议同步运行 `practice/` 中的示例
- 推荐节奏：第 1 周完成 00-04（权限建模），第 2 周完成 05-08（多租户与中台），周末完成 09 大作业

## 建议前置

- 至少掌握一门后端语言（示例以 Python 为主）
- 了解 REST API 基本概念（可先看 `learn-api-design/00`）
- 有 1 个以上业务系统开发经验，能联系自己项目中的权限痛点
