import json
tasks = [{"title": "复习", "done": True}]
restored = json.loads(json.dumps(tasks, ensure_ascii=False))
print(restored[0]["title"], restored[0]["done"])
