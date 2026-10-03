"""中介者模式示例：Agent 协作调度

多个 Agent 不再互相直接引用，都通过调度器（中介者）传话。
协调逻辑集中在中介者：谁说了什么，下一步该叫谁。

与观察者的区别：观察者是一对多广播；
中介者是"所有同事 → 中间人 → 目标"的多对多集中协调。
"""

from abc import ABC, abstractmethod


class Agent(ABC):
    def __init__(self, name: str, mediator: "Mediator"):
        self.name = name
        self._mediator = mediator       # 同事只认识中介者，不认识其他人

    @abstractmethod
    def notify(self, event: str) -> None: ...   # 收到中介者转来的消息

    def send(self, event: str) -> None:
        self._mediator.notify(self, event)      # 说话都通过中介者


class Mediator(ABC):
    @abstractmethod
    def notify(self, sender: Agent, event: str) -> None: ...


class Orchestrator(Mediator):
    def __init__(self):
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        self._agents[agent.name] = agent

    def notify(self, sender: Agent, event: str) -> None:
        # ★ 协调逻辑集中在这里
        if event == "research_done":
            self._agents["coder"].notify("开始编码")
        elif event == "coding_done":
            self._agents["reviewer"].notify("开始审查")
        elif event == "review_done":
            print("全部完成")


class Researcher(Agent):
    def notify(self, event: str) -> None:
        print(f"[研究员] 收到: {event}")


class Coder(Agent):
    def notify(self, event: str) -> None:
        print(f"[编码员] 收到: {event}")
        self.send("coding_done")        # 干完活，通过中介者汇报


class Reviewer(Agent):
    def notify(self, event: str) -> None:
        print(f"[审查员] 收到: {event}")
        self.send("review_done")


def main():
    orchestrator = Orchestrator()
    researcher = Researcher("researcher", orchestrator)
    coder = Coder("coder", orchestrator)
    reviewer = Reviewer("reviewer", orchestrator)
    orchestrator.register(researcher)
    orchestrator.register(coder)
    orchestrator.register(reviewer)

    print("研究员开始调研...")
    researcher.send("research_done")


if __name__ == "__main__":
    main()
