# 第 01 节：dio 网络层封装

## 本节目标

- 用 dio 统一管理请求
- 掌握拦截器（日志、鉴权、重试）
- 建立可替换、可测试的网络层

## 一、为什么用 dio

dio 是 Flutter 最流行的 HTTP 客户端（对应 Web 的 Axios）：

- 拦截器（请求/响应/错误）
- 超时、取消、上传下载进度
- FormData、JSON 自动转换

```powershell
flutter pub add dio
```

## 二、基础配置

```dart
final dio = Dio(
  BaseOptions(
    baseUrl: 'https://api.taskflow.example.com',
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 15),
    contentType: 'application/json',
  ),
);
```

## 三、拦截器：横切关注点

```dart
class AuthInterceptor extends Interceptor {
  final TokenStorage storage;
  AuthInterceptor(this.storage);

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await storage.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }
}

class LogInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    debugPrint('→ ${options.method} ${options.uri}');
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    debugPrint('← ${response.statusCode} ${response.requestOptions.uri}');
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    debugPrint('✗ ${err.type} ${err.requestOptions.uri}');
    handler.next(err);
  }
}

dio.interceptors.addAll([
  AuthInterceptor(tokenStorage),
  LogInterceptor(),
]);
```

拦截器与 Web 对照：

| Web | Flutter |
|-----|---------|
| Axios request interceptor 加 token | dio onRequest |
| Axios response interceptor | onResponse / onError |
| 统一错误提示 | onError 转业务异常 |

## 四、超时与重试

```dart
Future<Response> requestWithRetry(
  Dio dio,
  RequestOptions options, {
  int maxRetries = 2,
}) async {
  var retries = 0;
  while (true) {
    try {
      return await dio.fetch(options);
    } on DioException catch (e) {
      final canRetry =
          e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.receiveTimeout ||
          e.type == DioExceptionType.connectionError;

      if (canRetry && retries < maxRetries) {
        retries++;
        await Future.delayed(Duration(seconds: retries * 2));  // 退避
        continue;
      }
      rethrow;
    }
  }
}
```

原则：**只对网络类错误重试**；4xx 业务错误重试没意义。

## 五、取消请求

```dart
final cancelToken = CancelToken();

Future<void> load() async {
  try {
    await dio.get('/tasks', cancelToken: cancelToken);
  } on DioException catch (e) {
    if (e.type == DioExceptionType.cancel) {
      debugPrint('用户取消了请求');
    }
  }
}

// 离开页面时取消
@override
void dispose() {
  cancelToken.cancel('页面销毁');
  super.dispose();
}
```

## 六、统一错误模型

```dart
class ApiException implements Exception {
  final int? statusCode;
  final String message;
  const ApiException({this.statusCode, required this.message});

  @override
  String toString() => 'ApiException($statusCode): $message';
}

// 错误拦截器统一转换
@override
void onError(DioException err, ErrorInterceptorHandler handler) {
  final message = switch (err.type) {
    DioExceptionType.connectionTimeout => '连接超时',
    DioExceptionType.receiveTimeout => '响应超时',
    DioExceptionType.connectionError => '网络不可用',
    DioExceptionType.badResponse => err.response?.data?['detail'] ?? '服务异常(${err.response?.statusCode})',
    _ => '未知错误',
  };
  handler.next(
    DioException(
      requestOptions: err.requestOptions,
      error: ApiException(statusCode: err.response?.statusCode, message: message),
    ),
  );
}
```

UI 层只面对 `ApiException`，不关心 dio 细节。

## 动手练习

1. 封装 `DioProvider`（Riverpod Provider），统一配置 baseUrl 与超时
2. 加日志拦截器，观察每个请求的完整链路
3. 写一个请求 GitHub 公开 API 的示例，处理加载/成功/错误三态

## 验收标准

- 能画出一条请求经过的拦截器链路
- 网络错误能转换为统一的 ApiException
- 支持取消与重试
