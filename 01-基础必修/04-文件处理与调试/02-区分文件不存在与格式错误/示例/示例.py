import json
try:
    json.loads("{bad}")
except json.JSONDecodeError:
    print("数据格式错误，请检查文件")
