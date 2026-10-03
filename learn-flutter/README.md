# Flutter 跨平台移动开发 — 系统课程

## 课程概述

以 **Dart 3 + Flutter** 为核心，面向已有开发经验的工程师，系统补齐跨平台 App 开发能力。课程不教编程基础，Dart 部分通过「与 TypeScript/Python 对照」速成，UI、状态、网络、工程化部分直接复用你已有的 React、REST、测试与 CI/CD 经验。

最终产出：**TaskFlow 移动客户端**，与本仓库现有 Django + DRF 后端打通，完成从「会写代码」到「能独立发布 App」的闭环。

## 课程定位

- 适合已完成 `learn-tools`、`learn-fullstack` 或 `learn-se` 任一主线的学习者
- 语言阶段约 4 天，不重复讲解变量/循环/函数等基础概念
- 全程围绕贯穿项目 **TaskFlow App** 动手实践
- 兼容 Windows 开发环境（先跑 Windows 桌面端 + Android），iOS 构建所需条件单独说明

## 贯穿项目：TaskFlow App

对接 [`learn-fullstack`](../learn-fullstack/) 的 Django REST Framework 后端，逐阶段实现：

- 登录/注册（JWT，Access/Refresh 自动刷新）
- 项目与任务列表、详情、筛选、排序
- 新建/编辑任务、状态流转
- 文件上传与下载
- WebSocket 实时通知
- 本地缓存与离线可用

## 课程结构（10 个阶段）

### 🟢 语言与环境（第 1–2 阶段）

| 阶段 | 内容 | 预计时长 |
|------|------|----------|
| 01 | Dart 3 语言速成（经验者向） | 4 天 |
| 02 | Flutter 环境与工程结构 | 2 天 |

### 🔵 UI 与状态（第 3–5 阶段）

| 阶段 | 内容 | 预计时长 |
|------|------|----------|
| 03 | Widget 与 UI 构建 | 7 天 |
| 04 | 状态管理（Provider → Riverpod） | 5 天 |
| 05 | 路由与导航（go_router） | 3 天 |

### 🟡 数据与网络（第 6–7 阶段）

| 阶段 | 内容 | 预计时长 |
|------|------|----------|
| 06 | 数据模型与本地存储 | 4 天 |
| 07 | 网络与 TaskFlow API 对接 | 5 天 |

### 🟠 工程与生产（第 8–10 阶段）

| 阶段 | 内容 | 预计时长 |
|------|------|----------|
| 08 | 测试与工程质量 | 4 天 |
| 09 | 平台能力与原生集成 | 5 天 |
| 10 | 构建发布与生产运维 | 4 天 |

**总计：约 43 天（6–7 周，每天 2–3 小时）**，可按自身节奏调整；已有 React 经验的读者可跳过部分 UI 课时。

## 技术栈总览

```text
┌────────────────────────────────────────────┐
│                  UI 层                      │
│  Flutter（稳定版）+ Dart 3 + Material 3     │
│  Widget 组合、主题、动画、响应式布局         │
├────────────────────────────────────────────┤
│              状态与数据层                    │
│  Riverpod + go_router                      │
│  freezed / json_serializable               │
│  dio + WebSocket                            │
│  drift / sqflite + shared_preferences       │
├────────────────────────────────────────────┤
│                 平台层                      │
│  Platform Channel、权限、通知、相机/相册      │
│  Windows / Android / iOS / Web 多端适配     │
├────────────────────────────────────────────┤
│                 工程化                      │
│  flutter_test + integration_test + golden   │
│  GitHub Actions + Fastlane + Sentry         │
└────────────────────────────────────────────┘
```

## 学习路线图

```text
第01阶段 → 第02阶段 → 第03阶段 → 第04阶段 → 第05阶段
 Dart速成   环境/工程    Widget与UI   状态管理   路由导航

                                                      ↓

第06阶段 → 第07阶段 → 第08阶段 → 第09阶段 → 第10阶段
 数据存储   网络对接    测试/CI    平台能力    构建发布
            TaskFlow API            原生集成
```

## 与已有知识的对照

| 你已经掌握的 | Flutter 世界对应 |
|-------------|-----------------|
| TypeScript / JavaScript | Dart 3 |
| React 组件 / JSX | Widget / 声明式 UI |
| useState / useEffect | StatefulWidget / Riverpod |
| React Router | go_router |
| Axios / fetch | dio / HttpClient |
| Zustand / Redux | Riverpod / Bloc |
| Jest / Vitest / Playwright | flutter_test / integration_test |
| npm / pnpm / uv | pub / dart pub |
| Tailwind / MUI | Material 3 / Cupertino |
| Django REST API | 直接作为 TaskFlow App 的后端 |

## 目录说明

```text
learn-flutter/
├── README.md              # 本文件：课程总览
├── GETTING_STARTED.md     # 环境搭建与快速上手
├── STUDY_ROADMAP.md       # 周计划与每日节奏
├── stage-01-dart-basics/  # 每个阶段一个目录
│   ├── README.md          # 阶段总览与课时清单
│   ├── 01-课时.md          # 详细讲解（45 节正文已完成）
│   ├── exercises/         # 练习题
│   ├── code/              # 示例代码
│   └── project/           # TaskFlow 增量代码
└── project/taskflow_app/  # 贯穿项目根目录（随阶段演进）
```

## 快速入口

- 环境搭建与 5 分钟上手 → [`GETTING_STARTED.md`](GETTING_STARTED.md)
- 完整周计划 → [`STUDY_ROADMAP.md`](STUDY_ROADMAP.md)
- 从 Dart 速成开始 → [`stage-01-dart-basics/`](stage-01-dart-basics/)
