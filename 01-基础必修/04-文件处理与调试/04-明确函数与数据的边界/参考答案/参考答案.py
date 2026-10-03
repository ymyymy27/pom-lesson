def clean_title(title):
    title = title.strip()
    if not title:
        raise ValueError("任务名称不能为空")
    return title

print(clean_title("  阅读  "))
try:
    clean_title("   ")
except ValueError:
    print("已拒绝空任务")
