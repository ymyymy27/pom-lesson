# 第4课：高级 Git 技巧

## 1. git stash - 临时保存工作

### 场景
你正在写代码，写到一半要切分支修 bug，但当前改动还不想提交。

```bash
# 保存当前工作（工作区变干净）
git stash
# Saved working directory and index state WIP on feature: a1b2c3d xxx

# 查看 stash 列表
git stash list
# stash@{0}: WIP on feature: a1b2c3d xxx

# 恢复最近一次 stash
git stash pop              # 恢复并删除 stash
git stash apply            # 恢复但保留 stash（可多次 apply）

# 恢复指定 stash
git stash apply stash@{1}

# 删除 stash
git stash drop stash@{0}  # 删除指定
git stash clear            # 清空所有

# 带描述的 stash（推荐）
git stash push -m "登录功能写了一半"
```

### 实际流程
```bash
# 1. 写代码写到一半...
# 2. 突然要修 bug
git stash push -m "新功能写了一半"
# 3. 切分支修 bug
git switch main
git switch -c hotfix/xxx
# 修复...提交...合并...
# 4. 回来继续
git switch feature/login
git stash pop
# 代码回来了，继续写
```

---

## 2. git rebase - 变基

### 和 merge 的区别

**merge：** 保留分支历史，产生合并提交
```
main:    A → B → E → M（合并提交）
              \       /
feature:       C → D
```

**rebase：** 把分支"嫁接"到最新的 main 上，线性历史
```
变基前：
main:    A → B → E
              \
feature:       C → D

变基后：
main:    A → B → E
                  \
feature:           C' → D'     ← 提交被"重放"到 E 之后
```

### 基本用法

```bash
# 在功能分支上执行
git switch feature/login
git rebase main
# 把 feature 的提交移到 main 最新提交之后

# 如果有冲突
# 1. 解决冲突文件
# 2. git add .
# 3. git rebase --continue
# 或者放弃 rebase
# git rebase --abort
```

### 什么时候用 rebase vs merge？

| 场景 | 推荐 | 原因 |
|------|------|------|
| 合并功能分支到 main | merge | 保留完整历史 |
| 同步 main 更新到功能分支 | rebase | 保持线性历史 |
| 已推送到远程的分支 | merge | rebase 会改写历史 |
| 个人本地分支 | rebase | 更干净 |

**黄金法则：** 不要对已推送到远程的公共分支做 rebase！

---

## 3. git cherry-pick - 摘取提交

### 场景
只想把某个分支的**某一个提交**搬到当前分支。

```bash
# 查看要摘取的提交
git log --oneline feature/login
# a1b2c3d 修复表单验证     ← 只要这个
# e4f5g6h 添加登录页面

# 摘取
git switch main
git cherry-pick a1b2c3d

# 摘取多个
git cherry-pick a1b2c3d e4f5g6h

# 摘取但不自动提交（可以修改后再提交）
git cherry-pick a1b2c3d --no-commit
```

---

## 4. git tag - 标签

### 用途
给重要的提交打标签，通常用于标记版本号。

```bash
# 创建轻量标签
git tag v1.0.0

# 创建附注标签（推荐）
git tag -a v1.0.0 -m "发布 1.0.0 版本"

# 给历史提交打标签
git tag -a v0.9.0 a1b2c3d -m "Beta 版本"

# 查看标签
git tag                    # 列出所有标签
git show v1.0.0            # 查看标签详情

# 推送标签到远程
git push origin v1.0.0     # 推送单个
git push origin --tags     # 推送所有标签

# 删除标签
git tag -d v1.0.0                    # 删除本地
git push origin --delete v1.0.0      # 删除远程
```

### 版本号规范（Semantic Versioning）
```
v主版本.次版本.修订号
v1.2.3

主版本：不兼容的 API 修改
次版本：向后兼容的功能新增
修订号：向后兼容的 bug 修复
```

---

## 5. 回退与撤销

### 5.1 撤销工作区修改

```bash
# 丢弃某个文件的修改（还没 add）
git checkout -- app.py      # 老写法
git restore app.py          # 新写法（推荐）

# 丢弃所有修改
git restore .
```

### 5.2 撤销暂存（已 add，还没 commit）

```bash
git reset HEAD app.py       # 老写法
git restore --staged app.py # 新写法（推荐）
```

### 5.3 撤销提交

```bash
# 撤销最近一次提交，保留代码改动
git reset --soft HEAD~1

# 撤销最近一次提交，改动回到工作区
git reset --mixed HEAD~1    # 默认模式

# 撤销最近一次提交，丢弃所有改动（危险！）
git reset --hard HEAD~1

# 安全撤销（创建一个新提交来"反转"旧提交）
git revert HEAD             # 不改写历史，适合已推送的提交
```

### reset 三种模式对比

| 模式 | 提交 | 暂存区 | 工作区 | 适用 |
|------|------|--------|--------|------|
| `--soft` | ✗ 撤销 | ✓ 保留 | ✓ 保留 | 重新组织提交 |
| `--mixed` | ✗ 撤销 | ✗ 清空 | ✓ 保留 | 重新 add |
| `--hard` | ✗ 撤销 | ✗ 清空 | ✗ 丢弃 | 彻底回退 |

### 5.4 恢复误删

```bash
# 查看所有操作记录（包括被撤销的）
git reflog
# a1b2c3d HEAD@{0}: reset: moving to HEAD~1
# e4f5g6h HEAD@{1}: commit: 被误删的提交

# 恢复到某个操作点
git reset --hard e4f5g6h
```

**reflog 是你的最后安全网！** 只要提交过，几乎都能恢复。

---

## 6. 交互式 rebase（整理提交历史）

```bash
# 整理最近 3 个提交
git rebase -i HEAD~3
```

打开编辑器：
```
pick a1b2c3d 添加登录功能
pick e4f5g6h 修复typo
pick i7j8k9l 又修复一个typo

# 可用命令:
# pick   = 保留提交
# squash = 合并到上一个提交
# reword = 修改提交信息
# drop   = 删除提交
```

**常用场景：** 把多个小提交合并成一个
```
pick a1b2c3d 添加登录功能
squash e4f5g6h 修复typo          ← 合并到上面
squash i7j8k9l 又修复一个typo    ← 合并到上面
```

---

## 7. 动手练习

1. 练习 `git stash`：写代码写到一半，stash，切分支，再回来 pop
2. 创建 `v1.0.0` 标签
3. 故意提交一个错误，用 `git revert` 撤销
4. 用 `git reset --soft HEAD~1` 撤销提交但保留代码
5. 用 `git reflog` 查看操作历史

---

## 8. 小结

| 命令 | 作用 |
|------|------|
| `git stash` | 临时保存工作 |
| `git rebase main` | 变基到 main |
| `git cherry-pick 提交ID` | 摘取某个提交 |
| `git tag -a v1.0.0 -m "信息"` | 创建标签 |
| `git restore 文件` | 撤销工作区修改 |
| `git reset --soft HEAD~1` | 撤销提交保留代码 |
| `git revert HEAD` | 安全撤销提交 |
| `git reflog` | 查看所有操作记录 |

---

**下一课：** `05_git_workflow.md` - 工作流实战
