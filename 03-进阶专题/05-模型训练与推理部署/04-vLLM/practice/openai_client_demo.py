"""OpenAI 兼容客户端示例 — 需先启动 vLLM 服务。

启动服务:
  python -m vllm.entrypoints.openai.api_server \\
      --model Qwen/Qwen2.5-7B-Instruct \\
      --served-model-name qwen-7b \\
      --api-key changeme \\
      --port 8000

运行:
  python openai_client_demo.py
"""

import os
import sys

from openai import OpenAI

BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
API_KEY = os.getenv("VLLM_API_KEY", "changeme")
MODEL = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")


def chat_once(client: OpenAI) -> None:
    print("=== 非流式对话 ===")
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "用一句话介绍 vLLM"}],
        max_tokens=128,
        temperature=0.7,
    )
    print(resp.choices[0].message.content)
    print(f"usage: {resp.usage}\n")


def chat_stream(client: OpenAI) -> None:
    print("=== 流式对话 ===")
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "写一句关于 AI 的诗"}],
        max_tokens=64,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
    print("\n")


def main() -> int:
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    try:
        models = client.models.list()
        print(f"可用模型: {[m.id for m in models.data]}\n")
    except Exception as exc:
        print(f"无法连接 vLLM 服务 ({BASE_URL}): {exc}")
        print("请先启动 vLLM api_server，或设置 VLLM_BASE_URL 环境变量。")
        return 1

    chat_once(client)
    chat_stream(client)
    return 0


if __name__ == "__main__":
    sys.exit(main())
