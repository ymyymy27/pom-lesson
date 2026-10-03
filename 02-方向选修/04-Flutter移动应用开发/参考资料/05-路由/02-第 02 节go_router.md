> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 02 节：go_router

## 本节目标

- 用 go_router 声明式配置全部路由
- 实现底部导航的 ShellRoute
- 用 redirect 做登录守卫

## 一、为什么用 go_router

对应 React Router v6：URL 驱动、支持深链接、重定向、嵌套布局。Flutter 官方推荐。

```powershell
flutter pub add go_router
```

## 二、基础配置

```dart
final router = GoRouter(
  initialLocation: '/tasks',
  routes: [
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginPage(),
    ),
    GoRoute(
      path: '/tasks',
      builder: (context, state) => const TaskListPage(),
      routes: [
        // 嵌套路由：/tasks/123
        GoRoute(
          path: ':taskId',
          builder: (context, state) =>
              TaskDetailPage(taskId: state.pathParameters['taskId']!),
        ),
      ],
    ),
  ],
);

MaterialApp.router(
  routerConfig: router,
  theme: ...,
)
```

参数读取：

```dart
state.pathParameters['taskId'];      // 路径参数 /tasks/123
state.uri.queryParameters['tab'];    // 查询参数 ?tab=done
state.extra;                          // 任意对象（类型安全传对象）
```

## 三、跳转：go vs push

```dart
// go：类似浏览器跳转，地址变化，栈会"归一化"（重复跳同一页不会叠层）
context.go('/tasks/123');

// push：压栈，保留返回上一页
context.push('/tasks/new');

// 返回
context.pop();
```

经验：**底部导航切换用 go，打开新页面用 push**。

## 四、ShellRoute：底部导航共享布局

```dart
GoRouter(
  routes: [
    ShellRoute(
      builder: (context, state, child) => HomeShell(child: child),
      routes: [
        GoRoute(path: '/tasks', builder: (_, __) => const TaskListPage()),
        GoRoute(path: '/projects', builder: (_, __) => const ProjectListPage()),
        GoRoute(path: '/profile', builder: (_, __) => const ProfilePage()),
      ],
    ),
    GoRoute(path: '/login', builder: (_, __) => const LoginPage()),
  ],
)
```

```dart
class HomeShell extends StatelessWidget {
  const HomeShell({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: switch (GoRouterState.of(context).uri.path) {
          '/projects' => 1,
          '/profile' => 2,
          _ => 0,
        },
        onDestinationSelected: (i) => context.go(['/tasks', '/projects', '/profile'][i]),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.task), label: '任务'),
          NavigationDestination(icon: Icon(Icons.folder), label: '项目'),
          NavigationDestination(icon: Icon(Icons.person), label: '我的'),
        ],
      ),
    );
  }
}
```

ShellRoute 类似 React Router 的嵌套 Layout Route：子页面共享外壳，切换时只换内容区。

## 五、redirect：登录守卫

```dart
GoRouter(
  redirect: (context, state) {
    final isLoggedIn = context.read(authControllerProvider).isLoggedIn;
    final isLoginPage = state.matchedLocation == '/login';

    if (!isLoggedIn && !isLoginPage) {
      return '/login';                       // 未登录 → 踢去登录页
    }
    if (isLoggedIn && isLoginPage) {
      return '/tasks';                       // 已登录 → 不再显示登录页
    }
    return null;                             // 放行
  },
)
```

`redirect` 在每次导航前执行，返回新的路径就重定向。登录状态变化后需要刷新路由判定：

```dart
// 登录成功后
context.pushReplacement('/tasks');
// 或 router.refresh() 重新触发 redirect
```

## 六、错误页

```dart
GoRouter(
  errorBuilder: (context, state) => Scaffold(
    body: Center(
      child: Column(
        children: [
          const Icon(Icons.error_outline, size: 64),
          const SizedBox(height: 12),
          Text('页面不存在：${state.uri}'),
          FilledButton(onPressed: () => context.go('/tasks'), child: const Text('回首页')),
        ],
      ),
    ),
  ),
)
```

## 动手练习

1. 把 TaskFlow 全部页面迁到 go_router（登录、底部导航三页、详情、新建）
2. 实现登录守卫：未登录访问任何受保护页都跳登录
3. 加一个 404 错误页

## 验收标准

- 能写出嵌套路由 + 路径参数
- 能解释 go 与 push 的差异
- 能实现"登录态变化后 redirect 自动生效"
