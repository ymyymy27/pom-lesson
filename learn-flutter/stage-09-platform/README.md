# 第 09 阶段：平台能力与原生集成

## 学习目标

完成本阶段后，你将能够：
- 理解并处理 Android / iOS 权限模型与隐私合规
- 集成相机、相册、定位、本地与远程通知
- 使用 Platform Channel 与原生代码互调
- 完成 Web / 桌面 / 平板响应式适配
- 使用 DevTools 做性能剖析并优化包体积

## 前置要求

- 完成 Stage 08
- 建议准备一台 Android 真机（USB 调试）

## 课程内容

| 节 | 课时文件 | 内容 |
|----|-------------|------|
| 1 | `01-权限与隐私.md` | 权限模型、Manifest/Info.plist 声明、权限请求库 |
| 2 | `02-相机相册定位通知.md` | image_picker/camera、location、本地与远程通知 |
| 3 | `03-PlatformChannel.md` | MethodChannel/EventChannel、原生侧实现、平台隔离测试 |
| 4 | `04-响应式与多端适配.md` | 响应式布局、窗口尺寸、Web 部署、桌面端差异 |
| 5 | `05-性能剖析与包体积.md` | DevTools 性能剖析、const/懒加载、tree-shake、启动优化 |

## 练习与产出

- `exercises/`：权限申请与 Platform Channel 练习
- `project/`：任务拍照上传 + 通知推送 + 性能分析报告

## 预计时长：5 天

## 验收标准

- Android 真机上可拍照上传任务附件
- 收到任务变更推送并可点击跳转
- 产出性能分析报告并列出 3 项已做的优化
