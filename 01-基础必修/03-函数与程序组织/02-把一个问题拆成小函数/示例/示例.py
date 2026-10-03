def count_unfinished(tasks):
    count = 0
    for task in tasks:
        if not task["done"]:
            count += 1
    return count

print(count_unfinished([{"done": True}, {"done": False}]))
