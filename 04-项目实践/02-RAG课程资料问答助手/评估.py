import json
from pathlib import Path
from 问答助手 import ask
base=Path(__file__).resolve().parent
documents=json.loads((base/"课程资料.json").read_text(encoding="utf-8"))
questions=json.loads((base/"评估问题.json").read_text(encoding="utf-8"))
for method in ["keyword","vector"]:
    correct=0
    for item in questions:
        result=ask(item["question"],documents,method)
        found=result["sources"][0]["source"] if result["sources"] else None
        correct += found == item["expected"]
        print(method,item["question"],found==item["expected"])
    print(f"{method}: {correct}/{len(questions)}，仅用于当前小样本实验")
