import secrets
import hashlib

from .database import get_db, new_id, now


def create_client_portal_token(
    client_id,
    business_id
):

    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode()
    ).hexdigest()

    with get_db() as db:

        client = db.execute(
            """
            SELECT id
            FROM clients
            WHERE id = ?
              AND business_id = ?
            """,
            (
                client_id,
                business_id
            )
        ).fetchone()

        if not client:
            raise ValueError(
                "Client not found."
            )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS
            client_portal_tokens
            (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                business_id TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TEXT,
                revoked INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )

        token_id = new_id()

        db.execute(
            """
            INSERT INTO client_portal_tokens
            (
                id,
                client_id,
                business_id,
                token_hash,
                expires_at,
                revoked,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                token_id,
                client_id,
                business_id,
                token_hash,
                None,
                0,
                now()
            )
        )

    return {
        "token": raw_token,
        "token_id": token_id,
        "client_id": client_id
    }


def authenticate_client_token(
    token
):

    token_hash = hashlib.sha256(
        token.encode()
    ).hexdigest()

    with get_db() as db:

        row = db.execute(
            """
            SELECT
                client_id,
                business_id
            FROM client_portal_tokens
            WHERE token_hash = ?
              AND revoked = 0
            """,
            (
                token_hash,
            )
        ).fetchone()

    if not row:
        return None

    return dict(row)


def revoke_client_token(
    token_id,
    business_id
):

    with get_db() as db:

        db.execute(
            """
            UPDATE client_portal_tokens
            SET revoked = 1
            WHERE id = ?
              AND business_id = ?
            """,
            (
                token_id,
                business_id
            )
        )

    return {
        "status": "revoked",
        "token_id": token_id
    }
