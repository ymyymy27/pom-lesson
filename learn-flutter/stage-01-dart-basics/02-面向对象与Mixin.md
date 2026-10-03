# 第 02 节：面向对象与 Mixin

## 本节目标

- 掌握 Dart 的类、构造器、继承、接口
- 理解 mixin 与 TS 的 mixin / 组合的区别
- 会用增强枚举和 sealed class 建模业务状态

## 一、类与构造器

```dart
class Task {
  final String title;
  final int priority;

  // 默认构造器，required 必填
  const Task({required this.title, this.priority = 0});

  // 命名构造器
  Task.draft(this.title) : priority = 1;

  // 工厂构造器：可以返回子类或做校验
  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      title: json['title'] as String,
      priority: json['priority'] as int? ?? 0,
    );
  }

  // getter：看起来像属性，本质是方法
  String get label => '[$priority] $title';
}
```

要点：

- `this.title` 简写：构造参数直接赋值给同名字段
- `required` 等价于 TS 的必填参数
- `const` 构造器：对象在编译期确定且不可变，Flutter 里大量使用
- `factory` 类似 TS 里的 `static from()` 工厂模式

## 二、继承与覆写

```dart
class Project extends Task {
  final int memberCount;
  const Project({required super.title, this.memberCount = 1});

  @override
  String get label => '项目：${super.label}（$memberCount 人）';
}
```

Dart 是单继承，但任何类都可以被 `implements` 当作接口使用：

```dart
abstract class Repository {
  Future<List<Task>> fetchTasks();
}

// implements 要求实现接口的全部成员
class MockRepository implements Repository {
  @override
  Future<List<Task>> fetchTasks() async => [];
}
```

## 三、Mixin（Dart 特色）

TS 没有原生 mixin，通常用"组合"或"多个函数混合"模拟。Dart 用 `with` 直接混入一组实现：

```dart
mixin Loggable {
  void log(String msg) => print('[${DateTime.now()}] $msg');
}

mixin Cacheable {
  final Map<String, Object> _cache = {};
  void cache(String key, Object value) => _cache[key] = value;
}

class TaskService with Loggable, Cacheable {
  Future<String> fetch(String id) async {
    log('开始获取 $id');
    cache(id, 'data');
    return 'data';
  }
}
```

适用场景：把"日志、缓存、时间戳"这类横切能力拆成 mixin，多个类复用。注意：mixin 里可以有自己的字段和实现，这是它与"接口"最大的区别。

## 四、增强枚举（Dart 2.17+）

```dart
enum TaskStatus {
  todo('待办'),
  doing('进行中'),
  done('已完成');

  final String label;
  const TaskStatus(this.label);
}

void main() {
  print(TaskStatus.doing.label);      // 进行中
  print(TaskStatus.values);           // 所有枚举值
}
```

## 五、sealed class（Dart 3，建模状态利器）

```dart
sealed class LoadState {}

class Loading extends LoadState {}
class Success<T> extends LoadState {
  final T data;
  Success(this.data);
}
class Failure extends LoadState {
  final String message;
  Failure(this.message);
}

String render(LoadState state) => switch (state) {
  Loading() => '加载中…',
  Success(data: final d) => '数据：$d',
  Failure(message: final m) => '错误：$m',
};
```

`sealed` 保证所有子类都在同一个文件里，switch 穷尽检查——少写一个分支编译器就报错。这是 Flutter 状态建模的标配。

## 常见坑

- Dart 没有 `interface` 关键字，接口用 `abstract class` + `implements`
- `private` 用下划线 `_` 前缀表示，只对"所在库（文件）"生效
- `final` 字段必须在构造器或声明处赋值，不能延迟赋值（用 `late`）

## 动手练习

1. 用类建模 TaskFlow 的实体：`User`、`Task`、`Project`，并给出 `fromJson`
2. 用 `sealed class` 定义任务详情的四种加载状态，写一个 `switch` 渲染函数
3. 把"可记录创建时间"抽成 mixin，并让 `Task` 使用它

## 验收标准

- 能说清 `extends`、`implements`、`with` 三种复用方式的区别
- 能写出带命名构造器和 factory 构造器的类
- 能用 sealed class + switch 表达式做到穷尽检查
