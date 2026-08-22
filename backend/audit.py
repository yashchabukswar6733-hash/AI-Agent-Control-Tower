import json
from datetime import datetime

from .database import get_db


def log_activity(
    entity_type,
    entity_id,
    action,
    details=None
):
    """
    Record an important system/agent action.

    This is intentionally simple and reusable across
    Lead, Sales, Customer, Payment and Workflow agents.
    """

    if details is None:
        details = {}

    if not isinstance(details, str):
        details = json.dumps(
            details,
            ensure_ascii=False,
            default=str
        )

    created_at = datetime.now().isoformat()

    with get_db() as db:
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
                str(entity_type),
                str(entity_id),
                str(action),
                details,
                created_at
            )
        )

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "details": details,
        "created_at": created_at
    }


def list_activity(
    entity_type=None,
    entity_id=None,
    limit=100
):
    """
    Retrieve recent activity.
    """

    limit = max(
        1,
        min(int(limit), 500)
    )

    query = """
        SELECT *
        FROM activity_log
    """

    conditions = []
    values = []

    if entity_type is not None:
        conditions.append(
            "entity_type = ?"
        )
        values.append(
            str(entity_type)
        )

    if entity_id is not None:
        conditions.append(
            "entity_id = ?"
        )
        values.append(
            str(entity_id)
        )

    if conditions:
        query += " WHERE " + " AND ".join(
            conditions
        )

    query += """
        ORDER BY created_at DESC
        LIMIT ?
    """

    values.append(limit)

    with get_db() as db:
        rows = db.execute(
            query,
            tuple(values)
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]
