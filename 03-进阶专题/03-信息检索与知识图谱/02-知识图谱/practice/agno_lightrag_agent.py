"""第11课示例：LightRAG Server + Agno（HTTP Toolkit，生产推荐）。

前置：
  1. 启动 LightRAG Server（默认 http://localhost:9621）
     参考：https://github.com/HKUDS/LightRAG/blob/main/docs/LightRAG-API-Server.md
  2. 上传文档：POST /documents/text 或 /documents/upload
  3. uv pip install -r requirements-agno.txt && pip install httpx
  4. set OPENAI_API_KEY=sk-...

环境变量（可选）：
  LIGHTRAG_URL=http://localhost:9621
  LIGHTRAG_API_KEY=your-key

运行：python agno_lightrag_agent.py
"""

import os

import httpx
from agno.agent import Agent
from agno.tools import Toolkit
from dotenv import load_dotenv

load_dotenv()

LIGHTRAG_URL = os.getenv("LIGHTRAG_URL", "http://localhost:9621").rstrip("/")
LIGHTRAG_API_KEY = os.getenv("LIGHTRAG_API_KEY", "")
MAX_RESULT_CHARS = 4000


class LightRAGToolkit(Toolkit):
    """LightRAG Server REST API 封装 — 文档自动构图 + Graph RAG 检索。"""

    def __init__(self):
        super().__init__(name="lightrag")
        self.register(self.query_hybrid)
        self.register(self.query_local)
        self.register(self.query_global)
        self.register(self.query_mix)

    def _headers(self) -> dict:
        if LIGHTRAG_API_KEY:
            return {"X-API-Key": LIGHTRAG_API_KEY}
        return {}

    def _post_query(self, question: str, mode: str) -> str:
        payload = {
            "query": question,
            "mode": mode,
            "include_references": True,
        }
        try:
            r = httpx.post(
                f"{LIGHTRAG_URL}/query",
                json=payload,
                headers=self._headers(),
                timeout=60.0,
            )
            r.raise_for_status()
        except httpx.ConnectError:
            return (
                f"无法连接 LightRAG Server ({LIGHTRAG_URL})。"
                "请先启动 LightRAG Server 并上传文档。"
            )
        except httpx.HTTPStatusError as exc:
            return f"LightRAG 请求失败: {exc.response.status_code} {exc.response.text[:200]}"

        data = r.json()
        answer = data.get("response", str(data))
        refs = data.get("references", [])
        if refs:
            ref_lines = [f"- {ref.get('file_path', ref.get('reference_id', '?'))}" for ref in refs[:5]]
            answer += "\n\n【引用】\n" + "\n".join(ref_lines)
        return answer[:MAX_RESULT_CHARS]

    def query_hybrid(self, question: str) -> str:
        """文档库混合检索（默认首选）。结合局部实体与全局主题，适合大多数文档问答。"""
        return self._post_query(question, mode="hybrid")

    def query_local(self, question: str) -> str:
        """围绕具体实体/概念的局部检索。适合点名某人、某项目、某条款的问题。"""
        return self._post_query(question, mode="local")

    def query_global(self, question: str) -> str:
        """跨文档全局主题归纳。适合「有哪些类型/主题/趋势」类宏观问题。"""
        return self._post_query(question, mode="global")

    def query_mix(self, question: str) -> str:
        """图谱 + 向量深度融合。适合需要多跳推理的复杂文档问题。"""
        return self._post_query(question, mode="mix")


def create_lightrag_agent() -> Agent:
    return Agent(
        name="LightRAGAgent",
        model=os.getenv("AGNO_MODEL", "openai:gpt-4o"),
        tools=[LightRAGToolkit()],
        tool_call_limit=3,
        instructions=[
            "你是文档知识库助手，只能基于 lightrag 工具回答。",
            "默认使用 query_hybrid；具体实体用 query_local；宏观总结用 query_global；复杂多跳用 query_mix。",
            "工具无结果或连接失败时如实说明，不要编造。",
        ],
    )


def main():
    agent = create_lightrag_agent()
    question = os.getenv("DEMO_QUESTION", "文档中的主要内容主题有哪些？")
    print(f"LightRAG URL: {LIGHTRAG_URL}")
    print(f"问题：{question}\n")
    response = agent.run(question)
    print(response.content)


if __name__ == "__main__":
    main()
