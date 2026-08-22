import os
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database import get_db, new_id, now
from backend.services.billing_service import get_razorpay_client
from backend.services.payment_verification import (
    VerifyPaymentRequest,
    record_successful_payment
)

router = APIRouter(
    prefix="/billing",
    tags=["Billing"]
)


class CreateOrderRequest(BaseModel):
    business_id: int
    amount: int
    description: str = "AI WhatsApp Lead Automation"


@router.post("/orders")
def create_order(data: CreateOrderRequest):

    if data.amount < 100:
        raise HTTPException(
            status_code=400,
            detail="Minimum order amount is ₹100."
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

    client = get_razorpay_client()

    order = client.order.create({
        "amount": data.amount * 100,
        "currency": "INR",
        "receipt": f"biz_{data.business_id}_{new_id()}",
        "notes": {
            "business_id": str(data.business_id),
            "description": data.description
        }
    })

    return {
        "order_id": order["id"],
        "amount": data.amount,
        "currency": "INR",
        "business_id": data.business_id,
        "key_id": os.getenv("RAZORPAY_KEY_ID")
    }


@router.post("/verify")
def verify_payment(
    data: VerifyPaymentRequest
):
    return record_successful_payment(data)
