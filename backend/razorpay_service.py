import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


RAZORPAY_API = "https://api.razorpay.com/v1"


def get_credentials():
    key_id = os.getenv(
        "RAZORPAY_KEY_ID",
        ""
    ).strip()

    key_secret = os.getenv(
        "RAZORPAY_KEY_SECRET",
        ""
    ).strip()

    if not key_id or not key_secret:
        raise RuntimeError(
            "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET "
            "must be configured before creating real orders."
        )

    return key_id, key_secret


def create_order(
    amount_rupees,
    receipt,
    notes=None,
):
    if amount_rupees <= 0:
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    if not receipt:
        raise ValueError(
            "Payment receipt is required."
        )

    key_id, key_secret = get_credentials()

    amount_paise = int(
        round(float(amount_rupees) * 100)
    )

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": str(receipt),
    }

    if notes:
        payload["notes"] = {
            str(k): str(v)
            for k, v in notes.items()
        }

    body = json.dumps(payload).encode("utf-8")

    credentials = (
        f"{key_id}:{key_secret}"
    ).encode("utf-8")

    authorization = base64.b64encode(
        credentials
    ).decode("ascii")

    request = urllib.request.Request(
        f"{RAZORPAY_API}/orders",
        data=body,
        method="POST",
        headers={
            "Authorization": (
                f"Basic {authorization}"
            ),
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:

            response_body = response.read()

            return json.loads(
                response_body.decode("utf-8")
            )

    except urllib.error.HTTPError as error:
        response_body = error.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Razorpay order creation failed "
            f"({error.code}): {response_body}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Unable to connect to Razorpay: {error}"
        ) from error


if __name__ == "__main__":
    print("=" * 60)
    print("RAZORPAY PAYMENT SERVICE")
    print("=" * 60)

    try:
        get_credentials()
        print(
            "Razorpay credentials: CONFIGURED"
        )
        print(
            "Real order creation: READY"
        )

    except RuntimeError:
        print(
            "Razorpay credentials: NOT CONFIGURED"
        )
        print(
            "Add real credentials to .env before "
            "creating live orders."
        )
