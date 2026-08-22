import os
import time

from .database import get_db
from .payment_agent import (
    process_business
)


POLL_SECONDS = int(
    os.getenv(
        "PAYMENT_POLL_SECONDS",
        "60"
    )
)


def get_business_ids():

    with get_db() as db:

        rows = db.execute(
            """
            SELECT id
            FROM businesses
            WHERE status != 'disabled'
            """
        ).fetchall()

    return [
        row["id"]
        for row in rows
    ]


def run():

    print("=" * 60)
    print("AI PAYMENT AUTOMATION AGENT STARTED")
    print(
        f"Polling every {POLL_SECONDS} seconds"
    )
    print("=" * 60)

    while True:

        try:

            for business_id in get_business_ids():

                results = process_business(
                    business_id
                )

                if results:

                    print(
                        f"Business {business_id}: "
                        f"{len(results)} payment record(s) created"
                    )

        except Exception as error:

            print(
                "PAYMENT WORKER ERROR:",
                error
            )

        time.sleep(
            POLL_SECONDS
        )


if __name__ == "__main__":

    run()
