> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 03 节：Riverpod 核心

## 本节目标

- 理解 Provider 的概念与作用域
- 用 Notifier / NotifierProvider 管理业务状态
- 掌握 `ref.watch` / `ref.read` / `select`

## 一、Riverpod 是什么

Riverpod 是 Provider 的作者 Remi 推出的下一代状态管理库：

- **编译期类型安全**：依赖缺失编译时就发现
- **Provider 即全局声明**：状态定义与 UI 解耦
- **可测试**：Provider 可以单独 override
- **自动销毁**：`autoDispose` 按需释放

安装：

```powershell
flutter pub add flutter_riverpod
```

## 二、ProviderScope：一切的开始

```dart
void main() {
  runApp(
    const ProviderScope(          // 类似 React 的 Redux Provider
      child: TaskFlowApp(),
    ),
  );
}
```

## 三、最简单的 Provider：常量/依赖

```dart
final apiBaseUrlProvider = Provider<String>((ref) => 'https://api.example.com');
```

读取：

```dart
final url = ref.watch(apiBaseUrlProvider);
```

## 四、Notifier + NotifierProvider：业务状态

```dart
class TaskListNotifier extends Notifier<List<Task>> {
  @override
  List<Task> build() => [];

  void addTask(Task task) {
    state = [...state, task];
  }

  void toggleDone(String id) {
    state = [
      for (final t in state)
        if (t.id == id) t.copyWith(done: !t.done) else t,
    ];
  }

  void removeTask(String id) {
    state = state.where((t) => t.id != id).toList();
  }
}

final taskListProvider =
    NotifierProvider<TaskListNotifier, List<Task>>(TaskListNotifier.new);
```

注意：**永远不要直接改 state 内部**（如 `state.add(...)`），要赋新值，UI 才能感知。

组件中使用：

```dart
class TaskListPage extends ConsumerWidget {
  const TaskListPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tasks = ref.watch(taskListProvider);      // 依赖监听
    return ListView.builder(
      itemCount: tasks.length,
      itemBuilder: (_, i) => TaskCard(task: tasks[i]),
    );
  }
}

// 触发动作（不监听）
ref.read(taskListProvider.notifier).addTask(task);
```

## 五、ConsumerWidget / ConsumerStatefulWidget

| 组件 | 用途 |
|------|------|
| `ConsumerWidget` | 无状态组件里用 `ref` |
| `ConsumerStatefulWidget` | 需要生命周期 + ref |
| `Consumer` | 在任意 build 里局部包裹 |

## 六、select：只监听需要的字段

```dart
// 只看数量，任务内容变化不重建
final count = ref.watch(
  taskListProvider.select((tasks) => tasks.length),
);
```

## 七、autoDispose：自动释放

```dart
final detailProvider = FutureProvider.autoDispose<Task>((ref) async {
  final id = ref.watch(selectedTaskIdProvider);
  return api.getTask(id);
});
```

没有组件再监听时自动销毁，防止内存泄漏（比如离开详情页后取消请求）。

## 常见坑

- `Notifier` 的 `build()` 里如果 `ref.watch` 了其他 Provider，那个值变化会导致 Notifier 重建（要理解这一点）
- 在 `build` 外不能 `ref.watch`，只能 `ref.read`
- 改 `state` 必须赋新对象，`List`/`Map` 同理

## 动手练习

1. 把 TaskFlow 任务列表迁到 `TaskListNotifier`（增、删、切换完成）
2. 用 `select` 让"任务数量角标"只监听数量
3. 给任务详情做一个 `autoDispose` 的加载 Provider

## 验收标准

- 能写出 Notifier + NotifierProvider + 组件消费的完整链路
- 能说清 `ref.watch` 与 `ref.read` 的差异
- 能解释 `state = ...` 而不是 `state.add(...)` 的原因
