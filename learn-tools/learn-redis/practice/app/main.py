"""FastAPI + Redis 实战 — 在 practice/ 目录运行: uvicorn app.main:app --reload"""
from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path
from typing import Optional

import redis
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel

# 允许从 practice/ 根目录导入 cache_service 等模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cache_service import CacheService
from rate_limiter import SlidingWindowRateLimiter

from . import store

app = FastAPI(title="learn-redis demo")

redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
cache = CacheService(redis_client, prefix="myapp:cache")
limiter = SlidingWindowRateLimiter(redis_client)


class LoginBody(BaseModel):
    username: str
    password: str


class ArticleBody(BaseModel):
    title: str
    body: str


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request, limit: int, window: int) -> None:
    key = f"{client_ip(request)}:{request.url.path}"
    if limiter.is_limited(key, limit=limit, window_seconds=window):
        raise HTTPException(status_code=429, detail="Too many requests")


def create_session(user_id: int, ttl: int = 86400) -> str:
    session_id = secrets.token_urlsafe(32)
    redis_client.setex(
        f"myapp:session:{session_id}",
        ttl,
        json.dumps({"user_id": user_id}),
    )
    return session_id


def get_session_user(session_id: Optional[str]) -> dict | None:
    if not session_id:
        return None
    raw = redis_client.get(f"myapp:session:{session_id}")
    if not raw:
        return None
    payload = json.loads(raw)
    return store.get_user(payload["user_id"])


@app.get("/health")
def health():
    try:
        redis_client.set("_health", "1", ex=5)
        ok = redis_client.get("_health") == "1"
    except redis.RedisError:
        ok = False
    return {"status": "ok" if ok else "degraded", "redis": ok}


@app.get("/articles")
def list_articles(request: Request):
    check_rate_limit(request, limit=100, window=60)
    return {"data": store.list_articles()}


@app.get("/articles/{article_id}")
def get_article(article_id: int, request: Request):
    check_rate_limit(request, limit=100, window=60)
    key = f"article:{article_id}"
    cached = cache.get(key)
    if cached is not None:
        return {"source": "cache", "data": cached}

    article = store.get_article(article_id)
    if article is None:
        raise HTTPException(404)

    cache.set(key, article, ttl=300)
    return {"source": "db", "data": article}


@app.post("/articles")
def create_article(body: ArticleBody, request: Request):
    user = get_session_user(request.cookies.get("session_id"))
    if not user:
        raise HTTPException(401, detail="Login required")

    article = store.create_article(body.title, body.body)
    cache.delete(f"article:{article['id']}")
    return {"data": article}


@app.post("/auth/login")
def login(body: LoginBody, response: Response):
    user = store.authenticate(body.username, body.password)
    if not user:
        raise HTTPException(401, detail="Invalid credentials")
    session_id = create_session(user["id"])
    response.set_cookie("session_id", session_id, httponly=True, max_age=86400)
    return {"user": user}


@app.get("/auth/me")
def me(request: Request):
    user = get_session_user(request.cookies.get("session_id"))
    if not user:
        raise HTTPException(401)
    return {"user": user}


@app.post("/auth/logout")
def logout(response: Response, request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        redis_client.delete(f"myapp:session:{session_id}")
    response.delete_cookie("session_id")
    return {"ok": True}
