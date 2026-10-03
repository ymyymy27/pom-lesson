"""第11课示例：AgentOS 服务化组织图谱 Agent。

运行：
  docker compose up -d && python seed_demo_graph.py
  uv pip install -r requirements-agno.txt
  set OPENAI_API_KEY=sk-...
  python agno_graph_agentos.py

访问：http://localhost:7777/docs
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agno.db.sqlite import SqliteDb
from agno.os import AgentOS
from agno_graph_agent import create_org_agent
from dotenv import load_dotenv

load_dotenv()

org_agent = create_org_agent(
    db=SqliteDb(db_file="org_agent.db"),
    structured=False,
)

agent_os = AgentOS(agents=[org_agent], tracing=True)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="agno_graph_agentos:app", reload=True, port=7777)
