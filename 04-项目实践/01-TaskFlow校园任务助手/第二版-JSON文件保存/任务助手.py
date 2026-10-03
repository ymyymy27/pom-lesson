import argparse
import json
import os
import tempfile
from pathlib import Path

def load(path):
    path = Path(path)
    if not path.exists():
        return []
    try:
        tasks = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("数据文件损坏，原文件已保留，请检查 JSON") from error
    if not isinstance(tasks, list):
        raise ValueError("任务数据必须是列表")
    ids = set()
    for task in tasks:
        if not isinstance(task, dict) or type(task.get("id")) is not int or task["id"] <= 0:
            raise ValueError("任务编号必须是正整数")
        if task["id"] in ids or not isinstance(task.get("title"), str) or not task["title"].strip():
            raise ValueError("编号重复或任务名称无效")
        if type(task.get("done")) is not bool:
            raise ValueError("完成状态必须是布尔值")
        ids.add(task["id"])
    return tasks

def save(path, tasks):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # 先写临时文件，成功后替换，减少中途退出造成的数据损坏。
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         delete=False, suffix=".tmp") as output:
            name = output.name
            json.dump(tasks, output, ensure_ascii=False, indent=2)
        os.replace(name, path)
    finally:
        if name and Path(name).exists():
            Path(name).unlink()

def execute(path, action, title=None, task_id=None):
    tasks = load(path)
    if action == "add":
        title = (title or "").strip()
        if not title:
            raise ValueError("任务名称不能为空")
        tasks.append({"id": max((t["id"] for t in tasks), default=0)+1,
                      "title": title, "done": False})
    elif action in {"done", "delete"}:
        task = next((t for t in tasks if t["id"] == task_id), None)
        if task is None:
            raise ValueError("任务编号不存在")
        if action == "done":
            task["done"] = True
        else:
            tasks.remove(task)
    elif action != "list":
        raise ValueError("不支持的操作")
    if action != "list":
        save(path, tasks)
    return tasks

def main():
    parser = argparse.ArgumentParser(description="个人任务助手；同一时间只运行一个写入进程")
    parser.add_argument("--file", default="tasks.json")
    parser.add_argument("action", choices=["add", "list", "done", "delete"])
    parser.add_argument("--title")
    parser.add_argument("--id", type=int)
    args = parser.parse_args()
    try:
        print(json.dumps(execute(args.file, args.action, args.title, args.id), ensure_ascii=False, indent=2))
    except (ValueError, OSError) as error:
        parser.exit(1, f"操作失败：{error}\n")

if __name__ == "__main__":
    main()
