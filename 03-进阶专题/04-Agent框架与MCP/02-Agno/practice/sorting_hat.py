"""第1课示例：扫描文件夹并提议整理方案。

运行：python sorting_hat.py
"""

from pathlib import Path

from agno.agent import Agent
from agno.tools.workspace import Workspace

folder = Path(__file__).parent

sorting_hat = Agent(
    name="Sorting Hat",
    model="openai:gpt-4o",
    tools=[Workspace(root=str(folder), allowed=["read", "list", "search"])],
    instructions=(
        "Walk the folder, figure out what's there, and propose a clean organization. "
        "Decide the categories yourself. Return a tidy summary, a category breakdown, "
        "and a folder tree. Reply in Chinese."
    ),
    markdown=True,
)

if __name__ == "__main__":
    sorting_hat.print_response(f"Inventory and organize {folder}", stream=True)
