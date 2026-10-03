# 第2课：SKILL.md 结构详解 & 元数据编写

## 1. SKILL.md 的整体结构

SKILL.md 由两大部分组成：**YAML 元数据** 和 **Markdown 正文**。

```markdown
---                          ← YAML 开始标记
name: my-skill-name          ← 必填：技能名称
description: 技能描述...      ← 必填：AI 靠它判断是否加载
version: 1.0                 ← 可选：版本号
author: your-name            ← 可选：作者
---                          ← YAML 结束标记

# 技能标题                    ← 正文开始

## 使用场景
...

## 执行指令
...

## 示例
...

## 行为准则
...
```

这个格式叫做 **YAML Frontmatter** —— 很多工具都用它（Hugo、Jekyll、Obsidian 等），
就是在文件开头用 `---` 包裹一段 YAML 格式的配置信息。

---

## 2. 元数据详解（YAML Frontmatter）

### 2.1 必填字段

#### name（技能名称）

```yaml
name: code-review-helper
```

**规则：**
- 只能使用**小写字母、数字和连字符**（kebab-case）
- 最多 **64 个字符**
- 这就是技能的唯一标识，也是文件夹名
- 有些平台支持用 `/name` 作为斜杠命令直接调用

**好的命名：**
```
code-review-helper        ✅
python-naming-standard    ✅
git-commit-formatter      ✅
```

**坏的命名：**
```
Code Review Helper        ❌ （有大写和空格）
my_skill                  ❌ （用了下划线）
a                         ❌ （太短，不知道干什么）
super-duper-amazing-...   ❌ （太长，超过64字符）
```

#### description（技能描述）

```yaml
description: >-
  为代码添加专业注释。适合缺少文档、可读性差的代码。
  常见触发场景：加注释、写文档、explain code。
```

**这是整个 Skill 最关键的字段！** 因为：
1. AI 启动时**只读取 name 和 description**
2. 用户发送任务后，AI 用 description 判断"这个任务跟我有没有关系"
3. 如果 description 写得不好，AI 就不会加载你的 Skill

**description 写作要点：**
- 说清楚**做什么**（功能）
- 说清楚**什么时候用**（触发场景）
- 列出**触发关键词**（提高匹配率）
- 最多 **1024 个字符**

**好的 description：**
```yaml
description: >-
  当用户要求重构、审查或编写 Python 代码时，
  自动应用团队内部命名规范。
  触发场景：写Python、代码审查、重构、命名规范。
```

**差的 description：**
```yaml
description: 一个很厉害的技能     ← 太模糊，AI 不知道什么时候用
description: Python               ← 信息不足
```

### 2.2 可选字段

```yaml
---
name: pdf-processing
description: 从 PDF 中提取文本和表格，填写表单，并合并文档
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
  tags:
    - pdf
    - document
    - extraction
trigger_keywords:
  - PDF
  - 提取文本
  - 填写表单
  - 合并文档
---
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `license` | 开源许可证 | `Apache-2.0`、`MIT` |
| `version` | 版本号 | `"1.0"` |
| `author` | 作者/组织 | `your-name` |
| `tags` | 标签（便于搜索） | `[python, code-review]` |
| `trigger_keywords` | 触发关键词（提高匹配率） | `[加注释, 写文档]` |

> `trigger_keywords` 是**强烈推荐**的字段，能大幅提高 AI 自动匹配的准确率。

---

## 3. 正文详解（Markdown 部分）

元数据之后就是正文 —— 这是 AI 真正执行时读取的指令。
以下是推荐的正文结构：

### 3.1 技能标题 & 角色设定

```markdown
# Git Commit 规范助手

你现在是「Git Commit 规范专家」。
你的任务是帮助用户编写符合 Conventional Commits 规范的提交信息。
```

**要点：**
- 用 `#` 标题让结构清晰
- 开头可以给 AI 一个**角色身份**（提高专业度）
- 一句话说清楚核心任务

### 3.2 使用场景

```markdown
## 使用场景

当以下情况时使用此技能：
- 用户准备提交代码（git commit）
- 用户询问如何写 commit message
- 用户要求审查已有的 commit 信息
- 用户需要生成 changelog
```

**要点：**
- 明确列出**什么时候该触发**
- 和 description 呼应但可以更详细
- 帮助 AI 更准确地判断

### 3.3 执行指令（核心部分）

```markdown
## 执行指令

### 格式要求
每条 commit message 必须遵循以下格式：

\```
<type>(<scope>): <subject>

<body>

<footer>
\```

### type 类型（必选）
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档变更
- `style`: 代码格式（不影响逻辑）
- `refactor`: 重构（不是新功能也不是修 bug）
- `test`: 添加测试
- `chore`: 构建过程或辅助工具变动

### 规则
1. subject 不超过 50 个字符
2. subject 使用祈使语气（"add" 而非 "added"）
3. body 每行不超过 72 个字符
4. 如果有关联 issue，在 footer 中标注
```

**要点：**
- 这是 Skill 的**灵魂**，写得越具体越好
- 用编号列表确保执行顺序
- 用代码块展示格式要求
- 明确边界条件和约束

### 3.4 示例（Few-shot）

