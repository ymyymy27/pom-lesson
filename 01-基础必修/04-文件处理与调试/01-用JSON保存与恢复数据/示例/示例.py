import json
tasks = [{"title": "实验", "done": False}]
text = json.dumps(tasks, ensure_ascii=False)
restored = json.loads(text)
print(restored[0]["title"])
