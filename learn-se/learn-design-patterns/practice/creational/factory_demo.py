"""工厂方法模式示例：文档导出"""

from abc import ABC, abstractmethod


class Document(ABC):
    @abstractmethod
    def render(self) -> str: ...


class PDFDocument(Document):
    def render(self) -> str:
        return "[PDF] Document content rendered as PDF"


class MarkdownDocument(Document):
    def render(self) -> str:
        return "[MD] Document content rendered as Markdown"


class DocumentCreator(ABC):
    @abstractmethod
    def create_document(self) -> Document: ...

    def export(self) -> str:
        doc = self.create_document()
        return doc.render()


class PDFCreator(DocumentCreator):
    def create_document(self) -> Document:
        return PDFDocument()


class MarkdownCreator(DocumentCreator):
    def create_document(self) -> Document:
        return MarkdownDocument()


def main():
    creators = {
        "pdf": PDFCreator(),
        "md": MarkdownCreator(),
    }
    for name, creator in creators.items():
        print(f"{name}: {creator.export()}")


if __name__ == "__main__":
    main()
