"""抽象工厂模式示例：模型供应商族（AI 开发版）

核心思想：一个工厂 = 一整套配套产品。
业务代码只认 ModelFactory 接口，保证 chat 和 embedding
永远来自同一供应商，不会"OpenAI 的聊天 + Anthropic 的向量"混搭。
"""

from abc import ABC, abstractmethod


# --- 产品接口 ---

class ChatModel(ABC):
    @abstractmethod
    def chat(self, message: str) -> str: ...


class EmbeddingModel(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]: ...


# --- OpenAI 族的具体产品 ---

class OpenAIChat(ChatModel):
    def chat(self, message: str) -> str:
        return f"[OpenAI] 回复: {message}"


class OpenAIEmbedding(EmbeddingModel):
    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2]  # 示意向量，真实场景由模型计算


# --- Anthropic 族的具体产品 ---

class AnthropicChat(ChatModel):
    def chat(self, message: str) -> str:
        return f"[Anthropic] 回复: {message}"


class AnthropicEmbedding(EmbeddingModel):
    def embed(self, text: str) -> list[float]:
        return [0.3, 0.4]  # 示意向量


# --- 抽象工厂：每个子类代表一整"族" ---

class ModelFactory(ABC):
    @abstractmethod
    def create_chat(self) -> ChatModel: ...

    @abstractmethod
    def create_embedding(self) -> EmbeddingModel: ...


class OpenAIStack(ModelFactory):
    def create_chat(self) -> ChatModel:
        return OpenAIChat()

    def create_embedding(self) -> EmbeddingModel:
        return OpenAIEmbedding()


class AnthropicStack(ModelFactory):
    def create_chat(self) -> ChatModel:
        return AnthropicChat()

    def create_embedding(self) -> EmbeddingModel:
        return AnthropicEmbedding()


# --- 业务代码：只认抽象工厂，绝不混搭 ---

def build_rag_app(factory: ModelFactory) -> str:
    chat = factory.create_chat()      # 和 embedding 一定来自同一族
    embed = factory.create_embedding()
    return f"{chat.chat('你好')} | 向量: {embed.embed('你好')}"


def main():
    stacks = {
        "openai": OpenAIStack(),
        "anthropic": AnthropicStack(),
    }
    for name, factory in stacks.items():
        print(f"{name}: {build_rag_app(factory)}")


if __name__ == "__main__":
    main()
