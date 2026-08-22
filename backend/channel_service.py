import os
import smtplib
import requests

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ============================================================
# EMAIL
# ============================================================

def email_configured():
    return bool(
        os.getenv("SMTP_HOST", "").strip()
        and os.getenv("SMTP_USERNAME", "").strip()
        and os.getenv("SMTP_PASSWORD", "").strip()
        and os.getenv("SMTP_FROM", "").strip()
    )


def send_email(
    to: str,
    subject: str,
    body: str
):

    if not email_configured():
        raise RuntimeError(
            "SMTP email configuration is missing."
        )

    to = str(to).strip()

    if not to:
        raise ValueError(
            "Recipient email is required."
        )

    message = MIMEMultipart()
    message["From"] = os.getenv(
        "SMTP_FROM"
    )
    message["To"] = to
    message["Subject"] = subject

    message.attach(
        MIMEText(
            body,
            "plain",
            "utf-8"
        )
    )

    host = os.getenv(
        "SMTP_HOST"
    )

    port = int(
        os.getenv(
            "SMTP_PORT",
            "587"
        )
    )

    username = os.getenv(
        "SMTP_USERNAME"
    )

    password = os.getenv(
        "SMTP_PASSWORD"
    )

    with smtplib.SMTP(
        host,
        port,
        timeout=30
    ) as server:

        server.starttls()

        server.login(
            username,
            password
        )

        server.sendmail(
            message["From"],
            [to],
            message.as_string()
        )

    return {
        "success": True,
        "channel": "email",
        "recipient": to
    }


# ============================================================
# FACEBOOK / META
# ============================================================

def meta_configured():

    return bool(
        os.getenv(
            "META_ACCESS_TOKEN",
            ""
        ).strip()
    )


def send_facebook_message(
    recipient_id: str,
    message: str
):

    token = os.getenv(
        "META_ACCESS_TOKEN",
        ""
    ).strip()

    page_id = os.getenv(
        "FACEBOOK_PAGE_ID",
        ""
    ).strip()

    if not token:
        raise RuntimeError(
            "META_ACCESS_TOKEN is missing."
        )

    if not page_id:
        raise RuntimeError(
            "FACEBOOK_PAGE_ID is missing."
        )

    url = (
        "https://graph.facebook.com/v25.0/"
        f"{page_id}/messages"
    )

    response = requests.post(
        url,
        params={
            "access_token": token
        },
        json={
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "text": message
            }
        },
        timeout=20
    )

    try:
        data = response.json()
    except Exception:
        data = {
            "raw": response.text
        }

    if not response.ok:
        raise RuntimeError(
            f"Facebook API error "
            f"{response.status_code}: {data}"
        )

    return data


# ============================================================
# INSTAGRAM
# ============================================================

def instagram_configured():

    return bool(
        os.getenv(
            "META_ACCESS_TOKEN",
            ""
        ).strip()
        and os.getenv(
            "INSTAGRAM_ACCOUNT_ID",
            ""
        ).strip()
    )


def send_instagram_message(
    recipient_id: str,
    message: str
):

    token = os.getenv(
        "META_ACCESS_TOKEN",
        ""
    ).strip()

    instagram_id = os.getenv(
        "INSTAGRAM_ACCOUNT_ID",
        ""
    ).strip()

    if not token:
        raise RuntimeError(
            "META_ACCESS_TOKEN is missing."
        )

    if not instagram_id:
        raise RuntimeError(
            "INSTAGRAM_ACCOUNT_ID is missing."
        )

    url = (
        "https://graph.facebook.com/v25.0/"
        f"{instagram_id}/messages"
    )

    response = requests.post(
        url,
        params={
            "access_token": token
        },
        json={
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "text": message
            }
        },
        timeout=20
    )

    try:
        data = response.json()
    except Exception:
        data = {
            "raw": response.text
        }

    if not response.ok:
        raise RuntimeError(
            f"Instagram API error "
            f"{response.status_code}: {data}"
        )

    return data


# ============================================================
# UNIFIED CHANNEL ROUTER
# ============================================================

def send_message(
    channel: str,
    recipient: str,
    message: str,
    subject: str = "Business enquiry"
):

    channel = (
        str(channel)
        .strip()
        .lower()
    )

    if channel == "email":

        return send_email(
            recipient,
            subject,
            message
        )

    if channel == "facebook":

        return send_facebook_message(
            recipient,
            message
        )

    if channel == "instagram":

        return send_instagram_message(
            recipient,
            message
        )

    raise ValueError(
        f"Unsupported channel: {channel}"
    )
