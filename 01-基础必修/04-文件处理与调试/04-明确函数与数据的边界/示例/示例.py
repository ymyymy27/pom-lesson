def clean_title(title):
    result = title.strip()
    if not result:
        raise ValueError("任务名称不能为空")
    return result

print(clean_title("  实验  "))
