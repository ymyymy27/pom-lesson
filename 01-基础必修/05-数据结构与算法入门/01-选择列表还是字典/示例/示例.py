tasks = [{"id": 1, "title": "阅读"}, {"id": 2, "title": "实验"}]
by_id = {task["id"]: task for task in tasks}
print(by_id[2]["title"])
