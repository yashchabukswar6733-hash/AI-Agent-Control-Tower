import os
import httpx

from dotenv import load_dotenv

load_dotenv()


GRAPH_API_VERSION = os.getenv(
    "WHATSAPP_GRAPH_API_VERSION",
    "v23.0"
)


class WhatsAppService:

    def __init__(
        self,
        access_token: str,
        phone_number_id: str
    ):
        self.access_token = access_token
        self.phone_number_id = phone_number_id

    async def send_text(
        self,
        recipient_phone: str,
        message: str
    ):
        if not self.access_token:
            raise ValueError(
                "WhatsApp access token is not configured."
            )

        if not self.phone_number_id:
            raise ValueError(
                "WhatsApp phone number ID is not configured."
            )

        url = (
            f"https://graph.facebook.com/"
            f"{GRAPH_API_VERSION}/"
            f"{self.phone_number_id}/messages"
        )

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message,
            },
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

        if response.status_code >= 400:
            raise RuntimeError(
                f"WhatsApp API error "
                f"{response.status_code}: "
                f"{response.text}"
            )

        return response.json()
