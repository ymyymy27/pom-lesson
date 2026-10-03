> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 01 节：环境搭建与 flutter doctor

## 本节目标

- 在 Windows 上装好 Flutter 并让 `flutter doctor` 全绿（或明确知道缺什么）
- 准备好两个运行目标：Windows 桌面端 + Android 设备/模拟器
- 创建第一个 Flutter 项目

## 一、安装 Flutter SDK（Windows）

1. 打开 [Flutter 官方安装页](https://docs.flutter.dev/get-started/install/windows)，下载最新稳定版 SDK 压缩包
2. 解压到固定目录，例如 `C:\src\flutter`（**不要放中文/空格路径**，避免工具链问题）
3. 把 `C:\src\flutter\bin` 加入系统环境变量 PATH
4. 打开新终端，验证：

```powershell
flutter --version
```

国内网络建议配置镜像（官方中文文档有说明）：

```powershell
$env:PUB_HOSTED_URL = "https://pub.flutter-io.cn"
$env:FLUTTER_STORAGE_BASE_URL = "https://storage.flutter-io.cn"
```

> 环境变量只对当前终端生效；要永久生效请通过"系统属性 → 环境变量"配置。

## 二、运行依赖

| 目标设备 | 需要什么 | 说明 |
|----------|----------|------|
| Windows 桌面 | **Visual Studio 2022**（勾选"使用 C++ 的桌面开发"工作负载） | 首次最常缺的就是它 |
| Android | Android SDK + 平台工具 | 装 Android Studio 即可自动带 |
| Chrome | Chrome 浏览器 | 无需额外配置 |
| Android 真机 | USB 调试 + 手机驱动 | 开发者选项里开启 |

编辑器推荐 **VS Code + Flutter/Dart 插件**，或 **Android Studio**（模拟器管理更顺手）。

## 三、检查环境

```powershell
flutter doctor
```

输出逐行说明（常见状态）：

- `[√] Flutter` — SDK 正常
- `[√] Windows Version` — 系统正常
- `[×] Visual Studio` — 缺 C++ 桌面开发组件，去 Visual Studio Installer 补装
- `[×] Android toolchain` — 缺 Android SDK，装 Android Studio 或用 `flutter doctor --android-licenses` 接受许可
- `[√] Chrome` — Web 目标可用

诊断命令：

```powershell
flutter doctor -v            # 详细版本信息
flutter devices              # 列出当前可用设备
flutter emulators            # 列出 Android 模拟器
```

## 四、创建第一个项目

```powershell
flutter create taskflow_app
cd taskflow_app
flutter run -d windows       # Windows 桌面端运行
flutter run -d chrome        # 浏览器运行（预览快）
flutter run -d <设备ID>      # 用 flutter devices 查设备ID
```

创建时可以指定平台：

```powershell
flutter create --platforms=windows,android taskflow_app
```

## 五、理解项目结构（先记住这些）

```text
taskflow_app/
├── lib/                 # 你的 Dart 代码（90% 时间在这里）
│   └── main.dart        # 入口
├── test/                # 测试
├── android/             # Android 原生壳（Gradle/Manifest）
├── windows/             # Windows 原生壳（C++）
├── web/                 # Web 壳
├── pubspec.yaml         # 依赖与资源声明（最重要）
└── analysis_options.yaml # 静态检查规则
```

## 动手练习

1. 跑 `flutter doctor` 并逐项核对，把缺失项补到全绿
2. 创建 `taskflow_app` 项目，分别在 Windows 桌面端和 Chrome 里跑起来
3. 用 `flutter devices` 确认至少有两个可用目标

## 验收标准

- `flutter doctor` 无红叉（黄色警告可接受，但要能解释是什么）
- 能在 Windows 桌面端运行官方模板
- 能说出 `lib/`、`pubspec.yaml`、`android/` 三个目录的职责
