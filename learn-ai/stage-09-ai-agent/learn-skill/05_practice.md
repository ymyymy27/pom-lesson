# 第5课：实战演练 —— 从零创建你的第一个 Skill

## 1. 本课目标

这节课我们从零开始，手把手创建一个完整的 Skill，并在实际环境中验证它的效果。

**我们要创建的 Skill：「技术文章转公众号」**

功能：把一篇技术文章自动转换为公众号排版风格，包括：
- 添加吸引人的标题
- 调整段落结构
- 添加引导语和总结
- 优化排版格式
- 输出 Markdown 格式（可直接粘贴到公众号编辑器）

---

## 2. 第1步：创建目录结构

### 选择你的 AI 工具

根据你使用的工具，选择对应的命令：

**Claude Code 用户：**
```powershell
# 在项目根目录下运行
mkdir -p .claude/skills/tech-article-to-wechat
```

**Cursor 用户：**
```powershell
# 在项目根目录下运行
mkdir -p .cursor/skills/tech-article-to-wechat
```

**Windsurf 用户：**
```powershell
# 在项目根目录下运行
mkdir .windsurf\workflows -Force
```

**GitHub Copilot 用户：**
```powershell
# 在项目根目录下运行
mkdir -p .github/skills/tech-article-to-wechat
```

> 下面的教程以 Claude Code 为主要示例，其他平台只需调整文件路径。

---

## 3. 第2步：编写 SKILL.md

### 3.1 先写元数据

在对应目录下创建 `SKILL.md` 文件（Windsurf 用户创建 `tech-article-to-wechat.md`）。

首先写好元数据部分：

```yaml
---
name: tech-article-to-wechat
description: >-
  将技术文章转换为微信公众号排版风格。自动添加吸引人的标题、
  引导语、段落优化、要点提炼和总结。
  输出 Markdown 格式，可直接粘贴到公众号编辑器。
  触发场景：转公众号、公众号排版、文章改写、wechat article。
trigger_keywords:
  - 公众号
  - 转公众号
  - 公众号排版
  - 文章改写
  - wechat
version: 1.0
author: learner
---
```

**写作思路：**
- `name`：简洁的 kebab-case 命名
- `description`：说清楚做什么 + 什么时候用 + 输出什么格式
- `trigger_keywords`：列出用户可能说的触发词

### 3.2 写角色设定和使用场景

```markdown
# 技术文章转公众号助手

你是一名资深的技术自媒体编辑，擅长将专业技术文章改写为
适合微信公众号阅读的风格，既保持技术准确性，又让非专业读者也能读懂。

## 使用场景

当以下情况时使用此技能：
- 用户提供一篇技术文章/博客，要求转换为公众号风格
- 用户要求优化技术文章的排版和可读性
- 用户需要为技术内容添加引导语或总结
```

### 3.3 写执行指令（核心部分）

```markdown
## 执行指令

按照以下步骤处理用户提供的技术文章：

### 第1步：分析原文
- 提取文章的核心主题和关键技术点
- 识别目标读者群体
- 判断文章的技术深度

### 第2步：改写标题
- 原标题通常是技术性的，需要改为更吸引人的版本
- 标题要有"信息增量"，让读者知道能学到什么
- 控制在 20 字以内

标题公式：
- "XXX，看这一篇就够了"
- "3分钟搞懂 XXX"
- "为什么你应该学 XXX？"
- "XXX 完全指南（附实战案例）"

### 第3步：添加引导语
在文章开头添加 2-3 句话的引导语：
- 点出读者的痛点
- 说明这篇文章能解决什么问题
- 制造继续阅读的动力

### 第4步：优化正文结构
- 长段落拆分为短段落（每段不超过 3-4 行）
- 关键概念用 **加粗** 突出
- 代码块保留，但添加简明注释
- 复杂概念用类比解释
- 适当添加小标题分隔内容

### 第5步：添加要点提炼
在文章中间或末尾添加"划重点"板块：
- 用编号列表总结 3-5 个核心要点
- 每个要点一句话说清

### 第6步：添加结尾
- 总结全文核心观点（2-3句话）
- 添加互动引导（如：你在工作中遇到过类似问题吗？欢迎留言讨论）
```

### 3.4 写输出格式

