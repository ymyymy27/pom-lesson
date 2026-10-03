"""桥接模式示例：聊天机器人能力 × 模型供应商

两个维度都要独立变化：
- 抽象维度：机器人的能力（基础对话 / 带工具）
- 实现维度：模型供应商（OpenAI / Ollama）

用继承组合会爆炸（2×2 种组合 = 4 个类，n×m 更夸张），
桥接拆成两个类层次，靠"组合"任意搭配。
"""

from abc import ABC, abstractmethod


# --- 实现维度：模型供应商 ---

class Model(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...


class OpenAIModel(Model):
    def generate(self, prompt: str) -> str:
        return f"[OpenAI] {prompt}"


class OllamaModel(Model):
    def generate(self, prompt: str) -> str:
        return f"[Ollama] {prompt}"


# --- 抽象维度：机器人的能力 ---

class ChatBot(ABC):
    def __init__(self, model: Model):
        self.model = model          # 桥：抽象握着实现的引用

    @abstractmethod
    def chat(self, message: str) -> str: ...


class BasicBot(ChatBot):
    def chat(self, message: str) -> str:
        return self.model.generate(f"直接回答: {message}")


class ToolBot(ChatBot):
    def chat(self, message: str) -> str:
        return self.model.generate(f"先调用工具再回答: {message}")


def main():
    openai = OpenAIModel()
    ollama = OllamaModel()

    # 2×2 任意组合，不需要为每种组合写一个类
    bots = [
        BasicBot(openai),   # 基础对话 × OpenAI
        ToolBot(openai),    # 带工具 × OpenAI
        BasicBot(ollama),   # 基础对话 × Ollama
        ToolBot(ollama),    # 带工具 × Ollama
    ]
    for bot in bots:
        print(bot.chat("今天天气如何"))


if __name__ == "__main__":
    main()
