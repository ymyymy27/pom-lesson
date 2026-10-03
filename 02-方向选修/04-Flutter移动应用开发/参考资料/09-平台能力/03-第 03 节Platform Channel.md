> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 03 节：Platform Channel

## 本节目标

- 理解 Dart 与原生代码互调的边界
- 用 MethodChannel 调用原生方法
- 用 EventChannel 接收原生事件流

## 一、什么时候需要原生代码

Flutter 插件覆盖了大部分场景；以下情况才需要写原生：

- 系统 API 没有对应插件
- 性能敏感的密集计算（原生侧）
- 复用公司已有的原生 SDK

## 二、MethodChannel：调用原生方法

Dart 侧：

```dart
import 'package:flutter/services.dart';

const _channel = MethodChannel('taskflow/native');

Future<String> getDeviceInfo() async {
  try {
    final result = await _channel.invokeMethod<String>('getDeviceInfo');
    return result ?? 'unknown';
  } on PlatformException catch (e) {
    throw ApiException(message: '原生调用失败: ${e.message}');
  }
}
```

Android 侧（Kotlin，`MainActivity.kt`）：

```kotlin
class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            "taskflow/native"
        ).setMethodCallHandler { call, result ->
            when (call.method) {
                "getDeviceInfo" -> result.success("Android ${android.os.Build.VERSION.RELEASE}")
                else -> result.notImplemented()
            }
        }
    }
}
```

iOS 侧（Swift，`AppDelegate.swift`）：

```swift
let controller = window?.rootViewController as! FlutterViewController
let channel = FlutterMethodChannel(name: "taskflow/native",
                                   binaryMessenger: controller.binaryMessenger)
channel.setMethodCallHandler { call, result in
  if call.method == "getDeviceInfo" {
    result("iOS \(UIDevice.current.systemVersion)")
  } else {
    result(FlutterMethodNotImplemented)
  }
}
```

对应 Web：`window` 的原生能力（如 navigator）就是 JS 与浏览器原生 API 的通道。

## 三、EventChannel：原生事件流

Dart 侧：

```dart
const _eventChannel = EventChannel('taskflow/battery');

Stream<int> batteryLevel() {
  return _eventChannel.receiveBroadcastStream().map((e) => e as int);
}
```

Android 侧要点：`EventChannel.StreamHandler`，`onListen` 开始上报，`onCancel` 停止。

## 四、类型映射

| Dart | Android | iOS |
|------|---------|-----|
| null | null | NSNull |
| bool | Boolean | NSNumber(bool) |
| int | Int | NSNumber |
| double | Double | NSNumber |
| String | String | NSString |
| List | List | NSArray |
| Map | Map | NSDictionary |

只传可序列化类型，不要传函数/对象引用。

## 五、可测试性：Platform Interface

直接把 `MethodChannel` 写死在业务代码里难以测试。正确姿势是抽象：

```dart
abstract class NativeInfo {
  Future<String> getDeviceInfo();
}

class MethodChannelNativeInfo implements NativeInfo {
  // 上面 MethodChannel 实现
}

class FakeNativeInfo implements NativeInfo {
  @override
  Future<String> getDeviceInfo() async => '测试设备';
}
```

测试时注入 Fake，原生代码留到集成测试。

## 动手练习

1. 实现 `getBatteryLevel`（MethodChannel，Android 原生侧写 Kotlin）
2. 实现一个 EventChannel 输出系统时间变化
3. 为 NativeInfo 写 Fake 并接入单测

## 验收标准

- 能说清 MethodChannel / EventChannel 的适用场景
- 能独立完成一次 Dart ↔ Kotlin 的调用
- 原生能力被抽象，业务代码可测试
