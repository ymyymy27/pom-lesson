import sqlite3
with sqlite3.connect(":memory:") as db:
    db.execute("CREATE TABLE tasks(id INTEGER PRIMARY KEY)")
    db.executemany("INSERT INTO tasks VALUES (?)", [(1,),(2,)])
    db.execute("DELETE FROM tasks WHERE id=?", (1,))
    print(db.execute("SELECT id FROM tasks").fetchone()[0])
