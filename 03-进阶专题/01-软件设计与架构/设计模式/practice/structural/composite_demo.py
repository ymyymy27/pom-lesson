"""组合模式示例：任务树（Agent 任务分解）

树形结构：叶子任务（原子操作）和任务组（容器）实现同一个接口。
客户端统一调用 run()，不用判断它是叶子还是组——
组的 run() 递归汇总所有子任务的执行结果。
"""

from abc import ABC, abstractmethod


class Task(ABC):
    @abstractmethod
    def run(self) -> list[str]: ...


# --- 叶子：原子任务 ---

class AtomicTask(Task):
    def __init__(self, name: str):
        self.name = name

    def run(self) -> list[str]:
        return [f"执行: {self.name}"]


# --- 容器：任务组，可再套子任务 ---

class TaskGroup(Task):
    def __init__(self, name: str):
        self.name = name
        self.children: list[Task] = []

    def add(self, task: Task) -> None:
        self.children.append(task)

    def run(self) -> list[str]:
        results = []
        for child in self.children:
            results.extend(child.run())   # 递归：子任务可能是叶子也可能是组
        return results


def main():
    # 建一棵任务树："写技术报告"
    root = TaskGroup("写技术报告")
    root.add(AtomicTask("收集需求"))

    research = TaskGroup("调研")
    research.add(AtomicTask("读论文 A"))
    research.add(AtomicTask("读论文 B"))
    research.add(AtomicTask("整理笔记"))
    root.add(research)

    root.add(AtomicTask("撰写正文"))
    root.add(AtomicTask("校对发布"))

    # 客户端：不管叶子还是组，统一 run()
    for step in root.run():
        print(step)


if __name__ == "__main__":
    main()
