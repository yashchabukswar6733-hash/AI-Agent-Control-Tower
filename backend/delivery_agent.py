import json

from .database import get_db, new_id, now


DEFAULT_DELIVERY_TASKS = [
    "Review client requirements",
    "Configure client workspace",
    "Configure requested integrations",
    "Configure automation workflows",
    "Connect notification channels",
    "Perform implementation review",
    "Mark delivery ready"
]


def create_client_delivery(
    client_id,
    business_id,
    onboarding_id
):

    with get_db() as db:

        existing = db.execute(
            """
            SELECT *
            FROM client_delivery_tasks
            WHERE client_id = ?
              AND business_id = ?
            ORDER BY position
            """,
            (
                client_id,
                business_id
            )
        ).fetchall()

        if existing:

            return {
                "status": "already_created",
                "tasks": [
                    dict(row)
                    for row in existing
                ]
            }

        created_at = now()

        for position, task_name in enumerate(
            DEFAULT_DELIVERY_TASKS,
            start=1
        ):

            db.execute(
                """
                INSERT INTO client_delivery_tasks
                (
                    id,
                    client_id,
                    business_id,
                    onboarding_id,
                    task_name,
                    position,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id(),
                    client_id,
                    business_id,
                    onboarding_id,
                    task_name,
                    position,
                    "pending",
                    created_at,
                    created_at
                )
            )

        db.execute(
            """
            UPDATE client_onboarding
            SET status = ?,
                updated_at = ?
            WHERE id = ?
              AND client_id = ?
              AND business_id = ?
            """,
            (
                "delivery_started",
                created_at,
                onboarding_id,
                client_id,
                business_id
            )
        )

        db.execute(
            """
            UPDATE clients
            SET status = ?,
                updated_at = ?
            WHERE id = ?
              AND business_id = ?
            """,
            (
                "delivery",
                created_at,
                client_id,
                business_id
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
                "delivery_started",
                "Client delivery workflow created.",
                created_at
            )
        )

    return {
        "status": "created",
        "client_id": client_id,
        "onboarding_id": onboarding_id,
        "task_count": len(
            DEFAULT_DELIVERY_TASKS
        )
    }


def get_client_delivery(
    client_id,
    business_id
):

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *
            FROM client_delivery_tasks
            WHERE client_id = ?
              AND business_id = ?
            ORDER BY position
            """,
            (
                client_id,
                business_id
            )
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def connect_delivery_to_workflow(
    client_id,
    business_id,
    onboarding_id
):

    from .implementation_planner import (
        create_implementation_plan
    )

    from .execution_workflow import (
        create_execution_workflow
    )

    with get_db() as db:

        requirements = db.execute(
            """
            SELECT id
            FROM onboarding_requirements
            WHERE client_id = ?
              AND business_id = ?
            LIMIT 1
            """,
            (
                client_id,
                business_id
            )
        ).fetchone()

        if not requirements:

            raise ValueError(
                "Client requirements are not submitted."
            )

    plan = create_implementation_plan(
        client_id=client_id,
        business_id=business_id
    )

    workflow = create_execution_workflow(
        client_id=client_id,
        business_id=business_id,
        plan_id=plan["plan_id"]
    )

    with get_db() as db:

        db.execute(
            """
            UPDATE client_onboarding
            SET status = ?,
                updated_at = ?
            WHERE id = ?
              AND client_id = ?
              AND business_id = ?
            """,
            (
                "automation_ready",
                now(),
                onboarding_id,
                client_id,
                business_id
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
                "automation_workflow_ready",
                json.dumps({
                    "plan_id": plan["plan_id"],
                    "workflow_id": workflow["workflow_id"]
                }),
                now()
            )
        )

    return {
        "client_id": client_id,
        "onboarding_id": onboarding_id,
        "plan_id": plan["plan_id"],
        "workflow_id": workflow["workflow_id"],
        "status": "automation_ready"
    }
