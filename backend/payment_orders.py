from fastapi import HTTPException, Request

from .razorpay_service import create_order
from .database import get_db, new_id, now


def create_payment_order(
    request: Request,
    amount: float,
    client_id: str,
    description: str = "AI Automation Setup",
):
    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Amount must be greater than zero."
        )

    if not client_id:
        raise HTTPException(
            status_code=400,
            detail="client_id is required."
        )

    # Resolve the authenticated business.
    business = request.state.business

    if not business:
        raise HTTPException(
            status_code=401,
            detail="Business authentication required."
        )

    business_id = business["id"]

    with get_db() as db:

        client = db.execute(
            """
            SELECT id, name, company
            FROM clients
            WHERE id = ?
              AND business_id = ?
            LIMIT 1
            """,
            (
                client_id,
                business_id,
            )
        ).fetchone()

        if not client:
            raise HTTPException(
                status_code=404,
                detail="Client not found for this business."
            )

        payment_id = new_id()

        receipt = f"pay_{payment_id}"

        razorpay_order = create_order(
            amount_rupees=amount,
            receipt=receipt,
            notes={
                "business_id": business_id,
                "client_id": client_id,
                "payment_id": payment_id,
                "description": description,
            },
        )

        db.execute(
            """
            INSERT INTO payments (
                id,
                client_id,
                business_id,
                client_name,
                company,
                amount,
                payment_type,
                status,
                created_at,
                updated_at,
                razorpay_order_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payment_id,
                client["id"],
                business_id,
                client["name"],
                client["company"],
                amount,
                "setup",
                "pending",
                now(),
                now(),
                razorpay_order["id"],
            ),
        )

    return {
        "success": True,
        "payment_id": payment_id,
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key_id": razorpay_order.get(
            "key_id"
        ),
        "amount": razorpay_order["amount"],
        "currency": razorpay_order["currency"],
        "client": {
            "id": client["id"],
            "name": client["name"],
            "company": client["company"],
        },
    }
