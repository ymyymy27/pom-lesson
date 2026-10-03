> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第4课：跨平台 Skill 适配（Claude Code / Copilot / Cursor / Windsurf）

## 1. 为什么要了解跨平台？

Agent Skill 的标准正在被各大 AI 工具采纳，但每个平台的实现细节略有不同：
- 文件存放位置不同
- 元数据格式略有差异
- 触发机制各有特色

了解这些差异，你就能**写一次 Skill，适配多个平台**。

---

## 2. 各平台对比总览

| 平台 | 项目级位置 | 全局位置 | 核心文件 | 触发方式 |
|------|-----------|---------|---------|---------|
| **Claude Code** | `.claude/skills/<name>/` | `~/.claude/skills/<name>/` | `SKILL.md` | 自动匹配 / `/name` 命令 |
| **GitHub Copilot** | `.github/skills/<name>/` | VS Code 用户设置 | `SKILL.md` | 自动匹配 |
| **Cursor** | `.cursor/skills/<name>/` | 全局设置 | `SKILL.md` | 自动匹配 / 从 GitHub 安装 |
| **Windsurf** | `.windsurf/workflows/` | 全局规则 | `<name>.md` | `/name` 斜杠命令 |

---

## 3. Claude Code —— 原生支持，体验最完整

### 3.1 Skill 存放位置

Claude Code 有两个级别的 Skill 存放位置：

**全局 Skill（所有项目共用）：**
```
~/.claude/skills/
├── code-comment-expert/
│   └── SKILL.md
├── git-commit-formatter/
│   └── SKILL.md
└── translation-helper/
    └── SKILL.md
```

**项目级 Skill（只在该项目中生效）：**
```
your-project/
├── .claude/
│   └── skills/
│       └── python-naming-standard/
│           └── SKILL.md
├── src/
│   └── ...
└── README.md
```

**优先级：** 项目级 > 全局（同名时项目级覆盖全局）

### 3.2 创建一个 Claude Code Skill

```bash
# 1. 创建目录
mkdir -p .claude/skills/my-first-skill

# 2. 创建 SKILL.md
# 在 .claude/skills/my-first-skill/ 下创建 SKILL.md
```

SKILL.md 内容：
```markdown
---
name: my-first-skill
description: >-
  描述你的技能做什么、什么时候用。
trigger_keywords:
  - 关键词1
  - 关键词2
---

# 技能标题

## 执行指令
...
```

### 3.3 使用方式

**自动触发：**
```
> 帮我写一个计算折扣的函数
Claude 自动匹配并加载相关 Skill
```

**手动触发（斜杠命令）：**
```
> /my-first-skill 处理这段代码
```

### 3.4 安装社区 Skill

Claude Code 支持从官方市场安装预设技能：

```bash
# 注册官方市场
/plugin marketplace add anthropics/skills

# 安装技能包
/plugin install document-skills@anthropic-agent-skills

# 查看已安装的插件
/plugin
```

### 3.5 让 AI 帮你创建 Skill

Claude Code 有一个强大的内置功能 —— 你可以对它说：

```
帮我把刚才关于 Docker 部署的配置逻辑总结成一个 Skill
```

AI 会自动在 `.claude/skills/` 下生成完整的 SKILL.md。

### 3.6 动态变量

Claude Code Skill 支持动态变量：

```markdown
---
name: session-logger
description: 记录当前会话活动
---

请将以下内容写入日志文件：
logs/${CLAUDE_SESSION_ID}.log
$ARGUMENTS
```

| 变量 | 说明 |
|------|------|
| `$ARGUMENTS` | 斜杠命令后面的所有参数 |
| `$ARGUMENTS[0]` | 第一个参数 |
| `$N` / `$0` | 同 `$ARGUMENTS[N]` |
| `${CLAUDE_SESSION_ID}` | 当前会话 ID |

---

## 4. GitHub Copilot —— VS Code 原生集成

### 4.1 Skill 存放位置

```
your-project/
├── .github/
│   └── skills/
│       └── code-review/
│           └── SKILL.md
└── src/
    └── ...
```

### 4.2 与 Claude Code 的差异

| 对比项 | Claude Code | GitHub Copilot |
|--------|-----------|----------------|
| 存放路径 | `.claude/skills/` | `.github/skills/` |
| 全局位置 | `~/.claude/skills/` | VS Code 用户设置 |
| 斜杠命令 | 支持 `/name` | 暂不支持 |
| 动态变量 | 支持 `$ARGUMENTS` 等 | 暂不支持 |
| 市场安装 | 支持 `/plugin` | 通过 VS Code 扩展 |

### 4.3 SKILL.md 格式

