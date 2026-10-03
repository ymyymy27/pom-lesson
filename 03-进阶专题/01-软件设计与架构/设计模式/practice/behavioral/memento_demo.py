"""备忘录模式示例：Agent 执行检查点

三个角色：
- Originator（Agent）：能生成快照、能恢复快照
- Memento（快照）：不透明对象，只有 Originator 能读写
- Caretaker（Checkpointer）：只负责保管快照，不碰内容

应用：长任务每步存检查点，某步失败后回滚到上一个安全点重试。
"""

from dataclasses import dataclass, field


@dataclass
class AgentState:
    step: int = 0
    messages: list[str] = field(default_factory=list)
    tool_results: list[str] = field(default_factory=list)


class Memento:
    """快照：不透明，只有 Originator 能读写"""

    def __init__(self, state: AgentState):
        self._state = state


class Agent:                                    # Originator
    def __init__(self):
        self._state = AgentState()

    def save(self) -> Memento:                  # 生成快照
        return Memento(AgentState(
            self._state.step,
            list(self._state.messages),         # 可变字段要复制，不能共享
            list(self._state.tool_results),
        ))

    def restore(self, memento: Memento) -> None:  # 恢复快照
        self._state = memento._state            # 只有 Originator 能读快照内容

    def run_step(self, message: str, tool_result: str | None = None) -> None:
        self._state.step += 1
        self._state.messages.append(message)
        if tool_result:
            self._state.tool_results.append(tool_result)

    def __repr__(self) -> str:
        s = self._state
        return f"step={s.step}, messages={s.messages}, tools={s.tool_results}"


class Checkpointer:                             # Caretaker：只保管，不碰内容
    def __init__(self):
        self._history: list[Memento] = []

    def checkpoint(self, memento: Memento) -> None:
        self._history.append(memento)

    def rollback(self, agent: Agent) -> bool:
        if self._history:
            agent.restore(self._history.pop())
            return True
        return False


def main():
    agent = Agent()
    checkpointer = Checkpointer()

    checkpointer.checkpoint(agent.save())       # 安全点 0
    agent.run_step("step1: 检索文档", "docs")
    checkpointer.checkpoint(agent.save())       # 安全点 1
    agent.run_step("step2: 调用工具", "tool-ok")
    print("第3步失败前:", agent)

    checkpointer.rollback(agent)                # 回滚到最近安全点
    print("回滚后    :", agent)

    agent.run_step("step2 重试", "tool-ok")
    print("重试后    :", agent)


if __name__ == "__main__":
    main()
