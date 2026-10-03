# 快速开始

欢迎学习 **Flutter 跨平台移动开发**。本课程假设你已具备编程基础（Python / TypeScript 任一即可），并了解 REST API 与 Git——这些你已经在 `learn-fullstack` / `learn-tools` / `learn-se` 中掌握了，所以可以直接进入 Flutter 生态。

## 前置要求

- 会用命令行（PowerShell 即可）
- 熟悉 JSON、REST、Git（已有）
- 不需要任何移动开发经验
- 推荐：已完成 `learn-fullstack` 前 6 个阶段（方便 Stage 07 对接 TaskFlow 后端）

## 环境准备（Windows）

1. 下载并解压 [Flutter SDK](https://docs.flutter.dev/get-started/install/windows)（选择最新稳定版）
2. 将 `flutter\bin` 加入系统 PATH，终端运行 `flutter doctor` 检查依赖
3. 安装编辑器二选一：
   - **VS Code** + Flutter 与 Dart 插件（轻量，推荐）
   - **Android Studio**（自带 Android SDK / 模拟器，体积较大）
4. 国内网络建议配置 Flutter 镜像源（PUB_HOSTED_URL、FLUTTER_STORAGE_BASE_URL），详见官方中文文档

## 目标设备怎么选

| 设备 | 上手速度 | 说明 |
|------|----------|------|
| Windows 桌面端 | 最快 | 无需手机，`flutter run -d windows` 即可 |
| Android 模拟器 | 较快 | 需开启虚拟化，Android Studio 创建 AVD |
| Android 真机 | 快 | USB 调试打开即可，推荐日常用 |
| iOS 模拟器/真机 | 需要 macOS | Windows 上可先学，构建阶段再考虑 |
| Web 端 | 快 | `flutter run -d chrome`，适合快速预览 UI |

**建议：前 6 个阶段用 Windows 桌面端 + Chrome 预览，Stage 09 再切 Android 真机。**

## 学习步骤

1. 阅读 [课程总览](README.md)，了解 10 个阶段
2. 从 [第 01 阶段：Dart 3 语言速成](stage-01-dart-basics/) 开始；如果自测通过可跳过部分课时
3. 每阶段：读 `README.md` → 按课时文档学习 → 完成 `exercises/` → 在 `project/` 里迭代 TaskFlow App
4. Stage 07 之前启动 TaskFlow 后端（[`learn-fullstack/project/taskflow/`](../learn-fullstack/project/taskflow/)），开始前后端联调

## 第一个里程碑

完成 Stage 02 后，你应能在 Windows 桌面端跑起官方计数器 App，并理解 `main.dart` 每一行的作用。完成 Stage 03 后，你会拥有 TaskFlow 登录页 + 任务列表页的静态 UI。

## 预计时长

约 **43 天（6–7 周）**，每天 2–3 小时。有 React 经验者可压缩到 4–5 周。

## 下一步

👉 进入 [第 01 阶段：Dart 3 语言速成](stage-01-dart-basics/)
