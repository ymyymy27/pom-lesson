"""vLLM 异步压测客户端 — 需 GPU 上运行的 vLLM 服务。

用法:
  python benchmark_client.py
  python benchmark_client.py --concurrency 64 --requests 200
"""

from __future__ import annotations

import argparse
import asyncio
import os
import statistics
import sys
import time

from openai import AsyncOpenAI

BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
API_KEY = os.getenv("VLLM_API_KEY", "changeme")
MODEL = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")


async def benchmark(
    concurrency: int,
    num_requests: int,
    max_tokens: int,
    prompt: str,
) -> int:
    client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
    latencies: list[float] = []
    ttfts: list[float] = []
    sem = asyncio.Semaphore(concurrency)

    async def one_request() -> None:
        async with sem:
            start = time.perf_counter()
            ttft: float | None = None
            try:
                stream = await client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    stream=True,
                )
                async for chunk in stream:
                    if chunk.choices[0].delta.content and ttft is None:
                        ttft = time.perf_counter() - start
            except Exception as exc:
                print(f"请求失败: {exc}")
                return
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)
            if ttft is not None:
                ttfts.append(ttft)

    wall_start = time.perf_counter()
    await asyncio.gather(*[one_request() for _ in range(num_requests)])
    wall = time.perf_counter() - wall_start

    if not latencies:
        print("无成功请求，请检查 vLLM 服务是否运行。")
        return 1

    def pct(data: list[float], p: float) -> float:
        s = sorted(data)
        return s[min(int(len(s) * p), len(s) - 1)]

    print(f"目标: {BASE_URL}  model={MODEL}")
    print(f"并发={concurrency}, 请求数={num_requests}, max_tokens={max_tokens}")
    print(f"QPS: {num_requests / wall:.2f}")
    print(
        f"E2E  avg={statistics.mean(latencies):.3f}s  "
        f"p50={pct(latencies, 0.5):.3f}s  p95={pct(latencies, 0.95):.3f}s"
    )
    if ttfts:
        print(
            f"TTFT avg={statistics.mean(ttfts):.3f}s  "
            f"p95={pct(ttfts, 0.95):.3f}s"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="vLLM 压测客户端")
    parser.add_argument("--concurrency", type=int, default=32)
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--prompt", default="用100字介绍机器学习")
    args = parser.parse_args()
    return asyncio.run(
        benchmark(args.concurrency, args.requests, args.max_tokens, args.prompt)
    )


if __name__ == "__main__":
    sys.exit(main())
