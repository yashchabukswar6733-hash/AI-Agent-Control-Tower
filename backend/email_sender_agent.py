import os
import smtplib
from email.message import EmailMessage

from .database import get_db, now


SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM = os.getenv(
    "SMTP_FROM",
    SMTP_USERNAME
).strip()


def smtp_configured():

    return bool(
        SMTP_HOST
        and SMTP_USERNAME
        and SMTP_PASSWORD
        and SMTP_FROM
    )


def send_email(
    recipient,
    subject,
    body
):

    if not smtp_configured():

        raise RuntimeError(
            "SMTP configuration is missing."
        )

    recipient = str(
        recipient
    ).strip()

    if not recipient:
        raise ValueError(
            "Recipient email is required."
        )

    message = EmailMessage()

    message["From"] = SMTP_FROM
    message["To"] = recipient
    message["Subject"] = subject

    message.set_content(
        str(body).strip()
    )

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT,
        timeout=30
    ) as server:

        server.starttls()

        server.login(
            SMTP_USERNAME,
            SMTP_PASSWORD
        )

        server.send_message(
            message
        )

    return {
        "sent": True,
        "recipient": recipient
    }


def send_lead_response(
    lead_id,
    business_id
):

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
            raise ValueError(
                "Lead not found."
            )

        lead = dict(lead)

        if not lead.get("email"):
            raise ValueError(
                "Lead does not have an email address."
            )

        existing = db.execute(
            """
            SELECT id
            FROM activity_log
            WHERE entity_type = ?
              AND entity_id = ?
              AND action = ?
            LIMIT 1
            """,
            (
                "lead",
                lead_id,
                "customer_email_sent"
            )
        ).fetchone()

        if existing:

            return {
                "sent": False,
                "already_sent": True,
                "lead_id": lead_id
            }

        import json

        try:

            analysis = json.loads(
                lead.get(
                    "ai_analysis",
                    "{}"
                )
            )

        except Exception:

            analysis = {}

        body = str(
            analysis.get(
                "sales_reply",
                ""
            )
        ).strip()

        if not body:

            body = (
                "Thank you for contacting us. "
                "We have received your enquiry "
                "and will get back to you shortly."
            )

        company = (
            lead.get(
                "business",
                ""
            )
            or "our team"
        )

        subject = (
            f"Thank you for contacting {company}"
        )

    result = send_email(
        lead["email"],
        subject,
        body
    )

    with get_db() as db:

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
                "customer_email_sent",
                f"Email sent to {lead['email']}",
                now()
            )
        )

        db.execute(
            """
            UPDATE leads
            SET updated_at = ?
            WHERE id = ?
              AND business_id = ?
            """,
            (
                now(),
                lead_id,
                business_id
            )
        )

    return {
        "sent": True,
        "already_sent": False,
        "lead_id": lead_id,
        "recipient": lead["email"]
    }
