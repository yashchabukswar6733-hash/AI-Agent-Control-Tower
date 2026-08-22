import os
import re
import logging

from fastapi import APIRouter, Request, HTTPException
from dotenv import load_dotenv

from backend.database import get_db, new_id, now
from backend.services.ai_sales_service import generate_sales_response
from backend.services.whatsapp_service import WhatsAppService

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/webhooks",
    tags=["WhatsApp"],
)


def normalize_phone(phone: str) -> str:
    return re.sub(r"\D", "", phone or "")


def extract_ai_reply(ai_result: str):
    """
    Extract structured sales-agent output.

    Returns:
        reply, status, score, summary, next_action
    """

    text = str(ai_result or "").strip()

    reply = ""
    status = "QUALIFYING"
    score = 0
    summary = ""
    next_action = ""

    if "REPLY:" in text:
        reply = text.split("REPLY:", 1)[1]

        if "STATUS:" in reply:
            reply = reply.split("STATUS:", 1)[0]

    if "STATUS:" in text:
        status_part = text.split("STATUS:", 1)[1]

        if "SCORE:" in status_part:
            status_part = status_part.split("SCORE:", 1)[0]

        status = status_part.strip().upper()

    if "SCORE:" in text:
        score_part = text.split("SCORE:", 1)[1]

        if "SUMMARY:" in score_part:
            score_part = score_part.split("SUMMARY:", 1)[0]

        try:
            score = int(
                re.search(
                    r"\d+",
                    score_part
                ).group()
            )
        except (AttributeError, ValueError):
            score = 0

    if "SUMMARY:" in text:
        summary_part = text.split("SUMMARY:", 1)[1]

        if "NEXT_ACTION:" in summary_part:
            summary_part = summary_part.split(
                "NEXT_ACTION:",
                1
            )[0]

        summary = summary_part.strip()

    if "NEXT_ACTION:" in text:
        next_action = (
            text.split("NEXT_ACTION:", 1)[1]
            .strip()
        )

    allowed_statuses = {
        "QUALIFYING",
        "INTERESTED",
        "HANDOFF_REQUIRED",
    }

    if status not in allowed_statuses:
        status = "QUALIFYING"

    score = max(0, min(100, score))

    return (
        reply.strip(),
        status,
        score,
        summary.strip(),
        next_action.strip(),
    )


@router.get("/whatsapp")
async def verify_whatsapp_webhook(request: Request):
    """
    Meta WhatsApp webhook verification endpoint.
    """

    params = request.query_params

    mode = params.get("hub.mode")
    verify_token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    expected_token = os.getenv(
        "WHATSAPP_VERIFY_TOKEN",
        "",
    ).strip()

    if (
        mode == "subscribe"
        and verify_token
        and expected_token
        and verify_token == expected_token
        and challenge
    ):
        return int(challenge)

    raise HTTPException(
        status_code=403,
        detail="WhatsApp webhook verification failed.",
    )


