import sqlite3
with sqlite3.connect(":memory:") as db:
    db.executescript("CREATE TABLE tasks(course TEXT, done INTEGER); INSERT INTO tasks VALUES ('Python',1),('Python',0),('SQL',1);")
    print(db.execute("SELECT course, COUNT(*) FROM tasks GROUP BY course ORDER BY course").fetchall())
