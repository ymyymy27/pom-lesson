"""建造者模式示例：构建复杂 Email 对象"""

from dataclasses import dataclass, field


@dataclass
class Email:
    to: str
    subject: str
    body: str = ""
    cc: list[str] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)
    priority: str = "normal"


class EmailBuilder:
    def __init__(self, to: str, subject: str):
        self._email = Email(to=to, subject=subject)

    def body(self, text: str) -> "EmailBuilder":
        self._email.body = text
        return self

    def cc(self, *addresses: str) -> "EmailBuilder":
        self._email.cc.extend(addresses)
        return self

    def attach(self, *files: str) -> "EmailBuilder":
        self._email.attachments.extend(files)
        return self

    def high_priority(self) -> "EmailBuilder":
        self._email.priority = "high"
        return self

    def build(self) -> Email:
        if not self._email.body:
            raise ValueError("Email body is required")
        return self._email


def main():
    email = (
        EmailBuilder("user@example.com", "Task Assigned")
        .body("You have been assigned to Task #42.")
        .cc("manager@example.com")
        .attach("spec.pdf")
        .high_priority()
        .build()
    )
    print(email)


if __name__ == "__main__":
    main()
