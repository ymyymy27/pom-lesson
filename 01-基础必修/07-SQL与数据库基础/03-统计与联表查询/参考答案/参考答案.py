import sqlite3
with sqlite3.connect(":memory:") as db:
    db.executescript("CREATE TABLE courses(id INTEGER PRIMARY KEY,name TEXT); CREATE TABLE tasks(course_id INTEGER); INSERT INTO courses VALUES(1,'Python'); INSERT INTO tasks VALUES(1),(1);")
    row = db.execute("SELECT c.name, COUNT(*) FROM courses c JOIN tasks t ON c.id=t.course_id GROUP BY c.id,c.name").fetchone()
    print(row[0],row[1])
