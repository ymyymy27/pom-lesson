> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 03 节：drift 数据库

## 本节目标

- 建立 drift 表结构与 DAO
- 掌握增删改查与响应式监听
- 理解迁移策略

## 一、为什么用 drift

drift 是 Flutter 上类型安全的 SQLite 封装（对应 Web 的 IndexedDB / 后端的 PostgreSQL）。SQL 能力完整，且带**响应式查询**：表变了，监听它的 UI 自动刷新。

```powershell
flutter pub add drift sqlite3_flutter_libs path_provider path
flutter pub add dev:drift_dev dev:build_runner
```

## 二、定义表

```dart
// lib/features/tasks/data/db/app_database.dart
import 'package:drift/drift.dart';

class Tasks extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get title => text().withLength(min: 1, max: 200)();
  BoolColumn get done => boolean().withDefault(const Constant(false))();
  IntColumn get priority => integer().withDefault(const Constant(0))();
  DateTimeColumn get createdAt => dateTime().withDefault(currentDateAndTime)();
  DateTimeColumn get dueDate => dateTime().nullable()();
  IntColumn get projectId => integer().nullable()();       // 所属项目
  IntColumn get serverId => integer().nullable()();    // 对应后端主键
}

@DriftDatabase(tables: [Tasks])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 1;
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dir = await getApplicationDocumentsDirectory();
    final file = File(p.join(dir.path, 'taskflow.sqlite'));
    return NativeDatabase.createInBackground(file);
  });
}
```

生成：

```powershell
dart run build_runner build --delete-conflicting-outputs
```

## 三、DAO：查询逻辑

```dart
@DriftAccessor(tables: [Tasks])
class TaskDao extends DatabaseAccessor<AppDatabase> with _$TaskDaoMixin {
  TaskDao(super.db);

  // 监听：表变化自动推送
  Stream<List<Task>> watchAll() => select(tasks).watch();

  Future<List<Task>> getByProject(int projectId) =>
      (select(tasks)..where((t) => t.projectId.equals(projectId))).get();

  Future<int> insertTask(TasksCompanion row) =>
      into(tasks).insert(row);

  Future<bool> markDone(int id, bool done) =>
      (update(tasks)..where((t) => t.id.equals(id)))
          .write(TasksCompanion(done: Value(done)));

  Future<int> deleteTask(int id) =>
      (delete(tasks)..where((t) => t.id.equals(id))).go();
}
```

注意：生成的模型类是 `Task`（表名 Tasks 去掉 s），插入时用 `TasksCompanion`：

```dart
await dao.insertTask(
  TasksCompanion.insert(
    title: task.title,
    done: Value(task.done),
    priority: Value(task.priority),
  ),
);
```

## 四、响应式接入 Riverpod

```dart
final taskDaoProvider = Provider<TaskDao>((ref) {
  return TaskDao(ref.watch(dbProvider));
});

// UI 直接监听数据库
final localTasksProvider = StreamProvider<List<Task>>((ref) {
  return ref.watch(taskDaoProvider).watchAll();
});
```

数据库一变，UI 自动更新——本地离线缓存就有了"单一数据源"。

## 五、迁移策略

表结构变了，schemaVersion +1，在 `MigrationStrategy` 里写迁移：

```dart
@override
MigrationStrategy get migration => MigrationStrategy(
  onCreate: (m) async {
    await m.createAll();
  },
  onUpgrade: (m, from, to) async {
    if (from < 2) {
      await m.addColumn(tasks, tasks.dueDate);   // 示例：新增列
    }
  },
);
```

原则：**永远不要改旧版本的表结构定义来迁就旧数据**；用迁移脚本，线上用户的数据才不会丢。

## 动手练习

1. 建 Tasks 表（含 serverId 用于同步），生成代码
2. 写 DAO：插入、按标题模糊搜索、标记完成、删除
3. 用一个 StreamProvider 把"本地任务列表"接到 UI

## 验收标准

- 能独立定义表 + 生成代码 + 读写
- 能解释 Companion 与实体模型的区别
- 能说清 schemaVersion 与迁移的关系
