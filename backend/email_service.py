import os
import smtplib
from email.message import EmailMessage


class EmailConfigurationError(Exception):
    pass


def send_email(
    to: str,
    subject: str,
    body: str
):

    host = os.getenv("SMTP_HOST", "").strip()
    port = int(
        os.getenv("SMTP_PORT", "587")
    )
    username = os.getenv(
        "SMTP_USERNAME",
        ""
    ).strip()
    password = os.getenv(
        "SMTP_PASSWORD",
        ""
    ).strip()
    sender = os.getenv(
        "SMTP_FROM_EMAIL",
        ""
    ).strip()

    if not host:
        raise EmailConfigurationError(
            "SMTP_HOST is not configured."
        )

    if not username:
        raise EmailConfigurationError(
            "SMTP_USERNAME is not configured."
        )

    if not password:
        raise EmailConfigurationError(
            "SMTP_PASSWORD is not configured."
        )

    if not sender:
        raise EmailConfigurationError(
            "SMTP_FROM_EMAIL is not configured."
        )

    to = str(to).strip()

    if not to:
        raise ValueError(
            "Recipient email is required."
        )

    message = EmailMessage()

    message["From"] = sender
    message["To"] = to
    message["Subject"] = str(
        subject
    )

    message.set_content(
        str(body)
    )

    with smtplib.SMTP(
        host,
        port,
        timeout=30
    ) as smtp:

        smtp.starttls()

        smtp.login(
            username,
            password
        )

        smtp.send_message(
            message
        )

    return {
        "status": "sent",
        "to": to,
        "subject": subject
    }
