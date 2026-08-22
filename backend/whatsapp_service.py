import os
from typing import Optional

import requests


GRAPH_API_VERSION = os.getenv(
    "WHATSAPP_GRAPH_API_VERSION",
    "v23.0"
).strip()

WHATSAPP_ACCESS_TOKEN = os.getenv(
    "WHATSAPP_ACCESS_TOKEN",
    ""
).strip()

WHATSAPP_PHONE_NUMBER_ID = os.getenv(
    "WHATSAPP_PHONE_NUMBER_ID",
    ""
).strip()


class WhatsAppConfigurationError(Exception):
    pass


def whatsapp_configured() -> bool:

    return bool(
        WHATSAPP_ACCESS_TOKEN
        and WHATSAPP_PHONE_NUMBER_ID
    )


def send_whatsapp_message(
    to: str,
    message: str,
    access_token: Optional[str] = None,
    phone_number_id: Optional[str] = None,
) -> dict:

    # --------------------------------------------------------
    # Per-client credentials take priority.
    # Global .env credentials remain available as fallback.
    # --------------------------------------------------------

    token = (
        str(access_token).strip()
        if access_token
        else WHATSAPP_ACCESS_TOKEN
    )

    sender_phone_number_id = (
        str(phone_number_id).strip()
        if phone_number_id
        else WHATSAPP_PHONE_NUMBER_ID
    )

    if not token:

        raise WhatsAppConfigurationError(
            "WhatsApp access token is not configured."
        )

    if not sender_phone_number_id:

        raise WhatsAppConfigurationError(
            "WhatsApp phone number ID is not configured."
        )

    to = str(to).strip()
    message = str(message).strip()

    if not to:

        raise ValueError(
            "Recipient WhatsApp number is required."
        )

    if not message:

        raise ValueError(
            "WhatsApp message cannot be empty."
        )

    url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_API_VERSION}/"
        f"{sender_phone_number_id}/messages"
    )

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message,
        },
    }

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
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


def verify_whatsapp_configuration() -> dict:

    return {
        "configured": whatsapp_configured(),

        "phone_number_id_present": bool(
            WHATSAPP_PHONE_NUMBER_ID
        ),

        "access_token_present": bool(
            WHATSAPP_ACCESS_TOKEN
        ),

        "graph_api_version": GRAPH_API_VERSION,
    }
