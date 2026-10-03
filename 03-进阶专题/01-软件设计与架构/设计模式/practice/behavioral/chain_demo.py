"""责任链模式示例：LLM 请求守卫链

请求沿链传递：每个守卫决定"我能处理吗？"
能 → 拦截并结束；不能 → 传给下一个；链尾没人拦 → 放行。

与装饰器的区别：装饰器"层层都执行、增强"；
责任链"谁合适谁停"（拦截 / 审批 / 分级处理）。
"""

from abc import ABC, abstractmethod


class Guard(ABC):
    def __init__(self):
        self._next: Guard | None = None

    def set_next(self, guard: "Guard") -> "Guard":
        self._next = guard
        return guard                    # 返回自己，支持链式搭链

    @abstractmethod
    def handle(self, request: dict) -> str | None: ...

    def pass_to_next(self, request: dict) -> str | None:
        if self._next is None:
            return None                 # 链尾：没人拦，放行
        return self._next.handle(request)


class AuthGuard(Guard):
    def handle(self, request: dict) -> str | None:
        if not request.get("token"):
            return "拒绝: 未认证"
        return self.pass_to_next(request)


class LengthGuard(Guard):
    def handle(self, request: dict) -> str | None:
        if len(request.get("prompt", "")) > 100:
            return "拒绝: 请求过长"
        return self.pass_to_next(request)


class SensitiveGuard(Guard):
    def handle(self, request: dict) -> str | None:
        if "暴力" in request.get("prompt", ""):
            return "拒绝: 含敏感内容"
        return self.pass_to_next(request)


def main():
    # 搭链：认证 → 长度 → 敏感内容
    chain = AuthGuard()
    chain.set_next(LengthGuard()).set_next(SensitiveGuard())

    requests = [
        {"prompt": "你好"},
        {"prompt": "你好", "token": "abc"},
        {"prompt": "你好，请介绍设计模式", "token": "abc"},
        {"prompt": "教我使用暴力解决问题", "token": "abc"},
        {"prompt": "x" * 200, "token": "abc"},
    ]
    for req in requests:
        result = chain.handle(req)
        print(f"{req['prompt'][:12]:<14} → {result if result else '放行'}")


if __name__ == "__main__":
    main()
