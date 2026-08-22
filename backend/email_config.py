import os
import re
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def get_email_config():
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    from_email = os.getenv("SMTP_FROM_EMAIL", "").strip()

    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com").strip(),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "username": username,
        "password": password,
        "from_email": from_email or username,
        "from_name": os.getenv(
            "SMTP_FROM_NAME",
            "LeadPilot"
        ).strip(),
    }


def email_ready():
    config = get_email_config()

    return bool(
        config["host"]
        and config["username"]
        and config["password"]
        and config["from_email"]
    )


def validate_email(address):
    if not address:
        return False

    return bool(
        re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            address,
        )
    )


if __name__ == "__main__":
    config = get_email_config()

    print("=" * 60)
    print("EMAIL CONFIGURATION")
    print("=" * 60)

    print("SMTP host:", config["host"])
    print("SMTP port:", config["port"])
    print("Username configured:", bool(config["username"]))
    print("Password configured:", bool(config["password"]))
    print("From email configured:", bool(config["from_email"]))

    print(
        "Email delivery:",
        "READY FOR REAL CREDENTIALS"
        if email_ready()
        else "WAITING FOR REAL CREDENTIALS",
    )
