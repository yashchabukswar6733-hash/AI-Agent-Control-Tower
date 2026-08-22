import os

from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse

from .leads import lead_manager
from .lead_agent import process_lead
from .whatsapp_service import send_whatsapp_message


router = APIRouter(
    prefix="/webhooks",
    tags=["WhatsApp Webhooks"]
)


@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query("", alias="hub.mode"),
    hub_verify_token: str = Query("", alias="hub.verify_token"),
    hub_challenge: str = Query("", alias="hub.challenge"),
):

    expected = os.getenv(
        "WHATSAPP_VERIFY_TOKEN",
        ""
    ).strip()

    if (
        hub_mode == "subscribe"
        and expected
        and hub_verify_token == expected
    ):
        return PlainTextResponse(
            hub_challenge
        )

    return PlainTextResponse(
        "Forbidden",
        status_code=403
    )


@router.post("/whatsapp")
async def receive_whatsapp_webhook(
    request: Request
):

    payload = await request.json()

    print("========================================")
    print("WHATSAPP MESSAGE RECEIVED")
    print("========================================")

    try:

        for entry in payload.get(
            "entry",
            []
        ):

            for change in entry.get(
                "changes",
                []
            ):

                value = change.get(
                    "value",
                    {}
                )

                metadata = value.get(
                    "metadata",
                    {}
                )

                phone_number_id = metadata.get(
                    "phone_number_id"
                )

                business_id = os.getenv(
                    "WHATSAPP_BUSINESS_ID",
                    ""
                ).strip()

                if not business_id:
                    print(
                        "WHATSAPP_BUSINESS_ID is not configured."
                    )
                    continue

                for message in value.get(
                    "messages",
                    []
                ):

                    sender = message.get(
                        "from"
                    )

                    message_type = message.get(
                        "type"
                    )

                    if not sender:
                        continue

                    if message_type != "text":
                        continue

                    text = (
                        message
                        .get("text", {})
                        .get("body", "")
                        .strip()
                    )

                    if not text:
                        continue

                    print(
                        f"Customer {sender}: {text}"
                    )

                    # ----------------------------------------
                    # CREATE LEAD
                    # ----------------------------------------

                    lead = lead_manager.create_lead(
                        business_id=business_id,
                        name=f"WhatsApp {sender}",
                        phone=sender,
                        email="",
                        business="WhatsApp Customer",
                        requirement=text
                    )

                    lead_id = lead["id"]

                    print(
                        f"Lead created: {lead_id}"
                    )

                    # ----------------------------------------
                    # AI QUALIFICATION
                    # ----------------------------------------

                    processed = process_lead(
                        lead_id,
                        business_id
                    )

                    # ----------------------------------------
                    # EXTRACT AI SALES REPLY
                    # ----------------------------------------

                    reply = ""

                    try:

                        import json

                        analysis = json.loads(
                            processed.get(
                                "ai_analysis",
                                "{}"
                            )
                        )

                        reply = analysis.get(
                            "sales_reply",
                            ""
                        )

                    except Exception as error:

                        print(
                            "AI analysis parsing error:",
                            error
                        )

                    if not reply:

                        reply = (
                            "Thanks for contacting us! "
                            "We received your requirement. "
                            "Our AI sales assistant will "
                            "help you with the next steps."
                        )

                    # ----------------------------------------
                    # SEND AI RESPONSE
                    # ----------------------------------------

                    result = send_whatsapp_message(
                        to=sender,
                        message=reply
                    )

                    print(
                        "AI WHATSAPP REPLY SENT"
                    )

                    print(result)

    except Exception as error:

        print(
            "WHATSAPP WEBHOOK ERROR:",
            error
        )

    return {
        "status": "received"
    }