```markdown
## 输出格式（严格遵守）

最终输出必须是以下 Markdown 格式：

\```markdown
# [改写后的标题]

> [引导语，2-3句话]

---

[优化后的正文...]

---

## 划重点

1. 要点1
2. 要点2
3. 要点3

---

[结尾总结 + 互动引导]
\```

注意：
- 全文使用中文
- 技术术语首次出现时用中文+英文，如：渐进式披露（Progressive Disclosure）
- 代码块保留原样，但添加中文注释
- 不要使用 emoji（公众号排版可能显示异常）
```

### 3.5 写示例

```markdown
## 示例

### 输入示例
\```
原文标题：Progressive Disclosure in Agent Skills
原文内容：Progressive disclosure is a design pattern where
information is revealed gradually...
\```

### 输出示例
\```markdown
# 一个设计模式，让你的 AI 技能省下 80% 的 Token

> 你是否遇到过这样的问题：给 AI 写了一大堆提示词，结果 Token
> 消耗飙升，响应速度变慢？今天介绍的这个设计模式，能帮你彻底
> 解决这个问题。

---

渐进式披露（Progressive Disclosure）是一种信息设计模式...

---

## 划重点

1. 渐进式披露 = 只在需要时才加载信息
2. 分三层：元数据 → 核心指令 → 资源文件
3. 能节省 80% 以上的 Token 消耗

---

你在使用 AI 工具时，有没有遇到上下文窗口不够用的情况？
欢迎在评论区分享你的经验。
\```
```

### 3.6 写行为准则

```markdown
## 行为准则

- 保持技术准确性，不要为了通俗化而扭曲技术概念
- 不要添加原文没有的技术内容（可以添加类比和解释）
- 如果原文有代码示例，必须保留
- 不要使用过于"营销化"的语言（如："震惊！""99%的人不知道"）
- 如果原文内容过长（>3000字），先询问用户是否需要精简
- 用中文输出，除非用户特别要求其他语言
```

---

## 4. 第3步：完整的 SKILL.md 文件

把上面所有部分组合起来，完整文件如下：

```markdown
---
name: tech-article-to-wechat
description: >-
  将技术文章转换为微信公众号排版风格。自动添加吸引人的标题、
  引导语、段落优化、要点提炼和总结。
  输出 Markdown 格式，可直接粘贴到公众号编辑器。
  触发场景：转公众号、公众号排版、文章改写、wechat article。
trigger_keywords:
  - 公众号
  - 转公众号
  - 公众号排版
  - 文章改写
  - wechat
version: 1.0
author: learner
---

# 技术文章转公众号助手

你是一名资深的技术自媒体编辑，擅长将专业技术文章改写为
适合微信公众号阅读的风格，既保持技术准确性，又让非专业读者也能读懂。

## 使用场景

当以下情况时使用此技能：
- 用户提供一篇技术文章/博客，要求转换为公众号风格
- 用户要求优化技术文章的排版和可读性
- 用户需要为技术内容添加引导语或总结

## 执行指令

按照以下步骤处理用户提供的技术文章：

### 第1步：分析原文
- 提取文章的核心主题和关键技术点
- 识别目标读者群体
- 判断文章的技术深度

### 第2步：改写标题
- 原标题通常是技术性的，需要改为更吸引人的版本
- 标题要有"信息增量"，让读者知道能学到什么
- 控制在 20 字以内

标题公式：
- "XXX，看这一篇就够了"
- "3分钟搞懂 XXX"
- "为什么你应该学 XXX？"
- "XXX 完全指南（附实战案例）"

### 第3步：添加引导语
在文章开头添加 2-3 句话的引导语：
- 点出读者的痛点
- 说明这篇文章能解决什么问题
- 制造继续阅读的动力

### 第4步：优化正文结构
- 长段落拆分为短段落（每段不超过 3-4 行）
- 关键概念用 **加粗** 突出
- 代码块保留，但添加简明注释
- 复杂概念用类比解释
- 适当添加小标题分隔内容

### 第5步：添加要点提炼
在文章中间或末尾添加"划重点"板块：
- 用编号列表总结 3-5 个核心要点
- 每个要点一句话说清

### 第6步：添加结尾
- 总结全文核心观点（2-3句话）
- 添加互动引导（如：你在工作中遇到过类似问题吗？欢迎留言讨论）

## 输出格式（严格遵守）

最终输出必须是以下结构：

# [改写后的标题]

> [引导语，2-3句话]

---

[优化后的正文...]

---

## 划重点

1. 要点1
2. 要点2
3. 要点3

---

[结尾总结 + 互动引导]

注意：
- 全文使用中文
- 技术术语首次出现时用中文+英文，如：渐进式披露（Progressive Disclosure）
- 代码块保留原样，但添加中文注释
- 不要使用 emoji（公众号排版可能显示异常）

## 行为准则

- 保持技术准确性，不要为了通俗化而扭曲技术概念
- 不要添加原文没有的技术内容（可以添加类比和解释）
- 如果原文有代码示例，必须保留
- 不要使用过于"营销化"的语言（如："震惊！""99%的人不知道"）
- 如果原文内容过长（>3000字），先询问用户是否需要精简
- 用中文输出，除非用户特别要求其他语言
```

