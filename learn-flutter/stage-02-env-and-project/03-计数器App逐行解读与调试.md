# 第 03 节：计数器 App 逐行解读与调试

## 本节目标

- 逐行理解 Flutter 官方模板（计数器）
- 掌握热重载、热重启的区别与用法
- 学会 DevTools、断点、日志三种调试手段

## 一、官方计数器逐行解读

```dart
import 'package:flutter/material.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      home: const MyHomePage(title: 'Flutter Demo Home Page'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});
  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  int _counter = 0;                 // 可变状态

  void _incrementCounter() {
    setState(() {
      _counter++;                   // 通知 Flutter 重建
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('You have pushed the button this many times:'),
            Text('$_counter', style: Theme.of(context).textTheme.headlineMedium),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _incrementCounter,
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ),
    );
  }
}
```

逐行要点：

- `MyHomePage extends StatefulWidget`：**Widget 本身不可变**，可变状态放在 `State` 里
- `createState()`：创建 State 实例（只创建一次）
- `widget.title`：State 通过 `widget` 访问组件配置
- `setState`：改变数据 + 通知重建，等价于 React 的 setState（但必须手动调用）
- `Theme.of(context)`：向上查找主题，等价于 `useTheme()`

## 二、StatefulWidget 与 React 对照

| React | Flutter |
|-------|---------|
| `useState(0)` | `int _counter = 0` + `setState` |
| `props` | `widget.xxx` |
| `useEffect` 挂载 | `initState()` |
| `useEffect` 清理 | `dispose()` |
| 函数组件重渲染 | `build()` 重新执行 |

## 三、热重载 vs 热重启

| 操作 | 触发 | 保留状态吗 | 何时用 |
|------|------|-----------|--------|
| 热重载（Hot Reload） | 保存文件自动 / `r` | ✅ 保留 | 改 UI、改 build 逻辑 |
| 热重启（Hot Restart） | `R` | ❌ 重置 | 改了 `main()`、全局变量、原生注册 |
| 全量重启 | `q` 退出再 `flutter run` | ❌ | 改了原生代码 / pubspec 依赖 |

注意：**新增依赖（pubspec 改动）必须全量重启**；新增文件某些情况也要热重启。

## 四、调试三件套

### 1. 日志

```dart
debugPrint('点击了按钮，计数: $_counter');   // 开发调试专用
print('普通日志');                            // 也能用，但线上要避免
```

`debugPrint` 会智能分块，避免长日志被截断。

### 2. 断点

VS Code：

1. 在代码行号左侧点击设置断点
2. F5 启动调试（或 `flutter run` 后按 `o` 打开 DevTools）
3. 命中断点后可查看变量、调用栈、逐行执行

### 3. DevTools

`flutter run` 运行中按 `o`，或 VS Code 命令面板执行 "Dart: Open DevTools"。常用面板：

| 面板 | 用途 |
|------|------|
| Widget Inspector | 像浏览器元素检查器一样查看 Widget 树 |
| Timeline | 性能分析，看帧耗时 |
| Memory | 内存与泄漏 |
| Network | HTTP 请求查看（Stage 07 常用） |

## 五、常见报错与解决

| 报错 | 原因 | 处理 |
|------|------|------|
| `RenderFlex overflowed` | Column/Row 内容超出屏幕 | 加 `Expanded` / `SingleChildScrollView` |
| `setState() called after dispose` | 异步回调在组件销毁后更新状态 | 检查 `mounted` |
| `Could not find the correct Provider` | 未在祖先挂 Provider | 检查 ProviderScope 位置 |
| `Undefined class 'X'` | 依赖没加或没导入 | `flutter pub add X` + import |

## 动手练习

1. 把计数器改成"减一"和"清零"两个按钮
2. 在 `_incrementCounter` 里加 `debugPrint`，用热重载看控制台输出
3. 故意把 `Column` 的 children 加到 10 个，触发 overflow，用 Widget Inspector 观察并修复

## 验收标准

- 能解释 `setState` 为什么必须包裹数据修改
- 能熟练使用热重载/热重启/全量重启
- 能通过 Widget Inspector 找到任意一个 Widget 在树中的位置
