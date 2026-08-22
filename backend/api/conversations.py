from fastapi import APIRouter, HTTPException

from backend.database import get_db

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"]
)


@router.get("/{customer_phone}")
def get_conversation(customer_phone: str):

    phone = "".join(
        c for c in customer_phone
        if c.isdigit()
    )

    if not phone:
        raise HTTPException(
            status_code=400,
            detail="Invalid customer phone."
        )

    with get_db() as db:

        rows = db.execute(
            """
            SELECT
                id,
                business_id,
                customer_phone,
                customer_name,
                direction,
                message,
                whatsapp_message_id,
                status,
                created_at
            FROM whatsapp_messages
            WHERE customer_phone = ?
            ORDER BY created_at ASC
            """,
            (phone,)
        ).fetchall()

    return {
        "customer_phone": phone,
        "messages": [
            dict(row)
            for row in rows
        ],
        "total": len(rows)
    }


@router.get("")
def list_conversations():

    with get_db() as db:

        rows = db.execute(
            """
            SELECT
                business_id,
                customer_phone,
                MAX(customer_name) AS customer_name,
                MAX(created_at) AS last_message_at,
                COUNT(*) AS message_count
            FROM whatsapp_messages
            GROUP BY business_id, customer_phone
            ORDER BY last_message_at DESC
            """
        ).fetchall()

    return {
        "conversations": [
            dict(row)
            for row in rows
        ]
    }


@router.get("/recent")
def recent_conversations(limit: int = 50):

    limit = max(1, min(limit, 100))

    with get_db() as db:

        rows = db.execute(
            """
            SELECT
                w.business_id,
                w.customer_phone,
                w.customer_name,
                w.message,
                w.direction,
                w.created_at
            FROM whatsapp_messages w
            INNER JOIN (
                SELECT
                    business_id,
                    customer_phone,
                    MAX(created_at) AS latest
                FROM whatsapp_messages
                GROUP BY business_id, customer_phone
            ) latest
            ON w.business_id = latest.business_id
            AND w.customer_phone = latest.customer_phone
            AND w.created_at = latest.latest
            ORDER BY w.created_at DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

    return {
        "conversations": [
            dict(row)
            for row in rows
        ]
    }
