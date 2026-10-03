import sqlite3
db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE items(id INTEGER PRIMARY KEY)")
try:
    with db:
        db.execute("INSERT INTO items VALUES(1)")
        db.execute("INSERT INTO items VALUES(1)")
except sqlite3.IntegrityError:
    pass
print(db.execute("SELECT COUNT(*) FROM items").fetchone()[0])
db.close()
