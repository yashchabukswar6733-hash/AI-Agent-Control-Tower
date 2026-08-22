import sqlite3
import time
from pathlib import Path

from .lead_qualification_agent import qualify_lead

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "saas.db"


def get_new_leads():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    try:
        return db.execute(
            """
            SELECT id
            FROM leads
            WHERE status = 'new'
            ORDER BY created_at ASC
            LIMIT 20
            """
        ).fetchall()
    finally:
        db.close()


def run_once():
    leads = get_new_leads()

    processed = 0

    for lead in leads:
        try:
            qualify_lead(lead["id"])
            processed += 1
        except Exception as error:
            print(
                f"LEAD WORKER ERROR [{lead['id']}]: {error}"
            )

    return processed


def run():
    print("=" * 60)
    print("REAL LEAD AUTOMATION WORKER")
    print("Polling every 15 seconds")
    print("=" * 60)

    while True:
        try:
            count = run_once()

            if count:
                print(
                    f"Processed {count} new lead(s)."
                )

        except Exception as error:
            print(
                "WORKER ERROR:",
                error
            )

        time.sleep(15)


if __name__ == "__main__":
    run()
