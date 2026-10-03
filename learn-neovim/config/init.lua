--[[
  Neovim 入门配置
  这是你学习 Neovim 的第一个配置
  每一行都有注释说明作用

  使用方法：
  将此文件内容复制到你的 Neovim 配置文件中
  Windows:  %LOCALAPPDATA%\nvim\init.lua
  macOS/Linux: ~/.config/nvim/init.lua

  安装插件管理器 lazy.nvim:
  git clone https://github.com/folke/lazy.nvim.git ~/.local/share/nvim/lazy/lazy.nvim
]]

-- ============================================================
-- 第 1 部分：基础选项
-- ============================================================

-- 设置空格替代 Tab（Tab 宽度为 4）
vim.opt.expandtab = true
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
vim.opt.softtabstop = 4

-- 显示行号
vim.opt.number = true
-- 显示相对行号（方便看到上下多少行）
vim.opt.relativenumber = true

-- 高亮当前行
vim.opt.cursorline = true

-- 启用鼠标（可以用鼠标调整窗口大小和光标位置）
vim.opt.mouse = "a"

-- 使用系统剪切板
vim.opt.clipboard = "unnamedplus"

-- 开启语法高亮
vim.opt.termguicolors = true

-- 搜索设置
vim.opt.incsearch = true      -- 增量搜索（边打边显示）
vim.opt.hlsearch = true       -- 高亮所有搜索结果
vim.opt.ignorecase = true     -- 搜索忽略大小写
vim.opt.smartcase = true      -- 有大写字母时区分大小写

-- 缩进和显示
vim.opt.autoindent = true     -- 自动保持缩进
vim.opt.smartindent = true    -- 智能缩进
vim.opt.wrap = false          -- 关闭自动换行（横向滚动）
vim.opt.scrolloff = 5         -- 光标上下保持 5 行上下文
vim.opt.sidescrolloff = 8    -- 左右保持 8 列上下文

-- 分屏方向（更直觉）
vim.opt.splitright = true     -- 新窗口在右边
vim.opt.splitbelow = true    -- 新窗口在下方

-- 命令行
vim.opt.cmdheight = 2         -- 命令行高度（留足够空间显示信息）
vim.opt.showcmd = true        -- 在底部显示输入的命令
vim.opt.showmode = true       -- 显示当前模式（INSERT 等）

-- 其他
vim.opt.hidden = true         -- 允许切换未保存的 buffer
vim.opt.backup = false        -- 关闭备份文件
vim.opt.writebackup = false
vim.opt.swapfile = false
vim.opt.undofile = true       -- 持久撤销历史
vim.opt.undolevels = 10000

-- 补全选项
vim.opt.wildmenu = true       -- 命令行补全增强
vim.opt.wildmode = "longest:full,full"
vim.opt.completeopt = { "menu", "menuone", "noinsert" }

-- 文件类型检测
vim.filetype.add({
  extension = {
    conf = "nginx",
    mdx = "mdx",
  },
})

-- ============================================================
-- 第 2 部分：快捷键映射
-- ============================================================

-- 基础设置
vim.g.mapleader = " "         -- Leader 键设为空格（最顺手）
vim.g.maplocalleader = " "

local map = vim.keymap.set

-- 快速保存/退出
map("n", "<leader>w", "<cmd>w<cr>", { desc = "保存文件" })
map("n", "<leader>q", "<cmd>q<cr>", { desc = "退出当前窗口" })
map("n", "<leader>Q", "<cmd>q!<cr>", { desc = "强制退出" })
map("n", "<leader>W", "<cmd>w!<cr>", { desc = "强制保存" })

-- 快速清空搜索高亮（按完 leader 后不用急着松开）
map("n", "<leader><space>", "<cmd>noh<cr>", { desc = "清空搜索高亮" })

-- 窗口导航（不用 Ctrl+w，直接用 leader + h/j/k/l）
map("n", "<leader>h", "<cmd>wincmd h<cr>", { desc = "切换到左边窗口" })
map("n", "<leader>j", "<cmd>wincmd j<cr>", { desc = "切换到下边窗口" })
map("n", "<leader>k", "<cmd>wincmd k<cr>", { desc = "切换到上边窗口" })
map("n", "<leader>l", "<cmd>wincmd l<cr>", { desc = "切换到右边窗口" })

-- 分屏
map("n", "<leader>sv", "<cmd>vsp<cr>", { desc = "垂直分屏" })
map("n", "<leader>sh", "<cmd>sp<cr>", { desc = "水平分屏" })

-- Buffer 切换
map("n", "<leader>bn", "<cmd>bn<cr>", { desc = "下一个 buffer" })
map("n", "<leader>bp", "<cmd>bp<cr>", { desc = "上一个 buffer" })
map("n", "<leader>bd", "<cmd>bd<cr>", { desc = "删除当前 buffer" })
map("n", "<leader>bls", "<cmd>ls<cr>", { desc = "列出所有 buffer" })

-- 标签页
map("n", "<leader>tn", "<cmd>tabnew<cr>", { desc = "新建标签页" })
map("n", "<leader>tc", "<cmd>tabclose<cr>", { desc = "关闭标签页" })
map("n", "<leader>to", "<cmd>tabonly<cr>", { desc = "只保留当前标签页" })

-- 快速移动（行内）
map("n", "0", "^", { desc = "跳到行首非空字符（替代 0^）" })

-- 搜索居中（搜索结果出来时光标行居中）
map("n", "n", "nzz", { desc = "搜索下一处并居中" })
map("n", "N", "Nzz", { desc = "搜索上一处并居中" })
map("n", "*", "*zz", { desc = "搜索光标下单词并居中" })
map("n", "#", "#zz", { desc = "搜索光标下单词并居中" })

-- 缩进快捷键
map("n", "<", "<<", { desc = "减少缩进" })
map("n", ">", ">>", { desc = "增加缩进" })
map("v", "<", "<gv", { desc = "减少缩进并保持选中" })
map("v", ">", ">gv", { desc = "增加缩进并保持选中" })

-- 移动选中文本（Visual 模式下）
map("v", "J", ":m '>+1<cr>gv=gv", { desc = "下移选中行" })
map("v", "K", ":m '<-2<cr>gv=gv", { desc = "上移选中行" })

-- ============================================================
-- 第 3 部分：颜色主题
-- ============================================================

-- 设置主题（默认内置主题，可按第 10 课安装更多）
vim.cmd([[colorscheme ron]])

-- ============================================================
-- 第 4 部分：自动命令
-- ============================================================

-- 自动去除行尾空格
vim.api.nvim_create_autocmd("BufWritePre", {
  pattern = "*",
  command = [[%s/\s\+$//e]],
})

-- 高亮匹配的括号
vim.opt.showmatch = true

-- 新文件自动设置文件类型
vim.api.nvim_create_autocmd("BufNewFile", {
  pattern = "*.lua",
  command = "setfiletype lua",
})

-- ============================================================
-- 入门提示：安装插件后在这里添加
-- ============================================================
--
--[[
  推荐的插件配置（安装 lazy.nvim 后使用）:

  插件列表见：lessons/10_plugins/lesson.md

  使用 lazy.nvim 安装插件示例（添加到上方 "自动命令" 部分之后）:

  local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
  if not vim.loop.fs_stat(lazypath) then
    vim.fn.system({
      "git", "clone", "--filter=blob:none",
      "https://github.com/folke/lazy.nvim.git",
      "--branch=stable", lazypath,
    })
  end
  vim.opt.rtp:prepend(lazypath)

  require("lazy").setup({
    -- 在这里添加插件
    -- { "folke/tokyonight.nvim" },
  })
]]
