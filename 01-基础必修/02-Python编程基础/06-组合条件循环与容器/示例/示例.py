tasks = [{"title": "预习", "done": True}, {"title": "实验", "done": False}]
count = 0
for task in tasks:
    if not task["done"]:
        count += 1
print(count)
