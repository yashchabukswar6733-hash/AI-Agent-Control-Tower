import os
import time

from .email_agent import (
    process_email_inbox
)


POLL_SECONDS = int(
    os.getenv(
        "EMAIL_POLL_SECONDS",
        "60"
    )
)


def run():

    print("=" * 60)
    print("AI EMAIL AUTOMATION AGENT STARTED")
    print(
        f"Polling every {POLL_SECONDS} seconds"
    )
    print("=" * 60)

    while True:

        try:

            results = process_email_inbox()

            if results:

                print(
                    f"EMAIL AGENT: "
                    f"{len(results)} email lead(s) processed."
                )

        except Exception as error:

            print(
                "EMAIL AGENT ERROR:",
                error
            )

        time.sleep(
            POLL_SECONDS
        )


if __name__ == "__main__":

    run()
