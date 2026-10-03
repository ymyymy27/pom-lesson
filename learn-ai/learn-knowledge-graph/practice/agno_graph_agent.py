"""第11课示例：Agno + 组织知识图谱（GraphRepository Toolkit）。

前置：
  docker compose up -d
  python seed_demo_graph.py
  uv pip install -r requirements-agno.txt
  set OPENAI_API_KEY=sk-...

运行：python agno_graph_agent.py
"""

import os
import sys
from pathlib import Path

# 允许从 practice 目录直接 import graph_api
sys.path.insert(0, str(Path(__file__).parent))

from agno.agent import Agent
from agno.tools import Toolkit
from dotenv import load_dotenv
from graph_api import GraphRepository, NEO4J_AUTH, NEO4J_URI
from neo4j import GraphDatabase
from pydantic import BaseModel, Field

load_dotenv()


class ProjectFact(BaseModel):
    project_name: str
    role: str | None = None


class PersonProjectsAnswer(BaseModel):
    person_name: str
    projects: list[ProjectFact]
    note: str = Field(default="", description="补充说明，无则留空")


class OrgGraphToolkit(Toolkit):
    """组织图谱只读工具集 — 生产推荐模式，替代任意 Cypher。"""

    def __init__(self, repo: GraphRepository):
        super().__init__(name="org_graph")
        self.repo = repo
        self.register(self.search_people)
        self.register(self.get_person_projects)
        self.register(self.get_neighbors)

    def search_people(self, name: str, limit: int = 5) -> str:
        """按姓名模糊搜索在职员工。适用于「找张三」「谁叫李四」；返回 id 供后续工具使用。"""
        results = self.repo.search_people(name, limit=limit)
        if not results:
            return "未找到匹配人员。"
        return str(results)

    def get_person_projects(self, person_id: str) -> str:
        """获取员工的部门与参与项目。person_id 必须来自 search_people，不要猜测。"""
        data = self.repo.get_person_with_projects(person_id)
        if not data:
            return "人员不存在。"
        return str(data)

    def get_neighbors(self, entity_id: str, limit: int = 20) -> str:
        """获取实体一度邻居及关系类型。适用于汇报链、部门归属、项目关联。"""
        data = self.repo.get_neighbors(entity_id, limit=limit)
        if not data:
            return "实体不存在或无邻居。"
        return str(data)


def create_org_agent(*, db=None, structured: bool = True) -> Agent:
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    repo = GraphRepository(driver)
    toolkit = OrgGraphToolkit(repo)

    kwargs = {
        "name": "OrgGraphAgent",
        "model": os.getenv("AGNO_MODEL", "openai:gpt-4o"),
        "tools": [toolkit],
        "tool_call_limit": 5,
        "instructions": [
            "你是组织架构知识图谱助手，只能基于 org_graph 工具回答。",
            "找人员时先 search_people，再用返回的 id 调用 get_person_projects。",
            "关系、汇报链问题用 get_neighbors。",
            "工具无结果时明确说不知道，不要编造。",
        ],
    }
    if db is not None:
        kwargs["db"] = db
        kwargs["add_history_to_context"] = True
        kwargs["num_history_runs"] = 3
    if structured:
        kwargs["response_model"] = PersonProjectsAnswer

    return Agent(**kwargs)


def main():
    agent = create_org_agent()
    question = "张三参与了哪些项目？他在项目中的角色是什么？"
    print(f"问题：{question}\n")
    response = agent.run(question)
    if isinstance(response.content, PersonProjectsAnswer):
        print(response.content.model_dump_json(indent=2, ensure_ascii=False))
    else:
        print(response.content)


if __name__ == "__main__":
    main()
