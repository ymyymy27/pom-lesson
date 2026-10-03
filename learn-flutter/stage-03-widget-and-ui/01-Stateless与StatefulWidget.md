# 第 01 节：Stateless 与 StatefulWidget

## 本节目标

- 分清无状态/有状态组件，理解生命周期
- 掌握 `setState`、`widget`、`key` 的用法
- 理解"状态放哪里"的基本原则

## 一、两种 Widget

```dart
// 无状态：所有数据来自外部参数，自身不变
class TaskCard extends StatelessWidget {
  const TaskCard({super.key, required this.title, this.done = false});
  final String title;
  final bool done;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: Icon(done ? Icons.check_circle : Icons.radio_button_unchecked),
        title: Text(title),
      ),
    );
  }
}
```

```dart
// 有状态：内部有会变化的数据
class TaskCheckbox extends StatefulWidget {
  const TaskCheckbox({super.key, required this.title});
  final String title;

  @override
  State<TaskCheckbox> createState() => _TaskCheckboxState();
}

class _TaskCheckboxState extends State<TaskCheckbox> {
  bool _done = false;

  @override
  Widget build(BuildContext context) {
    return CheckboxListTile(
      title: Text(widget.title),
      value: _done,
      onChanged: (v) => setState(() => _done = v ?? false),
    );
  }
}
```

规则：**能无状态就无状态**。内部状态越少，组件越容易测试和复用。

## 二、生命周期（有状态组件）

```dart
class _TaskListState extends State<TaskList> {
  late final Future<List<String>> _tasks;

  @override
  void initState() {
    super.initState();
    _tasks = fetchTasks();        // 只执行一次的初始化（挂载）
  }

  @override
  void didUpdateWidget(TaskList oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.projectId != widget.projectId) {
      _tasks = fetchTasks();      // 外部参数变化时响应
    }
  }

  @override
  void dispose() {
    // 释放控制器、取消订阅
    super.dispose();
  }

  @override
  Widget build(BuildContext context) { ... }
}
```

对照 React 生命周期：

| React | Flutter |
|-------|---------|
| `useEffect(..., [])` 挂载 | `initState()` |
| `useEffect(..., [dep])` | `didUpdateWidget` |
| 卸载清理 | `dispose()` |
| 渲染 | `build()` |

## 三、setState 的正确姿势

```dart
// ✅ 正确：在回调里修改数据
setState(() {
  _count++;
});

// ❌ 错误：直接改数据不通知
_count++;

// ❌ 错误：setState 里做耗时操作
setState(() {
  _data = await fetch();   // 不允许，setState 回调必须同步
});
```

异步获取数据后再更新（注意 `mounted` 检查）：

```dart
Future<void> _load() async {
  final data = await fetchTasks();
  if (!mounted) return;              // 组件可能已销毁
  setState(() => _tasks = data);
}
```

## 四、Key 的作用

`key` 让 Flutter 在重建时**认出同一个 Widget**（类似 React 列表的 key）：

```dart
ListView.builder(
  itemBuilder: (context, i) => TaskCard(
    key: ValueKey(task.id),          // 身份稳定，避免状态错乱
    title: tasks[i].title,
  ),
);
```

不传 key 时按位置匹配；位置变化（排序、增删）会造成状态错位。

## 五、状态放哪里？

```text
只给一个组件用     → 放组件内部 State
兄弟组件共享       → 提升到共同父级（状态提升）
全 App 共享        → Stage 04 的 Provider / Riverpod
```

## 动手练习

1. 把 TaskFlow 任务卡片做成 StatelessWidget，接收 title / priority / done
2. 做一个 `ExpandableTaskCard`：点击标题展开详情（内部状态）
3. 在 `didUpdateWidget` 里响应 `projectId` 变化并重新加载数据

## 验收标准

- 能画出 StatefulWidget 的生命周期时序
- 能说出 `widget` 与 `state` 的分工
- 能在异步更新前用 `mounted` 防止泄漏报错
