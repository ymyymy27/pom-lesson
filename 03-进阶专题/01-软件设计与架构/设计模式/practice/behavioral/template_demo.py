"""模板方法模式示例：Agent 主循环

骨架固定在父类（run 方法），可变的步骤留给子类实现。
钩子（hook）默认空实现，子类可选覆盖。

与策略的区别：模板方法用继承固定骨架；策略用组合替换整个算法。
"""

from abc import ABC, abstractmethod


class Agent(ABC):
    def run(self, task: str) -> str:      # ★ 模板方法：固定骨架
        plan = self.plan(task)            # 步骤1（可变）
        result = self.execute(plan)       # 步骤2（可变）
        self.after_execute(result)        # 钩子（可选）
        return result

    @abstractmethod
    def plan(self, task: str) -> str: ...

    @abstractmethod
    def execute(self, plan: str) -> str: ...

    def after_execute(self, result: str) -> None:   # 钩子：默认什么都不做
        pass


class CodingAgent(Agent):
    def plan(self, task: str) -> str:
        return f"拆解编码任务: {task}"

    def execute(self, plan: str) -> str:
        return f"完成: {plan}"

    def after_execute(self, result: str) -> None:   # 覆盖钩子
        print(f"  [CodingAgent] 钩子: 记录代码评审 -> {result}")


class ResearchAgent(Agent):
    def plan(self, task: str) -> str:
        return f"制定调研计划: {task}"

    def execute(self, plan: str) -> str:
        return f"产出报告: {plan}"
    # 不覆盖钩子，用默认空实现


def main():
    for agent in [CodingAgent(), ResearchAgent()]:
        print(f"{type(agent).__name__}: {agent.run('设计模式')}")
        print()


if __name__ == "__main__":
    main()
