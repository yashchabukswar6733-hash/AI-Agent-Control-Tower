import json
import sqlite3
from pathlib import Path
from datetime import datetime

from .database import new_id
from .onboarding_service import create_onboarding


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "saas.db"


def now():
    return datetime.utcnow().isoformat()


def activate_verified_payment(
    provider_event_id,
    payload
):
    event = payload.get("payload", {})
    payment_entity = (
        event.get("payment", {})
        .get("entity", {})
    )

    razorpay_payment_id = payment_entity.get("id")
    razorpay_order_id = payment_entity.get("order_id")

    if not razorpay_payment_id:
        raise ValueError(
            "Verified Razorpay payment ID missing."
        )

    if not razorpay_order_id:
        raise ValueError(
            "Verified Razorpay order ID missing."
        )

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    payment = db.execute(
        """
        SELECT *
        FROM payments
        WHERE razorpay_order_id = ?
        LIMIT 1
        """,
        (razorpay_order_id,)
    ).fetchone()

    if not payment:
        db.close()
        raise ValueError(
            "Internal payment record not found for Razorpay order."
        )

    # Idempotency: never activate the same payment twice.
    if payment["status"] == "paid":
        onboarding = db.execute(
            """
            SELECT *
            FROM client_onboarding
            WHERE payment_id = ?
            LIMIT 1
            """,
            (payment["id"],)
        ).fetchone()

        db.close()

        return {
            "already_processed": True,
            "payment_id": payment["id"],
            "onboarding": (
                dict(onboarding)
                if onboarding
                else None
            )
        }

    payment_date = now()

    db.execute(
        """
        UPDATE payments
        SET status = ?,
            payment_date = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            "paid",
            payment_date,
            payment_date,
            payment["id"]
        )
    )

    # Create the client if the payment belongs to a
    # valid business/client relationship.
    client = None

    if payment["client_id"]:
        client = db.execute(
            """
            SELECT *
            FROM clients
            WHERE id = ?
              AND business_id = ?
            LIMIT 1
            """,
            (
                payment["client_id"],
                payment["business_id"]
            )
        ).fetchone()

    if not client:
        db.close()
        raise ValueError(
            "Payment has no valid client for its business."
        )

    db.commit()
    db.close()

    onboarding = create_onboarding(
        client_id=client["id"],
        business_id=payment["business_id"],
        payment_id=payment["id"]
    )

    return {
        "already_processed": False,
        "payment_id": payment["id"],
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_order_id": razorpay_order_id,
        "client_id": client["id"],
        "business_id": payment["business_id"],
        "onboarding": onboarding
    }
