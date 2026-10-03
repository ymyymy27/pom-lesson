> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 02 节：Widget 测试

## 本节目标

- 用 testWidgets 渲染组件并断言
- 模拟点击、输入等交互
- 隔离网络依赖，让测试稳定

## 一、最小 Widget 测试

```dart
testWidgets('按钮点击后计数增加', (tester) async {
  await tester.pumpWidget(const CounterApp());

  expect(find.text('0'), findsOneWidget);

  await tester.tap(find.byIcon(Icons.add));
  await tester.pump();                      // 触发重建

  expect(find.text('1'), findsOneWidget);
});
```

常用查找器：

```dart
find.text('登录')              // 按文本
find.byIcon(Icons.add)         // 按图标
find.byType(TextField)         // 按类型
find.byKey(const Key('submit'))// 按 key（推荐给重要控件加 key）
find.widgetWithText(FilledButton, '登录')
```

## 二、输入与表单测试

```dart
testWidgets('表单校验：空标题提示错误', (tester) async {
  await tester.pumpWidget(
    const ProviderScope(child: MaterialApp(home: NewTaskPage())),
  );

  await tester.enterText(
    find.byKey(const Key('titleField')),
    '',
  );
  await tester.tap(find.byKey(const Key('submitButton')));
  await tester.pump();

  expect(find.text('请输入标题'), findsOneWidget);
});
```

## 三、等待异步：pump 家族

```dart
await tester.pump();                    // 触发一帧
await tester.pump(const Duration(seconds: 1));  // 推进假时钟
await tester.pumpAndSettle();           // 反复 pump 直到没有动画/请求
```

注意：

- 有**无限动画**（转圈 loading）时 `pumpAndSettle` 会超时，改用 `pump` 固定次数
- 真实网络请求不要出现在 Widget 测试里（会失败/不稳定），用 Mock Repository

## 四、注入 Mock，隔离网络

```dart
testWidgets('列表页显示任务', (tester) async {
  final repo = MockTaskRepository();
  when(() => repo.fetchTasks(projectId: any(named: 'projectId')))
      .thenAnswer((_) async => [Task(id: 1, title: '测试任务')]);

  await tester.pumpWidget(
    ProviderScope(
      overrides: [taskRepositoryProvider.overrideWithValue(repo)],
      child: const MaterialApp(home: TaskListPage()),
    ),
  );
  await tester.pumpAndSettle();

  expect(find.text('测试任务'), findsOneWidget);
});
```

## 五、常见断言

```dart
expect(find.text('加载失败'), findsNothing);   // 不存在
expect(find.byType(CircularProgressIndicator), findsOneWidget);
expect(tester.takeException(), isNull);         // 没有未捕获异常
```

## 动手练习

1. 给登录页写 3 个测试：空表单、格式错误、提交成功跳转
2. 给任务列表页写测试：Mock 返回 2 条数据 → 渲染 2 张卡片；失败 → 显示错误视图
3. 给 PriorityBadge 写测试：不同优先级显示不同颜色/文案

## 验收标准

- 能写出交互类 Widget 测试（点击、输入、异步加载）
- 测试中无真实网络请求
- 知道 pump 与 pumpAndSettle 的取舍
