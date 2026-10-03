import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
==============================================================================
第1课：MCP 协议概述与核心概念
==============================================================================

什么是 MCP？
-----------
MCP（Model Context Protocol，模型上下文协议）是 Anthropic 于 2024 年底
提出的开放协议，目标是标准化 LLM 与外部工具/数据源的连接方式。

核心问题：为什么需要 MCP？
--------------------------
没有 MCP 的世界（N×M 问题）：
  每个 AI 应用要单独适配每个工具/数据源

  AI应用1 ──适配──→ 工具A
  AI应用1 ──适配──→ 工具B
  AI应用2 ──适配──→ 工具A   ← 重复工作！
  AI应用2 ──适配──→ 工具B
  ... N个应用 × M个工具 = N×M 次适配

有 MCP 的世界（N+M 方案）：
  AI应用1 ──MCP──→ MCP Server(工具A)
  AI应用2 ──MCP──→ MCP Server(工具A)  ← 同一个Server，零适配！
  AI应用1 ──MCP──→ MCP Server(工具B)
  AI应用2 ──MCP──→ MCP Server(工具B)
  ... N个应用 + M个Server = N+M 次开发

类比：
- USB 之前：每种设备一种接口（打印机口、鼠标口、键盘口...）
- USB 之后：统一接口，任何设备即插即用
- MCP = AI 世界的 USB

本课内容：
1. MCP 协议的核心概念
2. Client-Server 架构
3. 三种能力（Tools / Resources / Prompts）
4. 通信协议（JSON-RPC）
5. 与 Function Calling 的关系
==============================================================================
"""

import json

print("=" * 60)
print("第1课：MCP 协议概述与核心概念")
print("=" * 60)

# ============================================================================
# 1. MCP 架构概览
# ============================================================================
print("\n--- 1. MCP 架构概览 ---")
print("""
MCP 采用 Client-Server 架构：

┌─────────────────────────────────────────────────────┐
│                    MCP 架构                          │
│                                                     │
│  ┌──────────────┐    MCP协议    ┌──────────────┐   │
│  │  MCP Client  │ ◄──────────► │  MCP Server  │   │
│  │  (AI应用端)  │   JSON-RPC   │  (工具/数据)  │   │
│  └──────┬───────┘              └──────┬───────┘   │
│         │                             │            │
│    ┌────┴────┐                ┌───────┴───────┐   │
│    │  LLM    │                │  外部资源      │   │
│    │  应用   │                │  - API         │   │
│    │  Claude │                │  - 数据库      │   │
│    │  GPT    │                │  - 文件系统    │   │
│    │  Cursor │                │  - 网络服务    │   │
│    └─────────┘                └───────────────┘   │
└─────────────────────────────────────────────────────┘

角色说明：
- MCP Host:   运行 AI 应用的宿主程序（如 Claude Desktop, Cursor, IDE）
- MCP Client: Host 中负责与 Server 通信的组件
- MCP Server: 提供工具/资源/提示的服务端程序
""")

# ============================================================================
# 2. MCP Server 的三种能力
# ============================================================================
print("\n--- 2. MCP Server 的三种能力 ---")
print("""
MCP Server 可以向 Client 暴露三种能力：

┌────────────────────────────────────────────────────────┐
│  能力        │  对应概念        │  说明                 │
├────────────────────────────────────────────────────────┤
│  Tools       │  Function Call   │  LLM 可调用的函数     │
│  (工具)      │  (函数调用)      │  如：搜索/计算/查询   │
│              │                  │  由 LLM 决定何时调用  │
├────────────────────────────────────────────────────────┤
│  Resources   │  上下文数据      │  LLM 可读取的数据源   │
│  (资源)      │  (类似GET API)   │  如：文件/数据库/配置 │
│              │                  │  由应用程序控制读取   │
├────────────────────────────────────────────────────────┤
│  Prompts     │  Prompt模板      │  预定义的交互模板     │
│  (提示)      │  (可复用模板)    │  如：代码审查模板     │
│              │                  │  由用户选择使用       │
└────────────────────────────────────────────────────────┘

