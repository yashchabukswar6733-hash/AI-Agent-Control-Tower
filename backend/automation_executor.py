import json
from datetime import datetime

from .database import get_db, now


def execute_workflow_step(
    workflow_id,
    step_id,
    business_id
):

    with get_db() as db:

        step = db.execute(
            """
            SELECT *
            FROM implementation_workflow_steps
            WHERE id = ?
              AND workflow_id = ?
              AND business_id = ?
            """,
            (
                step_id,
                workflow_id,
                business_id
            )
        ).fetchone()

        if not step:
            raise ValueError(
                "Workflow step not found."
            )

        step = dict(step)

        workflow = db.execute(
            """
            SELECT *
            FROM implementation_workflows
            WHERE id = ?
              AND business_id = ?
            """,
            (
                workflow_id,
                business_id
            )
        ).fetchone()

        if not workflow:
            raise ValueError(
                "Implementation workflow not found."
            )

        started_at = now()

        db.execute(
            """
            UPDATE implementation_workflow_steps
            SET status = ?,
                updated_at = ?
            WHERE id = ?
              AND business_id = ?
            """,
            (
                "running",
                started_at,
                step_id,
                business_id
            )
        )

        db.execute(
            """
            UPDATE implementation_workflows
            SET status = ?,
                updated_at = ?
            WHERE id = ?
              AND business_id = ?
            """,
            (
                "running",
                started_at,
                workflow_id,
                business_id
            )
        )

    title = step["title"].lower()
    description = step["description"].lower()

    action = "manual_configuration_required"

    if "email" in title or "email" in description:
        action = "email_integration"

    elif (
        "instagram" in title
        or "instagram" in description
    ):
        action = "instagram_integration"

    elif (
        "facebook" in title
        or "facebook" in description
    ):
        action = "facebook_integration"

    elif (
        "whatsapp" in title
        or "whatsapp" in description
    ):
        action = "whatsapp_integration"

    elif (
        "webhook" in title
        or "webhook" in description
    ):
        action = "webhook_configuration"

    elif (
        "deploy" in title
        or "deploy" in description
    ):
        action = "deployment"

    result = {
        "action": action,
        "status": "awaiting_connector",
        "message": (
            "This workflow step has been classified. "
            "The corresponding real integration connector "
            "must execute it."
        ),
        "executed_at": datetime.utcnow().isoformat()
    }

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
                "awaiting_connector",
                json.dumps(result),
                now(),
                step_id,
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
                "workflow_step",
                step_id,
                "workflow_step_classified",
                json.dumps(result),
                now()
            )
        )

    return {
        "workflow_id": workflow_id,
        "step_id": step_id,
        "status": "awaiting_connector",
        "result": result
    }
