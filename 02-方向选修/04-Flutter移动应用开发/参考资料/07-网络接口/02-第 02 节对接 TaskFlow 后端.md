> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 02 节：对接 TaskFlow 后端

## 本节目标

- 把 DRF API 的响应映射为 Dart 模型
- 处理分页与统一错误结构
- 用 Mock 数据先开发，再切真实后端

## 一、确认后端接口（DRF 视角）

假设 TaskFlow 后端（learn-fullstack）提供：

```text
GET    /api/tasks/?project=1&page=1
GET    /api/tasks/{id}/
POST   /api/tasks/
PATCH  /api/tasks/{id}/
DELETE /api/tasks/{id}/
```

DRF 默认分页响应：

```json
{
  "count": 42,
  "next": "http://.../api/tasks/?page=2",
  "previous": null,
  "results": [
    { "id": 1, "title": "写教程", "done": false, "priority": 8,
      "created_at": "2026-08-11T10:00:00+08:00" }
  ]
}
```

## 二、分页模型

```dart
class PageResult<T> {
  const PageResult({required this.count, required this.results, this.next});
  final int count;
  final List<T> results;
  final String? next;           // 有下一页才有值
}

PageResult<Task> parseTasks(Map<String, dynamic> json) => PageResult(
  count: json['count'] as int,
  results: (json['results'] as List).map((e) => Task.fromJson(e as Map<String, dynamic>)).toList(),
  next: json['next'] as String?,
);
```

## 三、Repository 实现

```dart
class TaskApiRepository implements TaskRepository {
  TaskApiRepository(this._dio);
  final Dio _dio;

  @override
  Future<PageResult<Task>> fetchTasks({String? projectId, int page = 1}) async {
    final resp = await _dio.get('/api/tasks', queryParameters: {
      if (projectId != null) 'project': projectId,
      'page': page,
    });
    return parseTasks(resp.data as Map<String, dynamic>);
  }

  @override
  Future<Task> createTask(TaskDraft draft) async {
    final resp = await _dio.post('/api/tasks', data: draft.toJson());
    return Task.fromJson(resp.data as Map<String, dynamic>);
  }
}
```

## 四、错误处理统一化

DRF 校验错误结构是 `{"field": ["错误信息"]}`，转换成人话：

```dart
String extractErrorMessage(Object? data) {
  if (data is Map<String, dynamic>) {
    if (data['detail'] is String) return data['detail'] as String;
    return data.entries
        .map((e) => '${e.key}: ${e.value}')
        .join('\n');
  }
  return '请求失败';
}
```

## 五、Mock 先行，后切真实

```dart
class TaskMockRepository implements TaskRepository {
  @override
  Future<PageResult<Task>> fetchTasks({String? projectId, int page = 1}) async {
    await Future.delayed(const Duration(milliseconds: 400));  // 模拟延迟
    return PageResult(
      count: mockTasks.length,
      results: mockTasks,
      next: page < 3 ? '/api/tasks/?page=${page + 1}' : null,
    );
  }
}

final taskRepositoryProvider = Provider<TaskRepository>((ref) {
  final useMock = ref.watch(useMockApiProvider);   // 调试开关
  return useMock
      ? TaskMockRepository()
      : TaskApiRepository(ref.watch(dioProvider));
});
```

这样 UI 开发不被后端阻塞，切换只在 Provider 一处。

## 动手练习

1. 在 TaskFlow 后端（learn-fullstack）确认任务接口的字段与分页结构
2. 写 `TaskApiRepository` 完整 CRUD + 分页
3. 写 Mock Repository，开发 UI 时用 `useMockApi = true`，联调时切 false

## 验收标准

- 能读懂 DRF 分页/错误响应并映射为模型
- UI 与 Repository 解耦，可切换数据源
- 列表支持分页加载更多
