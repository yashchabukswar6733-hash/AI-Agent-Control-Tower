import os
import re

from fastapi import APIRouter, Request, HTTPException
from dotenv import load_dotenv

from backend.database import get_db, new_id, now
from backend.services.ai_sales_service import generate_sales_response
from backend.services.whatsapp_service import WhatsAppService

load_dotenv()

router = APIRouter(
    prefix="/webhooks",
    tags=["WhatsApp"]
)


def normalize_phone(phone):
    return re.sub(r"\D", "", phone or "")


@router.get("/whatsapp")
async def verify_whatsapp_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    verify_token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    expected_token = os.getenv(
        "WHATSAPP_VERIFY_TOKEN",
        ""
    )

    if (
        mode == "subscribe"
        and verify_token
        and expected_token
        and verify_token == expected_token
    ):
        return int(challenge)

    raise HTTPException(
        status_code=403,
        detail="WhatsApp webhook verification failed."
    )


@router.post("/whatsapp")
async def receive_whatsapp_webhook(
    request: Request
):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload."
        )

    if payload.get("object") != "whatsapp_business_account":
        return {"status": "ignored"}

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            metadata = value.get("metadata", {})
            phone_number_id = metadata.get(
                "phone_number_id"
            )

            if not phone_number_id:
                continue

            messages = value.get("messages", [])
            contacts = value.get("contacts", [])

            contact_name = ""

            if contacts:
                contact_name = (
                    contacts[0]
                    .get("profile", {})
                    .get("name", "")
                )

            for message in messages:
                if message.get("type") != "text":
                    continue

                customer_phone = normalize_phone(
                    message.get("from", "")
                )

                whatsapp_message_id = message.get(
                    "id",
                    ""
                )

                text_body = (
                    message.get("text", {})
                    .get("body", "")
                    .strip()
                )

                if not customer_phone or not text_body:
                    continue

                with get_db() as db:

                    business = db.execute(
                        """
                        SELECT *
                        FROM businesses
                        WHERE whatsapp_phone_number_id = ?
                        AND active = 1
                        LIMIT 1
                        """,
                        (phone_number_id,)
                    ).fetchone()

                    if not business:
                        continue

                    business_id = business["id"]

                    # ---------------------------------------------
                    # Store inbound WhatsApp message
                    # ---------------------------------------------

                    db.execute(
                        """
                        INSERT INTO whatsapp_messages
                        (
                            id,
                            business_id,
                            customer_phone,
                            customer_name,
                            direction,
                            message,
                            whatsapp_message_id,
                            status,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            new_id(),
                            business_id,
                            customer_phone,
                            contact_name,
                            "inbound",
                            text_body,
                            whatsapp_message_id,
                            "received",
                            now()
                        )
                    )

                    # ---------------------------------------------
                    # Create or update CRM lead
                    # ---------------------------------------------

                    lead = db.execute(
                        """
                        SELECT *
                        FROM leads
                        WHERE phone = ?
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        (customer_phone,)
                    ).fetchone()

                    if not lead:
                        lead_id = new_id()

                        db.execute(
                            """
                            INSERT INTO leads
                            (
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
                                updated_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                lead_id,
                                contact_name or customer_phone,
                                customer_phone,
                                "",
                                "",
                                text_body,
                                "new",
                                0,
                                "",
                                "",
                                now(),
                                now()
                            )
                        )

                    else:
                        lead_id = lead["id"]

                        previous_requirement = (
                            lead["requirement"] or ""
                        )

                        combined_requirement = (
                            previous_requirement
                            + "\n"
                            + text_body
                        ).strip()

                        db.execute(
                            """
                            UPDATE leads
                            SET requirement = ?,
                                updated_at = ?
                            WHERE id = ?
                            """,
                            (
                                combined_requirement[-10000:],
                                now(),
                                lead_id
                            )
                        )

                    # ---------------------------------------------
                    # Load business AI configuration
                    # ---------------------------------------------

                    settings = db.execute(
                        """
                        SELECT *
                        FROM business_settings
                        WHERE business_id = ?
                        LIMIT 1
                        """,
                        (business_id,)
                    ).fetchone()

                    # Don't send automated sales messages until
                    # the business has configured its AI.
                    if not settings:
                        continue

                    # ---------------------------------------------
                    # Generate AI response
                    # ---------------------------------------------

                    ai_result = generate_sales_response(
                        business=business,
                        settings=settings,
                        customer_name=(
                            contact_name
                            or customer_phone
                        ),
                        customer_message=text_body
                    )

                    if "REPLY:" not in ai_result:
                        continue

                    reply = ai_result.split(
                        "REPLY:",
                        1
                    )[1]

                    if "STATUS:" in reply:
                        reply = reply.split(
                            "STATUS:",
                            1
                        )[0]

                    reply = reply.strip()

                    if not reply:
                        continue

                    # ---------------------------------------------
                    # Send through official WhatsApp API
                    # ---------------------------------------------

                    whatsapp = WhatsAppService(
                        access_token=(
                            business[
                                "whatsapp_access_token"
                            ]
                        ),
                        phone_number_id=phone_number_id
                    )

                    response = await whatsapp.send_text(
                        recipient_phone=customer_phone,
                        message=reply
                    )

                    # ---------------------------------------------
                    # Store outbound AI response
                    # ---------------------------------------------

                    response_message_id = ""

                    messages_response = (
                        response.get("messages", [])
                    )

                    if messages_response:
                        response_message_id = (
                            messages_response[0]
                            .get("id", "")
                        )

                    db.execute(
                        """
                        INSERT INTO whatsapp_messages
                        (
                            id,
                            business_id,
                            customer_phone,
                            customer_name,
                            direction,
                            message,
                            whatsapp_message_id,
                            status,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            new_id(),
                            business_id,
                            customer_phone,
                            contact_name,
                            "outbound",
                            reply,
                            response_message_id,
                            "sent",
                            now()
                        )
                    )

                    db.execute(
                        """
                        UPDATE leads
                        SET status = ?,
                            ai_analysis = ?,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            "contacted",
                            ai_result[-5000:],
                            now(),
                            lead_id
                        )
                    )

    return {
        "status": "received"
    }
