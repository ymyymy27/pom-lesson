for raw in ["12", "abc"]:
    try:
        number = int(raw)
    except ValueError:
        print("请输入整数")
    else:
        print(number)
