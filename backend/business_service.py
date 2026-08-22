import secrets
from datetime import datetime, timedelta, timezone

from .database import get_db, new_id, now


SESSION_DAYS = 30


def create_business(
    business_name: str,
    owner_name: str,
    email: str,
    phone: str,
    plan: str
):

    business_name = business_name.strip()
    owner_name = owner_name.strip()
    email = email.strip().lower()
    phone = phone.strip()

    allowed_plans = {
        "Starter",
        "Growth",
        "Business"
    }

    if plan not in allowed_plans:
        plan = "Starter"

    if not business_name:
        raise ValueError("Business name is required")

    if not owner_name:
        raise ValueError("Owner name is required")

    if not email or "@" not in email:
        raise ValueError("Valid business email is required")

    with get_db() as db:

        existing = db.execute(
            """
            SELECT id
            FROM businesses
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if existing:
            raise ValueError(
                "A workspace already exists for this email"
            )

        business_id = new_id()
        created_at = now()

        db.execute(
            """
            INSERT INTO businesses
            (
                id,
                business_name,
                owner_name,
                email,
                phone,
                plan,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                business_id,
                business_name,
                owner_name,
                email,
                phone,
                plan,
                "trial",
                created_at
            )
        )

    token = create_session(business_id)

    return {
        "business_id": business_id,
        "token": token,
        "business": {
            "id": business_id,
            "business_name": business_name,
            "owner_name": owner_name,
            "email": email,
            "phone": phone,
            "plan": plan,
            "status": "trial",
            "created_at": created_at
        }
    }


def create_session(business_id: str):

    token = secrets.token_urlsafe(48)

    created = datetime.now(timezone.utc)

    expires = created + timedelta(
        days=SESSION_DAYS
    )

    with get_db() as db:

        db.execute(
            """
            INSERT INTO business_sessions
            (
                token,
                business_id,
                created_at,
                expires_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                token,
                business_id,
                created.isoformat(),
                expires.isoformat()
            )
        )

    return token


def get_business_by_token(token: str):

    if not token:
        return None

    with get_db() as db:

        row = db.execute(
            """
            SELECT
                b.*
            FROM business_sessions s
            JOIN businesses b
                ON b.id = s.business_id
            WHERE s.token = ?
            """,
            (token,)
        ).fetchone()

    if not row:
        return None

    return dict(row)


def login_business(email: str):

    email = email.strip().lower()

    with get_db() as db:

        business = db.execute(
            """
            SELECT *
            FROM businesses
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

    if not business:
        raise ValueError(
            "No workspace exists for this email"
        )

    token = create_session(
        business["id"]
    )

    return {
        "business_id": business["id"],
        "token": token,
        "business": dict(business)
    }


def logout(token: str):

    if not token:
        return

    with get_db() as db:

        db.execute(
            """
            DELETE FROM business_sessions
            WHERE token = ?
            """,
            (token,)
        )
