# 第 08 阶段：测试与工程质量

## 学习目标

完成本阶段后，你将能够：
- 编写 Dart 单元测试并使用 mock 隔离依赖
- 编写 Widget 测试验证交互行为
- 使用 integration_test 与 golden 快照做回归保护
- 配置 lint 规则与 GitHub Actions CI 流水线

## 前置要求

- 完成 Stage 07
- 熟悉测试金字塔与 TDD 思想（`learn-se` / `learn-pytest`）

## 课程内容

| 节 | 课时文件 | 内容 |
|----|-------------|------|
| 1 | `01-单元测试与Mock.md` | test 组织、mockito/mocktail、纯逻辑与 Repository 测试 |
| 2 | `02-Widget测试.md` | pumpWidget、find、tester 交互、异步与计时器处理 |
| 3 | `03-集成测试与Golden.md` | integration_test、golden 快照、平台差异处理 |
| 4 | `04-静态检查与CI.md` | flutter analyze、lint 规则、GitHub Actions 流水线 |

## 练习与产出

- `exercises/`：单元测试 + Widget 测试练习
- `project/`：核心逻辑覆盖率 80%+，登录页/任务列表页补测试
- `.github/workflows/flutter-ci.yml`：PR 自动测试

## 预计时长：4 天

## 验收标准

- `flutter analyze` 无告警
- 核心逻辑单测覆盖率 ≥ 80%
- CI 在推送时自动执行 analyze + test
