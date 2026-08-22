import os
import time

from .database import get_db
from .onboarding_agent import (
    onboard_all_paid_clients
)


POLL_SECONDS = int(
    os.getenv(
        "ONBOARDING_POLL_SECONDS",
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
    print("AI CLIENT ONBOARDING AGENT STARTED")
    print(
        f"Polling every {POLL_SECONDS} seconds"
    )
    print("=" * 60)

    while True:

        try:

            for business_id in get_business_ids():

                results = onboard_all_paid_clients(
                    business_id
                )

                created = [
                    item
                    for item in results
                    if item.get("created")
                ]

                if created:

                    print(
                        f"Business {business_id}: "
                        f"{len(created)} client(s) onboarded"
                    )

        except Exception as error:

            print(
                "ONBOARDING WORKER ERROR:",
                error
            )

        time.sleep(
            POLL_SECONDS
        )


if __name__ == "__main__":

    run()
