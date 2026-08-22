import time
import traceback

from .database import get_db, now
from .automation_executor import execute_workflow_step


POLL_SECONDS = 30


def get_pending_steps():

    with get_db() as db:

        rows = db.execute(
            """
            SELECT
                s.id,
                s.workflow_id,
                s.business_id,
                s.position,
                s.title,
                s.description
            FROM implementation_workflow_steps s
            JOIN implementation_workflows w
              ON w.id = s.workflow_id
            WHERE s.status = 'pending'
              AND w.status IN ('pending', 'running')
            ORDER BY
                s.workflow_id,
                s.position
            """
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def mark_workflow_status(
    workflow_id,
    business_id
):

    with get_db() as db:

        remaining = db.execute(
            """
            SELECT COUNT(*) AS count
            FROM implementation_workflow_steps
            WHERE workflow_id = ?
              AND business_id = ?
              AND status IN ('pending', 'running')
            """,
            (
                workflow_id,
                business_id
            )
        ).fetchone()["count"]

        waiting = db.execute(
            """
            SELECT COUNT(*) AS count
            FROM implementation_workflow_steps
            WHERE workflow_id = ?
              AND business_id = ?
              AND status = 'awaiting_connector'
            """,
            (
                workflow_id,
                business_id
            )
        ).fetchone()["count"]

        failed = db.execute(
            """
            SELECT COUNT(*) AS count
            FROM implementation_workflow_steps
            WHERE workflow_id = ?
              AND business_id = ?
              AND status = 'failed'
            """,
            (
                workflow_id,
                business_id
            )
        ).fetchone()["count"]

        if failed:

            status = "failed"

        elif remaining:

            status = "running"

        elif waiting:

            status = "awaiting_connector"

        else:

            status = "completed"

        db.execute(
            """
            UPDATE implementation_workflows
            SET status = ?,
                updated_at = ?
            WHERE id = ?
              AND business_id = ?
            """,
            (
                status,
                now(),
                workflow_id,
                business_id
            )
        )


def process_pending_steps():

    steps = get_pending_steps()

    processed = 0

    for step in steps:

        try:

            execute_workflow_step(
                workflow_id=step["workflow_id"],
                step_id=step["id"],
                business_id=step["business_id"]
            )

            mark_workflow_status(
                workflow_id=step["workflow_id"],
                business_id=step["business_id"]
            )

            processed += 1

        except Exception as error:

            print(
                "WORKFLOW STEP ERROR:",
                error
            )

            traceback.print_exc()

            with get_db() as db:

                db.execute(
                    """
                    UPDATE implementation_workflow_steps
                    SET status = ?,
                        result = ?,
                        updated_at = ?
                    WHERE id = ?
                      AND business_id = ?
                    """,
                    (
                        "failed",
                        str(error),
                        now(),
                        step["id"],
                        step["business_id"]
                    )
                )

            mark_workflow_status(
                workflow_id=step["workflow_id"],
                business_id=step["business_id"]
            )

    return processed


def run_worker():

    print("=" * 60)
    print("AI IMPLEMENTATION WORKER STARTED")
    print(f"Polling every {POLL_SECONDS} seconds")
    print("=" * 60)

    while True:

        try:

            count = process_pending_steps()

            if count:

                print(
                    f"Processed {count} workflow step(s)."
                )

        except Exception as error:

            print(
                "WORKER ERROR:",
                error
            )

            traceback.print_exc()

        time.sleep(
            POLL_SECONDS
        )


if __name__ == "__main__":

    run_worker()
