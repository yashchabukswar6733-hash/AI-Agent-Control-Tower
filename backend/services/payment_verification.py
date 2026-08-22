import os
import hmac
import hashlib
import json

from fastapi import HTTPException
from pydantic import BaseModel

from backend.database import get_db, new_id, now


class VerifyPaymentRequest(BaseModel):
    business_id: int
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    amount: int


def verify_signature(
    order_id,
    payment_id,
    signature
):

    secret = os.getenv(
        "RAZORPAY_KEY_SECRET",
        ""
    )

    if not secret:
        raise RuntimeError(
            "RAZORPAY_KEY_SECRET is not configured."
        )

    message = (
        f"{order_id}|{payment_id}"
    ).encode()

    expected = hmac.new(
        secret.encode(),
        message,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        expected,
        signature
    )


def record_successful_payment(
    data: VerifyPaymentRequest
):

    if not verify_signature(
        data.razorpay_order_id,
        data.razorpay_payment_id,
        data.razorpay_signature
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid Razorpay payment signature."
        )

    with get_db() as db:

        business = db.execute(
            """
            SELECT *
            FROM businesses
            WHERE id = ?
            AND active = 1
            """,
            (data.business_id,)
        ).fetchone()

        if not business:
            raise HTTPException(
                status_code=404,
                detail="Business not found."
            )

        event_id = new_id()

        db.execute(
            """
            INSERT INTO billing_events
            (
                id,
                business_id,
                event_type,
                razorpay_event_id,
                payload,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                data.business_id,
                "payment.verified",
                data.razorpay_payment_id,
                json.dumps({
                    "order_id":
                        data.razorpay_order_id,
                    "payment_id":
                        data.razorpay_payment_id,
                    "amount":
                        data.amount
                }),
                now()
            )
        )

    return {
        "status": "paid",
        "payment_id": data.razorpay_payment_id,
        "order_id": data.razorpay_order_id,
        "amount": data.amount
    }
