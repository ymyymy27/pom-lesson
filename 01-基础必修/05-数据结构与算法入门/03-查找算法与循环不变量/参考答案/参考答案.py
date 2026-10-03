def find_index(items, target):
    for index, value in enumerate(items):
        if value == target:
            return index
    return -1

for items, target in [([4,8,12],4),([4,8,12],8),([4,8,12],9),([],1)]:
    print(find_index(items,target))
