"""结构型 7 模式速查骨架（复习用）

每个模式只保留"机关"（最关键的结构），完整示例见对应 demo 文件。
回忆方法：场景 → 机关 → 关键一行。
"""

from abc import ABC, abstractmethod


# 1. 适配器 — 机关：实现"目标接口"，内部调用第三方

class Target(ABC):
    @abstractmethod
    def request(self) -> str: ...


class ThirdParty:
    def specific_request(self) -> str:
        return "third-party result"


class Adapter(Target):
    def __init__(self, third: ThirdParty):
        self._third = third

    def request(self) -> str:                       # 实现目标接口
        return f"adapted: {self._third.specific_request()}"  # 内部翻译


# 2. 桥接 — 机关：抽象持有实现的引用

class Renderer(ABC):
    @abstractmethod
    def render(self) -> str: ...


class ConsoleRenderer(Renderer):
    def render(self) -> str:
        return "console"


class Shape(ABC):
    def __init__(self, renderer: Renderer):
        self._renderer = renderer                   # ★ 桥

    @abstractmethod
    def draw(self) -> str: ...


class Circle(Shape):
    def draw(self) -> str:
        return f"circle on {self._renderer.render()}"


# 3. 组合 — 机关：统一接口 + 递归汇总

class Node(ABC):
    @abstractmethod
    def count(self) -> int: ...


class Leaf(Node):
    def count(self) -> int:
        return 1


class Branch(Node):
    def __init__(self):
        self._children: list[Node] = []

    def add(self, node: Node) -> None:
        self._children.append(node)

    def count(self) -> int:
        return sum(c.count() for c in self._children)   # ★ 递归


# 4. 装饰器 — 机关：转发前后加料，可层层嵌套

class Service(ABC):
    @abstractmethod
    def work(self) -> str: ...


class RealService(Service):
    def work(self) -> str:
        return "core"


class Decorator(Service):
    def __init__(self, svc: Service):
        self._svc = svc

    def work(self) -> str:
        return self._svc.work()                     # ★ 转发


class Logging(Decorator):
    def work(self) -> str:
        result = self._svc.work()                   # 转发给内层
        return f"log[{result}]"                     # 转发后加料


# 5. 外观 — 机关：一个高层方法，内部编排一堆子系统

class LLM:
    def generate(self) -> str:
        return "answer"


class Memory:
    def recall(self) -> str:
        return "history"


class Facade:
    def __init__(self):
        self._llm = LLM()
        self._memory = Memory()

    def run(self) -> str:                           # ★ 对外只有一个入口
        return f"{self._memory.recall()} + {self._llm.generate()}"


# 6. 享元 — 机关：工厂池按 key 复用，没有才造

class ToolSpec:
    def __init__(self, name: str):
        self.name = name


class ToolRegistry:
    _pool: dict[str, ToolSpec] = {}

    @classmethod
    def get(cls, name: str) -> ToolSpec:
        if name not in cls._pool:
            cls._pool[name] = ToolSpec(name)        # 没有才造
        return cls._pool[name]                      # ★ 有就复用


# 7. 代理 — 机关：同一接口 + 控制访问（延迟创建）

class Client(ABC):
    @abstractmethod
    def call(self) -> str: ...


class Real(Client):
    def call(self) -> str:
        return "real"


class Proxy(Client):
    def __init__(self):
        self._real: Real | None = None

    def call(self) -> str:
        if self._real is None:                      # ★ 控制：延迟创建
            self._real = Real()
        return self._real.call()


def main():
    print("1 适配器:", Adapter(ThirdParty()).request())
    print("2 桥接:", Circle(ConsoleRenderer()).draw())
    branch = Branch()
    branch.add(Leaf())
    branch.add(Leaf())
    print("3 组合:", branch.count())
    print("4 装饰器:", Logging(RealService()).work())
    print("5 外观:", Facade().run())
    spec_a = ToolRegistry.get("search")
    spec_b = ToolRegistry.get("search")
    print("6 享元 (同一个对象?):", spec_a is spec_b)
    print("7 代理:", Proxy().call())


if __name__ == "__main__":
    main()
