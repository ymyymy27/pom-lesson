# 第3课：远程仓库与协作

## 1. 远程仓库是什么？

### 一句话解释
**远程仓库就是云端的代码备份** —— 你本地的代码推上去，团队成员拉下来，大家协作开发。

### 常用远程平台
| 平台 | 特点 |
|------|------|
| **GitHub** | 全球最大，开源首选 |
| **GitLab** | 可私有部署，企业常用 |
| **Gitee** | 国内平台，速度快 |
| **Bitbucket** | Atlassian 生态 |

---

## 2. 连接远程仓库

### 2.1 SSH Key 配置（推荐，免密码）

```bash
# 1. 生成 SSH 密钥
ssh-keygen -t ed25519 -C "你的邮箱@example.com"
# 一路回车即可

# 2. 查看公钥
cat ~/.ssh/id_ed25519.pub
# 复制输出的内容

# 3. 添加到 GitHub
# GitHub → Settings → SSH and GPG keys → New SSH key → 粘贴

# 4. 测试连接
ssh -T git@github.com
# Hi username! You've successfully authenticated...
```

### 2.2 关联远程仓库

```bash
# 方法1：先有本地仓库，关联远程
git remote add origin git@github.com:你的用户名/仓库名.git

# 方法2：直接克隆远程仓库
git clone git@github.com:用户名/仓库名.git

# 查看远程仓库
git remote -v
# origin  git@github.com:user/repo.git (fetch)
# origin  git@github.com:user/repo.git (push)
```

**origin** 是远程仓库的默认名字，可以改但一般不改。

---

## 3. 推送与拉取

### 3.1 推送（push）

```bash
# 首次推送（设置上游分支）
git push -u origin main
# -u 表示设置 upstream，以后只需 git push

# 后续推送
git push

# 推送指定分支
git push origin feature/login
```

### 3.2 拉取（pull）

```bash
# 拉取并合并（最常用）
git pull
# 等于 git fetch + git merge

# 只获取不合并（看看远程有什么更新）
git fetch
git log origin/main --oneline    # 查看远程 main 的提交

# 拉取并变基（更干净的历史）
git pull --rebase
```

### 3.3 push vs pull

| 操作 | 方向 | 说明 |
|------|------|------|
| `git push` | 本地 → 远程 | 把你的提交推到云端 |
| `git pull` | 远程 → 本地 | 把云端的更新拉到本地 |
| `git fetch` | 远程 → 本地 | 只下载，不合并 |

---

## 4. 协作流程

### 4.1 个人项目流程

```bash
# 每天开始
git pull                          # 拉取最新（如果多设备）

# 开发...
git add . && git commit -m "xxx"  # 提交

# 每天结束
git push                          # 推送到云端
```

### 4.2 团队协作流程（Fork + PR）

```
1. Fork 原始仓库到你的账号
2. Clone 你 Fork 的仓库到本地
3. 创建功能分支，开发并提交
4. Push 到你的远程仓库
5. 在 GitHub 上发起 Pull Request（PR）
6. 代码审查（Code Review）
7. 合并到主仓库
```

```bash
# 1. Fork 后克隆你的仓库
git clone git@github.com:你的用户名/repo.git
cd repo

# 2. 添加原始仓库为 upstream
git remote add upstream git@github.com:原作者/repo.git

# 3. 创建功能分支
git switch -c feature/my-feature

# 4. 开发并提交
git add . && git commit -m "添加新功能"

# 5. 推送到你的远程
git push origin feature/my-feature

# 6. 在 GitHub 网页上创建 Pull Request

# 7. 同步原始仓库的更新
git fetch upstream
git switch main
git merge upstream/main
git push origin main
```

### 4.3 团队协作流程（共享仓库）

```bash
# 所有人 Clone 同一个仓库
git clone git@github.com:team/project.git

# 创建功能分支（不直接在 main 上开发！）
git switch -c feature/my-task

# 开发...提交...
git add . && git commit -m "完成xxx功能"

# 推送分支到远程
git push origin feature/my-task

# 在 GitHub 上创建 PR，请求合并到 main
# 队友 Review 后合并

# 合并后拉取最新 main
git switch main
git pull
```

---

## 5. 常见问题

### push 被拒绝

```bash
git push
# ! [rejected] main -> main (non-fast-forward)
# 原因：远程有你没有的提交

# 解决：先 pull 再 push
git pull              # 可能需要解决冲突
git push
```

### 拉取时有冲突

```bash
git pull
# CONFLICT: 冲突了

# 解决冲突（和第2课一样）
# 1. 编辑冲突文件
# 2. git add .
# 3. git commit
# 4. git push
```

### 不小心推错了

```bash
# 撤销最新提交（保留代码改动）
git reset --soft HEAD~1
git push --force         # ⚠️ 强制推送，团队慎用！

# 更安全的方式：用 revert 创建一个"反向提交"
git revert HEAD
git push
```

---

## 6. GitHub 实用功能

### Issues（问题追踪）
```
用来记录 bug、功能需求、讨论
提交时引用：git commit -m "修复登录bug，closes #12"
```

### README.md
```
项目首页展示的文档
用 Markdown 写项目介绍、使用说明、安装步骤
```

### .gitignore 模板
```
GitHub 创建仓库时可以选择语言对应的 .gitignore 模板
也可以去 https://gitignore.io 生成
```

### GitHub Pages
```
免费的静态网站托管
Settings → Pages → 选择分支
```

---

## 7. 动手练习

1. 在 GitHub 上创建一个 `git-practice` 仓库
2. 本地创建项目，关联远程仓库，推送
3. 在 GitHub 网页上编辑文件，然后本地 `git pull`
4. 练习 Fork 一个开源项目，提交一个 PR（可以是修改 typo）
5. 在两台设备（或两个文件夹模拟）之间用 push/pull 同步代码

---

## 8. 小结

| 命令 | 作用 |
|------|------|
| `git remote add origin URL` | 关联远程仓库 |
| `git push -u origin main` | 首次推送 |
| `git push` | 推送到远程 |
| `git pull` | 拉取远程更新 |
| `git fetch` | 获取远程信息（不合并） |
| `git clone URL` | 克隆远程仓库 |

**日常节奏：** `pull → 开发 → add → commit → push`

---

**下一课：** `04_advanced_git.md` - 高级 Git 技巧
