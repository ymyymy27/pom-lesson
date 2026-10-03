"""推理服务并发压测 — 输出 TTFT / TPOT / 总吞吐。

用法:
    python benchmark_client.py --base-url http://localhost:8000/v1 \
        --model Qwen/Qwen2.5-7B-Instruct \
        --concurrency 16 --requests 64

注意:
    - 测试前建议先预热服务（跑几轮请求）
    - 报告必须附带并发与分位延迟
"""

from __future__ import annotations

import argparse
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from openai import OpenAI


@dataclass
class Result:
    ttft: float
    total: float
    output_tokens: int
    ok: bool = True


def run_one(base_url: str, api_key: str, model: str, prompt: str, max_tokens: int) -> Result:
    client = OpenAI(base_url=base_url, api_key=api_key)
    started = time.perf_counter()
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            stream=True,
        )
        ttft: float | None = None
        tokens = 0
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                if ttft is None:
                    ttft = time.perf_counter() - started
                tokens += 1
        total = time.perf_counter() - started
        if ttft is None:
            return Result(0.0, total, tokens, ok=False)
        return Result(ttft, total, tokens)
    except Exception:
        return Result(0.0, time.perf_counter() - started, 0, ok=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="推理服务并发压测")
    parser.add_argument("--base-url", default="http://localhost:8000/v1")
    parser.add_argument("--api-key", default="unused")
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--prompt", default="写一段 200 字左右的短文，介绍推理引擎。")
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--concurrency", type=int, default=16)
    parser.add_argument("--requests", type=int, default=64)
    args = parser.parse_args()

    print(
        f"压测: model={args.model} concurrency={args.concurrency} "
        f"requests={args.requests}"
    )
    results: list[Result] = []
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [
            pool.submit(
                run_one,
                args.base_url,
                args.api_key,
                args.model,
                args.prompt,
                args.max_tokens,
            )
            for _ in range(args.requests)
        ]
        for future in as_completed(futures):
            results.append(future.result())
    wall = time.perf_counter() - started

    ok = [r for r in results if r.ok]
    failed = len(results) - len(ok)
    total_tokens = sum(r.output_tokens for r in ok)
    ttfts = [r.ttft for r in ok]
    tpots = [r.total / max(r.output_tokens, 1) for r in ok]

    def pct(values: list[float], p: float) -> float:
        if not values:
            return 0.0
        return statistics.quantiles(sorted(values), n=100, method="inclusive")[p - 1]

    print("\n结果:")
    print(f"  墙钟时间      : {wall:.1f}s")
    print(f"  成功率        : {len(ok)}/{len(results)} ({100 * len(ok) / len(results):.1f}%)")
    print(f"  总输出 tokens : {total_tokens}")
    print(f"  总吞吐        : {total_tokens / wall:.1f} tok/s")
    print(f"  TTFT P50/P99  : {pct(ttfts, 50):.3f}s / {pct(ttfts, 99):.3f}s")
    print(f"  TPOT P50/P99  : {pct(tpots, 50):.3f}s / {pct(tpots, 99):.3f}s")
    if failed:
        print(f"  !!! {failed} 个请求失败（超时/连接错误），请检查服务与超时设置")


if __name__ == "__main__":
    main()
