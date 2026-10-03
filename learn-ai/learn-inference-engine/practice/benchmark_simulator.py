"""批处理模式模拟器 — 无需 GPU，理解静态 vs 连续批处理差异。

运行: python benchmark_simulator.py
"""

from __future__ import annotations

import argparse
import random
import statistics


def simulate_requests(n: int, seed: int = 42) -> list[int]:
    rng = random.Random(seed)
    # 模拟 50~300 个输出 token 的请求
    return [rng.randint(50, 300) for _ in range(n)]


def static_batching(tokens: list[int], batch_size: int, base_ms: float = 1.0) -> dict:
    total_ms = 0.0
    per_request: list[float] = []
    for i in range(0, len(tokens), batch_size):
        batch = tokens[i : i + batch_size]
        batch_time = base_ms * max(batch) * 0.4
        total_ms += batch_time
        per_request.extend([batch_time] * len(batch))
    return {
        "mode": "static",
        "total_ms": total_ms,
        "avg_latency_ms": statistics.mean(per_request),
        "throughput_tps": sum(tokens) / (total_ms / 1000),
    }


def continuous_batching(tokens: list[int], batch_size: int, base_ms: float = 1.0) -> dict:
    remaining = tokens.copy()
    completed: list[float] = []
    total_ms = 0.0
    while remaining:
        batch = remaining[:batch_size]
        remaining = remaining[len(batch) :]
        step_cost = base_ms * statistics.mean(batch) * 0.25
        total_ms += step_cost
        done_idx = min(range(len(batch)), key=lambda i: batch[i])
        completed.append(step_cost)
        # 完成一个立即补一个（核心差异）
        if remaining:
            remaining.insert(0, batch[done_idx])
    return {
        "mode": "continuous",
        "total_ms": total_ms,
        "avg_latency_ms": statistics.mean(completed),
        "throughput_tps": sum(tokens) / (total_ms / 1000),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="批处理模式模拟器")
    parser.add_argument("--requests", type=int, default=50, help="请求数量")
    parser.add_argument("--batch-size", type=int, default=8, help="批大小")
    args = parser.parse_args()

    tokens = simulate_requests(args.requests)
    print(f"{args.requests} 个请求（输出 token 50–300），批大小={args.batch_size}\n")
    print(f"{'模式':<14} {'总时间(ms)':>12} {'平均延迟(ms)':>14} {'吞吐(t/s)':>12}")
    print("-" * 56)
    results = [static_batching(tokens, args.batch_size), continuous_batching(tokens, args.batch_size)]
    for r in results:
        print(
            f"{r['mode']:<14} {r['total_ms']:>12.0f} "
            f"{r['avg_latency_ms']:>14.1f} {r['throughput_tps']:>12.0f}"
        )
    speedup = results[1]["throughput_tps"] / results[0]["throughput_tps"]
    print(f"\n连续批处理吞吐约为静态的 {speedup:.1f} 倍（vLLM 核心优势之一）。")
    print("试试 --batch-size 4 或 16，观察差距如何变化。")


if __name__ == "__main__":
    main()
