"""OpenAI 兼容客户端演示 — 流式与非流式。

用法:
    python openai_client_demo.py [--base-url URL] [--model NAME] [--prompt TEXT]
"""

from __future__ import annotations

import argparse

from openai import OpenAI


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenAI 兼容推理服务客户端")
    parser.add_argument("--base-url", default="http://localhost:8000/v1")
    parser.add_argument("--api-key", default="unused")
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--prompt", default="用三句话介绍推理引擎")
    parser.add_argument("--max-tokens", type=int, default=256)
    args = parser.parse_args()

    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    messages = [{"role": "user", "content": args.prompt}]

    print("== 非流式 ==")
    resp = client.chat.completions.create(
        model=args.model,
        messages=messages,
        max_tokens=args.max_tokens,
        stream=False,
    )
    print(resp.choices[0].message.content)

    print("\n== 流式 ==")
    stream = client.chat.completions.create(
        model=args.model,
        messages=messages,
        max_tokens=args.max_tokens,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
    print()


if __name__ == "__main__":
    main()
