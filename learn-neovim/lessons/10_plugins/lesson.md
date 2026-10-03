# 第 10 课：插件入门

> 目标：了解 Neovim 插件生态，并安装第一个插件

## 10.1 什么是插件

插件 = 扩展 Neovim 功能的 Lua/VimScript 代码。

现代 Neovim 使用 `init.lua` 代替传统的 `init.vim`，用 Lua 配置。

## 10.2 Neovim 配置目录

```
Windows:  %LOCALAPPDATA%\nvim\
macOS/Linux: ~/.config/nvim/

init.lua              入口文件
lua/                  Lua 模块目录
plugin/               插件配置目录
```

## 10.3 插件管理器

推荐使用 `lazy.nvim`（现代、简洁、性能好）：

### 快速安装（初始化）

```bash
# 备份旧配置
mv ~/.config/nvim ~/.config/nvim.bak

# 全新安装 lazy.nvim
git clone https://github.com/folke/lazy.nvim.git ~/.local/share/nvim/lazy/lazy.nvim
```

### `init.lua` 示例结构

```lua
-- init.lua
-- 加载额外 Lua 模块
require("user.options")
require("user.keymaps")
require("user.plugins")
```

## 10.4 推荐的第一个插件：oil.nvim

`oil.nvim` = 内置文件管理器，在 Neovim 中用 `oil` 打开目录，像 VS Code 侧边栏一样操作文件。

## 10.5 推荐的插件清单

| 插件 | 用途 |
|------|------|
| `folke/lazy.nvim` | 插件管理器 |
| `nvim-treesitter/nvim-treesitter` | 语法高亮与解析 |
| `neovim/nvim-lspconfig` | LSP 配置 |
| `nvim-telescope/telescope.nvim` | 模糊搜索 |
| `nvim-tree/nvim-tree.lua` | 文件树 |
| `folke/oil.nvim` | 文件管理器 |
| `L3MON4D3/LuaSnip` | 代码片段 |
| `hrsh7th/nvim-cmp` | 自动补全 |
| `folke/tokyonight.nvim` | 主题 |
| `folke/which-key.nvim` | 快捷键提示 |

## 10.6 最小插件示例（init.lua）

```lua
-- init.lua

-- 设置选项
vim.g.mapleader = " "
vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.clipboard = "unnamedplus"
vim.opt.termguicolors = true
vim.opt.splitright = true
vim.opt.splitbelow = true

-- 快捷键示例
vim.keymap.set("n", "<leader>w", "<cmd>w<cr>", { desc = "保存文件" })
vim.keymap.set("n", "<leader>q", "<cmd>q<cr>", { desc = "退出" })
vim.keymap.set("n", "<leader>e", "<cmd>Explore<cr>", { desc = "打开文件浏览器" })
```

## 10.7 查看已安装插件

```vim
:lua vim.print(require("lazy").plugins())
:Lazy                   " lazy.nvim 的插件管理 UI
```

## 10.8 练习任务

1. 查看 Neovim 的配置目录位置：`:echo stdpath("config")`
2. 创建一个简单的 `init.lua`（参考上面的示例）
3. 尝试安装一个简单的插件（如 tokyonight 主题）
4. 用 `:Lazy` 打开插件管理界面

## 10.9 进度检查

- [ ] 知道 Neovim 配置目录在哪
- [ ] 能写简单的 `init.lua`
- [ ] 能安装和管理插件
- [ ] 知道去哪里找插件（github.com）
