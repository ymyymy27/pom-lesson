"""用户服务 — 第 4 课 Mock 测试示例"""

from dataclasses import dataclass


class UserNotFoundError(Exception):
    pass


@dataclass
class User:
    id: int
    name: str
    email: str = ""


class UserService:
    def __init__(self, repo):
        self.repo = repo

    def get(self, user_id: int) -> User:
        user = self.repo.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        return user

    def create(self, name: str, email: str) -> User:
        user = User(id=0, name=name, email=email)
        return self.repo.save(user)
