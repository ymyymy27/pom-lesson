import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

def execute(path, action, title=None, task_id=None):
    if action not in {"add", "list", "done", "delete"}:
        raise ValueError("不支持的操作")
    if action == "add":
        title = (title or "").strip()
        if not title:
            raise ValueError("任务名称不能为空")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as db:
        db.row_factory = sqlite3.Row
        with db:
            db.execute("CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL CHECK(length(trim(title)) > 0), done INTEGER NOT NULL DEFAULT 0 CHECK(done IN (0,1)))")
            if action == "add":
                db.execute("INSERT INTO tasks(title) VALUES (?)", (title,))
            elif action in {"done", "delete"}:
                query = "UPDATE tasks SET done=1 WHERE id=?" if action == "done" else "DELETE FROM tasks WHERE id=?"
                if db.execute(query, (task_id,)).rowcount == 0:
                    raise ValueError("任务编号不存在")
            rows = db.execute("SELECT id,title,done FROM tasks ORDER BY id").fetchall()
    return [{"id": r["id"], "title": r["title"], "done": bool(r["done"])} for r in rows]

def main():
    parser = argparse.ArgumentParser(description="SQLite任务助手")
    parser.add_argument("--db", default="tasks.sqlite3")
    parser.add_argument("action", choices=["add", "list", "done", "delete"])
    parser.add_argument("--title")
    parser.add_argument("--id", type=int)
    args = parser.parse_args()
    try:
        print(json.dumps(execute(args.db, args.action, args.title, args.id), ensure_ascii=False, indent=2))
    except (ValueError, OSError, sqlite3.Error) as error:
        parser.exit(1, f"操作失败：{error}\n")

if __name__ == "__main__":
    main()
