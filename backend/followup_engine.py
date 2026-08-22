import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "saas.db"


def now():
    return datetime.utcnow().isoformat()


def create_followup_tables():
    db = sqlite3.connect(DB_PATH)

    db.executescript("""
    CREATE TABLE IF NOT EXISTS lead_followups (
        id TEXT PRIMARY KEY,
        lead_id TEXT NOT NULL,
        business_id TEXT NOT NULL,
        channel TEXT NOT NULL,
        sequence INTEGER NOT NULL DEFAULT 1,
        scheduled_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        subject TEXT DEFAULT '',
        message TEXT DEFAULT '',
        provider_message_id TEXT DEFAULT '',
        error TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_lead_followups_pending
    ON lead_followups(status, scheduled_at);

    CREATE INDEX IF NOT EXISTS idx_lead_followups_business
    ON lead_followups(business_id);
    """)

    db.commit()
    db.close()


def schedule_followups():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    try:
        leads = db.execute("""
            SELECT
                l.id,
                l.business_id,
                l.name,
                l.email,
                l.requirement,
                l.score
            FROM leads l
            WHERE l.status IN ('qualified', 'contacted')
              AND l.email != ''
              AND NOT EXISTS (
                  SELECT 1
                  FROM lead_followups f
                  WHERE f.lead_id = l.id
              )
            ORDER BY l.created_at ASC
            LIMIT 100
        """).fetchall()

        created = 0
        timestamp = now()

        for lead in leads:
            lead_id = lead["id"]
            business_id = lead["business_id"]
            name = lead["name"]
            requirement = lead["requirement"] or ""

            messages = [
                (
                    1,
                    timedelta(minutes=5),
                    "Following up on your enquiry",
                    f"Hi {name}, thanks for your enquiry. "
                    f"We received your request regarding {requirement or 'our services'}. "
                    f"We'll be happy to help you with the next step."
                ),
                (
                    2,
                    timedelta(hours=24),
                    "Checking in regarding your enquiry",
                    f"Hi {name}, just checking in regarding your enquiry. "
                    f"If you'd like to continue, reply to this email and we'll help you with the next step."
                ),
                (
                    3,
                    timedelta(days=3),
                    "Final follow-up",
                    f"Hi {name}, we're following up one last time regarding your enquiry. "
                    f"If you're still interested, simply reply and we'll continue from there."
                ),
            ]

            for sequence, delay, subject, message in messages:
                followup_id = uuid.uuid4().hex[:12]
                scheduled = (
                    datetime.utcnow() + delay
                ).isoformat()

                db.execute("""
                    INSERT INTO lead_followups (
                        id,
                        lead_id,
                        business_id,
                        channel,
                        sequence,
                        scheduled_at,
                        status,
                        subject,
                        message,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    followup_id,
                    lead_id,
                    business_id,
                    "email",
                    sequence,
                    scheduled,
                    "pending",
                    subject,
                    message,
                    timestamp,
                    timestamp,
                ))

                created += 1

        db.commit()

        return created

    finally:
        db.close()


if __name__ == "__main__":
    create_followup_tables()

    count = schedule_followups()

    print("=" * 60)
    print("FOLLOW-UP ENGINE")
    print("=" * 60)
    print(f"Follow-up records created: {count}")
    print("Status: READY")
