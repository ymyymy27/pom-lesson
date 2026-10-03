> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第 11 课：LSP 与代码补全

> 2025–2026 补充课 — 现代 Neovim 开发工作流  
> 前置：[`10_plugins/lesson.md`](<../10_plugins/第 10 课插件入门.md>)

## 1. 什么是 LSP？

**Language Server Protocol（LSP）** 是编辑器和语言工具之间的标准协议。

```
Neovim（客户端）  ←──LSP──→  Language Server（pyright/tsserver/rust-analyzer）
     │                              │
  补全/跳转/诊断              理解代码语义
```

没有 LSP 的 Neovim = 高效文本编辑器  
有 LSP 的 Neovim = 轻量 IDE

---

## 2. 推荐插件栈（2026）

| 插件 | 作用 |
|------|------|
| **lazy.nvim** | 插件管理（第 10 课已学） |
| **nvim-lspconfig** | LSP 服务器配置 |
| **nvim-cmp** | 补全 UI |
| **mason.nvim** | 自动安装 LSP/D linter/formatter |
| **none-ls.nvim** | 额外 formatter/linter 接入 |
| **which-key.nvim** | 快捷键提示 |

---

## 3. 最小 LSP 配置

在 `config/init.lua` 中添加：

```lua
-- Mason：安装 LSP 服务器
require("mason").setup()
require("mason-lspconfig").setup({
  ensure_installed = { "pyright", "ts_ls", "lua_ls", "jsonls" },
  automatic_installation = true,
})

-- LSP 通用能力
local capabilities = require("cmp_nvim_lsp").default_capabilities()

local on_attach = function(client, bufnr)
  local opts = { buffer = bufnr, silent = true }
  vim.keymap.set("n", "gd", vim.lsp.buf.definition, opts)
  vim.keymap.set("n", "gr", vim.lsp.buf.references, opts)
  vim.keymap.set("n", "K", vim.lsp.buf.hover, opts)
  vim.keymap.set("n", "<leader>rn", vim.lsp.buf.rename, opts)
  vim.keymap.set("n", "<leader>ca", vim.lsp.buf.code_action, opts)
  vim.keymap.set("n", "[d", vim.diagnostic.goto_prev, opts)
  vim.keymap.set("n", "]d", vim.diagnostic.goto_next, opts)
end

-- 配置各语言 LSP
local lspconfig = require("lspconfig")
lspconfig.pyright.setup({ capabilities = capabilities, on_attach = on_attach })
lspconfig.ts_ls.setup({ capabilities = capabilities, on_attach = on_attach })
lspconfig.lua_ls.setup({ capabilities = capabilities, on_attach = on_attach })
```

---

## 4. 补全配置（nvim-cmp）

```lua
local cmp = require("cmp")

cmp.setup({
  snippet = {
    expand = function(args)
      require("luasnip").lsp_expand(args.body)
    end,
  },
  mapping = cmp.mapping.preset.insert({
    ["<C-Space>"] = cmp.mapping.complete(),
    ["<CR>"] = cmp.mapping.confirm({ select = true }),
    ["<Tab>"] = cmp.mapping.select_next_item(),
    ["<S-Tab>"] = cmp.mapping.select_prev_item(),
  }),
  sources = {
    { name = "nvim_lsp" },
    { name = "buffer" },
    { name = "path" },
  },
})
```

---

## 5. 常用 LSP 快捷键

| 快捷键 | 功能 |
|--------|------|
| `gd` | 跳转到定义 |
| `gr` | 查找引用 |
| `K` | 悬停文档 |
| `<leader>rn` | 重命名符号 |
| `<leader>ca` | 代码动作（Quick Fix） |
| `[d` / `]d` | 上一个/下一个诊断 |
| `<C-Space>` | 触发补全 |

---

## 6. Python 开发工作流

```lua
-- pyright 额外配置
lspconfig.pyright.setup({
  settings = {
    python = {
      analysis = {
        typeCheckingMode = "basic",  -- 或 "strict"
        autoImportCompletions = true,
      },
    },
  },
  capabilities = capabilities,
  on_attach = on_attach,
})
```

配合本工作区项目：

```
:e 03-进阶专题/04-Agent框架与MCP/01-Agent基础/learn-mcp/01_what_is_mcp.py
gd          → 跳转到 import 的定义
K           → 查看函数文档
<leader>rn  → 重命名变量
```

---

## 7. 格式化与 Lint

```lua
-- none-ls（nvim-null-ls 继任者）
local null_ls = require("null-ls")
null_ls.setup({
  sources = {
    null_ls.builtins.formatting.black,       -- Python
    null_ls.builtins.formatting.prettier,    -- JS/TS/JSON
    null_ls.builtins.diagnostics.ruff,       -- Python lint（2026 推荐）
  },
})

-- 保存时自动格式化
vim.api.nvim_create_autocmd("BufWritePre", {
  callback = function()
    vim.lsp.buf.format({ async = false })
  end,
})
```

> **2026 趋势：** Ruff 替代 flake8+isort+black 成为 Python 默认 linter/formatter；Biome 替代 ESLint+Prettier 用于 JS/TS。

---

## 8. 与 IDE 的对比

| 能力 | VS Code/Cursor | Neovim + LSP |
|------|----------------|--------------|
| 补全 | ✅ | ✅ |
| 跳转/引用 | ✅ | ✅ |
| 重构 | ✅ 强 | ✅ 基础 |
| 调试 | ✅ DAP | ✅ nvim-dap |
| AI 辅助 | ✅ 内置 | 插件（copilot.vim 等） |
| 资源占用 | 高 | **低** |
| 远程 SSH | 可用 | **极快** |

---

## 9. 动手练习

1. 安装 Mason + lspconfig + cmp，打开 Python 文件验证补全
2. 用 `gd` 跳转到函数定义，用 `gr` 查找所有引用
3. 用 `<leader>rn` 重命名一个变量，观察所有引用同步更新
4. 配置 Ruff formatter，保存时自动格式化

---

## 10. 自检清单

- [ ] 能解释 LSP 的工作原理
- [ ] 会配置 pyright + nvim-cmp
- [ ] 熟练使用 gd/gr/K/重命名/代码动作
- [ ] 知道 Mason 的作用
- [ ] 能配置保存时自动格式化

---

## 下一步

- Treesitter 语法高亮 → 建议第 12 课
- Telescope 模糊搜索 → 建议第 12 课
- DAP 调试 → roadmap 阶段五

## 参考

- [nvim-lspconfig](https://github.com/neovim/nvim-lspconfig)
- [Mason.nvim](https://github.com/williamboman/mason.nvim)
- [Neovim LSP 官方文档](https://neovim.io/doc/user/lsp.html)
