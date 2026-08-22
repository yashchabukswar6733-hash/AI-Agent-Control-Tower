from datetime import datetime
import sqlite3
from .database import BASE_DIR, new_id


def create_onboarding(client_id, business_id, payment_id):
    db = sqlite3.connect(BASE_DIR / "saas.db")
    db.row_factory = sqlite3.Row

    existing = db.execute(
        """
        SELECT *
        FROM client_onboarding
        WHERE client_id = ?
          AND business_id = ?
        LIMIT 1
        """,
        (client_id, business_id)
    ).fetchone()

    if existing:
        db.close()
        return dict(existing)

    onboarding_id = new_id()
    now = datetime.utcnow().isoformat()

    db.execute(
        """
        INSERT INTO client_onboarding
        (
            id,
            client_id,
            business_id,
            payment_id,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            onboarding_id,
            client_id,
            business_id,
            payment_id,
            "pending",
            now,
            now
        )
    )

    db.commit()

    row = db.execute(
        """
        SELECT *
        FROM client_onboarding
        WHERE id = ?
        """,
        (onboarding_id,)
    ).fetchone()

    db.close()

    return dict(row)


def update_onboarding_status(
    onboarding_id,
    business_id,
    status
):
    allowed = {
        "pending",
        "in_progress",
        "whatsapp_pending",
        "active",
        "completed",
        "suspended"
    }

    if status not in allowed:
        raise ValueError("Invalid onboarding status.")

    db = sqlite3.connect(BASE_DIR / "saas.db")
    db.row_factory = sqlite3.Row

    now = datetime.utcnow().isoformat()

    db.execute(
        """
        UPDATE client_onboarding
        SET status = ?,
            updated_at = ?
        WHERE id = ?
          AND business_id = ?
        """,
        (
            status,
            now,
            onboarding_id,
            business_id
        )
    )

    db.commit()

    row = db.execute(
        """
        SELECT *
        FROM client_onboarding
        WHERE id = ?
          AND business_id = ?
        """,
        (
            onboarding_id,
            business_id
        )
    ).fetchone()

    db.close()

    if not row:
        raise ValueError("Onboarding record not found.")

    return dict(row)


def get_client_onboarding(
    client_id,
    business_id
):
    db = sqlite3.connect(BASE_DIR / "saas.db")
    db.row_factory = sqlite3.Row

    row = db.execute(
        """
        SELECT *
        FROM client_onboarding
        WHERE client_id = ?
          AND business_id = ?
        LIMIT 1
        """,
        (
            client_id,
            business_id
        )
    ).fetchone()

    db.close()

    return dict(row) if row else None
