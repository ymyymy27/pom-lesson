"""命令模式示例：任务操作 + 撤销"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Task:
    title: str
    status: str = "todo"


class Command(ABC):
    @abstractmethod
    def execute(self) -> None: ...

    @abstractmethod
    def undo(self) -> None: ...


class CompleteTaskCommand(Command):
    def __init__(self, task: Task):
        self._task = task
        self._previous_status = task.status

    def execute(self) -> None:
        self._previous_status = self._task.status
        self._task.status = "done"
        print(f"Completed: {self._task.title}")

    def undo(self) -> None:
        self._task.status = self._previous_status
        print(f"Undone: {self._task.title} → {self._task.status}")


class CommandHistory:
    def __init__(self):
        self._history: list[Command] = []

    def execute(self, command: Command) -> None:
        command.execute()
        self._history.append(command)

    def undo_last(self) -> None:
        if self._history:
            self._history.pop().undo()


def main():
    task = Task("Write architecture doc")
    history = CommandHistory()

    history.execute(CompleteTaskCommand(task))
    print(f"Status: {task.status}")

    history.undo_last()
    print(f"Status: {task.status}")


if __name__ == "__main__":
    main()
