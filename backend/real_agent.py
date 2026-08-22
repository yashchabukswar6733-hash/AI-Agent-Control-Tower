import os
import json
import requests
from datetime import datetime, timedelta

from .leads import lead_manager


def send_whatsapp(phone, message):
    token = os.getenv("WHATSAPP_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

    if not token or not phone_number_id:
        return {
            "sent": False,
            "mode": "not_configured",
            "message": "WhatsApp API credentials are not configured yet."
        }

    url = f"https://graph.facebook.com/v23.0/{phone_number_id}/messages"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {
            "body": message
        }
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=20
        )

        if response.ok:
            return {
                "sent": True,
                "mode": "whatsapp_cloud_api",
                "response": response.json()
            }

        return {
            "sent": False,
            "mode": "whatsapp_cloud_api",
            "error": response.text
        }

    except Exception as e:
        return {
            "sent": False,
            "mode": "whatsapp_cloud_api",
            "error": str(e)
        }


def run_real_agent(lead_id):

    lead = lead_manager.get_lead(lead_id)

    if not lead:
        raise ValueError(f"Lead {lead_id} not found")

    analysis = {}

    try:
        analysis = json.loads(
            lead.get("ai_analysis") or "{}"
        )
    except Exception:
        analysis = {}

    name = lead.get("name", "")
    business = lead.get("business", "")
    phone = lead.get("phone", "")

    temperature = analysis.get("temperature", "COLD")
    package = analysis.get(
        "recommended_package",
        "STARTER"
    )

    sales_reply = analysis.get(
        "sales_reply",
        f"Hi {name}! Thanks for contacting AutoPilot AI. "
        f"We can help {business} automate repetitive enquiries. "
        f"Would you be open to a quick 5-minute discussion?"
    )

    if temperature == "HOT":
        action = "Contact immediately"
    elif temperature == "WARM":
        action = "Contact within 24 hours"
    else:
        action = "Verify lead before outreach"

    outreach = send_whatsapp(
        phone,
        sales_reply
    )

    result = {
        "agent": "AutoPilot Sales Agent",
        "lead_id": lead_id,
        "lead": name,
        "business": business,
        "temperature": temperature,
        "score": lead.get("score", 0),
        "recommended_package": package,
        "action": action,
        "sales_message": sales_reply,
        "outreach": outreach,
        "follow_up_at": (
            datetime.utcnow() + timedelta(hours=24)
        ).isoformat(),
        "status": (
            "contacted"
            if outreach.get("sent")
            else "qualified"
        )
    }

    return result
