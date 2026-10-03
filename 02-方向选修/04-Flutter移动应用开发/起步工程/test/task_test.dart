import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taskflow_student/main.dart';

void main() {
  test('reject blank input and keep stable ids after deletion', () {
    final store = TaskStore();
    expect(() => store.add('   '), throwsArgumentError);
    final first = store.add(' 阅读 ');
    expect(first.title, '阅读');
    store.remove(first.id);
    expect(store.add('实验').id, 2);
  });

  testWidgets('add, complete and delete a task', (tester) async {
    await tester.pumpWidget(const TaskFlowApp());
    expect(find.text('暂无任务'), findsOneWidget);
    await tester.enterText(find.byKey(const Key('task-input')), '阅读课文');
    await tester.tap(find.text('添加'));
    await tester.pump();
    expect(find.text('阅读课文'), findsOneWidget);
    await tester.tap(find.byType(Checkbox));
    await tester.pump();
    expect(tester.widget<Checkbox>(find.byType(Checkbox)).value, isTrue);
    await tester.tap(find.byTooltip('删除任务'));
    await tester.pump();
    expect(find.text('暂无任务'), findsOneWidget);
  });

  testWidgets('blank input shows useful feedback', (tester) async {
    await tester.pumpWidget(const TaskFlowApp());
    await tester.tap(find.text('添加'));
    await tester.pump();
    expect(find.text('任务名称不能为空'), findsOneWidget);
    expect(find.text('暂无任务'), findsOneWidget);
  });
}
