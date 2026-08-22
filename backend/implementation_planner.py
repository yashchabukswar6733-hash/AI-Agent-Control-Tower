import json

from .database import get_db, new_id, now
from .ai_service import ask_ai


def create_implementation_plan(
    client_id,
    business_id
):

    with get_db() as db:

        requirements = db.execute(
            """
            SELECT *
            FROM onboarding_requirements
            WHERE client_id = ?
              AND business_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                client_id,
                business_id
            )
        ).fetchone()

        if not requirements:
            raise ValueError(
                "Client onboarding requirements not found."
            )

        requirements = dict(requirements)

    prompt = f"""
You are an automation implementation architect.

Create a practical implementation plan for this paying client.

Business:
{requirements["business_description"]}

Services:
{requirements["services"]}

Target customers:
{requirements["target_customers"]}

Goals:
{requirements["goals"]}

Website:
{requirements["website_url"]}

Notes:
{requirements["notes"]}

Return ONLY valid JSON with this structure:

{{
  "summary": "short implementation summary",
  "automations": [
    {{
      "name": "automation name",
      "purpose": "what it does",
      "priority": "high|medium|low",
      "dependencies": ["dependency"]
    }}
  ],
  "implementation_steps": [
    {{
      "step": 1,
      "title": "step title",
      "description": "what must be done"
    }}
  ]
}}

Do not invent credentials or claim that an integration is connected.
"""

    result = ask_ai(prompt)

    if not result:
        raise RuntimeError(
            "AI implementation planner returned no result."
        )

    try:

        if isinstance(result, str):

            plan = json.loads(result)

        else:

            plan = result

    except Exception:

        plan = {
            "summary": str(result),
            "automations": [],
            "implementation_steps": []
        }

    plan_id = new_id()
    created_at = now()

    with get_db() as db:

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS
            implementation_plans
            (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                business_id TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        db.execute(
            """
            INSERT INTO implementation_plans
            (
                id,
                client_id,
                business_id,
                plan_json,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan_id,
                client_id,
                business_id,
                json.dumps(plan),
                "ready",
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
                "implementation_plan_created",
                f"Implementation plan {plan_id} created.",
                created_at
            )
        )

    return {
        "plan_id": plan_id,
        "client_id": client_id,
        "status": "ready",
        "plan": plan
    }
