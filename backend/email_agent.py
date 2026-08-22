import os
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr

from .database import get_db, new_id, now


IMAP_HOST = os.getenv("EMAIL_IMAP_HOST", "").strip()
IMAP_PORT = int(os.getenv("EMAIL_IMAP_PORT", "993"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "").strip()
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "").strip()


def email_configured():

    return bool(
        IMAP_HOST
        and EMAIL_USERNAME
        and EMAIL_PASSWORD
    )


def decode_text(value):

    if not value:
        return ""

    parts = decode_header(value)

    result = []

    for text, encoding in parts:

        if isinstance(text, bytes):

            result.append(
                text.decode(
                    encoding or "utf-8",
                    errors="replace"
                )
            )

        else:

            result.append(
                str(text)
            )

    return "".join(result)


def extract_body(message):

    if message.is_multipart():

        for part in message.walk():

            content_type = part.get_content_type()
            disposition = str(
                part.get("Content-Disposition", "")
            )

            if (
                content_type == "text/plain"
                and "attachment" not in disposition
            ):

                payload = part.get_payload(
                    decode=True
                )

                if payload:

                    return payload.decode(
                        "utf-8",
                        errors="replace"
                    )

        return ""

    payload = message.get_payload(
        decode=True
    )

    if not payload:
        return ""

    return payload.decode(
        "utf-8",
        errors="replace"
    )


def get_business_email_accounts():

    with get_db() as db:

        rows = db.execute(
            """
            SELECT id, email
            FROM businesses
            WHERE status != 'disabled'
              AND email IS NOT NULL
              AND email != ''
            """
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def create_email_lead(
    business_id,
    sender_name,
    sender_email,
    subject,
    body
):

    lead_id = new_id()
    created_at = now()

    requirement = (
        f"Email subject: {subject}\n\n"
        f"Customer message:\n{body}"
    )

    with get_db() as db:

        existing = db.execute(
            """
            SELECT *
            FROM leads
            WHERE business_id = ?
              AND email = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                business_id,
                sender_email
            )
        ).fetchone()

        if existing:

            lead_id = existing["id"]

            db.execute(
                """
                UPDATE leads
                SET requirement = ?,
                    updated_at = ?
                WHERE id = ?
                  AND business_id = ?
                """,
                (
                    requirement,
                    created_at,
                    lead_id,
                    business_id
                )
            )

            return dict(
                db.execute(
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
            )

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
                updated_at,
                business_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead_id,
                sender_name,
                "",
                sender_email,
                "",
                requirement,
                "new",
                0,
                "",
                "",
                created_at,
                created_at,
                business_id
            )
        )

    return {
        "id": lead_id,
        "email": sender_email,
        "name": sender_name
    }


def fetch_new_emails():

    if not email_configured():

        return []

    mail = imaplib.IMAP4_SSL(
        IMAP_HOST,
        IMAP_PORT
    )

    mail.login(
        EMAIL_USERNAME,
        EMAIL_PASSWORD
    )

    mail.select("INBOX")

    status, data = mail.search(
        None,
        "UNSEEN"
    )

    if status != "OK":

        mail.logout()
        return []

    messages = []

    for number in data[0].split():

        status, raw = mail.fetch(
            number,
            "(RFC822)"
        )

        if status != "OK":
            continue

        message = email.message_from_bytes(
            raw[0][1]
        )

        sender_name, sender_email = parseaddr(
            message.get("From", "")
        )

        subject = decode_text(
            message.get("Subject", "")
        )

        body = extract_body(
            message
        )

        messages.append(
            {
                "message_id": message.get(
                    "Message-ID",
                    ""
                ),
                "sender_name": decode_text(
                    sender_name
                ),
                "sender_email": sender_email,
                "subject": subject,
                "body": body
            }
        )

    mail.logout()

    return messages


def process_email_inbox():

    if not email_configured():

        print(
            "EMAIL AGENT: Email credentials not configured."
        )

        return []

    businesses = (
        get_business_email_accounts()
    )

    emails = fetch_new_emails()

    results = []

    for message in emails:

        for business in businesses:

            lead = create_email_lead(
                business["id"],
                message["sender_name"],
                message["sender_email"],
                message["subject"],
                message["body"]
            )

            results.append(
                {
                    "business_id": business["id"],
                    "lead": lead
                }
            )

            break

    return results