控制权：
- Tools:     LLM 控制（模型决定是否调用）
- Resources: 应用控制（程序决定是否加载）
- Prompts:   用户控制（用户选择哪个模板）
""")

# ============================================================================
# 3. 通信协议：JSON-RPC 2.0
# ============================================================================
print("\n--- 3. 通信协议 ---")
print("""
MCP 使用 JSON-RPC 2.0 作为通信协议。

JSON-RPC 消息格式：
""")

# 3.1 请求（Request）
request_example = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "get_weather",
        "arguments": {
            "city": "北京"
        }
    }
}
print("请求（Client → Server）：")
print(json.dumps(request_example, ensure_ascii=False, indent=2))

# 3.2 响应（Response）
response_example = {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "content": [
            {
                "type": "text",
                "text": "北京：晴天，25°C，湿度40%"
            }
        ]
    }
}
print("\n响应（Server → Client）：")
print(json.dumps(response_example, ensure_ascii=False, indent=2))

# 3.3 通知（Notification，无 id）
notification_example = {
    "jsonrpc": "2.0",
    "method": "notifications/tools/list_changed"
}
print("\n通知（单向，无需回复）：")
print(json.dumps(notification_example, ensure_ascii=False, indent=2))

print("""
MCP 的核心方法：
┌─────────────────────────┬────────────────────────────┐
│  方法                    │  说明                       │
├─────────────────────────┼────────────────────────────┤
│  initialize              │  握手，协商能力             │
│  tools/list              │  列出可用工具               │
│  tools/call              │  调用工具                   │
│  resources/list          │  列出可用资源               │
│  resources/read          │  读取资源内容               │
│  prompts/list            │  列出可用提示模板           │
│  prompts/get             │  获取提示模板               │
│  ping                    │  心跳检测                   │
└─────────────────────────┴────────────────────────────┘
""")

# ============================================================================
# 4. MCP 的传输方式
# ============================================================================
print("\n--- 4. 传输方式 ---")
print("""
MCP 支持两种传输方式：

1. stdio（标准输入输出）
   - Client 启动 Server 进程
   - 通过 stdin/stdout 通信
   - 适合本地工具（文件操作、本地数据库）
   - 最简单、最常用
   
   Client ──stdin──→ Server进程
   Client ←─stdout── Server进程

