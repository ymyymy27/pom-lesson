import sqlite3
with sqlite3.connect(":memory:") as db:
    db.execute("CREATE TABLE tasks(id INTEGER PRIMARY KEY, done INTEGER)")
    db.execute("INSERT INTO tasks VALUES (1,0)")
    db.execute("UPDATE tasks SET done=? WHERE id=?", (1,1))
    print(db.execute("SELECT done FROM tasks WHERE id=1").fetchone()[0])
