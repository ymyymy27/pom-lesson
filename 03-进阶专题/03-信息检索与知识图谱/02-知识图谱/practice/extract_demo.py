"""LLM 抽取演示（需 OPENAI_API_KEY）。运行：python extract_demo.py"""

import json
import os
from pathlib import Path

SAMPLE_DOC = Path(__file__).parent / "data" / "sample_doc.txt"

EXTRACT_SYSTEM = """你是知识图谱抽取助手。严格按 Schema 输出 JSON。
只抽取文本中明确提到的实体和关系，不要推测。
实体 label 只能是：Person, Company, Department, Project。
关系 type 只能是：WORKS_AT, MEMBER_OF, WORKS_ON, REPORTS_TO, OWNED_BY, BELONGS_TO。"""

EXTRACT_USER = """文本：
{text}

输出 JSON：
{{"entities": [{{"label": str, "name": str, "temp_id": str, "confidence": float}}],
  "relations": [{{"type": str, "from_temp_id": str, "to_temp_id": str, "confidence": float}}]}}"""


def extract_with_llm(text: str) -> dict:
    from openai import OpenAI

    client = OpenAI()
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": EXTRACT_USER.format(text=text)},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(resp.choices[0].message.content)


def main():
    text = SAMPLE_DOC.read_text(encoding="utf-8")
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set. Showing expected output structure instead.")
        print(json.dumps({
            "entities": [
                {"label": "Person", "name": "张三", "temp_id": "e1", "confidence": 0.95},
                {"label": "Person", "name": "李四", "temp_id": "e2", "confidence": 0.95},
                {"label": "Project", "name": "订单系统", "temp_id": "e3", "confidence": 0.92},
            ],
            "relations": [
                {"type": "REPORTS_TO", "from_temp_id": "e1", "to_temp_id": "e2", "confidence": 0.9},
                {"type": "WORKS_ON", "from_temp_id": "e1", "to_temp_id": "e3", "confidence": 0.88},
                {"type": "OWNED_BY", "from_temp_id": "e3", "to_temp_id": "e2", "confidence": 0.85},
            ],
        }, ensure_ascii=False, indent=2))
        return

    result = extract_with_llm(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
