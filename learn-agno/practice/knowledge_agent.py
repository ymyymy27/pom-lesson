"""第3课示例：Session + Memory + 基于本地文档的简易 RAG。

运行：python knowledge_agent.py

说明：完整向量 RAG 需 LanceDB 等依赖。本示例用「文档注入 instructions」
演示 Knowledge 思路，降低入门依赖。进阶见官方 Agent with Knowledge 文档。
"""

from pathlib import Path

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

DOCS_DIR = Path(__file__).parent / "docs"
DB_FILE = Path(__file__).parent / "knowledge_agent.db"


def load_docs() -> str:
    parts = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        parts.append(f"## 文件: {path.name}\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(parts)


doc_context = load_docs()

agent = Agent(
    name="Docs Assistant",
    model="openai:gpt-4o",
    db=SqliteDb(db_file=str(DB_FILE)),
    enable_agentic_memory=True,
    add_history_to_context=True,
    num_history_runs=3,
    instructions=f"""你是 Agno 学习助手。仅根据以下文档回答问题，不知道就说不知道。

{doc_context}
""",
    markdown=True,
)

SESSION_ID = "learn-session-001"
USER_ID = "learner"


if __name__ == "__main__":
    print("=== 问题1：Agno 有哪些核心组件？ ===\n")
    agent.print_response(
        "Agno 有哪些核心组件？用中文简要列出。",
        session_id=SESSION_ID,
        user_id=USER_ID,
        stream=True,
    )

    print("\n=== 问题2：Session 连续性测试 ===\n")
    agent.print_response(
        "我上一个问题问的是什么？",
        session_id=SESSION_ID,
        user_id=USER_ID,
        stream=True,
    )
