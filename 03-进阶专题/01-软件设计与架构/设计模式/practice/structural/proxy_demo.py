"""代理模式示例：模型访问代理（虚拟代理 + 缓存代理）

客户端以为自己在用真实模型，实际通过代理：
- 虚拟代理：真实模型很贵，第一次真正调用时才创建
- 缓存代理：相同的提问直接返回缓存，不再花钱调 API

代理和装饰器结构几乎一样，但意图不同：
装饰器是"加功能"，代理是"替真实对象管访问"。
"""

from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def chat(self, prompt: str) -> str: ...


class RealLLM(LLMClient):
    """真实对象：初始化贵，调用也贵"""

    def __init__(self, api_key: str):
        print("  [真实模型] 加载配置、建立连接...")
        self.api_key = api_key

    def chat(self, prompt: str) -> str:
        print("  [真实模型] 调用远程 API...")
        return f"模型回答: {prompt}"


class LLMProxy(LLMClient):
    """代理：替客户端控制"什么时候碰真实对象" """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._real: RealLLM | None = None
        self._cache: dict[str, str] = {}

    def chat(self, prompt: str) -> str:
        if self._real is None:                 # 虚拟代理：第一次调用才创建
            self._real = RealLLM(self.api_key)
        if prompt in self._cache:              # 缓存代理：重复提问不花钱
            print("  [代理] 命中缓存，跳过 API 调用")
            return self._cache[prompt]
        result = self._real.chat(prompt)
        self._cache[prompt] = result
        return result


def main():
    print("创建代理（此时真实模型还没有被创建）")
    proxy = LLMProxy("sk-test")

    print("\n第一次提问:")
    print(proxy.chat("设计模式是什么"))

    print("\n第二次问同样的问题:")
    print(proxy.chat("设计模式是什么"))

    print("\n换个新问题:")
    print(proxy.chat("装饰器怎么用"))


if __name__ == "__main__":
    main()
