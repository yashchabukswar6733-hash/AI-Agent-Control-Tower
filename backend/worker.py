import os
import time
import traceback

from .database import get_db
from .followup_agent import send_due_followups


POLL_SECONDS = int(
    os.getenv("FOLLOWUP_POLL_SECONDS", "60")
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


def run_followup_worker():

    print("=" * 60)
    print("AI FOLLOW-UP WORKER STARTED")
    print(f"Polling every {POLL_SECONDS} seconds")
    print("=" * 60)

    while True:

        try:

            business_ids = get_business_ids()

            for business_id in business_ids:

                try:

                    results = send_due_followups(
                        business_id
                    )

                    if results:

                        print(
                            f"Business {business_id}: "
                            f"processed {len(results)} follow-ups"
                        )

                        for result in results:

                            print(
                                result
                            )

                except Exception as error:

                    print(
                        f"Business {business_id} failed: "
                        f"{error}"
                    )

            time.sleep(POLL_SECONDS)

        except KeyboardInterrupt:

            print(
                "Follow-up worker stopped."
            )

            break

        except Exception:

            traceback.print_exc()

            time.sleep(
                POLL_SECONDS
            )


if __name__ == "__main__":

    run_followup_worker()
