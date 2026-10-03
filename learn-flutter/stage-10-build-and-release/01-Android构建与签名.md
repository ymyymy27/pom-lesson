# 第 01 节：Android 构建与签名

## 本节目标

- 理解 debug / release 构建的区别
- 配置签名密钥并构建可发布 APK/AAB
- 用 ABI 分包控制体积

## 一、构建模式

| 模式 | 用途 | 特点 |
|------|------|------|
| debug | 开发 | 可调试、体积大、慢 |
| profile | 性能测试 | 接近 release，禁用调试 |
| release | 发布 | 优化、压缩、签名 |

```powershell
flutter run --release
flutter build apk --release
flutter build appbundle --release   # Google Play 推荐格式（AAB）
```

## 二、生成签名密钥

```powershell
keytool -genkeypair -v \
  -keystore taskflow-upload.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias upload
```

**密钥务必备份**：丢失 = 无法给已上架 App 升级，只能换包名重新上架。

## 三、配置签名

`android/key.properties`（不入库）：

```properties
storePassword=你的密码
keyPassword=你的密码
keyAlias=upload
storeFile=taskflow-upload.jks
```

`android/app/build.gradle.kts` 引用：

```kotlin
import java.util.Properties
import java.io.FileInputStream

val keystoreProperties = Properties().apply {
    val f = rootProject.file("key.properties")
    if (f.exists()) load(FileInputStream(f))
}

android {
    signingConfigs {
        create("release") {
            keyAlias = keystoreProperties["keyAlias"] as String?
            keyPassword = keystoreProperties["keyPassword"] as String?
            storeFile = keystoreProperties["storeFile"]?.let { file(it) }
            storePassword = keystoreProperties["storePassword"] as String?
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = true          // R8 压缩
            isShrinkResources = true        // 移除无用资源
        }
    }
}
```

## 四、R8 混淆

混淆缩小体积、增加逆向难度；但反射用的类要保留规则（`android/app/proguard-rules.pro`）：

```proguard
# 保留 Model 序列化（JSON 反射）
-keep class com.taskflow.app.model.** { *; }
# 保留 Gson/JSON 注解
-keepattributes Signature
```

发布前用真实设备完整回归一遍，混淆漏规则是发布崩溃的头号原因。

## 五、ABI 分包

```powershell
flutter build apk --release --split-per-abi
```

产物：

```text
build/app/outputs/flutter-apk/
├── app-arm64-v8a-release.apk    （主流手机）
├── app-armeabi-v7a-release.apk  （旧设备）
└── app-x86_64-release.apk       （模拟器）
```

Google Play 直接用 AAB，平台自动分发对应架构。

## 六、版本管理

`pubspec.yaml`：

```yaml
version: 1.2.3+45
#         ↑    ↑
#      版本号  构建号（Android 每次上传必须递增）
```

CI 里动态注入构建号，避免人工改错。

## 动手练习

1. 生成签名密钥并配置 release 签名
2. 构建 `--split-per-abi` 的 APK，安装到真机验证
3. 开启 R8 后跑一遍冒烟测试

## 验收标准

- 能产出签名完整、可安装的 release APK
- 密钥与 key.properties 已安全备份，且不入库
- 能解释 AAB 与 APK 的区别
