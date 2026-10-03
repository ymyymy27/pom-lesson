import sqlite3
with sqlite3.connect(":memory:") as db:
    db.execute("CREATE TABLE tasks(id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
    db.execute("INSERT INTO tasks(title) VALUES (?)", ("阅读",))
    print(db.execute("SELECT title FROM tasks").fetchone()[0])