2. SSE（Server-Sent Events over HTTP）
   - Server 运行为 HTTP 服务
   - Client 通过 HTTP 连接
   - 适合远程服务、多用户共享
   
   Client ──HTTP POST──→ Server(http://host:port)
   Client ←─SSE stream── Server

选择建议：
- 本地开发/个人使用 → stdio
- 团队共享/远程服务 → SSE
""")

# ============================================================================
# 5. MCP vs Function Calling
# ============================================================================
print("\n--- 5. MCP vs Function Calling ---")
print("""
MCP 和 Function Calling 不是替代关系，而是互补关系！

┌──────────────────┬──────────────────┬─────────────────┐
│                  │ Function Calling │      MCP        │
├──────────────────┼──────────────────┼─────────────────┤
│  定义            │  LLM的一种能力    │  通信协议标准    │
│  级别            │  模型级别         │  应用级别        │
│  关注点          │  如何让LLM调用函数│  如何连接工具    │
│  工具定义位置    │  代码中硬编码     │  Server动态提供  │
│  工具复用        │  每个项目重写     │  一次开发处处用  │
│  通信方式        │  API调用参数      │  JSON-RPC协议    │
│  生态系统        │  各自实现         │  统一标准        │
│  发现机制        │  无               │  tools/list     │
└──────────────────┴──────────────────┴─────────────────┘

它们的关系：
  MCP Server 提供工具定义 → MCP Client 获取 → 转换为 Function Calling 格式
  → LLM 通过 Function Calling 决定调用 → 通过 MCP 协议执行

  ┌──────┐   FC格式   ┌────────────┐  MCP协议  ┌────────────┐
  │ LLM  │ ←───────→ │ MCP Client │ ←──────→ │ MCP Server │
  └──────┘           └────────────┘           └────────────┘
""")

# ============================================================================
# 6. MCP 生态系统
# ============================================================================
print("\n--- 6. MCP 生态系统 ---")
print("""
已支持 MCP 的 Host 应用：
┌──────────────────────┬────────────────────────────────┐
│  应用                 │  说明                           │
├──────────────────────┼────────────────────────────────┤
│  Claude Desktop      │  Anthropic 官方桌面应用          │
│  Cursor              │  AI 编程 IDE                    │
│  Windsurf            │  AI 编程 IDE                    │
│  Continue            │  VS Code AI 插件                │
│  Cline               │  VS Code AI 插件                │
│  Zed                 │  现代代码编辑器                  │
└──────────────────────┴────────────────────────────────┘

官方和社区 MCP Server：
┌──────────────────────┬────────────────────────────────┐
│  Server              │  功能                           │
├──────────────────────┼────────────────────────────────┤
│  filesystem          │  文件系统操作                    │
│  github              │  GitHub API                     │
│  postgres / sqlite   │  数据库查询                     │
│  brave-search        │  网络搜索                       │
│  puppeteer           │  浏览器自动化                    │
│  slack               │  Slack 消息                     │
│  google-drive        │  Google Drive 文件              │
│  memory              │  知识图谱记忆                    │
│  fetch               │  HTTP 请求                      │
│  sequential-thinking │  分步推理                       │
└──────────────────────┴────────────────────────────────┘

查找更多：https://github.com/modelcontextprotocol/servers
""")

# ============================================================================
# 7. MCP 协议生命周期
# ============================================================================
print("\n--- 7. 协议生命周期 ---")
print("""
一次 MCP 会话的完整流程：

  1. 连接建立
     Client ──→ Server: initialize（能力协商）
     Client ←── Server: initialize response
     Client ──→ Server: initialized（确认）

  2. 能力发现
     Client ──→ Server: tools/list
     Client ←── Server: 工具列表
     Client ──→ Server: resources/list
     Client ←── Server: 资源列表

  3. 交互阶段
     Client ──→ Server: tools/call (调用工具)
     Client ←── Server: 工具结果
     Client ──→ Server: resources/read (读取资源)
     Client ←── Server: 资源内容
     ... (循环)

  4. 连接关闭
     Client ──→ Server: close
     (或 Server 进程退出)
""")

# ============================================================================
# 8. 核心概念总结
# ============================================================================
print("\n--- 8. 核心概念总结 ---")
print("""
┌──────────────────────────────────────────────────────────┐
│  概念              │  说明                                │
├──────────────────────────────────────────────────────────┤
│  MCP              │  Model Context Protocol               │
│                   │  标准化 LLM ↔ 工具的通信协议          │
│  MCP Host         │  运行AI应用的宿主（Claude/Cursor/IDE）│
│  MCP Client       │  Host 中与 Server 通信的组件          │
│  MCP Server       │  提供 Tools/Resources/Prompts 的服务  │
│  Tools            │  LLM 可调用的函数（模型控制）         │
│  Resources        │  LLM 可读取的数据（应用控制）         │
│  Prompts          │  预定义的交互模板（用户控制）         │
│  JSON-RPC 2.0     │  通信协议格式                         │
│  stdio            │  本地传输（标准输入输出）             │
│  SSE              │  远程传输（HTTP + Server-Sent Events）│
└──────────────────────────────────────────────────────────┘
""")

print("\n" + "=" * 60)
print("[完成] 第1课完成！你已经学会了：")
print("  [v] MCP 的定义和解决的问题（N×M → N+M）")
print("  [v] Client-Server 架构")
print("  [v] 三种能力（Tools / Resources / Prompts）")
print("  [v] JSON-RPC 通信协议")
print("  [v] stdio / SSE 两种传输方式")
print("  [v] MCP vs Function Calling 的关系")
print("  [v] MCP 生态系统现状")
print("=" * 60)
print("\n下一课：02_mcp_server_basics.py - MCP Server 基础")
