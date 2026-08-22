import os
import time

from .database import get_db
from .email_sender_agent import (
    send_lead_response
)


POLL_SECONDS = int(
    os.getenv(
        "EMAIL_SENDER_POLL_SECONDS",
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


def get_unsent_leads(
    business_id
):

    with get_db() as db:

        rows = db.execute(
            """
            SELECT l.id
            FROM leads l
            WHERE l.business_id = ?
              AND l.status = 'qualified'
              AND l.email IS NOT NULL
              AND l.email != ''
              AND NOT EXISTS (
                  SELECT 1
                  FROM activity_log a
                  WHERE a.entity_type = 'lead'
                    AND a.entity_id = l.id
                    AND a.action = 'customer_email_sent'
              )
            ORDER BY l.created_at ASC
            """,
            (
                business_id,
            )
        ).fetchall()

    return [
        row["id"]
        for row in rows
    ]


def run():

    print("=" * 60)
    print("AI EMAIL SENDING AGENT STARTED")
    print(
        f"Polling every {POLL_SECONDS} seconds"
    )
    print("=" * 60)

    while True:

        try:

            for business_id in get_business_ids():

                lead_ids = get_unsent_leads(
                    business_id
                )

                for lead_id in lead_ids:

                    try:

                        result = send_lead_response(
                            lead_id,
                            business_id
                        )

                        if result.get("sent"):

                            print(
                                f"Email sent for lead {lead_id}"
                            )

                    except Exception as error:

                        print(
                            f"Email send failed "
                            f"for lead {lead_id}:",
                            error
                        )

        except Exception as error:

            print(
                "EMAIL SENDER WORKER ERROR:",
                error
            )

        time.sleep(
            POLL_SECONDS
        )


if __name__ == "__main__":

    run()
