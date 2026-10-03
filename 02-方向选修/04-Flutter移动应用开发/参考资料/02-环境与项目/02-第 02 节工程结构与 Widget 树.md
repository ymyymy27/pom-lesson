> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 02 节：工程结构与 Widget 树

## 本节目标

- 读懂 `pubspec.yaml` 的依赖、资源、环境声明
- 理解 `runApp` → `MaterialApp` → `Scaffold` 的启动链路
- 建立"Widget 树"和"Element 树"的心智模型

## 一、pubspec.yaml 逐段解读

```yaml
name: taskflow_app
description: "TaskFlow 移动客户端"
publish_to: 'none'          # 不发布到 pub.dev
version: 1.0.0+1            # 版本号+构建号（Android 用）

environment:
  sdk: ^3.0.0               # Dart SDK 版本约束

dependencies:
  flutter:
    sdk: flutter            # Flutter 框架本身
  cupertino_icons: ^1.0.8   # iOS 风格图标
  # 后续会加：riverpod、go_router、dio、drift 等

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^4.0.0     # 官方 lint 规则

flutter:
  uses-material-design: true
  assets:                   # 静态资源声明处
    - assets/images/
  fonts:                    # 自定义字体
    - family: MyFont
      fonts:
        - asset: assets/fonts/MyFont.ttf
```

要点：**资源必须在这里声明才能用**，这是 Flutter 与 Web（直接放 public 目录）的重要差异。

## 二、启动链路：runApp 发生了什么

```dart
// lib/main.dart
import 'package:flutter/material.dart';

void main() {
  runApp(const TaskFlowApp());
}

class TaskFlowApp extends StatelessWidget {
  const TaskFlowApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TaskFlow',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('任务')),
      body: const Center(child: Text('你好，TaskFlow')),
    );
  }
}
```

执行过程：

1. `main()` 调用 `runApp(TaskFlowApp())`
2. Flutter 把 `TaskFlowApp` 挂到根节点，调用它的 `build`
3. `MaterialApp` 提供主题、路由、本地化等全局能力（类似 React 的 App 级 Provider）
4. `home` 指向 `HomePage`，最终渲染出 `Scaffold`（页面骨架）

## 三、Widget 树 / Element 树 / RenderObject 树

这是 Flutter 最重要的心智模型：

```text
Widget 树（你写的配置）        Element 树（运行时的实例）      Render 树（真正的绘制）
TaskFlowApp                  TaskFlowApp_Element            ...
  └─ MaterialApp               └─ ...                        ...
      └─ Scaffold                  └─ ...                    ...
          └─ Text('你好')              └─ ...                绘制文字
```

类比 React：

| React 概念 | Flutter 概念 |
|-----------|-------------|
| 组件（函数/类） | Widget |
| 虚拟 DOM 对比 | Element 树的 diff |
| 真实 DOM | RenderObject |
| `props` | `Widget` 构造参数 |
| `setState` 触发重渲染 | `setState` 触发 rebuild |

关键结论：

- **Widget 是"配置"，不可变**；每次 build 都新建 Widget 对象，代价很低
- Flutter 通过对比新旧 Widget 配置来复用 Element 和 RenderObject，而不是销毁重建
- `BuildContext` 是 Element 的句柄，用来向上找祖先（Theme、Navigator、Provider）

## 四、StatelessWidget 的 build 何时被调用

```text
父组件 rebuild → 传入新配置 → 子 build 重新执行
主题/本地化变化 → 依赖了 InheritedWidget 的组件 rebuild
```

和 React 一样：**父组件渲染不代表所有子组件都要重绘**，但 build 会重新执行；性能优化（`const`、`RepaintBoundary`）后面专门学。

## 动手练习

1. 修改模板：把 `home` 换成自定义的 `HomePage`，AppBar 标题改成"我的任务"
2. 在 `pubspec.yaml` 里添加 `assets/` 声明并放一张测试图片，在页面里显示
3. 把 `Text('你好，TaskFlow')` 换成 `Text('你好，${DateTime.now()}')`，观察热重载效果

## 验收标准

- 能画出自己项目的 Widget 树（从 runApp 到 Text）
- 能说清 Widget / Element / RenderObject 三者的分工
- 能在 pubspec 里正确声明一张图片资源并在页面显示
