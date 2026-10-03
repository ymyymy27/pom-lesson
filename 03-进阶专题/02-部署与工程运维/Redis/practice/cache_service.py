"""简易缓存服务 — 运行: python cache_service.py"""
from __future__ import annotations

import json
import time
from typing import Any, Callable, Optional

import redis


class CacheService:
    def __init__(self, client: redis.Redis, prefix: str = "myapp:cache", default_ttl: int = 3600):
        self.redis = client
        self.prefix = prefix
        self.default_ttl = default_ttl

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    def get(self, key: str) -> Optional[Any]:
        raw = self.redis.get(self._key(key))
        if raw is None:
            return None
        return json.loads(raw)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self.redis.setex(
            self._key(key),
            ttl or self.default_ttl,
            json.dumps(value, ensure_ascii=False),
        )

    def delete(self, key: str) -> None:
        self.redis.delete(self._key(key))

    def get_or_set(self, key: str, fetch: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        cached = self.get(key)
        if cached is not None:
            print(f"[HIT]  {key}")
            return cached
        print(f"[MISS] {key}")
        data = fetch()
        self.set(key, data, ttl)
        return data


def fake_db_query(user_id: int) -> dict:
    time.sleep(0.1)  # 模拟慢查询
    return {"id": user_id, "name": f"User-{user_id}"}


def main() -> None:
    client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    client.ping()

    cache = CacheService(client)
    cache.delete("user:1")

    u1 = cache.get_or_set("user:1", lambda: fake_db_query(1), ttl=60)
    u2 = cache.get_or_set("user:1", lambda: fake_db_query(1), ttl=60)
    assert u1 == u2
    print("OK — 第二次应只出现 [HIT]")


if __name__ == "__main__":
    main()
