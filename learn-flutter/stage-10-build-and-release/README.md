# 第 10 阶段：构建发布与生产运维

## 学习目标

完成本阶段后，你将能够：
- 完成 Android release 构建、签名与多渠道配置
- 走通应用商店上架流程（Google Play / 国内商店；iOS 条件说明）
- 集成 Sentry 崩溃监控与统一日志
- 搭建 Fastlane / Codemagic / GitHub Actions 发布流水线

## 前置要求

- 完成 Stage 09
- 熟悉 CI/CD 概念（`learn-fullstack` Stage 13）

## 课程内容

| 节 | 课时文件 | 内容 |
|----|-------------|------|
| 1 | `01-Android构建与签名.md` | release 构建、keystore、混淆、多渠道、版本号策略 |
| 2 | `02-应用商店上架.md` | 上架材料、审核要点、灰度发布、iOS 构建条件 |
| 3 | `03-崩溃监控与日志.md` | Sentry 集成、日志分级、发布前 checklist |
| 4 | `04-CI与CD发布流水线.md` | Fastlane / Codemagic / GitHub Actions、热更新方案对比 |

## 练习与产出

- `project/`：可安装的 release APK
- 上架准备文档（截图、描述、隐私政策）
- 一键发布流水线：推送代码 → 测试 → 构建 → 分发

## 预计时长：4 天

## 验收标准

- 能产出一个签名完整的 APK 并安装到真机
- 崩溃日志能实时上报到 Sentry 并收到告警
- 全流程文档化，其他人可按文档复现发布
