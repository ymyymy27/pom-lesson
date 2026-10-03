def passed(score):
    return score >= 60

assert passed(59) is False
assert passed(60) is True
print("2项检查通过")
