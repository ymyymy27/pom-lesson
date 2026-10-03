"""第4课示例：Research Team 多智能体协作。

运行：python research_team.py
"""

from agno.agent import Agent
from agno.team import Team

researcher = Agent(
    name="Researcher",
    model="openai:gpt-4o",
    instructions=(
        "你是调研员。列出与问题相关的要点、概念和参考信息。"
        "只输出调研笔记，不写最终报告。使用中文。"
    ),
)

writer = Agent(
    name="Writer",
    model="openai:gpt-4o",
    instructions=(
        "你是技术写手。根据调研结果写一份结构清晰的 Markdown 报告，"
        "包含：概述、核心要点、学习建议。使用中文。"
    ),
)

research_team = Team(
    name="Research Team",
    members=[researcher, writer],
    instructions="Researcher 先调研，Writer 再写报告。最终输出一份完整 Markdown 报告。",
    markdown=True,
)

if __name__ == "__main__":
    research_team.print_response(
        "为 Python 开发者写一份 Agno 框架入门介绍（500 字以内）",
        stream=True,
    )
