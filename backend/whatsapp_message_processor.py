from datetime import datetime
from .database import get_db, new_id
from .whatsapp_service import send_whatsapp_message


def process_incoming_whatsapp(
    business_id: str,
    customer_phone: str,
    message_text: str,
):
    message_text = (message_text or "").strip()

    if not business_id:
        raise ValueError("business_id is required")

    if not customer_phone:
        raise ValueError("customer_phone is required")

    if not message_text:
        return {
            "success": False,
            "reason": "empty_message"
        }

    now = datetime.utcnow().isoformat()

    with get_db() as db:

        business = db.execute(
            """
            SELECT *
            FROM businesses
            WHERE id = ?
            LIMIT 1
            """,
            (business_id,)
        ).fetchone()

        if not business:
            raise ValueError("Business not found")

        # Store incoming WhatsApp message
        db.execute(
            """
            INSERT INTO whatsapp_messages (
                id,
                business_id,
                phone,
                direction,
                message,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id(),
                business_id,
                customer_phone,
                "incoming",
                message_text,
                "received",
                now
            )
        )

        # Find existing lead
        lead = db.execute(
            """
            SELECT *
            FROM leads
            WHERE business_id = ?
              AND phone = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                business_id,
                customer_phone
            )
        ).fetchone()

        # Create lead automatically if customer is new
        if not lead:

            lead_id = new_id()

            db.execute(
                """
                INSERT INTO leads (
                    id,
                    name,
                    phone,
                    email,
                    business,
                    requirement,
                    status,
                    score,
                    ai_analysis,
                    follow_up,
                    created_at,
                    updated_at,
                    business_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead_id,
                    customer_phone,
                    customer_phone,
                    "",
                    business["business_name"],
                    message_text,
                    "new",
                    0,
                    "",
                    "",
                    now,
                    now,
                    business_id
                )
            )

            lead = db.execute(
                """
                SELECT *
                FROM leads
                WHERE id = ?
                """,
                (lead_id,)
            ).fetchone()

        else:

            db.execute(
                """
                UPDATE leads
                SET requirement = ?,
                    updated_at = ?
                WHERE id = ?
                  AND business_id = ?
                """,
                (
                    message_text,
                    now,
                    lead["id"],
                    business_id
                )
            )

    # Basic production-safe response layer.
    # AI generation will be connected to the existing AI service next.
    response_text = (
        f"Thanks for contacting {business['business_name']}. "
        "We received your message. Our AI assistant will help you shortly."
    )

    send_result = send_whatsapp_message(
        business_id=business_id,
        recipient_phone=customer_phone,
        message=response_text
    )

    with get_db() as db:

        db.execute(
            """
            INSERT INTO whatsapp_messages (
                id,
                business_id,
                phone,
                direction,
                message,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id(),
                business_id,
                customer_phone,
                "outgoing",
                response_text,
                "sent",
                datetime.utcnow().isoformat()
            )
        )

    return {
        "success": True,
        "business_id": business_id,
        "customer_phone": customer_phone,
        "lead_id": lead["id"],
        "response": response_text,
        "whatsapp": send_result
    }
