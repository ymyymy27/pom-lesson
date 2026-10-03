# 第 04 节：Riverpod 进阶

## 本节目标

- 用 FutureProvider / StreamProvider 处理异步
- 用 family 参数化 Provider
- 组合 Provider，避免重复请求

## 一、FutureProvider：异步加载

```dart
final tasksProvider = FutureProvider<List<Task>>((ref) async {
  final repo = ref.watch(taskRepositoryProvider);
  return repo.fetchTasks();
});
```

UI 用 `AsyncValue` 优雅处理三种状态：

```dart
class TaskListPage extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tasksAsync = ref.watch(tasksProvider);

    return switch (tasksAsync) {
      AsyncData(:final value) => ListView.builder(
          itemCount: value.length,
          itemBuilder: (_, i) => TaskCard(task: value[i]),
        ),
      AsyncError(:final error) => ErrorView(message: '$error'),
      _ => const Center(child: CircularProgressIndicator()),
    };
  }
}
```

`AsyncValue` 常用方法：

```dart
final data = asyncValue.value;             // 有数据则返回
asyncValue.when(
  data: (d) => ...,
  error: (e, st) => ...,
  loading: () => ...,
);
asyncValue.isLoading / hasValue / hasError
```

## 二、family：参数化 Provider

```dart
final taskDetailProvider =
    FutureProvider.family<Task, String>((ref, taskId) async {
  final repo = ref.watch(taskRepositoryProvider);
  return repo.fetchTask(taskId);
});

// 使用
ref.watch(taskDetailProvider(task.id));
```

每个参数值对应一个独立实例，详情页之间互不影响。

## 三、组合与依赖：Provider 依赖 Provider

```dart
final selectedProjectIdProvider = StateProvider<String?>((ref) => null);

final tasksProvider = FutureProvider<List<Task>>((ref) async {
  final projectId = ref.watch(selectedProjectIdProvider);  // 依赖
  if (projectId == null) return [];
  return ref.watch(taskRepositoryProvider).fetchTasks(projectId);
});
```

`selectedProjectIdProvider` 变化 → `tasksProvider` 自动重新请求 → UI 自动刷新。这个"响应式依赖链"是 Riverpod 最强大的地方。

## 四、StreamProvider：实时数据

```dart
final notificationProvider = StreamProvider<List<Notice>>((ref) {
  return ref.watch(wsServiceProvider).notices();   // 返回 Stream
});
```

WebSocket、数据库 watch、位置更新都适合 StreamProvider。

## 五、手动失效与刷新

```dart
// 下拉刷新
ref.invalidate(tasksProvider);

// 提交新任务后刷新
Future<void> submit() async {
  await repo.createTask(task);
  ref.invalidate(tasksProvider);        // 下次 watch 时重新请求
}
```

## 六、codegen（可选进阶）：riverpod_generator

手写 Provider 模板代码多，可以用 `@riverpod` 注解自动生成：

```dart
@riverpod
Future<List<Task>> tasks(TasksRef ref) async { ... }
```

需要 `build_runner`。**先学会手写，再决定是否引入 codegen**，理解优先级更高。

## 动手练习

1. 任务列表改为 FutureProvider 从 Mock Repository 加载
2. 下拉刷新用 `ref.invalidate`
3. 新建任务成功后自动刷新列表（组合 + invalidate）
4. 详情页用 `family`，每个任务独立加载

## 验收标准

- 能用 AsyncValue 处理加载/成功/失败三态
- 能画出一条"Provider 依赖链"（状态变化如何传导）
- 能说出 `invalidate` 与直接重新赋值的区别
