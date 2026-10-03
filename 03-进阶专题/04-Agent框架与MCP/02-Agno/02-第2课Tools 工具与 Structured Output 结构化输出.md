> 材料状态：进阶参考，已整理目录与链接；历史示例需要按课时环境复现。学习顺序以根目录《课程总览》为准。

# 第2课：Tools 工具与 Structured Output 结构化输出

## 1. Tools 是什么？

### 一句话解释

**Tools 就是 Agent 的「手和脚」** —— 没有工具，Agent 只能聊天；有了工具，它能查天气、读文件、调 API、跑代码。

### 工具调用流程

```
用户提问 → LLM 决定调用哪个工具 → 执行工具 → 结果回传给 LLM → 生成最终回答
```

---

## 2. 内置工具 vs 自定义工具

| 类型 | 适用场景 | 示例 |
|------|----------|------|
| 内置工具 | 通用能力 | `Workspace`、搜索、金融数据 |
| 自定义函数 | 业务逻辑 | 查数据库、调内部 API |
| MCP 工具 | 外部生态 | 接入 Cursor MCP 服务器 |

---

## 3. 自定义函数工具

### 3.1 基本写法

函数 **docstring** 会作为工具描述，LLM 据此决定是否调用：

```python
def get_weather(city: str) -> str:
    """获取指定城市的当前天气（模拟数据）"""
    data = {"北京": "晴 25°C", "上海": "多云 22°C"}
    return data.get(city, f"{city}: 暂无数据")

agent = Agent(
    model="openai:gpt-4o",
    tools=[get_weather],
    instructions="用工具查询天气后再回答用户。",
)
```

### 3.2 类型注解很重要

参数类型注解（`city: str`）会生成 JSON Schema，帮助 LLM 正确传参。

```python
def calculate(expression: str) -> str:
    """计算数学表达式，支持 + - * /"""
    try:
        result = eval(expression)  # 教学示例，生产环境勿用 eval
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"
```

### 3.3 多工具组合

```python
agent = Agent(
    model="openai:gpt-4o",
    tools=[get_weather, calculate],
)
```

---

## 4. Structured Output 结构化输出

### 4.1 为什么需要？

纯文本回复难以对接业务系统。Structured Output 让 Agent 返回 **Pydantic 模型**，可直接入库或传给前端。

### 4.2 定义响应模型

```python
from pydantic import BaseModel, Field

class WeatherReport(BaseModel):
    city: str = Field(description="城市名")
    condition: str = Field(description="天气状况")
    temperature: str = Field(description="温度")
    summary: str = Field(description="一句话总结")
```

### 4.3 绑定到 Agent

```python
agent = Agent(
    model="openai:gpt-4o",
    tools=[get_weather],
    response_model=WeatherReport,
    instructions="查询天气后，按 WeatherReport 格式返回。",
)

response = agent.run("北京天气怎么样？")
report: WeatherReport = response.content
print(report.city, report.temperature)
```

### 4.4 response_model 要点

| 要点 | 说明 |
|------|------|
| 使用 Pydantic v2 | `BaseModel` + `Field` |
| `Field(description=...)` | 帮助 LLM 理解字段含义 |
| `response.content` | 返回的是模型实例，不是字符串 |

---

## 5. 示例代码：tools_agent.py

本课示例在 `practice/tools_agent.py`，包含：

1. 自定义 `get_weather` 工具
2. `WeatherReport` 结构化输出
3. 终端打印 JSON 格式结果

运行：

```powershell
cd 03-进阶专题\04-Agent框架与MCP\02-Agno\practice
python tools_agent.py
```

---

## 6. 工具调用调试技巧

### 6.1 明确 instructions

```python
instructions="""
1. 用户问天气时，必须先调用 get_weather 工具
2. 不要编造天气数据
3. 用中文回复
"""
```

### 6.2 限制工具调用次数

生产环境可配合官方文档 [Tool Call Limit](https://docs.agno.com/examples/agents/tools/tool-call-limit) 防止无限循环。

---

## 7. 常用内置工具（扩展阅读）

安装额外依赖后可使用：

```python
# 网页搜索（需安装 duckduckgo-search 等）
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    tools=[DuckDuckGoTools()],
)
```

| 工具 | 用途 |
|------|------|
| `Workspace` | 本地文件 |
| `DuckDuckGoTools` | 网页搜索 |
| `YFinanceTools` | 股票/金融 |
| `MCPTools` | MCP 协议 |

---

## 动手练习

### 练习 1：新增工具

添加 `list_cities()` 工具，返回支持查询的城市列表 `["北京", "上海", "深圳"]`。

### 练习 2：扩展结构化模型

在 `WeatherReport` 中增加 `humidity: str` 字段，并让 Agent 填充该字段。

### 练习 3：纯结构化（无工具）

去掉 tools，仅让 Agent 根据常识生成 `WeatherReport`（对比有工具时的差异）。

---

## 验收标准

- [ ] 能编写带 docstring 和类型注解的自定义工具
- [ ] 能定义 Pydantic `response_model` 并解析 `response.content`
- [ ] `tools_agent.py` 运行成功，输出结构化 JSON
- [ ] 理解「工具 docstring = LLM 的工具说明书」

---

## 下一课预告

第3课学习 **Knowledge RAG** 和 **Memory 记忆**，让 Agent 能读文档并记住用户偏好。

**延伸阅读：**

- [Agent with Tools](https://docs.agno.com/agents/usage/agent-with-tools)
- [Agent with Structured Output](https://docs.agno.com/agents/usage/agent-with-structured-output)
- [examples/basics](https://docs.agno.com/examples/basics/overview)
