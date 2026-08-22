import time

from .lead_qualification_agent import qualify_lead
from .followup_engine import create_followup_tables, schedule_followups


def run_once():
    from .lead_worker import get_new_leads

    processed = 0

    for lead in get_new_leads():
        try:
            qualify_lead(lead["id"])
            processed += 1
        except Exception as error:
            print(
                f"QUALIFICATION ERROR [{lead['id']}]: {error}"
            )

    scheduled = schedule_followups()

    return processed, scheduled


def run():
    create_followup_tables()

    print("=" * 60)
    print("LEAD + FOLLOW-UP AUTOMATION")
    print("Polling every 30 seconds")
    print("=" * 60)

    while True:
        try:
            processed, scheduled = run_once()

            if processed or scheduled:
                print(
                    f"Qualified: {processed} | "
                    f"Follow-ups scheduled: {scheduled}"
                )

        except Exception as error:
            print("AUTOMATION ERROR:", error)

        time.sleep(30)


if __name__ == "__main__":
    run()
