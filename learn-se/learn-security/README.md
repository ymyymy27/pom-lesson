# 安全架构

面向架构师和 Tech Lead 的安全设计：认证授权、数据保护、威胁建模。

## 课程目录

| 课程 | 文件 | 内容 |
|------|------|------|
| 参考 | `00_security_overview.md` | 安全全景、STRIDE 威胁模型、安全左移 |
| 第1课 | `01_owasp_and_secure_coding.md` | OWASP Top 10、安全编码实践 |
| 第2课 | `02_auth_and_identity.md` | 认证 vs 授权、JWT/OAuth2、RBAC/ABAC |
| 第3课 | `03_threat_modeling.md` | STRIDE 威胁建模、攻击树 |
| 第4课 | `04_llm_and_agent_security.md` | OWASP LLM/Agentic AI Top 10、Prompt Injection、Agent Harness（2026 补充） |

> 注：目录中存在早期版本文件（`01_auth_and_access_control.md`、`02_security_for_architects.md`），以本表 canonical 版本为准。详见 [`COURSE_GAP_ANALYSIS.md`](../../COURSE_GAP_ANALYSIS.md)。

## 学习目标

- 能在架构设计阶段识别常见威胁并选择缓解措施
- 理解认证（Authentication）与授权（Authorization）的分工
- 掌握 API 和 Web 应用的安全基线

## 关联课程

- `learn-api-design/` — API 层安全设计
- `learn-architecture/04_architecture_decisions.md` — 安全相关 ADR
- `learn-fullstack/stage-05-auth/` — 认证实战
- `projects/capstone_taskflow.md` — TaskFlow 安全设计

## 学习方式

- 每课末尾有架构评审 Checklist，建议用于 Review 自己的项目
- 结合 OWASP 文档对照，不必死记，理解原理即可
