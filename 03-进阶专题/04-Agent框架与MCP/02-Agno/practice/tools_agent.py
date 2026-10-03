"""第2课示例：自定义工具 + Structured Output。

运行：python tools_agent.py
"""

from pydantic import BaseModel, Field

from agno.agent import Agent


def get_weather(city: str) -> str:
    """获取指定城市的当前天气（模拟数据，仅供学习）"""
    data = {
        "北京": "晴，25°C，湿度 40%",
        "上海": "多云，22°C，湿度 65%",
        "深圳": "阵雨，28°C，湿度 80%",
    }
    return data.get(city, f"{city}: 暂无数据")


class WeatherReport(BaseModel):
    city: str = Field(description="城市名称")
    condition: str = Field(description="天气状况")
    temperature: str = Field(description="温度")
    summary: str = Field(description="一句话中文总结")


agent = Agent(
    name="Weather Agent",
    model="openai:gpt-4o",
    tools=[get_weather],
    response_model=WeatherReport,
    instructions="用户问天气时必须先调用 get_weather 工具，再按 WeatherReport 格式返回。",
)


if __name__ == "__main__":
    response = agent.run("上海今天天气怎么样？")
    report: WeatherReport = response.content
    print(report.model_dump_json(indent=2, ensure_ascii=False))
