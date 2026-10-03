# 第 04 阶段：状态管理（Provider → Riverpod）

## 学习目标

完成本阶段后，你将能够：
- 理解 setState 的局限与状态提升的必要性
- 理解 InheritedWidget 原理，知道 Provider 如何工作
- 使用 Riverpod 管理同步、异步与组合状态
- 设计合理的状态分层（UI / Controller / Repository）
- 对比 Riverpod / Bloc / GetX，为项目做出选型决策

## 前置要求

- 完成 Stage 03
- 熟悉 React 的状态管理思路（Zustand / Redux 任意一种）

## 课程内容

| 节 | 课时文件 | 内容 |
|----|-------------|------|
| 1 | `01-从setState到状态提升.md` | 状态提升、回调地狱、为什么需要状态库 |
| 2 | `02-InheritedWidget与Provider.md` | 原理剖析、Provider 用法与局限 |
| 3 | `03-Riverpod核心.md` | Provider/StateProvider/Notifier、自动销毁 |
| 4 | `04-Riverpod进阶.md` | FutureProvider/StreamProvider、组合、ref.watch/listen、family |
| 5 | `05-架构分层与选型.md` | Feature 目录结构、Riverpod vs Bloc vs GetX、选型 ADR |

## 练习与产出

- `exercises/`：状态管理对比练习（同一功能三种实现）
- `project/`：TaskFlow 任务列表接入 Riverpod，实现筛选/排序/新建状态流
- 输出一份状态管理选型 ADR 文档

## 预计时长：5 天

## 验收标准

- 任务列表的筛选、排序、新建全部通过 Riverpod 驱动
- 登录态在页面间共享且刷新后不丢失
- 能解释 Riverpod 与 Provider 的本质区别
