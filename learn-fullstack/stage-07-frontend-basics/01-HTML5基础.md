# 第 01 节：HTML5 基础

## 一、什么是 HTML？

HTML（HyperText Markup Language）是构建网页的 **标记语言**，定义页面的 **结构和内容**。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TaskFlow</title>
</head>
<body>
    <h1>Hello, TaskFlow!</h1>
    <p>这是一个任务协作平台。</p>
</body>
</html>
```

---

## 二、HTML5 语义化标签

语义化标签让代码更有意义、更易读、更利于 SEO 和无障碍访问。

```html
<!-- ❌ 无语义 -->
<div class="header">...</div>
<div class="nav">...</div>
<div class="content">...</div>
<div class="footer">...</div>

<!-- ✅ 语义化 -->
<header>网站头部</header>
<nav>导航栏</nav>
<main>
    <article>
        <section>内容区块</section>
    </article>
    <aside>侧边栏</aside>
</main>
<footer>页脚</footer>
```

### 2.1 常用语义标签

| 标签 | 语义 | 使用场景 |
|------|------|---------|
| `<header>` | 页头 | 网站顶部、文章头部 |
| `<nav>` | 导航 | 导航菜单 |
| `<main>` | 主要内容 | 页面主体（每页只有一个） |
| `<article>` | 独立内容 | 文章、帖子、评论 |
| `<section>` | 主题分组 | 内容区块 |
| `<aside>` | 侧边内容 | 侧边栏、相关链接 |
| `<footer>` | 页脚 | 版权信息、链接 |
| `<figure>` | 独立内容 | 图片+说明 |
| `<figcaption>` | 说明文字 | 图片标题 |
| `<time>` | 时间 | 日期/时间 |
| `<mark>` | 高亮 | 搜索结果高亮 |

### 2.2 TaskFlow 页面结构示例

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TaskFlow - 任务协作平台</title>
</head>
<body>
    <header>
        <nav>
            <a href="/">TaskFlow</a>
            <ul>
                <li><a href="/projects">项目</a></li>
                <li><a href="/tasks">任务</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <section>
            <h1>我的任务</h1>
            <article>
                <h2>学习 React</h2>
                <p>完成组件和 Hooks 章节</p>
                <footer>
                    <time datetime="2025-06-01">2025年6月1日</time>
                    <span>优先级：高</span>
                </footer>
            </article>
        </section>

        <aside>
            <h3>任务统计</h3>
            <ul>
                <li>待办：10</li>
                <li>进行中：5</li>
                <li>已完成：20</li>
            </ul>
        </aside>
    </main>

    <footer>
        <p>&copy; 2025 TaskFlow. All rights reserved.</p>
    </footer>
</body>
</html>
```

---

## 三、表单

```html
<form action="/api/tasks/" method="POST">
    <!-- 文本输入 -->
    <label for="title">任务标题</label>
    <input type="text" id="title" name="title" placeholder="输入任务标题" required maxlength="200">

    <!-- 文本域 -->
    <label for="desc">描述</label>
    <textarea id="desc" name="description" rows="4" placeholder="任务描述..."></textarea>

    <!-- 下拉选择 -->
    <label for="status">状态</label>
    <select id="status" name="status">
        <option value="pending">待办</option>
        <option value="in_progress">进行中</option>
        <option value="completed">已完成</option>
    </select>

    <!-- 数字输入 -->
    <label for="priority">优先级 (0-10)</label>
    <input type="number" id="priority" name="priority" min="0" max="10" value="0">

    <!-- 日期 -->
    <label for="due">截止日期</label>
    <input type="date" id="due" name="due_date">

    <!-- 邮箱 -->
    <input type="email" name="email" placeholder="邮箱">

    <!-- 密码 -->
    <input type="password" name="password" minlength="8">

    <!-- 复选框 -->
    <label>
        <input type="checkbox" name="urgent"> 紧急任务
    </label>

    <!-- 单选 -->
    <label><input type="radio" name="type" value="bug"> Bug</label>
    <label><input type="radio" name="type" value="feature"> Feature</label>

    <!-- 文件上传 -->
    <input type="file" name="attachment" accept=".pdf,.doc,.docx">

    <!-- 隐藏字段 -->
    <input type="hidden" name="project_id" value="1">

    <button type="submit">创建任务</button>
    <button type="reset">重置</button>
</form>
```

### 3.1 HTML5 表单验证属性

| 属性 | 说明 | 示例 |
|------|------|------|
| `required` | 必填 | `<input required>` |
| `minlength` / `maxlength` | 最小/最大长度 | `minlength="8"` |
| `min` / `max` | 数字范围 | `min="0" max="10"` |
| `pattern` | 正则匹配 | `pattern="[A-Za-z]+"` |
| `placeholder` | 占位提示 | `placeholder="请输入"` |
| `disabled` | 禁用 | `<input disabled>` |
| `readonly` | 只读 | `<input readonly>` |
| `autofocus` | 自动聚焦 | `<input autofocus>` |

> 💡 前后端分离中，表单通常由 React 组件构建，HTML 原生表单了解即可。

---

## 四、常用标签速查

```html
<!-- 标题 -->
<h1>一级标题</h1> ~ <h6>六级标题</h6>

<!-- 文本 -->
<p>段落</p>
<span>行内文本</span>
<strong>加粗（语义：重要）</strong>
<em>斜体（语义：强调）</em>
<br> <!-- 换行 -->
<hr> <!-- 水平线 -->

<!-- 链接 -->
<a href="https://example.com" target="_blank" rel="noopener">新窗口打开</a>

<!-- 图片 -->
<img src="logo.png" alt="TaskFlow Logo" width="200" loading="lazy">

<!-- 列表 -->
<ul><li>无序列表</li></ul>
<ol><li>有序列表</li></ol>

<!-- 表格 -->
<table>
    <thead>
        <tr><th>标题</th><th>状态</th></tr>
    </thead>
    <tbody>
        <tr><td>任务1</td><td>待办</td></tr>
    </tbody>
</table>

<!-- 容器 -->
<div>块级容器</div>
<span>行内容器</span>
```

---

## 五、练习

1. 用语义化标签搭建 TaskFlow 的基础页面结构（header/nav/main/aside/footer）
2. 创建一个"新建任务"表单，包含标题、描述、状态、优先级、截止日期
3. 使用 HTML5 验证属性：标题必填、优先级 0-10、密码至少 8 位
4. 创建一个任务列表表格，包含 ID、标题、状态、负责人、截止日期
