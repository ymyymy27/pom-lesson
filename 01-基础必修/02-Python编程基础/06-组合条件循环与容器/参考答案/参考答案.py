tasks = [{"done": True}, {"done": False}, {"done": False}]
count = 0
for task in tasks:
    if not task["done"]:
        count += 1
print(count)
