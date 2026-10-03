# 第3课：渐进式披露机制 & 多文件 Skill 组织

## 1. 什么是渐进式披露？

### 问题场景

假设你写了一个超详细的 Skill，包括：
- 20 条执行规则
- 15 个示例
- 3 个参考文档
- 2 个可执行脚本

如果 AI 每次启动都把这些**全部加载**到上下文窗口中：
- 浪费大量 token（要花钱！）
- AI 处理速度变慢
- 其他重要信息被挤出上下文窗口
- 大部分时候根本用不到这些内容

### 解决方案：渐进式披露（Progressive Disclosure）

**核心思想：只在需要时才加载信息，像洋葱一样一层一层展开。**

```
第1层：元数据（始终加载）
    AI 启动时只读取 name + description
    几十个 Skill 加起来也就几百个 token
        |
        v
第2层：核心指令（按需加载）
    用户任务匹配到某个 Skill 后
    才读取该 SKILL.md 的完整正文
        |
        v
第3层：资源文件（按需加载）
    执行过程中需要模板/示例/参考资料时
    才读取对应的子文件
        |
        v
第4层：脚本执行（按需触发）
    需要运行代码时才执行 scripts/ 里的脚本
    脚本本身不加载到上下文中
```

### 类比理解

| 层级 | 类比 | Token 消耗 |
|------|------|-----------|
| 第1层：元数据 | 书的目录页 | 极小 |
| 第2层：核心指令 | 翻到对应的章节 | 中等 |
| 第3层：资源文件 | 看章节里引用的附录 | 按需 |
| 第4层：脚本执行 | 做章节里的实验 | 不消耗 token |

---

## 2. 从单文件到多文件 Skill

### 阶段1：单文件 Skill（入门）

当你的 Skill 比较简单（< 200行）时，一个 SKILL.md 就够了：

```
my-simple-skill/
└── SKILL.md              ← 所有内容都在这里
```

### 阶段2：多文件 Skill（进阶）

当 Skill 变复杂（> 500行），就需要拆分：

```
my-complex-skill/
├── SKILL.md              ← 核心指令（建议 < 400行）
├── examples/             ← 示例文件
│   ├── good-example.md
│   └── bad-example.md
├── references/           ← 参考文档
│   ├── style-guide.md
│   └── naming-rules.md
├── templates/            ← 模板文件
│   ├── component.tsx.md
│   └── api-handler.md
└── scripts/              ← 可执行脚本
    ├── validate.py
    └── format-check.sh
```

### 为什么要拆分？

| 不拆分（全放 SKILL.md） | 拆分到子文件 |
|------------------------|------------|
| 一次性加载所有内容 | 按需加载需要的部分 |
| Token 浪费严重 | Token 使用高效 |
| 文件过长难以维护 | 结构清晰好维护 |
| AI 容易"迷路" | AI 精准获取需要的信息 |

---

## 3. 多文件 Skill 的目录结构

### 3.1 推荐目录结构

```
my-skill/
├── SKILL.md              ← 必须：核心指令 + 元数据
│
├── templates/            ← 可选：常用模板
│   ├── react-component.md    AI 需要生成组件时读取
│   └── api-endpoint.md       AI 需要写 API 时读取
│
├── examples/             ← 可选：好例子和反例
│   ├── good.md               展示正确做法
│   └── anti-pattern.md       展示错误做法
│
├── references/           ← 可选：规范和参考文档
│   ├── coding-standard.md    编码规范
│   └── naming-convention.md  命名约定
│
└── scripts/              ← 可选：可执行代码
    ├── lint-check.py         代码检查脚本
    └── format.sh             格式化脚本
```

### 3.2 各目录的作用

#### templates/（模板）

存放 AI 生成内容时参考的模板：

```markdown
<!-- templates/react-component.md -->

# React 函数组件标准模板

\```tsx
import React from 'react';

interface ${ComponentName}Props {
  // props 定义
}

export const ${ComponentName}: React.FC<${ComponentName}Props> = ({
  // 解构 props
}) => {
  return (
    <div>
      {/* 组件内容 */}
    </div>
  );
};
\```

## 规则
- 使用函数组件，不用 class 组件
- Props 必须用 interface 定义
- 组件名使用 PascalCase
```

