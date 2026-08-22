import json
from datetime import datetime, timedelta

from .database import get_db, now


FOLLOW_UP_DAYS = {
    "HOT": 1,
    "WARM": 3,
    "COLD": 7,
}


def parse_datetime(value):

    if not value:
        return None

    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except Exception:
        return None


def get_follow_up_leads(
    business_id
):

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *
            FROM leads
            WHERE business_id = ?
              AND status = 'qualified'
            ORDER BY updated_at ASC
            """,
            (
                business_id,
            )
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def get_temperature(
    lead
):

    try:

        analysis = json.loads(
            lead.get(
                "ai_analysis",
                "{}"
            )
        )

        return str(
            analysis.get(
                "temperature",
                "COLD"
            )
        ).upper()

    except Exception:

        return "COLD"


def should_follow_up(
    lead
):

    updated = parse_datetime(
        lead.get("updated_at")
    )

    if not updated:
        return True

    temperature = get_temperature(
        lead
    )

    days = FOLLOW_UP_DAYS.get(
        temperature,
        7
    )

    cutoff = datetime.now(
        updated.tzinfo
    ) - timedelta(
        days=days
    )

    return updated <= cutoff


def create_follow_up(
    lead,
    business_id
):

    lead_id = lead["id"]

    temperature = get_temperature(
        lead
    )

    with get_db() as db:

        existing = db.execute(
            """
            SELECT id
            FROM activity_log
            WHERE entity_type = ?
              AND entity_id = ?
              AND action = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                "lead",
                lead_id,
                "follow_up_created"
            )
        ).fetchone()

        if existing:

            return {
                "created": False,
                "already_exists": True,
                "lead_id": lead_id
            }

        created_at = now()

        if temperature == "HOT":

            instruction = (
                "High-priority follow-up. "
                "Contact the lead and ask whether "
                "they want to proceed."
            )

        elif temperature == "WARM":

            instruction = (
                "Follow up with the lead, clarify "
                "their requirement and answer "
                "remaining questions."
            )

        else:

            instruction = (
                "Gentle follow-up. Ask whether the "
                "customer still needs automation help."
            )

        db.execute(
            """
            UPDATE leads
            SET follow_up = ?,
                updated_at = ?
            WHERE id = ?
              AND business_id = ?
            """,
            (
                instruction,
                created_at,
                lead_id,
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
                "lead",
                lead_id,
                "follow_up_created",
                instruction,
                created_at
            )
        )

    return {
        "created": True,
        "already_exists": False,
        "lead_id": lead_id,
        "temperature": temperature,
        "instruction": instruction
    }


def process_business(
    business_id
):

    leads = get_follow_up_leads(
        business_id
    )

    results = []

    for lead in leads:

        if not should_follow_up(
            lead
        ):
            continue

        try:

            result = create_follow_up(
                lead,
                business_id
            )

            results.append(
                result
            )

        except Exception as error:

            print(
                "FOLLOW-UP ERROR:",
                error
            )

    return results
