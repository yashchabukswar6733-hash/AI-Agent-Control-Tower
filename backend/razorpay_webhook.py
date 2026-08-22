from .payment_activation import activate_verified_payment
import hashlib
import hmac
import json
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, Header, HTTPException, Request

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "saas.db"

load_dotenv(BASE_DIR / ".env")

router = APIRouter(
    prefix="/webhooks/razorpay",
    tags=["Razorpay Webhooks"],
)


def now():
    return datetime.utcnow().isoformat()


def verify_signature(payload: bytes, signature: str) -> bool:
    secret = os.getenv(
        "RAZORPAY_WEBHOOK_SECRET",
        ""
    ).strip()

    if not secret:
        raise RuntimeError(
            "RAZORPAY_WEBHOOK_SECRET is not configured."
        )

    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected,
        signature,
    )


def record_event(
    event_type,
    provider_event_id,
    payload,
):
    db = sqlite3.connect(DB_PATH)

    try:
        event_id = uuid.uuid4().hex[:12]

        db.execute(
            """
            INSERT INTO billing_events (
                id,
                provider,
                event_type,
                provider_event_id,
                status,
                payload,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                "razorpay",
                event_type,
                provider_event_id,
                "received",
                json.dumps(payload),
                now(),
            ),
        )

        db.commit()

        return event_id

    except sqlite3.IntegrityError:
        # Duplicate webhook.
        return None

    finally:
        db.close()


def mark_event_processed(event_id):
    db = sqlite3.connect(DB_PATH)

    try:
        db.execute(
            """
            UPDATE billing_events
            SET status = ?
            WHERE id = ?
            """,
            (
                "processed",
                event_id,
            ),
        )

        db.commit()

    finally:
        db.close()


def mark_event_failed(event_id):
    db = sqlite3.connect(DB_PATH)

    try:
        db.execute(
            """
            UPDATE billing_events
            SET status = ?
            WHERE id = ?
            """,
            (
                "failed",
                event_id,
            ),
        )

        db.commit()

    finally:
        db.close()


@router.post("")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(
        default=""
    ),
):

    raw_body = await request.body()

    if not x_razorpay_signature:
        raise HTTPException(
            status_code=400,
            detail="Missing Razorpay signature.",
        )

    try:
        valid = verify_signature(
            raw_body,
            x_razorpay_signature,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    if not valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid Razorpay webhook signature.",
        )

    try:
        payload = json.loads(
            raw_body.decode("utf-8")
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload.",
        )

    event_type = str(
        payload.get("event", "")
    ).strip()

    if not event_type:
        raise HTTPException(
            status_code=400,
            detail="Missing Razorpay event type.",
        )

    provider_event_id = str(
        payload.get("id")
        or payload.get("payload", {})
            .get("payment", {})
            .get("entity", {})
            .get("id", "")
    ).strip()

    event_id = record_event(
        event_type,
        provider_event_id,
        payload,
    )

    # Razorpay can retry the same webhook.
    # A previously recorded event is already handled.
    if event_id is None:
        return {
            "received": True,
            "duplicate": True,
        }

    try:
        result = None

        if event_type == "payment.captured":
            result = activate_verified_payment(
                provider_event_id=provider_event_id,
                payload=payload
            )

        mark_event_processed(event_id)

        return {
            "received": True,
            "processed": True,
            "event": event_type,
            "activation": result
        }

    except Exception:
        mark_event_failed(event_id)
        raise


def install(app):
    app.include_router(router)