```markdown
## 示例

### 好的示例 ✅
\```
feat(auth): add OAuth2 login support

Implement Google and GitHub OAuth2 providers.
Add token refresh mechanism.

Closes #142
\```

### 坏的示例 ❌
\```
updated stuff          ← 太模糊
fix bug                ← 没说修了什么
Add new feature.       ← 没有 type 前缀
\```
```

**要点：**
- **示例极其重要！** AI 从示例中学习效果最好
- 同时给好例子和坏例子
- 用 ✅ ❌ 标记让 AI 一目了然

### 3.5 行为准则

```markdown
## 行为准则

- 永远不要自己编造 issue 编号
- 如果用户的修改涉及多个模块，建议拆分成多条 commit
- 不确定 type 时，询问用户而不是猜测
- 用中文回复，commit message 本身用英文
```

**要点：**
- 定义 AI **不该做什么**（同样重要！）
- 处理边界情况的策略
- 语言和风格要求

---

## 4. 完整的 SKILL.md 模板

把上面的内容组合起来，这是一个完整的模板：

```markdown
---
name: your-skill-name
description: >-
  简明扼要地说明技能做什么、什么时候用。
  列出常见触发关键词以提高匹配率。
trigger_keywords:
  - 关键词1
  - 关键词2
  - 关键词3
version: 1.0
author: your-name
---

# 技能标题

你现在是「XXX专家」。你的任务是...

## 使用场景

当以下情况时使用此技能：
- 场景1
- 场景2
- 场景3

## 执行指令

### 步骤1：XXX
具体说明...

### 步骤2：XXX
具体说明...

### 规则与约束
1. 规则1
2. 规则2
3. 规则3

## 示例

### 好的示例 ✅
...

### 坏的示例 ❌
...

## 行为准则
- 准则1
- 准则2
- 准则3

## 输出格式
说明输出应该是什么样的（纯文本/JSON/代码块等）
```

---

## 5. SKILL.md 编写的黄金法则

### 法则1：Description 决定生死

```
description 写不好 → AI 不会加载你的 Skill → 等于没写
```

花 50% 的时间在 description 上不过分。

### 法则2：指令要具体，不要抽象

```markdown
# 差 ❌
"请写出好的代码"

# 好 ✅
"所有函数必须以 _internal_ 前缀命名，参数类型使用 type hints，
返回值必须有 docstring 说明"
```

### 法则3：用示例代替解释

AI 从示例中学习的效果远好于纯文字描述。
如果你发现自己写了一大段解释，考虑能不能用一个示例代替。

### 法则4：控制长度

```
SKILL.md 建议控制在 400 行以内
超过 500-800 行时，拆分到子文件中（第3课详细讲）
```

### 法则5：用分隔符结构化

善用 Markdown 的标题（##）、列表（-）、代码块（```）、
分隔线（---）来组织内容，让 AI 更容易解析。

---

## 6. 动手练习

试着为以下场景各写一个 SKILL.md 的元数据部分（只写 `---` 之间的内容）：

**练习1：翻译助手**
```yaml
---
# 你来填写...
---
```

**练习2：代码审查**
```yaml
---
# 你来填写...
---
```

**练习3：技术文章摘要**
```yaml
---
# 你来填写...
---
```

### 参考答案

**练习1：**
```yaml
---
name: translation-helper
description: >-
  中英文互译助手。将中文翻译为地道的英文，或将英文翻译为通顺的中文。
  保持专业术语准确，技术文档风格。
  触发场景：翻译、translate、中译英、英译中。
trigger_keywords:
  - 翻译
  - translate
  - 中译英
  - 英译中
---
```

**练习2：**
```yaml
---
name: code-review-assistant
description: >-
  代码审查助手。检查代码质量、潜在 bug、性能问题和安全隐患。
  给出改进建议并按严重程度排序。
  触发场景：代码审查、code review、review、检查代码。
trigger_keywords:
  - code review
  - 代码审查
  - 检查代码
  - review PR
---
```

**练习3：**
```yaml
---
name: tech-article-summarizer
description: >-
  技术文章摘要生成器。提取文章核心观点、关键技术点和实用建议，
  生成结构化摘要。适合快速了解长篇技术博客或论文。
  触发场景：总结文章、摘要、summarize、概括。
trigger_keywords:
  - 总结
  - 摘要
  - summarize
  - 概括文章
---
```

---

## 7. 小结

| 部分 | 内容 | 重要度 |
|------|------|--------|
| `name` | 技能唯一标识，kebab-case | 必填 |
| `description` | AI 判断是否加载的依据 | 必填，最关键 |
| `trigger_keywords` | 触发关键词列表 | 强烈推荐 |
| `version` / `author` | 版本和作者信息 | 可选 |
| 角色设定 | 给 AI 一个专家身份 | 推荐 |
| 使用场景 | 明确何时触发 | 推荐 |
| 执行指令 | 具体步骤和规则 | 核心 |
| 示例 | 好例子 + 坏例子 | 极其重要 |
| 行为准则 | 定义边界和禁区 | 推荐 |

---

**下一课：** `03_progressive_disclosure.md` - 渐进式披露机制 & 多文件 Skill 组织
