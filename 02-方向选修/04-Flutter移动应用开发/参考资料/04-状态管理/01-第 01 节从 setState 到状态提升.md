> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 01 节：从 setState 到状态提升

## 本节目标

- 看清 setState 方案的边界在哪
- 掌握状态提升与回调传递
- 理解"为什么需要状态管理库"

## 一、setState 的问题：局部状态无法共享

```dart
// 问题：任务状态存在列表页里，新建页改了状态，列表页不知道
class TaskListPage extends StatefulWidget {
  ...
}

class _TaskListPageState extends State<TaskListPage> {
  final List<Task> _tasks = [];

  void _addTask(Task t) {
    setState(() => _tasks.add(t));   // 只有自己能改
  }
}
```

当两个页面/组件需要**同一份状态**时，setState 就失效了：

- 登录页写入 token，任务页要读
- 新建页新增任务，列表页要刷新
- 筛选栏选择状态，列表要联动

## 二、状态提升：把状态交给共同父级

```dart
class TaskBoard extends StatefulWidget {
  const TaskBoard({super.key});
  @override
  State<TaskBoard> createState() => _TaskBoardState();
}

class _TaskBoardState extends State<TaskBoard> {
  final List<Task> _tasks = [];
  TaskStatus _filter = TaskStatus.all;

  // 回调传给子组件
  void _onTaskCreated(Task task) {
    setState(() => _tasks.add(task));
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        FilterBar(
          current: _filter,
          onChanged: (f) => setState(() => _filter = f),
        ),
        Expanded(
          child: TaskListView(
            tasks: _tasks.where((t) => t.status == _filter).toList(),
            onTaskCreated: _onTaskCreated,
          ),
        ),
      ],
    );
  }
}
```

这就是 React 的"lifting state up"：状态放共同父级，子组件通过**回调**上报变化。

## 三、回调地狱：问题浮出水面

当层级变深：

```text
TaskBoard
  └─ TaskFilterPanel
      └─ StatusDropdown   ← 要改 filter
      └─ PrioritySlider   ← 要改 priority
  └─ TaskListView
      └─ TaskCard
          └─ TaskCheckbox ← 要改 done
```

每个中间层都要"转发"状态和回调，出现：

- **Prop drilling**：无关组件传递大量参数
- **无谓重建**：父级 setState 导致整棵树 rebuild
- **难以测试**：状态与 UI 耦合

## 四、StatefulWidget 的另一个问题：build 里不能读写"全局"

```dart
// ❌ 反模式：把状态挂在 static 上
class AuthStore {
  static String? token;
}
```

静态变量无法通知 UI 更新，也没有作用域管理。真正的需求是：

1. **状态存储在某处**（可被任意组件访问）
2. **状态变化时通知依赖它的组件重建**
3. **作用域可控**（App 级 / 页面级 / 局部）

这就是 Provider / Riverpod 要解决的问题。

## 五、什么时候还不该用状态库？

- 状态只在单个 Widget 内部（`_index`、展开/收起）→ 继续用 setState
- 页面级一次性数据（详情页加载）→ 用 FutureBuilder 或局部状态
- 过度设计会让小项目变复杂

## 动手练习

1. 在 TaskFlow 里实现"筛选栏 + 列表"的状态提升（不引入库）
2. 数一下你的组件树里有多少层"透传回调"，找 1 处最痛的记录下来
3. 列出 TaskFlow App 里"多页面共享的状态"清单（token、任务列表、筛选条件…）

## 验收标准

- 能画出 TaskFlow 中 3 个需要状态提升的场景
- 能说清 prop drilling 的两个代价
- 能判断"哪些状态该留在 setState，哪些该升级"
