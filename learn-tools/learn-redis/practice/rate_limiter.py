"""滑动窗口限流 — 运行: python rate_limiter.py"""
from __future__ import annotations

import time
import uuid

import redis


class SlidingWindowRateLimiter:
    def __init__(self, client: redis.Redis, prefix: str = "myapp:ratelimit"):
        self.redis = client
        self.prefix = prefix

    def is_limited(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        redis_key = f"{self.prefix}:{key}"
        member = f"{now}:{uuid.uuid4().hex}"

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(redis_key, 0, now - window_seconds)
        pipe.zadd(redis_key, {member: now})
        pipe.zcard(redis_key)
        pipe.expire(redis_key, window_seconds)
        _, _, count, _ = pipe.execute()
        return count > limit


def main() -> None:
    client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    client.ping()

    limiter = SlidingWindowRateLimiter(client)
    key = "demo:endpoint"

    blocked = 0
    for i in range(15):
        if limiter.is_limited(key, limit=10, window_seconds=60):
            blocked += 1
        print(f"request {i + 1}: {'BLOCKED' if blocked and i >= 10 else 'OK'}")

    print(f"blocked {blocked} / 15 requests (limit=10/min)")


if __name__ == "__main__":
    main()
