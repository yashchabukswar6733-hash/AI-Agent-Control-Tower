import json

from .database import get_db, new_id, now


def create_execution_workflow(
    client_id,
    business_id,
    plan_id
):

    with get_db() as db:

        plan = db.execute(
            """
            SELECT *
            FROM implementation_plans
            WHERE id = ?
              AND client_id = ?
              AND business_id = ?
            """,
            (
                plan_id,
                client_id,
                business_id
            )
        ).fetchone()

        if not plan:
            raise ValueError(
                "Implementation plan not found."
            )

        plan = dict(plan)

        existing = db.execute(
            """
            SELECT *
            FROM implementation_workflows
            WHERE plan_id = ?
              AND business_id = ?
            LIMIT 1
            """,
            (
                plan_id,
                business_id
            )
        ).fetchone()

        if existing:
            return {
                "workflow_id": existing["id"],
                "status": existing["status"],
                "existing": True
            }

        workflow_id = new_id()
        created_at = now()

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS implementation_workflows
            (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                business_id TEXT NOT NULL,
                plan_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS implementation_workflow_steps
            (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                business_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                result TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        db.execute(
            """
            INSERT INTO implementation_workflows
            (
                id,
                client_id,
                business_id,
                plan_id,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workflow_id,
                client_id,
                business_id,
                plan_id,
                "pending",
                created_at,
                created_at
            )
        )

        try:
            plan_data = json.loads(
                plan["plan_json"]
            )
        except Exception:
            plan_data = {}

        steps = plan_data.get(
            "implementation_steps",
            []
        )

        for position, step in enumerate(
            steps,
            start=1
        ):

            title = str(
                step.get(
                    "title",
                    f"Implementation step {position}"
                )
            )

            description = str(
                step.get(
                    "description",
                    ""
                )
            )

            db.execute(
                """
                INSERT INTO implementation_workflow_steps
                (
                    id,
                    workflow_id,
                    business_id,
                    position,
                    title,
                    description,
                    status,
                    result,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id(),
                    workflow_id,
                    business_id,
                    position,
                    title,
                    description,
                    "pending",
                    "",
                    created_at,
                    created_at
                )
            )

        db.execute(
            """
            INSERT INTO activity_log
            (
                entity_type,
                entity_id,
                action,
                details,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "client",
                client_id,
                "implementation_workflow_created",
                f"Workflow {workflow_id} created.",
                created_at
            )
        )

    return {
        "workflow_id": workflow_id,
        "client_id": client_id,
        "status": "pending",
        "steps_created": len(steps),
        "existing": False
    }
