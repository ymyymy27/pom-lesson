import sqlite3
with sqlite3.connect(":memory:") as db:
    db.execute("CREATE TABLE courses(id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    db.execute("INSERT INTO courses(name) VALUES (?)", ("程序设计",))
    print(db.execute("SELECT name FROM courses").fetchone()[0])
