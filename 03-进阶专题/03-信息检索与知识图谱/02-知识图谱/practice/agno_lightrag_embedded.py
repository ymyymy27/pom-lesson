"""第11课示例：嵌入式 LightRAG Core + Agno（单机 demo）。

安装：uv pip install lightrag-hku openai agno python-dotenv
环境：set OPENAI_API_KEY=sk-...

运行：python agno_lightrag_embedded.py

注意：官方推荐生产环境使用 LightRAG Server + agno_lightrag_agent.py。
"""

import asyncio
import os
from pathlib import Path

from agno.agent import Agent
from dotenv import load_dotenv

load_dotenv()

WORKING_DIR = os.getenv("LIGHTRAG_WORKING_DIR", "./lightrag_storage")
SAMPLE_DOC = Path(__file__).parent / "data" / "sample_doc.txt"

_rag = None
_rag_lock = asyncio.Lock()


async def get_lightrag():
    global _rag
    async with _rag_lock:
        if _rag is not None:
            return _rag

        from lightrag import LightRAG
        from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed

        rag = LightRAG(
            working_dir=WORKING_DIR,
            embedding_func=openai_embed,
            llm_model_func=gpt_4o_mini_complete,
            addon_params={"language": "Simplified Chinese"},
        )
        await rag.initialize_storages()
        _rag = rag
        return _rag


async def ensure_sample_ingested(rag) -> None:
    if not SAMPLE_DOC.exists():
        return
    text = SAMPLE_DOC.read_text(encoding="utf-8")
    await rag.ainsert(text, file_paths=str(SAMPLE_DOC))


def query_lightrag(question: str, mode: str = "hybrid") -> str:
    """查询 LightRAG 文档知识库。mode 可选 local|global|hybrid|mix|naive。"""

    async def _run():
        from lightrag import QueryParam

        rag = await get_lightrag()
        await ensure_sample_ingested(rag)
        return await rag.aquery(question, param=QueryParam(mode=mode))

    return asyncio.run(_run())


def create_embedded_agent() -> Agent:
    return Agent(
        name="EmbeddedLightRAGAgent",
        model=os.getenv("AGNO_MODEL", "openai:gpt-4o"),
        tools=[query_lightrag],
        tool_call_limit=2,
        instructions=[
            "文档类问题必须调用 query_lightrag。",
            "默认 mode=hybrid；复杂多跳可在问题中说明需要 mix 模式（通过多次调用尝试不同 mode）。",
        ],
    )


def main():
    agent = create_embedded_agent()
    question = "示例文档里提到了哪些人物或组织？"
    print(f"working_dir: {WORKING_DIR}")
    print(f"问题：{question}\n")
    response = agent.run(question)
    print(response.content)


if __name__ == "__main__":
    main()
