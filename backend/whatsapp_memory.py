from .database import get_db, new_id, now
from .leads import lead_manager


def find_lead_by_phone(business_id, phone):

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM leads
            WHERE business_id = ?
              AND phone = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                business_id,
                phone
            )
        ).fetchone()

    return dict(row) if row else None


def get_or_create_whatsapp_lead(
    business_id,
    customer_name,
    customer_phone,
    message
):

    lead = find_lead_by_phone(
        business_id,
        customer_phone
    )

    if lead:
        return lead

    return lead_manager.create_lead(
        business_id=business_id,
        name=customer_name or "WhatsApp Customer",
        phone=customer_phone,
        email="",
        business="WhatsApp Customer",
        requirement=message
    )


def save_whatsapp_message(
    business_id,
    lead_id,
    phone,
    direction,
    message
):

    message_id = new_id()
    created_at = now()

    with get_db() as db:

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS whatsapp_messages (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                lead_id TEXT,
                phone TEXT NOT NULL,
                direction TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        db.execute(
            """
            INSERT INTO whatsapp_messages
            (
                id,
                business_id,
                lead_id,
                phone,
                direction,
                message,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                business_id,
                lead_id,
                phone,
                direction,
                message,
                created_at
            )
        )

    return {
        "id": message_id,
        "business_id": business_id,
        "lead_id": lead_id,
        "phone": phone,
        "direction": direction,
        "message": message,
        "created_at": created_at
    }


def get_recent_conversation(
    business_id,
    phone,
    limit=20
):

    with get_db() as db:

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS whatsapp_messages (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                lead_id TEXT,
                phone TEXT NOT NULL,
                direction TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        rows = db.execute(
            """
            SELECT *
            FROM whatsapp_messages
            WHERE business_id = ?
              AND phone = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (
                business_id,
                phone,
                limit
            )
        ).fetchall()

    return [
        dict(row)
        for row in reversed(rows)
    ]
