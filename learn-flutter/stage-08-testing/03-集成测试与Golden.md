# 第 03 节：集成测试与 Golden

## 本节目标

- 用 integration_test 在真机/模拟器上跑端到端流程
- 用 golden 快照做 UI 回归

## 一、集成测试：真实环境端到端

```powershell
flutter pub add dev:integration_test --sdk=flutter
```

```dart
// integration_test/app_flow_test.dart
import 'package:integration_test/integration_test.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('登录 → 创建任务 → 列表出现', (tester) async {
    app.main();
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('emailField')), 'demo@taskflow.app');
    await tester.enterText(find.byKey(const Key('passwordField')), 'password123');
    await tester.tap(find.byKey(const Key('loginButton')));
    await tester.pumpAndSettle(const Duration(seconds: 1));

    await tester.tap(find.byKey(const Key('fabAdd')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('titleField')), '端到端任务');
    await tester.tap(find.byKey(const Key('saveButton')));
    await tester.pumpAndSettle(const Duration(seconds: 1));

    expect(find.text('端到端任务'), findsOneWidget);
  });
}
```

运行：

```powershell
flutter test integration_test -d windows
flutter test integration_test -d <Android设备ID>
```

集成测试的价值：验证**真链路**（登录 → API → 数据库 → UI），适合发布前跑冒烟。代价：慢、依赖环境，不适合频繁跑。

## 二、Golden 测试：UI 快照回归

Golden = 把组件渲染结果存成 PNG，之后每次测试对比像素。

```dart
testWidgets('任务卡片 golden', (tester) async {
  await tester.pumpWidget(
    const MaterialApp(
      home: Scaffold(
        body: TaskCard(task: Task(id: 1, title: '示例任务', priority: 8)),
      ),
    ),
  );

  await expectLater(
    find.byType(TaskCard),
    matchesGoldenFile('goldens/task_card.png'),
  );
});
```

首次生成：

```powershell
flutter test --update-goldens
```

之后每次跑测试都对比；UI 意外变化会失败。

## 三、Golden 注意事项

- 字体渲染跨平台有差异，CI 与本地要一致（可固定字体或接受平台差异）
- 动画/时间相关组件要固定时间（注入固定 clock）
- 只对**稳定组件**做 golden（按钮、卡片），不对整页做
- golden 文件入库，评审改动时能看到 diff

## 四、测试金字塔在 Flutter 的落点

```text
            ╱ 集成测试（少量：关键用户流程）
          ╱  Widget 测试（适中：页面交互）
        ╱   单元测试（大量：模型/逻辑）
```

比例参考：单测 70% / Widget 20% / 集成 10%。

## 动手练习

1. 给"登录 → 首页"写一条集成测试（用 Mock 或测试后端）
2. 给 PriorityBadge、TaskCard 生成 golden
3. 故意改一个样式，验证 golden 测试能抓住回归

## 验收标准

- 能在 Windows/Android 上跑通集成测试
- golden 变更流程熟悉（update → review → 提交）
- 能说出测试金字塔的比例与理由
