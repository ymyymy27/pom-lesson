"""分布式锁 — 运行: python distributed_lock.py"""
from __future__ import annotations

import threading
import time
import uuid
from contextlib import contextmanager
from typing import Generator

import redis

UNLOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


class RedisLock:
    def __init__(self, client: redis.Redis, name: str, ttl: int = 30):
        self.client = client
        self.key = f"myapp:lock:{name}"
        self.ttl = ttl
        self.token = str(uuid.uuid4())
        self._unlock = client.register_script(UNLOCK_SCRIPT)

    def acquire(self, retry_delay: float = 0.05, max_retries: int = 20) -> bool:
        for _ in range(max_retries):
            if self.client.set(self.key, self.token, nx=True, ex=self.ttl):
                return True
            time.sleep(retry_delay)
        return False

    def release(self) -> None:
        self._unlock(keys=[self.key], args=[self.token])


@contextmanager
def redis_lock(client: redis.Redis, name: str, ttl: int = 30) -> Generator[None, None, None]:
    lock = RedisLock(client, name, ttl=ttl)
    if not lock.acquire():
        raise TimeoutError(f"Could not acquire lock: {name}")
    try:
        yield
    finally:
        lock.release()


def main() -> None:
    client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    client.ping()

    stock_key = "myapp:stock:item:1"
    client.delete(stock_key, "myapp:lock:stock:item:1")
    client.set(stock_key, 1)

    success = 0
    counter_lock = threading.Lock()

    def worker(idx: int) -> None:
        nonlocal success
        try:
            with redis_lock(client, "stock:item:1", ttl=5):
                current = int(client.get(stock_key) or 0)
                if current <= 0:
                    print(f"worker {idx}: no stock")
                    return
                time.sleep(0.05)
                client.decr(stock_key)
                with counter_lock:
                    success += 1
                print(f"worker {idx}: deducted OK")
        except TimeoutError:
            print(f"worker {idx}: lock timeout")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"success count={success}, final stock={client.get(stock_key)}")


if __name__ == "__main__":
    main()