与 Claude Code 完全一致，共用同一套 SKILL.md 标准：

```markdown
---
name: copilot-code-review
description: >-
  审查代码质量，检查潜在问题。
  触发场景：code review、审查代码。
---

# 代码审查

## 执行指令
...
```

### 4.4 官方文档

更多细节参考：
```
https://code.visualstudio.com/docs/copilot/customization/agent-skills
```

---

## 5. Cursor —— AI 优先的编辑器

### 5.1 Skill 存放位置

```
your-project/
├── .cursor/
│   └── skills/
│       └── my-skill/
│           └── SKILL.md
└── src/
    └── ...
```

### 5.2 Cursor 特色功能

**从 GitHub 安装 Skill：**

Cursor 支持直接从 GitHub 仓库安装社区 Skill：
```
在 Cursor 设置中添加 GitHub 仓库 URL
Cursor 会自动下载并注册 Skill
```

**与 Cursor Rules 的配合：**

Cursor 同时支持 `.cursor/rules/` 和 `.cursor/skills/`：

```
.cursor/
├── rules/                    ← 全局规则（始终生效）
│   └── coding-standard.mdc
└── skills/                   ← 技能（按需加载）
    └── react-review/
        └── SKILL.md
```

| 对比 | rules/ | skills/ |
|------|--------|---------|
| 加载时机 | 始终加载 | 按需加载 |
| 适用场景 | 通用规范 | 特定任务流程 |
| Token 消耗 | 持续消耗 | 只在需要时消耗 |

**建议：** 通用的代码风格放 rules/，复杂的任务流程放 skills/。

---

## 6. Windsurf —— 通过 Workflow 实现

### 6.1 Windsurf 的实现方式

Windsurf 目前没有原生的 `skills/` 目录，但通过 **Workflow（工作流）** 实现了类似的功能。

**Workflow 存放位置：**
```
your-project/
├── .windsurf/
│   └── workflows/
│       └── my-workflow.md
└── src/
    └── ...
```

### 6.2 Workflow 文件格式

Windsurf 的 workflow 格式略有不同：

```markdown
---
description: 简短描述这个工作流做什么
---

# 工作流标题

## 步骤

1. 第一步做什么
2. 第二步做什么
// turbo
3. 第三步（标记为可自动执行）
4. 第四步
```

**与 SKILL.md 的差异：**

| 对比项 | SKILL.md | Windsurf Workflow |
|--------|----------|-------------------|
| 元数据 | `name` + `description` | 只有 `description` |
| 文件名 | 固定为 `SKILL.md` | 自定义 `<name>.md` |
| 目录 | `skills/<name>/SKILL.md` | `workflows/<name>.md` |
| 触发方式 | 自动匹配 / `/name` | `/name` 斜杠命令 |
| turbo 标记 | 不支持 | 支持（自动执行某步骤） |

### 6.3 创建一个 Windsurf Workflow

```bash
# 在项目根目录
mkdir -p .windsurf/workflows
```

创建 `.windsurf/workflows/code-review.md`：

```markdown
---
description: 审查当前文件的代码质量，检查潜在问题并给出改进建议
---

# 代码审查工作流

## 步骤

1. 读取当前打开的文件内容
2. 检查以下方面：
   - 代码风格是否一致
   - 是否有潜在的 bug
   - 是否有性能优化空间
   - 变量命名是否清晰
3. 按严重程度分类输出问题
4. 给出具体的修改建议和代码示例
```

**使用方式：** 在 Windsurf 聊天中输入 `/code-review`

### 6.4 Windsurf 全局规则

除了项目级 workflow，Windsurf 还支持全局规则：

**项目级规则文件：** `.windsurfrules`
```
放在项目根目录，对该项目始终生效
类似于 Cursor 的 .cursor/rules/
```

**全局规则：** 在 Windsurf 设置中配置
```
适用于所有项目的通用规则
```

### 6.5 Windsurf 记忆系统

Windsurf 还有独特的 **Memories（记忆）** 功能：

```
用户偏好 → 自动记录并在后续对话中应用
项目信息 → 记住项目的技术栈和架构
```

这与 Skill 的按需加载理念类似，但更自动化。

---

## 7. 跨平台 Skill 编写策略

### 7.1 一套 Skill 适配多平台

如果你想让一个 Skill 在多个平台都能用，推荐以下结构：

```
your-project/
├── .claude/skills/my-skill/SKILL.md       ← Claude Code
├── .github/skills/my-skill/SKILL.md       ← GitHub Copilot
├── .cursor/skills/my-skill/SKILL.md       ← Cursor
├── .windsurf/workflows/my-skill.md        ← Windsurf（需要转换格式）
└── skills/my-skill/SKILL.md               ← 源文件（维护用）
```

