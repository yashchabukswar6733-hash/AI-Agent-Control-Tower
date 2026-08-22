import sqlite3

db = sqlite3.connect("saas.db")

rows = db.execute(
    "SELECT name FROM sqlite_master WHERE type = ? ORDER BY name",
    ("table",)
).fetchall()

print("TABLES:")
for row in rows:
    print(" -", row[0])

db.close()
