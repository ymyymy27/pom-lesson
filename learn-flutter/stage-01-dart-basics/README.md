# 第 01 阶段：Dart 3 语言速成（经验者向）

## 学习目标

完成本阶段后，你将能够：
- 读懂并编写 Dart 代码，说出与 TypeScript / Python 的关键差异
- 掌握空安全、记录（record）、模式匹配等 Dart 3 特性
- 熟练使用类、继承、mixin、接口组织代码
- 使用 Future / Stream 编写异步代码
- 管理 pub 依赖并运行单元测试

## 前置要求

- 熟悉任意一门编程语言（TypeScript / Python 优先）
- 会使用终端和包管理器

## 课程内容

| 节 | 课时文件 | 内容 |
|----|-------------|------|
| 1 | `01-Dart语法速览与TypeScript对照.md` | 变量、类型推断、空安全、集合、记录、模式匹配 |
| 2 | `02-面向对象与Mixin.md` | 类、构造器、继承、接口、抽象类、mixin、增强枚举 |
| 3 | `03-函数式与集合操作.md` | 函数、闭包、高阶函数、集合 API、扩展方法 |
| 4 | `04-异步Future与Stream.md` | async/await、Future、Stream、错误传播、并发入门 |
| 5 | `05-泛型错误处理与依赖管理.md` | 泛型、异常、库与导入、pub 依赖、dart test |

## 练习与产出

- `exercises/`：每题一练的 Dart 练习题（含自测）
- `code/`：与 TypeScript 逐条对照的示例代码
- 用 Dart 重写你之前用 Python / TS 写过的某个小模块

## 预计时长：4 天

## 验收标准

- 能说出 Dart 与 TypeScript 的 5 个关键差异（空安全、record、mixin、扩展方法、isolate 等）
- 不查资料能写出带泛型和异步的函数
- `dart test` 全部通过