---

## 5. 第4步：测试你的 Skill

### 5.1 测试方法

**Claude Code：**
```
启动 claude，然后输入：
"帮我把以下文章转成公众号风格：[粘贴一篇技术文章]"
观察 AI 是否自动加载了你的 Skill
```

**Cursor：**
```
打开 Cursor 的 AI 聊天窗口，输入：
"帮我把这篇文章转成公众号排版"
```

**Windsurf：**
```
在聊天窗口输入：
"/tech-article-to-wechat [粘贴文章内容]"
```

### 5.2 测试用的示例文章

把下面这段技术文章作为输入来测试：

```
标题：Understanding Python Virtual Environments

A virtual environment is an isolated Python installation that allows
you to install packages without affecting the global Python installation.
This is crucial for managing dependencies across different projects.

To create a virtual environment, run: python -m venv .venv
To activate it on Windows: .venv\Scripts\Activate.ps1
To activate it on Mac/Linux: source .venv/bin/activate

Once activated, any pip install commands will only affect this
virtual environment. This means Project A can use numpy 1.24 while
Project B uses numpy 2.0, without any conflicts.

Best practices:
- Always use virtual environments for your projects
- Add .venv to .gitignore
- Use requirements.txt to record dependencies
- Create one virtual environment per project
```

### 5.3 检查输出质量

AI 的输出应该符合以下标准：

- [ ] 标题被改写为更吸引人的版本
- [ ] 有引导语（2-3句话）
- [ ] 段落被拆分为短段落
- [ ] 关键概念有加粗
- [ ] 技术术语有中英文对照
- [ ] 代码块被保留
- [ ] 有"划重点"板块
- [ ] 有结尾总结和互动引导
- [ ] 没有使用 emoji
- [ ] 全文中文

---

## 6. 第5步：迭代优化

第一次写的 Skill 很少能完美工作。以下是常见问题和解决方法：

### 问题1：AI 没有触发 Skill

**可能原因：**
- description 中的关键词和你的输入不匹配
- 文件路径不对

**解决方法：**
- 在 description 中添加更多触发关键词
- 检查文件是否在正确的目录下
- 尝试用斜杠命令手动触发：`/tech-article-to-wechat`

### 问题2：输出格式不对

**可能原因：**
- 输出格式部分写得不够具体

**解决方法：**
- 在"输出格式"部分添加更详细的结构说明
- 添加一个完整的输出示例
- 用"严格遵守"、"必须"等强调词

### 问题3：AI 过度改写，技术内容变味

**可能原因：**
- 行为准则中没有足够的约束

**解决方法：**
- 在行为准则中明确："不要修改技术细节"
- 添加具体的反例："不要把 venv 解释为'虚拟机器'"

### 问题4：SKILL.md 太长，加载慢

**解决方法：**
- 将示例拆分到 `examples/` 目录
- 将参考资料拆分到 `references/` 目录
- SKILL.md 只保留核心流程

---

## 7. 进阶：创建更多实用 Skill

学会了基本方法后，试试创建以下 Skill：

### Skill 创意1：Git Commit 规范助手
```
功能：自动生成符合 Conventional Commits 规范的提交信息
触发：用户要提交代码时
```

