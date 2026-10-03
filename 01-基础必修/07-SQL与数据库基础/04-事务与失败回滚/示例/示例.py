import sqlite3
db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE tasks(id INTEGER PRIMARY KEY)")
try:
    with db:
        db.execute("INSERT INTO tasks VALUES(1)")
        db.execute("INSERT INTO tasks VALUES(1)")
except sqlite3.IntegrityError:
    print("已回滚")
print(db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0])
db.close()
