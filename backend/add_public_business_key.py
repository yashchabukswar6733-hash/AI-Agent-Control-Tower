import sqlite3
import secrets

DB = "saas.db"

db = sqlite3.connect(DB)

columns = [
    row[1]
    for row in db.execute(
        "PRAGMA table_info(businesses)"
    ).fetchall()
]

if "public_key" not in columns:
    db.execute(
        "ALTER TABLE businesses ADD COLUMN public_key TEXT"
    )
    print("Added businesses.public_key")
else:
    print("businesses.public_key already exists")

# Give every existing business a unique public key.
rows = db.execute(
    """
    SELECT id
    FROM businesses
    WHERE public_key IS NULL
       OR public_key = ''
    """
).fetchall()

for row in rows:
    key = "lp_" + secrets.token_urlsafe(24)

    db.execute(
        """
        UPDATE businesses
        SET public_key = ?
        WHERE id = ?
        """,
        (key, row[0])
    )

    print(
        "Generated public key for business:",
        row[0]
    )

db.commit()

print()
print("PUBLIC BUSINESS KEY SETUP COMPLETE")

db.close()
