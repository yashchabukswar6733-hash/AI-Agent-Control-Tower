import json
import requests

from .database import get_db, new_id, now
from .leads import lead_manager
from .lead_agent import analyze_lead_with_ai


GRAPH_API_VERSION = "v23.0"


def send_business_whatsapp(
    business_id: str,
    phone: str,
    message: str
):
    """
    Send a WhatsApp message using the business's
    connected WhatsApp credentials.
    """

    with get_db() as db:

        account = db.execute(
            """
            SELECT *
            FROM whatsapp_accounts
            WHERE business_id = ?
              AND status = 'connected'
            LIMIT 1
            """,
            (business_id,)
        ).fetchone()

    if not account:
        raise RuntimeError(
            "No connected WhatsApp account for this business."
        )

    access_token = str(
        account["access_token"]
    ).strip()

    phone_number_id = str(
        account["phone_number_id"]
    ).strip()

    if not access_token:
        raise RuntimeError(
            "WhatsApp access token is missing."
        )

    if not phone_number_id:
        raise RuntimeError(
            "WhatsApp phone number ID is missing."
        )

    phone = str(phone).strip()
    message = str(message).strip()

    if not phone:
        raise ValueError(
            "Customer phone number is required."
        )

    if not message:
        raise ValueError(
            "WhatsApp message cannot be empty."
        )

    url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_API_VERSION}/"
        f"{phone_number_id}/messages"
    )

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=20
    )

    try:
        data = response.json()
    except Exception:
        data = {
            "raw_response": response.text
        }

    if not response.ok:
        raise RuntimeError(
            f"WhatsApp API error "
            f"{response.status_code}: {data}"
        )

    return data


def create_or_get_lead(
    business_id: str,
    phone: str,
    message: str,
    name: str = ""
):
    """
    Find an existing lead by phone.
    If none exists, create one.
    """

    with get_db() as db:

        row = db.execute(
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
                phone
            )
        ).fetchone()

    if row:
        lead = dict(row)

        requirement = str(
            lead.get("requirement", "")
        ).strip()

        if message and message not in requirement:

            new_requirement = (
                requirement +
                "\n" +
                message
            ).strip()

            lead_manager.update_lead(
                business_id=business_id,
                lead_id=lead["id"],
                requirement=new_requirement
            )

            lead = lead_manager.get_lead(
                business_id,
                lead["id"]
            )

        return lead

    return lead_manager.create_lead(
        business_id=business_id,
        name=name or "WhatsApp Customer",
        phone=phone,
        email="",
        business="",
        requirement=message
    )


def run_whatsapp_ai(
    business_id: str,
    phone: str,
    message: str,
    customer_name: str = ""
):
    """
    Complete AI sales automation:

    WhatsApp message
        ↓
    Lead
        ↓
    AI qualification
        ↓
    Save analysis
        ↓
    AI reply
        ↓
    WhatsApp reply
    """

    print(
        f"WhatsApp AI: New message from {phone}"
    )

    lead = create_or_get_lead(
        business_id=business_id,
        phone=phone,
        message=message,
        name=customer_name
    )

    if not lead:
        raise RuntimeError(
            "Unable to create or retrieve lead."
        )

    print(
        f"WhatsApp AI: Lead {lead['id']}"
    )

    ai = analyze_lead_with_ai(
        lead
    )

    reply = str(
        ai.get(
            "sales_reply",
            ""
        )
    ).strip()

    if not reply:
        reply = (
            "Thanks for contacting us. "
            "We've received your enquiry. "
            "Our AI sales assistant will "
            "help you shortly."
        )

    analysis = json.dumps(
        {
            "temperature": ai.get(
                "temperature",
                "COLD"
            ),
            "business_problem": ai.get(
                "business_problem",
                ""
            ),
            "recommended_package": ai.get(
                "recommended_package",
                "STARTER"
            ),
            "reason": ai.get(
                "reason",
                ""
            ),
            "sales_reply": reply,
            "next_action": ai.get(
                "next_action",
                ""
            )
        },
        ensure_ascii=False
    )

    updated_lead = lead_manager.update_lead(
        business_id=business_id,
        lead_id=lead["id"],
        status="qualified",
        score=ai.get(
            "score",
            0
        ),
        ai_analysis=analysis,
        follow_up=ai.get(
            "follow_up",
            ""
        )
    )

    print(
        "WhatsApp AI: Lead qualified."
    )

    result = send_business_whatsapp(
        business_id=business_id,
        phone=phone,
        message=reply
    )

    message_id = ""

    messages = result.get(
        "messages",
        []
    )

    if messages:
        message_id = messages[0].get(
            "id",
            ""
        )

    print(
        "WhatsApp AI: Reply sent."
    )

    return {
        "lead": updated_lead,
        "ai": ai,
        "reply": reply,
        "whatsapp_message_id": message_id
    }
