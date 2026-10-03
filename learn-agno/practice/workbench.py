"""第5课示例：AgentOS 本地服务。

运行：
  uv pip install -r requirements-os.txt
  python workbench.py

访问：
  http://localhost:7777/docs
  https://os.agno.com （Connect Local → http://localhost:7777）
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.os import AgentOS
from agno.tools.workspace import Workspace

workbench = Agent(
    name="Workbench",
    model="openai:gpt-4o",
    db=SqliteDb(db_file="workbench.db"),
    tools=[Workspace(root=".", allowed=["read", "list", "search"])],
    enable_agentic_memory=True,
    add_history_to_context=True,
    num_history_runs=3,
    instructions="你是开发工作台助手，可以浏览当前目录文件并帮助整理、分析代码。用中文回复。",
    markdown=True,
)

agent_os = AgentOS(agents=[workbench], tracing=True)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="workbench:app", reload=True)
