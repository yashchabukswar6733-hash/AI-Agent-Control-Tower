import os
import time

from .database import get_db
from .customer_response_agent import (
    generate_responses_for_new_leads
)


POLL_SECONDS = int(
    os.getenv(
        "RESPONSE_POLL_SECONDS",
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
    print("AI CUSTOMER RESPONSE AGENT STARTED")
    print(
        f"Polling every {POLL_SECONDS} seconds"
    )
    print("=" * 60)

    while True:

        try:

            for business_id in get_business_ids():

                results = (
                    generate_responses_for_new_leads(
                        business_id
                    )
                )

                if results:

                    print(
                        f"Business {business_id}: "
                        f"{len(results)} AI response(s) generated"
                    )

        except Exception as error:

            print(
                "RESPONSE WORKER ERROR:",
                error
            )

        time.sleep(
            POLL_SECONDS
        )


if __name__ == "__main__":

    run()