#### examples/（示例）

存放好的和坏的示例：

```markdown
<!-- examples/good.md -->

# 正确示例 ✅

## 示例1：简单查询
输入：用户要查询订单状态
输出：
\```sql
SELECT order_id, status, updated_at
FROM orders
WHERE user_id = :user_id
ORDER BY updated_at DESC
LIMIT 10;
\```

## 示例2：关联查询
...
```

```markdown
<!-- examples/anti-pattern.md -->

# 错误示例 ❌

## 反例1：SELECT *
\```sql
SELECT * FROM orders;    ← 永远不要用 SELECT *
\```

原因：浪费带宽，暴露不必要的字段

## 反例2：没有索引的大表查询
...
```

#### references/（参考文档）

存放 AI 需要遵循的规范：

```markdown
<!-- references/coding-standard.md -->

# 团队编码规范 v2.1

## 命名规则
- 变量：camelCase
- 常量：UPPER_SNAKE_CASE
- 类名：PascalCase
- 文件名：kebab-case

## 缩进
- 使用 2 个空格，不用 Tab
...
```

#### scripts/（脚本）

存放可执行的辅助脚本：

```python
# scripts/validate-props.py
import sys
import re

def validate_props(code: str) -> list:
    """检查 React 组件的 Props 是否符合规范"""
    issues = []
    if 'any' in code:
        issues.append("禁止使用 any 类型")
    if not re.search(r'interface \w+Props', code):
        issues.append("Props 必须用 interface 定义")
    return issues
```

---

## 4. 在 SKILL.md 中引用子文件

关键来了：怎么让 AI 知道什么时候去读子文件？

### 方法1：在指令中直接引用路径

```markdown
## 执行指令

### 生成 React 组件时
参考 `templates/react-component.md` 的标准结构。

### 审查代码时
对照 `references/coding-standard.md` 检查是否合规。

### 需要示例时
查看 `examples/good.md` 了解正确做法。
如果发现问题，参考 `examples/anti-pattern.md` 中的反例说明。

### 需要验证时
执行 `scripts/validate-props.py` 检查 Props 类型。
```

AI 看到这些路径引用后，会在需要时**自动读取对应文件**，而不是一次性全部加载。

### 方法2：条件触发

```markdown
## 执行指令

1. 分析用户的代码或需求
2. 如果是**新建组件** → 读取 `templates/react-component.md`
3. 如果是**代码审查** → 读取 `references/coding-standard.md`
4. 如果**不确定如何处理** → 读取 `examples/good.md` 获取灵感
5. 只有当用户**明确要求验证**时 → 执行 `scripts/validate-props.py`
```

这种写法更精确地控制了"什么条件下加载什么"。

---

## 5. 实际案例：React 组件审查 Skill

下面是一个完整的多文件 Skill 示例：

### 目录结构

```
react-component-review/
├── SKILL.md
├── templates/
│   ├── functional.tsx.md
│   └── hooks-pattern.md
├── examples/
│   ├── good.md
│   └── anti-pattern.md
├── references/
│   ├── hooks-rules.md
│   └── naming-convention.md
└── scripts/
    └── check-deps.py
```

### SKILL.md 内容

```markdown
---
name: react-component-review
description: >-
  审查 React 组件代码质量。检查 Hooks 使用规范、组件结构、
  Props 类型定义、性能优化机会。
  触发场景：审查React、review component、检查组件。
trigger_keywords:
  - react review
  - 审查组件
  - 检查 react
  - component review
version: 1.0
author: team-frontend
---

# React 组件审查专家

你是一名资深 React 前端工程师，专门审查 React 组件代码。

## 使用场景
- 用户提交 React 组件代码要求审查
- 用户询问组件写法是否正确
- 用户要求优化现有组件

## 审查流程

### 第1步：结构检查
- 是否使用函数组件（不允许 class 组件）
- Props 是否有 TypeScript 类型定义
- 组件是否过大（超过 200 行建议拆分）

### 第2步：Hooks 检查
- 对照 `references/hooks-rules.md` 检查 Hooks 使用
- 检查依赖数组是否完整
- 检查是否有不必要的 useEffect

### 第3步：性能检查
- 是否需要 useMemo / useCallback
- 是否有不必要的重渲染
- 列表是否有 key

### 第4步：输出报告
按以下格式输出：

\```
## 审查报告

### 🔴 严重问题（必须修复）
...

### 🟡 建议改进
...

### 🟢 做得好的地方
...
\```

## 行为准则
- 给出标准结构时，参考 `templates/functional.tsx.md`
- 发现 Hooks 违规时，引用 `references/hooks-rules.md` 具体条款
- 不确定时查看 `examples/good.md` 和 `examples/anti-pattern.md`
- 始终给出修改后的代码示例，不只是指出问题
```

