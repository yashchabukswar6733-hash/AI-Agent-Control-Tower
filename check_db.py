import sqlite3

db = sqlite3.connect("backend/control_tower.db")

tables = db.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("\nDATABASE TABLES:")
for table in tables:
    print("-", table[0])

db.close()