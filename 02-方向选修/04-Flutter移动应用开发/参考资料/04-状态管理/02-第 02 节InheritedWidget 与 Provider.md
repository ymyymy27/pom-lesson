> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 02 节：InheritedWidget 与 Provider

## 本节目标

- 理解 InheritedWidget 的"祖先共享 + 精准通知"机制
- 学会用 Provider 管理可监听状态
- 掌握 `context.watch` / `context.read`

## 一、InheritedWidget：Flutter 内置的共享机制

`Theme.of(context)` 能取到主题，靠的就是 InheritedWidget。它有两个能力：

1. **向下查找**：子组件用 `context.dependOn...` 向上找祖先
2. **精准通知**：只有"依赖了它"的组件才会在变化时重建

自己实现一个：

```dart
class AuthScope extends InheritedWidget {
  const AuthScope({
    super.key,
    required this.token,
    required super.child,
  });

  final String? token;

  static AuthScope? maybeOf(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<AuthScope>();

  @override
  bool updateShouldNotify(AuthScope oldWidget) => oldWidget.token != token;
}
```

但裸写 InheritedWidget 很繁琐：要手动管理"谁依赖了我"，也没有"状态变化通知"。

## 二、ChangeNotifier + Provider：官方推荐组合

```dart
class AuthController extends ChangeNotifier {
  String? _token;
  String? get token => _token;

  Future<void> login(String email, String password) async {
    _token = await api.login(email, password);
    notifyListeners();          // 通知所有监听者
  }

  void logout() {
    _token = null;
    notifyListeners();
  }
}
```

挂载到组件树：

```dart
// main.dart
ChangeNotifierProvider(
  create: (_) => AuthController(),
  child: const TaskFlowApp(),
)
```

组件里读取：

```dart
// 依赖监听：token 变化时当前组件重建
final token = context.watch<AuthController>().token;

// 只读不监听：调用方法、触发动作
context.read<AuthController>().logout();
```

| API | 行为 | 类比 |
|-----|------|------|
| `context.watch<T>()` | 依赖它，变化就重建 | `useSelector` |
| `context.read<T>()` | 不依赖，仅调用 | `store.dispatch` |
| `Consumer<T>` | 缩小重建范围 | `useSelector` 局部包裹 |
| `Selector<T, R>` | 只监听某个字段 | `useShallowSelector` |

## 三、缩小重建范围：Consumer

```dart
// 整个页面 watch → 任何通知都重建整个页面
// 用 Consumer 只重建需要的部分：
Consumer<AuthController>(
  builder: (context, auth, _) => Text(
    auth.token == null ? '未登录' : '已登录',
  ),
)
```

## 四、Provider 的局限

- 编译期不知道依赖是否存在：取不到时运行期才报错
- `notifyListeners` 粒度粗：一个字段变化，整个 controller 的监听者都重建
- 依赖注入方式不够声明式（Riverpod 的改进点）

Provider 适合中小项目；TaskFlow 我们直接上它的继任者 Riverpod。

## 动手练习

1. 把登录状态提升为 `AuthController extends ChangeNotifier`
2. 在 AppBar 上显示登录状态，登录/登出按钮用 `context.read` 触发
3. 用 Consumer 让"只有头像区"在登录后重建

## 验收标准

- 能画出 InheritedWidget 的查找与通知链路
- 能说清 `watch` 与 `read` 的区别
- 能说出 Provider 的两个局限
