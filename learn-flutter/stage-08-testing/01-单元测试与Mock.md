# 第 01 节：单元测试与 Mock

## 本节目标

- 用 flutter_test 组织单元测试
- 用 mocktail 隔离外部依赖
- 建立"纯逻辑必测、IO 层 Mock"的分层策略

## 一、测试结构

```text
test/
├── features/
│   ├── tasks/
│   │   ├── task_model_test.dart
│   │   └── task_list_notifier_test.dart
│   └── auth/
│       └── auth_notifier_test.dart
└── helpers/
    └── test_utils.dart
```

与你的 pytest 经验对应：

| pytest | Flutter |
|--------|---------|
| `def test_xxx()` | `test('描述', () {...})` |
| `assert` | `expect(actual, matcher)` |
| `@pytest.fixture` | `setUp` / `setUpAll` |
| `mock.patch` | `mocktail` 的 `when` / `verify` |
| `pytest -k xxx` | `flutter test --plain-name "xxx"` |

## 二、第一个测试

```dart
// test/features/tasks/task_model_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:taskflow_app/features/tasks/domain/task.dart';

void main() {
  group('Task 模型', () {
    test('fromJson 解析完整字段', () {
      final task = Task.fromJson({
        'id': 1,
        'title': '写测试',
        'done': true,
        'priority': 8,
      });
      expect(task.id, 1);
      expect(task.title, '写测试');
      expect(task.done, isTrue);
      expect(task.priority, 8);
    });

    test('fromJson 缺失字段使用默认值', () {
      final task = Task.fromJson({'id': 2, 'title': '空'});
      expect(task.done, isFalse);
      expect(task.priority, 0);
    });

    test('copyWith 只更新指定字段', () {
      final task = Task(id: 1, title: 'a', done: false);
      final updated = task.copyWith(done: true);
      expect(updated.done, isTrue);
      expect(updated.title, 'a');          // 未改的字段不变
    });
  });
}
```

## 三、Mock 外部依赖：mocktail

```powershell
flutter pub add dev:mocktail
```

```dart
class MockTaskRepository extends Mock implements TaskRepository {}

void main() {
  late MockTaskRepository repo;
  late ProviderContainer container;

  setUp(() {
    repo = MockTaskRepository();
    container = ProviderContainer(overrides: [
      taskRepositoryProvider.overrideWithValue(repo),
    ]);
  });

  test('加载成功时 state 为数据', () async {
    when(() => repo.fetchTasks(projectId: any(named: 'projectId')))
        .thenAnswer((_) async => [Task(id: 1, title: 't')]);

    final notifier = container.read(taskListProvider.notifier);
    await notifier.load();

    expect(container.read(taskListProvider), hasLength(1));
    verify(() => repo.fetchTasks(projectId: any(named: 'projectId'))).called(1);
  });

  test('加载失败时 state 保持为空并抛出', () async {
    when(() => repo.fetchTasks(projectId: any(named: 'projectId')))
        .thenThrow(const ApiException(message: '网络错误'));
    // ...
  });
}
```

关键点：

- `when` 定义行为，`verify` 断言调用，`any(named:)` 匹配任意参数
- 用 `ProviderContainer(overrides: [...])` 直接测 Notifier，不需要 UI

## 四、覆盖哪些逻辑

按价值排序：

1. **模型**：fromJson / toJson / copyWith / 校验
2. **Notifier/业务逻辑**：状态流转、边界条件
3. **纯工具函数**：格式化、计算
4. **Repository 与 API**：用 MockClient 或 dio adapter（轻量）
5. Widget 测试另开一节

## 五、覆盖率

```powershell
flutter test --coverage
genhtml coverage/lcov.info -o coverage/html   # 生成 HTML 报告
```

目标：核心逻辑（domain + notifier）覆盖率 ≥ 80%。不要追求 UI 代码全覆盖，性价比低。

## 动手练习

1. 为 Task / AuthSession 模型写完整单测
2. 为 TaskListNotifier 写 5 个测试（成功/失败/增删改/排序）
3. 跑覆盖率报告，确认 domain 层 ≥ 80%

## 验收标准

- 会用 mocktail 隔离 Repository
- 会测 Notifier 的状态流转
- 知道 pytest 与 flutter_test 的对应关系
