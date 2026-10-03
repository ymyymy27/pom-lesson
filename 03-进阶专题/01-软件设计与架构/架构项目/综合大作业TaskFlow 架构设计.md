> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 综合大作业：TaskFlow 架构设计

> 串联 learn-se 全部模块的综合练习。建议在第 12–14 周完成。

## 1. 项目背景

**TaskFlow** 是一个团队任务协作平台（与 `99-历史归档/旧版课程说明/Web旧导航/` 贯穿项目一致）：

```
核心功能：
  - 用户注册/登录（邮箱 + OAuth）
  - 项目管理（创建项目、邀请成员、角色权限）
  - 任务管理（创建、分配、状态流转、优先级、标签）
  - 看板视图（Kanban：Todo / In Progress / Done）
  - 评论与 @提及
  - 文件附件
  - 实时通知（任务分配、状态变更、评论）
  - 活动日志（Audit Log）
  - 可选：Slack/飞书集成、API 开放
```

## 2. 作业要求

你需要产出以下 **5 份交付物**：

| # | 交付物 | 对应模块 | 格式 |
|---|--------|---------|------|
| 1 | 限界上下文地图 | learn-domain-design | 图 + 说明 |
| 2 | 架构设计文档 | learn-architecture | C4 Level 2 图 + 说明 |
| 3 | 3 条 ADR | learn-architecture | ADR 模板 |
| 4 | 容量估算 | learn-system-design | 估算过程 |
| 5 | 非功能设计 | learn-reliability + learn-security + learn-api-design | 表格 |

---

## 3. 任务分解

### Task 1：领域建模（DDD）

```
要求：
  1. 识别至少 4 个限界上下文
  2. 画上下文地图（标注关系：Partnership / Customer-Supplier / ACL）
  3. 设计「Task」聚合：实体、值对象、不变量
  4. 列出至少 3 个领域事件

提示：
  - Task 的状态流转是核心：Todo → InProgress → Review → Done
  - 权限是横切关注点还是独立上下文？
  - Notification 是独立上下文还是 Task 的子域？

参考：learn-domain-design/02_aggregates_and_modeling.md
```

### Task 2：架构设计

```
假设：
  - 团队 8 人（4 后端 + 2 前端 + 1 PM + 1 QA）
  - 目标 6 个月 5000 团队注册
  - 预算 $1000/月

要求：
  1. 选择架构风格并说明理由
  2. 画 C4 Level 2 Container 图
  3. 标注每个容器的技术选型和职责
  4. 画出核心流程：「创建任务 → 分配 → 通知」的数据流

参考：learn-architecture/05_architecture_case_studies.md 案例 1
```

### Task 3：架构决策记录（ADR）

```
至少写 3 条 ADR，建议主题：

  ADR-001: 架构风格选择（单体 vs 微服务）
  ADR-002: 数据库选型（PostgreSQL vs MongoDB）
  ADR-003: 实时通知方案（WebSocket vs SSE vs Polling）
  ADR-004: 文件存储方案（Local vs S3）
  ADR-005: 缓存策略

每条 ADR 必须包含：背景、决策、考虑的选项、理由、后果
```

### Task 4：容量估算

```
假设 5000 团队、每团队 10 人、每人每天 30 次操作：

  1. 估算 DAU、峰值 QPS
  2. 估算存储（用户、任务、评论、附件，5 年）
  3. 估算带宽
  4. 判断是否需要缓存、CDN、读写分离

参考：learn-system-design/01_capacity_estimation.md
```

### Task 5：非功能设计

```
填写以下表格：

| 质量属性 | 目标 | 实现方案 |
|---------|------|---------|
| 可用性 | 99.9% | ? |
| 延迟 | p99 < 500ms | ? |
| 安全 | ? | 认证/授权/加密方案 |
| 可扩展 | 10x 用户增长 | ? |

额外：
  - 设计 API 版本策略（learn-api-design/02_api_versioning_and_contracts.md）
  - 列出 3 个 SLI 和对应的 SLO（learn-reliability/01_sli_slo_sla.md）
  - 识别 2 个安全风险及缓解措施（learn-security/02_security_for_architects.md）
  - 设计 REST API endpoint 列表（learn-api-design/01_rest_api_best_practices.md）
```

---

## 4. 评分标准（自检）

| 维度 | 优秀 | 合格 | 需改进 |
|------|------|------|--------|
| 领域建模 | 上下文清晰、聚合边界合理 | 有划分但边界模糊 | 按技术层拆分 |
| 架构选择 | 匹配团队/规模/预算 | 合理但理由不充分 | 过度设计/Under-design |
| ADR | 选项对比完整、理由充分 | 有 ADR 但缺选项 | 无 ADR |
| 容量估算 | 数量级正确、有假设说明 | 有估算但缺过程 | 无估算 |
| 非功能 | 覆盖可用/安全/性能 | 部分覆盖 | 未考虑 |

---

## 5. 参考架构（完成后再看）

<details>
<summary>点击展开参考方案（请先独立完成！）</summary>

```
推荐：模块化单体 + 事件驱动通知

┌─────────────────────────────────────────┐
│              FastAPI Monolith              │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌────────┐ │
│  │ User │ │Project│ │ Task │ │Notify  │ │
│  │Module│ │Module│ │Module│ │Module  │ │
│  └──┬───┘ └──┬───┘ └──┬───┘ └───┬────┘ │
│     └────────┴────────┴─────────┘      │
│              Domain Events              │
└──────────────────┬──────────────────────┘
                   ↓
         PostgreSQL + Redis + S3
                   ↓
         WebSocket Server（通知推送）

理由：
  - 8 人团队，单体最高效
  - 模块边界清晰，6 个月后按上下文拆分
  - 事件驱动解耦 Notification
  - $1000/月：2 台 App + PG + Redis + S3
```

</details>

---

## 6. 提交方式

在 `projects/your_name_taskflow/` 目录下创建：

```
projects/your_name_taskflow/
├── 01_context_map.md       # 或 .png
├── 02_architecture.md      # C4 图 + 说明
├── 03_adr/                 # ADR-001.md, ADR-002.md, ...
├── 04_capacity.md          # 容量估算
└── 05_non_functional.md    # 非功能设计
```

---

**恭喜完成 learn-se 全部课程！** 下一步：在 `99-历史归档/旧版课程说明/Web旧导航/` 中动手实现 TaskFlow。
