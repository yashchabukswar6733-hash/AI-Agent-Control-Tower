import os
import time

from .database import get_db
from .delivery_agent import (
    create_delivery_for_all_clients
)


POLL_SECONDS = int(
    os.getenv(
        "DELIVERY_POLL_SECONDS",
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
    print("AI CLIENT DELIVERY AGENT STARTED")
    print(
        f"Polling every {POLL_SECONDS} seconds"
    )
    print("=" * 60)

    while True:

        try:

            for business_id in get_business_ids():

                results = (
                    create_delivery_for_all_clients(
                        business_id
                    )
                )

                created = [
                    item
                    for item in results
                    if not item.get(
                        "already_exists",
                        False
                    )
                ]

                if created:

                    print(
                        f"Business {business_id}: "
                        f"delivery checked"
                    )

        except Exception as error:

            print(
                "DELIVERY WORKER ERROR:",
                error
            )

        time.sleep(
            POLL_SECONDS
        )


if __name__ == "__main__":

    run()
