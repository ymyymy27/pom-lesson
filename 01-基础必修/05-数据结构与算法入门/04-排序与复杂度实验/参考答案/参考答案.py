def bubble(items):
    result = list(items)
    for end in range(len(result)-1, 0, -1):
        for i in range(end):
            if result[i] > result[i+1]:
                result[i], result[i+1] = result[i+1], result[i]
    return result

print(bubble([3,1,2]))
print(bubble([]))
