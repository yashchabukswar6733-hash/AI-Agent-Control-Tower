import os
import sqlite3
import smtplib
import ssl
import time
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "saas.db"

load_dotenv(BASE_DIR / ".env")


def now():
    return datetime.utcnow().isoformat()


def get_config():
    return {
        "host": os.getenv("SMTP_HOST", "").strip(),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "username": os.getenv("SMTP_USERNAME", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", "").strip(),
        "from_email": os.getenv("SMTP_FROM_EMAIL", "").strip(),
        "from_name": os.getenv(
            "SMTP_FROM_NAME",
            "LeadPilot"
        ).strip(),
    }


def claim_pending_followups(limit=10):
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    try:
        rows = db.execute(
            """
            SELECT
                f.*,
                l.email,
                l.name
            FROM lead_followups f
            JOIN leads l
                ON l.id = f.lead_id
            WHERE f.status = 'pending'
              AND f.scheduled_at <= ?
              AND l.email != ''
            ORDER BY f.scheduled_at ASC
            LIMIT ?
            """,
            (now(), limit),
        ).fetchall()

        return rows

    finally:
        db.close()


def mark_followup_sent(followup_id, provider_message_id=""):
    db = sqlite3.connect(DB_PATH)

    try:
        db.execute(
            """
            UPDATE lead_followups
            SET
                status = 'sent',
                provider_message_id = ?,
                error = '',
                updated_at = ?
            WHERE id = ?
            """,
            (
                provider_message_id,
                now(),
                followup_id,
            ),
        )

        db.commit()

    finally:
        db.close()


def mark_followup_failed(followup_id, error):
    db = sqlite3.connect(DB_PATH)

    try:
        db.execute(
            """
            UPDATE lead_followups
            SET
                status = 'failed',
                error = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                str(error)[:2000],
                now(),
                followup_id,
            ),
        )

        db.commit()

    finally:
        db.close()


def send_email(config, recipient, recipient_name, subject, body):
    message = EmailMessage()

    message["From"] = (
        f"{config['from_name']} <{config['from_email']}>"
    )

    message["To"] = recipient
    message["Subject"] = subject

    message.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP(
        config["host"],
        config["port"],
        timeout=30,
    ) as server:

        server.starttls(context=context)

        server.login(
            config["username"],
            config["password"],
        )

        server.send_message(message)

    return "smtp"


def process_pending():
    config = get_config()

    required = [
        config["host"],
        config["username"],
        config["password"],
        config["from_email"],
    ]

    if not all(required):
        print(
            "EMAIL DELIVERY PAUSED: SMTP credentials are not configured."
        )
        return 0

    rows = claim_pending_followups()

    sent = 0

    for row in rows:
        try:
            provider_id = send_email(
                config=config,
                recipient=row["email"],
                recipient_name=row["name"],
                subject=row["subject"],
                body=row["message"],
            )

            mark_followup_sent(
                row["id"],
                provider_id,
            )

            sent += 1

            print(
                f"EMAIL SENT: {row['email']} "
                f"| followup={row['id']}"
            )

        except Exception as error:
            mark_followup_failed(
                row["id"],
                error,
            )

            print(
                f"EMAIL FAILED: {row['email']} "
                f"| {error}"
            )

    return sent


def run():
    print("=" * 60)
    print("REAL EMAIL DELIVERY WORKER")
    print("Polling every 30 seconds")
    print("=" * 60)

    while True:
        try:
            process_pending()

        except Exception as error:
            print(
                "EMAIL WORKER ERROR:",
                error,
            )

        time.sleep(30)


if __name__ == "__main__":
    run()
