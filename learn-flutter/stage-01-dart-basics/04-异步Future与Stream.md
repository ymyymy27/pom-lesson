# 第 04 节：异步 Future 与 Stream

## 本节目标

- 掌握 `Future` / `async` / `await`，理解与 JS Promise 的异同
- 掌握 `Stream`：监听、生成、广播
- 了解 isolate 与"单线程但异步"的执行模型

## 一、Future：一次性异步结果

Future 就是"未来的一个值"，对应 JS 的 Promise：

```dart
Future<String> fetchTask() async {
  await Future.delayed(const Duration(seconds: 1));
  return '任务数据';
}

void main() async {
  final data = await fetchTask();   // 暂停当前函数，等结果
  print(data);

  // 也可以用 then / catchError（等价于 JS 的 .then/.catch）
  fetchTask()
      .then((d) => print(d))
      .catchError((e) => print('失败: $e'));
}
```

错误处理：

```dart
try {
  final data = await fetchTask();
} on TimeoutException {
  print('超时');
} catch (e, st) {
  print('未知错误: $e\n$st');   // st 是堆栈
} finally {
  print('无论成败都会执行');
}
```

并发等待多个 Future：

```dart
final results = await Future.wait([
  fetchTasks(),
  fetchProjects(),
  fetchUsers(),
]);
```

## 二、Stream：持续多次的值

Stream 对应"数据流"：通知、进度、输入事件等**会持续到来**的值。

```dart
// 生成一个流：async* + yield
Stream<int> countdown(int n) async* {
  for (var i = n; i > 0; i--) {
    yield i;                          // 产出
    await Future.delayed(const Duration(seconds: 1));
  }
}

void main() {
  final sub = countdown(3).listen(
    (value) => print(value),          // 每次来数据
    onError: (e) => print('出错了: $e'),
    onDone: () => print('流结束'),
  );
  sub.cancel();   // 记得取消，避免内存泄漏
}
```

流的常用操作与集合一致：

```dart
final doubles = countdown(5)
    .where((n) => n.isEven)
    .map((n) => n * 2);
```

StreamController（手动控制数据源）：

```dart
final controller = StreamController<String>();
controller.add('hello');
controller.addError('boom');
controller.close();
```

默认 Stream 只能被一个监听者订阅；需要多处监听时用广播流：

```dart
final broadcast = StreamController<String>.broadcast();
```

## 三、Dart 的执行模型：单线程 + 事件循环

- Dart 代码默认跑在**一个线程**上（类似 JS）
- `async` 函数遇到 `await` 就"让出"，事件循环去处理其他任务
- 耗时 CPU 任务会卡住界面，用 **isolate** 另开一个"线程"：

```dart
import 'dart:isolate';

Future<int> heavyCompute() async {
  return Isolate.run(() {
    // 在独立 isolate 里执行，不阻塞主线程
    var sum = 0;
    for (var i = 0; i < 10000000; i++) sum += i;
    return sum;
  });
}
```

## 四、与前端经验对照

| 前端概念 | Dart 对应 |
|---------|----------|
| `Promise<T>` | `Future<T>` |
| `async/await` | `async/await`（几乎一样） |
| `EventEmitter` / `Observable` | `Stream` |
| `setTimeout` | `Future.delayed` |
| Web Worker | `Isolate` |
| `Promise.all` | `Future.wait` |

## 常见坑

- `await` 只能在 `async` 函数里用；main 要写成 `Future<void> main() async`
- 忘记 `.cancel()` 订阅会导致 Stream 监听器泄漏
- `Future.delayed` 不会取消任务，需要配合超时（`Future.timeout`）处理
- UI 线程不要直接做重计算，用 `Isolate.run` 或后续学的 `compute`

## 动手练习

1. 写一个 `fetchUser(id)`，模拟 500ms 延迟；用 `Future.wait` 并发取 3 个用户
2. 用 `async*` 写一个每秒产生一次进度的流，模拟文件上传 0–100%
3. 用 `StreamController` 实现一个简易事件总线：订阅、发消息、取消订阅

## 验收标准

- 能解释 Future 和 Stream 的适用场景差异
- 能写出带 `onError` / `onDone` 的流监听
- 能说出 isolate 解决的问题