---

## 6. 上下文窗口的变化过程

让我们用时间线看看渐进式披露如何工作：

```
T0: AI 启动
    上下文 = [系统提示词] + [所有Skill的name+description]
    Token消耗: 很小
        |
        v
T1: 用户说 "帮我审查这个React组件"
    AI 判断: 匹配 react-component-review Skill！
        |
        v
T2: 加载 SKILL.md 正文
    上下文 += [SKILL.md 完整内容]
    Token消耗: 中等（约 400 行）
        |
        v
T3: 审查到 Hooks 问题
    AI 需要具体规则 → 加载 references/hooks-rules.md
    上下文 += [hooks-rules.md]
    Token消耗: 按需增加
        |
        v
T4: 要给出正确写法
    AI 需要模板 → 加载 templates/functional.tsx.md
    上下文 += [functional.tsx.md]
    Token消耗: 按需增加
        |
        v
T5: 输出审查报告
    按 SKILL.md 定义的格式输出
    结束
```

**关键点：** 如果用户的组件没有 Hooks 问题，T3 就不会发生，省下了 token！

---

## 7. Skill 拆分的判断标准

### 什么时候保持单文件？

- SKILL.md 在 200 行以内
- 没有复杂的模板或大量示例
- 是一个简单的规则集

### 什么时候拆分为多文件？

- SKILL.md 超过 400-500 行
- 有多个使用场景，每个场景需要不同的参考资料
- 有可复用的模板
- 有需要执行的脚本
- 多人协作维护

### 拆分原则

```
核心原则
├── 核心规则 → 留在 SKILL.md
├── 详细资料 → 放入 references/
├── 输入输出模板 → 放入 templates/
├── 具体示例 → 放入 examples/
└── 可执行逻辑 → 放入 scripts/
```

---

## 8. 动手练习

### 练习：将一个臃肿的 SKILL.md 拆分为多文件结构

假设你有一个 800 行的 `api-design-helper/SKILL.md`，内容包括：
- REST API 设计规范（200 行）
- 正确的 API 示例（150 行）
- 错误的 API 示例（100 行）
- URL 命名规范（80 行）
- HTTP 状态码参考表（120 行）
- 请求/响应模板（150 行）

请思考：如何拆分？哪些留在 SKILL.md？哪些放到子文件？

### 参考答案

```
api-design-helper/
├── SKILL.md                        ← 约 150 行
│   （保留：角色设定、使用场景、审查流程、行为准则）
│
├── examples/
│   ├── good-api.md                 ← 150 行（正确示例）
│   └── bad-api.md                  ← 100 行（错误示例）
│
├── references/
│   ├── url-naming.md               ← 80 行（URL规范）
│   └── http-status-codes.md        ← 120 行（状态码表）
│
└── templates/
    └── request-response.md         ← 150 行（请求响应模板）
```

SKILL.md 从 800 行缩减到约 150 行，剩余内容按需加载。

---

## 9. 小结

| 概念 | 说明 |
|------|------|
| 渐进式披露 | 只在需要时才加载信息，分层展开 |
| 第1层：元数据 | name + description，始终加载 |
| 第2层：核心指令 | SKILL.md 正文，匹配后加载 |
| 第3层：资源文件 | 子文件，执行过程中按需加载 |
| 第4层：脚本 | scripts/，需要时才执行 |
| templates/ | 生成内容时参考的模板 |
| examples/ | 好例子和反例 |
| references/ | 规范和参考文档 |
| scripts/ | 可执行的辅助脚本 |
| 拆分标准 | SKILL.md 超过 400 行时考虑拆分 |

---

**下一课：** `04_cross_platform.md` - 跨平台 Skill 适配（Claude Code / Copilot / Cursor / Windsurf）
