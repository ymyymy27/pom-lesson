import 'package:flutter/material.dart';

void main() => runApp(const TaskFlowApp());

class Task {
  Task(this.id, this.title, {this.done = false});
  final int id;
  final String title;
  bool done;
}

class TaskStore {
  final List<Task> tasks = [];
  int _nextId = 1;

  Task add(String rawTitle) {
    final title = rawTitle.trim();
    if (title.isEmpty) {
      throw ArgumentError('任务名称不能为空');
    }
    final task = Task(_nextId++, title);
    tasks.add(task);
    return task;
  }

  void remove(int id) => tasks.removeWhere((task) => task.id == id);
}

class TaskFlowApp extends StatelessWidget {
  const TaskFlowApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'TaskFlow校园任务助手',
        theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
        home: const TaskPage(),
      );
}

class TaskPage extends StatefulWidget {
  const TaskPage({super.key});
  @override
  State<TaskPage> createState() => _TaskPageState();
}

class _TaskPageState extends State<TaskPage> {
  final store = TaskStore();
  final controller = TextEditingController();
  String? error;

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  void addTask() {
    try {
      setState(() {
        store.add(controller.text);
        controller.clear();
        error = null;
      });
    } on ArgumentError {
      setState(() => error = '任务名称不能为空');
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('TaskFlow校园任务助手')),
        body: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(children: [
            Row(children: [
              Expanded(
                  child: TextField(
                key: const Key('task-input'),
                controller: controller,
                decoration: InputDecoration(labelText: '新任务', errorText: error),
                onSubmitted: (_) => addTask(),
              )),
              const SizedBox(width: 12),
              FilledButton(onPressed: addTask, child: const Text('添加')),
            ]),
            const SizedBox(height: 16),
            const Text('此版使用内存，重新启动后任务清空。'),
            Expanded(
              child: store.tasks.isEmpty
                  ? const Center(child: Text('暂无任务'))
                  : ListView(children: [
                      for (final task in store.tasks)
                        ListTile(
                          key: ValueKey(task.id),
                          leading: Checkbox(
                              value: task.done,
                              onChanged: (value) =>
                                  setState(() => task.done = value ?? false)),
                          title: Text(task.title,
                              style: TextStyle(
                                  decoration: task.done
                                      ? TextDecoration.lineThrough
                                      : null)),
                          trailing: IconButton(
                              tooltip: '删除任务',
                              icon: const Icon(Icons.delete_outline),
                              onPressed: () => setState(() => store.remove(task.id))),
                        ),
                    ]),
            ),
          ]),
        ),
      );
}