@router.post("/whatsapp")
async def receive_whatsapp_webhook(
    request: Request,
):
    """
    Receives real WhatsApp Cloud API webhook events.
    """

    try:
        payload = await request.json()

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload.",
        )

    if payload.get("object") != "whatsapp_business_account":
        return {
            "status": "ignored",
        }

    processed = 0
    ignored = 0
    failed = 0

    for entry in payload.get("entry", []):

        for change in entry.get("changes", []):

            value = change.get("value", {})

            metadata = value.get(
                "metadata",
                {},
            )

            phone_number_id = (
                metadata.get("phone_number_id")
                or ""
            ).strip()

            if not phone_number_id:
                ignored += 1
                continue

            messages = value.get(
                "messages",
                [],
            )

            contacts = value.get(
                "contacts",
                [],
            )

            contact_name = ""

            if contacts:
                contact_name = (
                    contacts[0]
                    .get("profile", {})
                    .get("name", "")
                    .strip()
                )

            for message in messages:

                try:

                    if message.get("type") != "text":
                        ignored += 1
                        continue

                    customer_phone = normalize_phone(
                        message.get("from", "")
                    )

                    whatsapp_message_id = (
                        message.get("id", "")
                    )

                    text_body = (
                        message.get("text", {})
                        .get("body", "")
                        .strip()
                    )

                    if (
                        not customer_phone
                        or not text_body
                    ):
                        ignored += 1
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
                            (
                                phone_number_id,
                            ),
                        ).fetchone()

                        if not business:
                            logger.warning(
                                "No active business found for "
                                "WhatsApp phone_number_id=%s",
                                phone_number_id,
                            )

                            ignored += 1
                            continue

                        business_id = business["id"]

                        if whatsapp_message_id:

                            existing_message = db.execute(
                                """
                                SELECT id
                                FROM whatsapp_messages
                                WHERE whatsapp_message_id = ?
                                LIMIT 1
                                """,
                                (
                                    whatsapp_message_id,
                                ),
                            ).fetchone()

                            if existing_message:
                                ignored += 1
                                continue

                        # ---------------------------------------------
                        # Store inbound message
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
                                now(),
                            ),
                        )

                        # ---------------------------------------------
                        # Find lead FOR THIS BUSINESS
                        # ---------------------------------------------

                        lead = db.execute(
                            """
                            SELECT *
                            FROM leads
                            WHERE phone = ?
                            AND business = ?
                            ORDER BY updated_at DESC
                            LIMIT 1
                            """,
                            (
                                customer_phone,
                                business["business_name"],
                            ),
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
                                    (
                                        contact_name
                                        or customer_phone
                                    ),
                                    customer_phone,
                                    "",
                                    business[
                                        "business_name"
                                    ],
                                    text_body,
                                    "new",
                                    0,
                                    "",
                                    "",
                                    now(),
                                    now(),
                                ),
                            )

                        else:

                            lead_id = lead["id"]

                            previous_requirement = (
                                lead["requirement"]
                                or ""
                            )

                            combined_requirement = (
                                previous_requirement
                                + "\n"
                                + text_body
                            ).strip()

                            db.execute(
                                """
                                UPDATE leads
                                SET
                                    name = ?,
                                    requirement = ?,
                                    updated_at = ?
                                WHERE id = ?
                                """,
                                (
                                    (
                                        contact_name
                                        or lead["name"]
                                        or customer_phone
                                    ),
                                    combined_requirement[-10000:],
                                    now(),
                                    lead_id,
                                ),
                            )

                        # ---------------------------------------------
                        # Load AI settings
                        # ---------------------------------------------

                        settings = db.execute(
                            """
                            SELECT *
                            FROM business_settings
                            WHERE business_id = ?
                            LIMIT 1
                            """,
                            (
                                business_id,
                            ),
                        ).fetchone()

                        if not settings:
                            logger.warning(
                                "Business %s has no AI settings.",
                                business_id,
                            )

                            ignored += 1
                            continue

                        # ---------------------------------------------
                        # Load conversation history
                        # ---------------------------------------------

                        conversation_history = db.execute(
                            """
                            SELECT
                                direction,
                                message,
                                created_at
                            FROM whatsapp_messages
                            WHERE business_id = ?
                            AND customer_phone = ?
                            ORDER BY created_at DESC
                            LIMIT 20
                            """,
                            (
                                business_id,
                                customer_phone,
                            ),
                        ).fetchall()

                        conversation_history = list(
                            reversed(
                                conversation_history
                            )
                        )

                        # ---------------------------------------------
                        # AI SALES AGENT
                        # ---------------------------------------------

                        ai_result = generate_sales_response(
                            business=business,
                            settings=settings,
                            customer_name=(
                                contact_name
                                or customer_phone
                            ),
                            customer_message=text_body,
                            conversation_history=conversation_history,
                        )

                        (
                            reply,
                            status,
                            score,
                            summary,
                            next_action,
                        ) = extract_ai_reply(
                            ai_result
                        )

                        if not reply:

                            logger.warning(
                                "AI returned no usable reply "
                                "for business=%s",
                                business_id,
                            )

                            db.execute(
                                """
                                UPDATE leads
                                SET
                                    ai_analysis = ?,
                                    updated_at = ?
                                WHERE id = ?
                                """,
                                (
                                    str(ai_result)[-5000:],
                                    now(),
                                    lead_id,
                                ),
                            )

                            failed += 1
                            continue

                        # ---------------------------------------------
                        # HUMAN HANDOFF
                        # ---------------------------------------------

                        if status == "HANDOFF_REQUIRED":

                            handoff_message = (
                                settings[
                                    "human_handoff_message"
                                ]
                                if (
                                    "human_handoff_message"
                                    in settings.keys()
                                    and settings[
                                        "human_handoff_message"
                                    ]
                                )
                                else (
                                    "Thanks for your message. "
                                    "A member of our team will "
                                    "take over this conversation."
                                )
                            )

                            reply = handoff_message.strip()

                        # ---------------------------------------------
                        # WhatsApp credentials
                        # ---------------------------------------------

                        access_token = (
                            business[
                                "whatsapp_access_token"
                            ]
                            if (
                                "whatsapp_access_token"
                                in business.keys()
                            )
                            else ""
                        )

                        if not access_token:
                            logger.error(
                                "Business %s has no WhatsApp "
                                "access token.",
                                business_id,
                            )

                            failed += 1
                            continue

                        whatsapp = WhatsAppService(
                            access_token=access_token,
                            phone_number_id=phone_number_id,
                        )

                        # ---------------------------------------------
                        # SEND REAL WHATSAPP MESSAGE
                        # ---------------------------------------------

                        response = await whatsapp.send_text(
                            recipient_phone=customer_phone,
                            message=reply,
                        )

                        response_message_id = ""

                        messages_response = response.get(
                            "messages",
                            [],
                        )

                        if messages_response:

                            response_message_id = (
                                messages_response[0]
                                .get("id", "")
                            )

                        # ---------------------------------------------
                        # Store outbound message
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
                                "outbound",
                                reply,
                                response_message_id,
                                "sent",
                                now(),
                            ),
                        )

                        # ---------------------------------------------
                        # Lead status
                        # ---------------------------------------------

                        lead_status = "contacted"

                        if status == "INTERESTED":
                            lead_status = "interested"

                        elif status == "HANDOFF_REQUIRED":
                            lead_status = "handoff"

                        # ---------------------------------------------
                        # Save AI intelligence
                        # ---------------------------------------------

                        ai_analysis = (
                            f"STATUS: {status}\n"
                            f"SCORE: {score}\n"
                            f"SUMMARY: {summary}\n"
                            f"NEXT_ACTION: {next_action}\n"
                            f"RAW_AI:\n{str(ai_result)[-3000:]}"
                        )

                        db.execute(
                            """
                            UPDATE leads
                            SET
                                status = ?,
                                score = ?,
                                ai_analysis = ?,
                                follow_up = ?,
                                updated_at = ?
                            WHERE id = ?
                            """,
                            (
                                lead_status,
                                score,
                                ai_analysis[-5000:],
                                next_action,
                                now(),
                                lead_id,
                            ),
                        )

                        processed += 1

                except Exception as exc:

                    failed += 1

                    logger.exception(
                        "WhatsApp message processing failed: %s",
                        exc,
                    )

                    continue

    return {
        "status": "received",
        "processed": processed,
        "ignored": ignored,
        "failed": failed,
    }
