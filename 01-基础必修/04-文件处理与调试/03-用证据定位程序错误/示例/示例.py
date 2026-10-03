numbers = [2, 4, 6]
total = 0
for number in numbers:
    total += number
    print("当前累计", total)
print("平均", total / len(numbers))
