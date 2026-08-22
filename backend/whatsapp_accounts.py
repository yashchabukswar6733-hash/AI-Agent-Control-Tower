from .database import get_db, now


def init_whatsapp_accounts():

    with get_db() as db:

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS whatsapp_accounts (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL UNIQUE,
                phone_number_id TEXT NOT NULL UNIQUE,
                display_phone_number TEXT,
                verified_name TEXT,
                access_token TEXT,
                status TEXT NOT NULL DEFAULT 'connected',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def get_business_by_phone_number_id(
    phone_number_id
):

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM whatsapp_accounts
            WHERE phone_number_id = ?
              AND status = 'connected'
            LIMIT 1
            """,
            (
                phone_number_id,
            )
        ).fetchone()

    return dict(row) if row else None


def connect_whatsapp_account(
    business_id,
    phone_number_id,
    display_phone_number="",
    verified_name="",
    access_token=""
):

    import uuid

    account_id = uuid.uuid4().hex[:16]
    timestamp = now()

    with get_db() as db:

        existing = db.execute(
            """
            SELECT id
            FROM whatsapp_accounts
            WHERE business_id = ?
            """,
            (
                business_id,
            )
        ).fetchone()

        if existing:

            db.execute(
                """
                UPDATE whatsapp_accounts
                SET phone_number_id = ?,
                    display_phone_number = ?,
                    verified_name = ?,
                    access_token = ?,
                    status = 'connected',
                    updated_at = ?
                WHERE business_id = ?
                """,
                (
                    phone_number_id,
                    display_phone_number,
                    verified_name,
                    access_token,
                    timestamp,
                    business_id
                )
            )

            account_id = existing["id"]

        else:

            db.execute(
                """
                INSERT INTO whatsapp_accounts
                (
                    id,
                    business_id,
                    phone_number_id,
                    display_phone_number,
                    verified_name,
                    access_token,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'connected', ?, ?)
                """,
                (
                    account_id,
                    business_id,
                    phone_number_id,
                    display_phone_number,
                    verified_name,
                    access_token,
                    timestamp,
                    timestamp
                )
            )

    return {
        "id": account_id,
        "business_id": business_id,
        "phone_number_id": phone_number_id,
        "display_phone_number": display_phone_number,
        "verified_name": verified_name,
        "status": "connected"
    }

def get_safe_whatsapp_account(
    business_id
):

    with get_db() as db:

        row = db.execute(
            """
            SELECT
                id,
                business_id,
                phone_number_id,
                display_phone_number,
                verified_name,
                status,
                created_at,
                updated_at
            FROM whatsapp_accounts
            WHERE business_id = ?
            LIMIT 1
            """,
            (
                business_id,
            )
        ).fetchone()

    return dict(row) if row else None
