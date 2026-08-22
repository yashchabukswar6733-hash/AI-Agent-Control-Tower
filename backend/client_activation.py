from datetime import datetime
import uuid

from .database import get_db


def now():
    return datetime.utcnow().isoformat()


def new_id():
    return uuid.uuid4().hex[:12]


def activate_paid_client(
    business_id: str,
    client_name: str,
    company: str,
    phone: str = "",
    email: str = "",
    payment_id: str = ""
):
    if not business_id:
        raise ValueError("business_id is required")

    if not client_name:
        raise ValueError("client_name is required")

    if not company:
        raise ValueError("company is required")

    timestamp = now()

    with get_db() as db:

        business = db.execute(
            """
            SELECT id, business_name, active
            FROM businesses
            WHERE id = ?
            LIMIT 1
            """,
            (business_id,)
        ).fetchone()

        if not business:
            raise ValueError("Business not found")

        existing = db.execute(
            """
            SELECT *
            FROM clients
            WHERE business_id = ?
              AND (
                    email = ?
                    OR phone = ?
                  )
            LIMIT 1
            """,
            (business_id, email, phone)
        ).fetchone()

        if existing:
            client_id = existing["id"]

            db.execute(
                """
                UPDATE clients
                SET name = ?,
                    company = ?,
                    email = ?,
                    phone = ?,
                    status = 'active',
                    updated_at = ?
                WHERE id = ?
                  AND business_id = ?
                """,
                (
                    client_name,
                    company,
                    email,
                    phone,
                    timestamp,
                    client_id,
                    business_id
                )
            )
        else:
            client_id = new_id()

            db.execute(
                """
                INSERT INTO clients (
                    id,
                    name,
                    company,
                    status,
                    created_at,
                    business_id,
                    email,
                    phone,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    client_id,
                    client_name,
                    company,
                    "active",
                    timestamp,
                    business_id,
                    email,
                    phone,
                    timestamp
                )
            )

        onboarding = db.execute(
            """
            SELECT id
            FROM client_onboarding
            WHERE client_id = ?
              AND business_id = ?
            LIMIT 1
            """,
            (client_id, business_id)
        ).fetchone()

        if not onboarding:
            onboarding_id = new_id()

            db.execute(
                """
                INSERT INTO client_onboarding (
                    id,
                    client_id,
                    business_id,
                    status,
                    payment_id,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    onboarding_id,
                    client_id,
                    business_id,
                    "pending_whatsapp",
                    payment_id,
                    timestamp,
                    timestamp
                )
            )
        else:
            onboarding_id = onboarding["id"]

            db.execute(
                """
                UPDATE client_onboarding
                SET status = 'pending_whatsapp',
                    payment_id = ?,
                    updated_at = ?
                WHERE id = ?
                  AND client_id = ?
                  AND business_id = ?
                """,
                (
                    payment_id,
                    timestamp,
                    onboarding_id,
                    client_id,
                    business_id
                )
            )

        whatsapp = db.execute(
            """
            SELECT id
            FROM whatsapp_accounts
            WHERE business_id = ?
            LIMIT 1
            """,
            (business_id,)
        ).fetchone()

        if not whatsapp:
            whatsapp_id = new_id()

            db.execute(
                """
                INSERT INTO whatsapp_accounts (
                    id,
                    business_id,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    whatsapp_id,
                    business_id,
                    "pending_connection",
                    timestamp,
                    timestamp
                )
            )

        return {
            "success": True,
            "client_id": client_id,
            "onboarding_id": onboarding_id,
            "business_id": business_id,
            "status": "pending_whatsapp",
            "payment_id": payment_id
        }
