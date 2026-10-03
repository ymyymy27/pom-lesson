"""状态模式示例：任务状态流转"""

from abc import ABC, abstractmethod


class TaskState(ABC):
    @abstractmethod
    def start(self, task: "Task") -> None: ...

    @abstractmethod
    def complete(self, task: "Task") -> None: ...


class TodoState(TaskState):
    def start(self, task: "Task") -> None:
        task.transition_to(InProgressState())
        print(f"'{task.title}' → In Progress")

    def complete(self, task: "Task") -> None:
        raise ValueError("Cannot complete a todo task directly; start first")


class InProgressState(TaskState):
    def start(self, task: "Task") -> None:
        raise ValueError("Already in progress")

    def complete(self, task: "Task") -> None:
        task.transition_to(DoneState())
        print(f"'{task.title}' → Done")


class DoneState(TaskState):
    def start(self, task: "Task") -> None:
        raise ValueError("Task is already done")

    def complete(self, task: "Task") -> None:
        raise ValueError("Task is already done")


class Task:
    def __init__(self, title: str):
        self.title = title
        self._state: TaskState = TodoState()

    def transition_to(self, state: TaskState) -> None:
        self._state = state

    def start(self) -> None:
        self._state.start(self)

    def complete(self) -> None:
        self._state.complete(self)


def main():
    task = Task("Implement login")
    task.start()
    task.complete()
    try:
        task.start()
    except ValueError as e:
        print(f"Expected error: {e}")


if __name__ == "__main__":
    main()
