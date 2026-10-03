"""
Step 4：Text2Cypher 演示
=======================
让 LLM 根据 Schema 生成 Cypher。若本机有 Neo4j 驱动且配置了
NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD，会尝试执行只读查询。

注意：运行后观察生成的 Cypher，常见错误包括：
1. 关系方向写反（如把 REPORTS_TO 写成反向箭头）
2. 实体名截断或改写（如 '项目X' 变成 'X'）
3. 属性名/标签名不在 Schema 中
生产环境必须对生成结果做校验（试运行 + 结果合理性检查）。
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import chat_safe  # noqa: E402


SCHEMA_TEXT = """图数据库 Schema：
- Person: {name}
- Department: {name}
- Project: {name, stack}
- Technology: {name}

关系：
- (Person)-[:REPORTS_TO]->(Person)
- (Person)-[:MANAGES]->(Department)
- (Department)-[:OWNS]->(Project)
- (Person)-[:WORKS_ON]->(Project)
- (Project)-[:USES]->(Technology)
"""

CYPHER_PROMPT = """你是 Cypher 专家。根据 Schema 和用户问题，生成一条只读 Cypher 查询。
只输出 Cypher 语句，不要解释。

Schema：
{schema}

问题：{question}
"""


def main() -> None:
    questions = [
        "张三的上级管理的部门负责什么项目？",
        "项目X 使用了哪些技术？",
        "李四管理哪些部门？他管理的部门拥有哪些项目？",
    ]

    for q in questions:
        print("\n" + "=" * 66)
        print(f"问题：{q}")
        cypher = chat_safe(CYPHER_PROMPT.format(schema=SCHEMA_TEXT, question=q), max_tokens=200)
        print("生成的 Cypher：")
        print(cypher or "（LLM 不可用）")

        if cypher and "NEO4J_URI" in os.environ:
            try:
                from neo4j import GraphDatabase

                uri = os.environ["NEO4J_URI"]
                user = os.environ.get("NEO4J_USER", "neo4j")
                password = os.environ.get("NEO4J_PASSWORD", "")
                with GraphDatabase.driver(uri, auth=(user, password)) as driver:
                    with driver.session() as session:
                        records = session.run(cypher).data()
                        print("执行结果：")
                        for r in records:
                            print(" ", r)
            except ImportError:
                print("（未安装 neo4j 驱动，跳过执行。pip install neo4j 可启用）")
            except Exception as e:
                print(f"（执行失败：{e}）")
        else:
            print("（未配置 Neo4j，仅演示生成；配置 NEO4J_URI 后可执行）")


if __name__ == "__main__":
    main()
