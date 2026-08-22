import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "saas.db"


def now():
    return datetime.utcnow().isoformat()


def create_billing_tables():
    db = sqlite3.connect(DB_PATH)

    db.executescript("""
    CREATE TABLE IF NOT EXISTS client_onboarding (
        id TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        client_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending_payment',
        plan TEXT NOT NULL,
        setup_fee REAL NOT NULL DEFAULT 0,
        monthly_fee REAL NOT NULL DEFAULT 0,
        payment_status TEXT NOT NULL DEFAULT 'pending',
        activated_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS subscriptions (
        id TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        client_id TEXT NOT NULL,
        plan TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'inactive',
        provider TEXT DEFAULT '',
        provider_subscription_id TEXT DEFAULT '',
        current_period_start TEXT,
        current_period_end TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS billing_events (
        id TEXT PRIMARY KEY,
        business_id TEXT,
        client_id TEXT,
        provider TEXT NOT NULL,
        event_type TEXT NOT NULL,
        provider_event_id TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'received',
        payload TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_onboarding_business
    ON client_onboarding(business_id);

    CREATE INDEX IF NOT EXISTS idx_subscription_business
    ON subscriptions(business_id);

    CREATE INDEX IF NOT EXISTS idx_billing_events_provider_event
    ON billing_events(provider_event_id);
    """)

    db.commit()
    db.close()


def create_onboarding(
    business_id,
    client_id,
    plan,
    setup_fee,
    monthly_fee,
):
    if not business_id:
        raise ValueError("Business ID is required.")

    if not client_id:
        raise ValueError("Client ID is required.")

    onboarding_id = uuid.uuid4().hex[:12]
    timestamp = now()

    db = sqlite3.connect(DB_PATH)

    try:
        business = db.execute(
            """
            SELECT id
            FROM businesses
            WHERE id = ?
            LIMIT 1
            """,
            (business_id,),
        ).fetchone()

        if not business:
            raise ValueError("Business not found.")

        client = db.execute(
            """
            SELECT id
            FROM clients
            WHERE id = ?
              AND business_id = ?
            LIMIT 1
            """,
            (
                client_id,
                business_id,
            ),
        ).fetchone()

        if not client:
            raise ValueError(
                "Client does not belong to this business."
            )

        db.execute(
            """
            INSERT INTO client_onboarding (
                id,
                business_id,
                client_id,
                status,
                plan,
                setup_fee,
                monthly_fee,
                payment_status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                onboarding_id,
                business_id,
                client_id,
                "pending_payment",
                plan,
                float(setup_fee),
                float(monthly_fee),
                "pending",
                timestamp,
                timestamp,
            ),
        )

        db.commit()

        return onboarding_id

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def activate_after_verified_payment(
    onboarding_id,
    provider,
    provider_payment_id,
):
    if not provider_payment_id:
        raise ValueError(
            "Verified provider payment ID is required."
        )

    timestamp = now()

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    try:
        onboarding = db.execute(
            """
            SELECT *
            FROM client_onboarding
            WHERE id = ?
            LIMIT 1
            """,
            (onboarding_id,),
        ).fetchone()

        if not onboarding:
            raise ValueError(
                "Onboarding record not found."
            )

        # Never activate merely because this function was called.
        # The payment provider webhook must verify the payment first.
        db.execute(
            """
            UPDATE client_onboarding
            SET
                status = 'active',
                payment_status = 'paid',
                activated_at = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                timestamp,
                timestamp,
                onboarding_id,
            ),
        )

        subscription_id = uuid.uuid4().hex[:12]

        db.execute(
            """
            INSERT INTO subscriptions (
                id,
                business_id,
                client_id,
                plan,
                status,
                provider,
                provider_subscription_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                subscription_id,
                onboarding["business_id"],
                onboarding["client_id"],
                onboarding["plan"],
                "active",
                provider,
                provider_payment_id,
                timestamp,
                timestamp,
            ),
        )

        db.execute(
            """
            UPDATE businesses
            SET active = 1
            WHERE id = ?
            """,
            (onboarding["business_id"],),
        )

        db.commit()

        return {
            "onboarding_id": onboarding_id,
            "subscription_id": subscription_id,
            "status": "active",
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_billing_tables()

    print("=" * 60)
    print("CLIENT BILLING / ONBOARDING DATABASE")
    print("=" * 60)
    print("Tables ready.")
    print("Payment activation requires verified provider data.")
