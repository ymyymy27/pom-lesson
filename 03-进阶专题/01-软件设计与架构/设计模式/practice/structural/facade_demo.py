"""外观模式示例：Agent 统一入口

LLM、记忆、工具、检索器是一堆复杂的子系统，
外观（Agent）对外只提供一个 ask()，内部负责编排调用顺序。
子系统仍然可以单独使用——外观只是便捷路径，不是封锁。
"""


# --- 子系统：各自管各自的事 ---

class LLMClient:
    def generate(self, prompt: str) -> str:
        return f"回答: {prompt}"


class MemoryStore:
    def __init__(self):
        self.items: list[str] = []

    def remember(self, text: str) -> None:
        self.items.append(text)

    def recall(self) -> str:
        return "\n".join(self.items) if self.items else "(无历史)"


class ToolRunner:
    def execute(self, tool: str, args: str) -> str:
        return f"工具[{tool}] 执行: {args}"


class Retriever:
    def search(self, query: str) -> list[str]:
        return [f"文档片段: {query}"]


# --- 外观：对外只有 ask() 一个入口 ---

class Agent:
    def __init__(self):
        self.llm = LLMClient()
        self.memory = MemoryStore()
        self.tools = ToolRunner()
        self.retriever = Retriever()

    def ask(self, question: str) -> str:
        # 内部编排：回忆历史 → 检索文档 → 调用工具 → 拼 prompt → 让 LLM 回答 → 记住
        history = self.memory.recall()
        docs = self.retriever.search(question)
        tool_result = self.tools.execute("搜索", question)
        prompt = f"历史: {history}\n文档: {docs}\n工具: {tool_result}\n问题: {question}"
        answer = self.llm.generate(prompt)
        self.memory.remember(question)
        return answer


def main():
    agent = Agent()
    print(agent.ask("什么是设计模式"))
    print()
    print(agent.ask("装饰器怎么用"))


if __name__ == "__main__":
    main()
