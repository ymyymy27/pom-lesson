"""享元模式示例：Agent 共享工具定义

1000 个 Agent 实例不需要每人持有一份工具定义
（名称、描述、参数 schema 完全一样，而且可能很大）。

内部状态（工具定义）：不变、可共享 → 只存一份，大家引用
外部状态（agent 的 id、自己的状态）：各不相同 → 各自持有
"""


# --- 享元：内部状态，可共享 ---

class ToolSpec:
    def __init__(self, name: str, description: str, params_schema: dict):
        self.name = name
        self.description = description
        self.params_schema = params_schema   # 假设是很大的 JSON Schema


# --- 享元工厂：按 key 复用，没有才创建 ---

class ToolRegistry:
    _specs: dict[str, ToolSpec] = {}

    @classmethod
    def get(cls, name: str, description: str, params_schema: dict) -> ToolSpec:
        if name not in cls._specs:
            cls._specs[name] = ToolSpec(name, description, params_schema)
            print(f"[创建] {name}")
        return cls._specs[name]              # 已存在就直接复用


# --- 外部状态：每个 agent 自己的部分 ---

class AgentInstance:
    def __init__(self, agent_id: int, tool_names: list[str]):
        self.agent_id = agent_id
        self.tool_names = tool_names         # 只存名字，定义走共享注册表


def main():
    # 三种工具定义，各创建一次
    ToolRegistry.get("search", "搜索互联网", {"q": "str"})
    ToolRegistry.get("read_file", "读取文件", {"path": "str"})
    ToolRegistry.get("run_code", "执行代码", {"code": "str"})

    # 1000 个 Agent，每人只是引用这 3 份定义
    agents = [
        AgentInstance(i, ["search", "read_file", "run_code"])
        for i in range(1000)
    ]

    print(f"已创建 {len(agents)} 个 Agent，共享的工具定义只有 {len(ToolRegistry._specs)} 份")


if __name__ == "__main__":
    main()