### 7.2 实用建议

**方案1：手动复制（项目小、平台少）**
```
写好一个 SKILL.md，手动复制到各平台目录
简单粗暴，适合个人项目
```

**方案2：符号链接（推荐）**
```bash
# 维护一份源文件
mkdir -p skills/my-skill
# 创建 SKILL.md 在 skills/my-skill/ 下

# 用符号链接指向各平台
# Windows PowerShell（管理员权限）
New-Item -ItemType SymbolicLink -Path ".claude\skills\my-skill" -Target "..\..\skills\my-skill"
New-Item -ItemType SymbolicLink -Path ".github\skills\my-skill" -Target "..\..\skills\my-skill"
New-Item -ItemType SymbolicLink -Path ".cursor\skills\my-skill" -Target "..\..\skills\my-skill"
```

**方案3：只选一个平台**
```
如果你主要用一个 AI 工具，就只维护那个平台的格式
不需要过度工程化
```

### 7.3 Windsurf Workflow 转换

由于 Windsurf 的格式不同，需要简单转换：

**SKILL.md 格式（Claude/Copilot/Cursor）：**
```markdown
---
name: code-review
description: 审查代码质量
trigger_keywords:
  - review
  - 审查
---

# 代码审查专家

你是一名代码审查专家...

## 执行指令
1. 分析代码结构
2. 检查潜在问题
3. 输出审查报告
```

**转换为 Windsurf Workflow：**
```markdown
---
description: 审查代码质量，检查潜在问题并输出审查报告
---

# 代码审查

你是一名代码审查专家...

1. 分析代码结构
2. 检查潜在问题
3. 输出审查报告
```

**主要变化：**
- 去掉 `name` 和 `trigger_keywords`（Windsurf 用文件名作为命令名）
- `description` 简化
- 正文结构保持一致

---

## 8. Skill 的版本控制与团队共享

### 8.1 用 Git 管理 Skill

Skill 就是文件夹和 Markdown 文件，天然适合 Git 管理：

```bash
# 将 Skill 纳入版本控制
git add .claude/skills/
git add .github/skills/
git add .cursor/skills/
git add .windsurf/workflows/
git commit -m "feat: add code-review skill"
```

### 8.2 团队共享

**方式1：随项目提交**
```
Skill 文件放在项目仓库中
团队成员 clone 后自动获得
```

**方式2：独立 Skill 仓库**
```
创建一个 team-skills 仓库
通过 Git submodule 或手动链接到各项目
```

**方式3：官方市场**
```
发布到 skills.sh 或 agentskills.io
社区都能安装使用
```

### 8.3 .gitignore 设置

```gitignore
# 不要忽略 Skill 文件！
# 以下目录应该提交到 Git
# .claude/skills/
# .github/skills/
# .cursor/skills/
# .windsurf/workflows/
```

---

## 9. 动手练习

### 练习1：为你正在使用的 AI 工具创建目录结构

根据你主要使用的工具，创建对应的目录：

**如果你用 Claude Code：**
```bash
mkdir -p .claude/skills/hello-world
```

**如果你用 Cursor：**
```bash
mkdir -p .cursor/skills/hello-world
```

**如果你用 Windsurf：**
```bash
mkdir -p .windsurf/workflows
```

### 练习2：写一个简单的 Skill 并测试

创建一个"中文纠错助手"Skill，然后在你的 AI 工具中测试它是否能自动触发。

> 提示：第5课会手把手带你完成一个完整的实战练习。

---

## 10. 小结

| 平台 | Skill 位置 | 文件格式 | 特色 |
|------|-----------|---------|------|
| Claude Code | `.claude/skills/` | SKILL.md (YAML + MD) | 最完整，支持市场和动态变量 |
| GitHub Copilot | `.github/skills/` | SKILL.md (YAML + MD) | VS Code 原生集成 |
| Cursor | `.cursor/skills/` | SKILL.md (YAML + MD) | 支持 GitHub 安装 |
| Windsurf | `.windsurf/workflows/` | `<name>.md` (简化格式) | 支持 turbo 自动执行 |

### 核心记忆点

```
SKILL.md 格式在 Claude / Copilot / Cursor 之间基本通用

Windsurf 用 Workflow 实现，格式略有不同但理念相同

跨平台最简单的方案：维护一份源文件 + 符号链接

Skill 应该纳入 Git 版本控制，方便团队共享
```

---

**下一课：** `05-第5课实战演练 —— 从零创建你的第一个 Skill.md` - 实战演练 —— 从零创建你的第一个 Skill