### Skill 创意2：代码审查专家
```
功能：审查代码质量，按严重程度分类输出问题
触发：用户说"审查代码"、"code review"
```

### Skill 创意3：README 生成器
```
功能：根据项目代码自动生成 README.md
触发：用户说"生成 README"、"写项目说明"
```

### Skill 创意4：SQL 优化助手
```
功能：分析 SQL 查询，给出性能优化建议
触发：用户提供 SQL 查询
```

### Skill 创意5：API 文档生成器
```
功能：根据代码生成 API 文档
触发：用户说"生成 API 文档"、"document API"
```

---

## 8. Skill 开发检查清单

每次创建新 Skill 时，对照这个清单检查：

### 元数据
- [ ] name 使用 kebab-case，不超过 64 字符
- [ ] description 清晰说明功能和触发场景
- [ ] description 不超过 1024 字符
- [ ] 添加了 trigger_keywords

### 正文
- [ ] 有明确的角色设定
- [ ] 有使用场景列表
- [ ] 执行指令具体、可操作
- [ ] 有输出格式说明
- [ ] 有好例子和坏例子
- [ ] 有行为准则（包括"不该做什么"）

### 结构
- [ ] SKILL.md 不超过 400 行
- [ ] 超过 400 行的内容拆分到子文件
- [ ] 子文件在 SKILL.md 中有引用

### 测试
- [ ] 在目标 AI 工具中测试了自动触发
- [ ] 在目标 AI 工具中测试了手动触发
- [ ] 输出格式符合预期
- [ ] 边界情况有处理

---

## 9. 课程总结：5课知识回顾

```
第1课 - Skill 是什么
  Skill = 给 AI 的模块化培训手册
  本质：可复用 Prompt + 结构化格式 + 按需加载

第2课 - SKILL.md 结构
  YAML元数据（name + description）+ Markdown正文
  description 是最关键的字段

第3课 - 渐进式披露
  分层加载：元数据 → 核心指令 → 资源文件 → 脚本
  超过 400 行就拆分到子文件

第4课 - 跨平台适配
  Claude(.claude/) / Copilot(.github/) / Cursor(.cursor/) / Windsurf(.windsurf/)
  SKILL.md 格式在大多数平台通用

第5课 - 实战演练（本课）
  从零创建 Skill → 测试 → 迭代优化
```

---

## 10. 继续学习的资源

### 官方资源
- **Anthropic 官方 Skill 仓库**: https://github.com/anthropics/skills
- **Agent Skills 标准**: https://github.com/agentskills/agentskills
- **VS Code Copilot Skills 文档**: https://code.visualstudio.com/docs/copilot/customization/agent-skills

### 社区资源
- **Skill 市场**: https://skills.sh
- **SkillsMP（中文）**: https://skillsmp.com/zh
- **AgentSkills.io**: https://agentskills.io
- **Awesome Claude Skills**: https://github.com/ComposioHQ/awesome-claude-skills

### 上下文工程学习
- **Prompt Engineering Guide**: https://www.promptingguide.ai/guides/context-engineering-guide
- **Andrej Karpathy 关于上下文工程**: https://x.com/karpathy/status/1937902205765607626
- **12-Factor Agents**: https://github.com/humanlayer/12-factor-agents

---

## 11. 小结

| 步骤 | 内容 |
|------|------|
| 第1步 | 创建目录结构（根据你的 AI 工具选择路径） |
| 第2步 | 编写 SKILL.md（元数据 + 正文指令） |
| 第3步 | 测试 Skill（自动触发 + 手动触发） |
| 第4步 | 迭代优化（根据输出质量调整指令） |
| 第5步 | 团队共享（Git 版本控制） |

### 最终记忆

```
创建 Skill 的核心流程：

1. 想清楚 → 这个 Skill 解决什么问题？
2. 写元数据 → name + description（花50%时间在这）
3. 写指令 → 具体步骤、格式要求、示例
4. 设边界 → 行为准则、不该做什么
5. 测试 → 触发测试 + 输出质量检查
6. 迭代 → 根据实际效果不断优化
```

---

**恭喜你完成全部5课的学习！** 现在你已经掌握了 Agent Skill 的核心知识，可以开始创建自己的 Skill 来提升 AI 协作效率了。
