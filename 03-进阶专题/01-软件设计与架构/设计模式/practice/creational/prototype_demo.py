"""原型模式示例：Agent 配置模板克隆

核心思想：不从零"造"对象，而是复制一个已有模板再改。
关键机关：clone() 必须深拷贝，副本才完全独立，
否则改副本会连累原件（共享内部数据）。
"""

import copy


class AgentProfile:
    def __init__(self, name: str, model: str, tools: list[str], temperature: float):
        self.name = name
        self.model = model
        self.tools = tools          # 可变属性：深拷贝才有独立副本
        self.temperature = temperature

    def clone(self) -> "AgentProfile":
        return copy.deepcopy(self)  # 关键机关

    def __repr__(self) -> str:
        return f"AgentProfile({self.name!r}, {self.model!r}, {self.tools!r}, {self.temperature})"


def main():
    # 模板：默认的"工程师 Agent"
    template = AgentProfile(
        name="default-engineer",
        model="gpt-4o",
        tools=["read_file", "run_code", "search"],
        temperature=0.3,
    )

    # 从模板克隆两个实例，各改各的，互不影响
    alice = template.clone()
    alice.name = "alice"
    alice.tools.append("write_file")   # 只影响 alice

    bob = template.clone()
    bob.name = "bob"
    bob.temperature = 0.8              # 只影响 bob

    print("模板:", template)
    print("alice:", alice)
    print("bob  :", bob)
    print("alice 加了工具，模板没被连累:", "write_file" not in template.tools)


if __name__ == "__main__":
    main()
