def count_done(tasks):
    count = 0
    for task in tasks:
        if task["done"]:
            count += 1
    return count

print(count_done([]))
print(count_done([{"done": True}, {"done": True}]))
