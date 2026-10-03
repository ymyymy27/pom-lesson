# 第 01 节：Dart 语法速览（与 TypeScript 对照）

## 本节目标

- 快速建立 Dart 的语法直觉，不再把它当"新语言"学
- 掌握空安全、`final`/`const`、集合、record、模式匹配
- 能直接阅读 Flutter 示例代码

## 一、一句话理解 Dart

Dart 是 Google 开发的强类型语言，语法风格和 TypeScript / Java 同族：大括号、分号、`class`、`=>`。你已有的 TS 经验 80% 可以直接平移，剩下的 20% 是 Dart 特有的规则（最典型的是**空安全**）。

## 二、基础声明：var / final / const

| 关键字 | 含义 | 对应 TS |
|--------|------|---------|
| `var` | 类型推断，可重新赋值 | `let` + 类型推断 |
| `final` | 只能赋值一次，运行期确定 | `const`（注意语义不同） |
| `const` | 编译期常量，值不可变 | `as const` / 字面量 |

```dart
var count = 1;            // int，可改
final apiBase = 'https://api.example.com';  // 运行期定值，不可改
const timeout = 5;        // 编译期常量
```

> 与 TS 的关键差异：Dart 中 `final` 只保证"变量不能被重新赋值"，不保证"对象不可变"；TS 的 `const` 也是这个语义，不要被名字误导。

## 三、空安全（最重要的差异）

TS 靠 `strictNullChecks` 和类型体操处理 `null`；Dart 把可空性直接写进类型系统，**编译器强制你处理**。

```dart
String name = '张三';       // 非空类型
String? nickname;           // 可空类型，默认 null

// 三种常见处理方式：
final a = nickname ?? '默认昵称';   // 兜底
final b = nickname?.toUpperCase();  // 安全调用，b 是 String?
final c = nickname!;                // 断言非空（只有确定非空时才用）

late String later;   // 延迟初始化：声明时不赋值，首次访问前必须赋值
```

对照 TS：

```ts
// TypeScript
let nickname: string | null = null;
const a = nickname ?? '默认昵称';
```

**规则**：可空值不能直接当非空值用，编译器会报错。这不是麻烦，而是把"空指针崩溃"提前到编译期消灭。

## 四、内置类型与集合

```dart
// 基础类型
int age = 18;
double price = 19.9;
bool ok = true;
String s = 'hello ${age + 1}';   // 字符串插值

// List（相当于 TS 数组）
var tasks = <String>['学习', '编码'];
tasks.add('复盘');
var copy = [...tasks];           // 展开

// Set
var tags = <String>{'urgent', 'work'};

// Map（相当于 TS 对象/Map）
var task = <String, dynamic>{'id': 1, 'title': '写教程'};

// collection-if / collection-for（类似 JSX 的条件渲染）
var items = [for (var i = 0; i < 3; i++) i, if (ok) 99];
```

## 五、Record（Dart 3 新特性，TS 没有）

Record 是无名字的轻量组合类型，适合临时返回多个值：

```dart
// 位置记录
var pair = (1, 'one');
print(pair.$1);   // 1

// 命名记录
var user = (id: 1, name: '张三');
print(user.name);

// 函数返回多个值
(int, String) parse() => (200, 'OK');
final (code, message) = parse();   // 解构
```

## 六、模式匹配（Dart 3）

switch 从"语句"升级为"表达式"，且支持解构：

```dart
String describe(int code) => switch (code) {
  200 => '成功',
  404 => '未找到',
  _ => '其他',
};

// 解构 + 条件
var point = (x: 3, y: 4);
if (point case (x: var x, y: var y) when x > 0) {
  print('第一象限：$x,$y');
}
```

对照 TS：TS 需要 `switch` 语句 + 手动解构，Dart 3 的 `switch` 表达式和 pattern 更接近 Rust / Python 3.10+ 的 match。

## 七、控制流速览

```dart
for (var i = 0; i < 5; i++) { }
for (final t in tasks) { }
while (ok) { }
if (count > 0 && count < 10) { } else if (count == 0) { }
```

## 常见坑

- `const` 只能用编译期可确定的值；从函数返回的值必须用 `final`
- 字符串插值用 `$name` 或 `${expr}`，不是 `+` 拼接（虽然 `+` 也能用）
- `dynamic` 不是 `Object`：`dynamic` 关闭类型检查，尽量不用

## 动手练习

1. 把下面的 TS 代码改写成 Dart：

```ts
let user: { id: number; name: string | null } = { id: 1, name: null };
const displayName = user.name ?? '匿名';
const labels = [1, 2, 3].map((n) => `#${n}`);
```

2. 写一个返回 record 的函数，返回"最大数 + 它出现的下标"，并在 main 里解构打印。

## 验收标准

- 能解释 `?`、`!`、`??`、`late` 各自的作用
- 能说清 `var`、`final`、`const` 的区别
- 能用 record + 模式匹配重写一个之前写过的"返回多值"函数
