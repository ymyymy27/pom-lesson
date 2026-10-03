"""模拟内存数据库"""
from __future__ import annotations

ARTICLES: dict[int, dict] = {
    1: {"id": 1, "title": "Redis 入门", "body": "键值存储，速度极快。"},
    2: {"id": 2, "title": "缓存模式", "body": "Cache Aside 最常用。"},
}

USERS: dict[str, dict] = {
    "demo": {"id": 1, "username": "demo", "password": "demo123"},
}


def get_article(article_id: int) -> dict | None:
    return ARTICLES.get(article_id)


def list_articles() -> list[dict]:
    return list(ARTICLES.values())


def create_article(title: str, body: str) -> dict:
    new_id = max(ARTICLES.keys(), default=0) + 1
    article = {"id": new_id, "title": title, "body": body}
    ARTICLES[new_id] = article
    return article


def authenticate(username: str, password: str) -> dict | None:
    user = USERS.get(username)
    if user and user["password"] == password:
        return {"id": user["id"], "username": user["username"]}
    return None


def get_user(user_id: int) -> dict | None:
    for user in USERS.values():
        if user["id"] == user_id:
            return {"id": user["id"], "username": user["username"]}
    return None
