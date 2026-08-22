import json

from .database import get_db, now, new_id
from .whatsapp_service import send_whatsapp_message


def send_lead_sales_message(
    business_id: str,
    lead_id: str
):
    """
    Real WhatsApp sales agent.

    Gets the AI-generated sales reply from the lead,
    sends it through WhatsApp Cloud API,
    and records the activity.
    """

    with get_db() as db:

        lead = db.execute(
            """
            SELECT *
            FROM leads
            WHERE id = ?
              AND business_id = ?
            """,
            (
                lead_id,
                business_id
            )
        ).fetchone()

        if not lead:
            raise ValueError("Lead not found.")

        lead = dict(lead)

    phone = str(
        lead.get("phone", "")
    ).strip()

    if not phone:
        raise ValueError(
            "Lead does not have a WhatsApp phone number."
        )

    if not lead.get("ai_analysis"):
        raise ValueError(
            "Lead has not been processed by the AI sales agent yet."
        )

    try:
        analysis = json.loads(
            lead["ai_analysis"]
        )
    except Exception:
        raise ValueError(
            "Lead AI analysis is invalid."
        )

    message = str(
        analysis.get("sales_reply", "")
    ).strip()

    if not message:
        raise ValueError(
            "AI sales reply is empty."
        )

    # REAL WHATSAPP SEND
    result = send_whatsapp_message(
        to=phone,
        message=message
    )

    sent_at = now()

    with get_db() as db:

        db.execute(
            """
            UPDATE leads
            SET updated_at = ?
            WHERE id = ?
              AND business_id = ?
            """,
            (
                sent_at,
                lead_id,
                business_id
            )
        )

        db.execute(
            """
            INSERT INTO activity_log
            (
                entity_type,
                entity_id,
                action,
                details,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "lead",
                lead_id,
                "whatsapp_sales_message_sent",
                json.dumps(
                    {
                        "phone": phone,
                        "message": message,
                        "whatsapp_response": result
                    },
                    ensure_ascii=False
                ),
                sent_at
            )
        )

    return {
        "success": True,
        "lead_id": lead_id,
        "phone": phone,
        "message": message,
        "whatsapp_response": result,
        "sent_at": sent_at
    }
