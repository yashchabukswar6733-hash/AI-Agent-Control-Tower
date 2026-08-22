import json

from .database import get_db, now
from .lead_agent import analyze_lead_with_ai


def get_lead(
    lead_id,
    business_id
):

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM leads
            WHERE id = ?
              AND business_id = ?
            """,
            (
                lead_id,
                business_id
            )
        ).fetchone()

    return dict(row) if row else None


def generate_customer_response(
    lead_id,
    business_id
):

    lead = get_lead(
        lead_id,
        business_id
    )

    if not lead:
        raise ValueError(
            "Lead not found."
        )

    ai = analyze_lead_with_ai(
        lead
    )

    sales_reply = str(
        ai.get(
            "sales_reply",
            ""
        )
    ).strip()

    if not sales_reply:

        sales_reply = (
            "Thank you for contacting us. "
            "We have received your enquiry and "
            "will get back to you shortly."
        )

    analysis = {
        "temperature": ai.get(
            "temperature",
            "COLD"
        ),
        "business_problem": ai.get(
            "business_problem",
            ""
        ),
        "recommended_package": ai.get(
            "recommended_package",
            "STARTER"
        ),
        "reason": ai.get(
            "reason",
            ""
        ),
        "sales_reply": sales_reply,
        "next_action": ai.get(
            "next_action",
            ""
        )
    }

    with get_db() as db:

        db.execute(
            """
            UPDATE leads
            SET status = ?,
                score = ?,
                ai_analysis = ?,
                follow_up = ?,
                updated_at = ?
            WHERE id = ?
              AND business_id = ?
            """,
            (
                "qualified",
                ai.get("score", 0),
                json.dumps(
                    analysis,
                    ensure_ascii=False
                ),
                ai.get(
                    "follow_up",
                    ""
                ),
                now(),
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
                "ai_response_generated",
                sales_reply,
                now()
            )
        )

    return {
        "lead_id": lead_id,
        "score": ai.get(
            "score",
            0
        ),
        "temperature": ai.get(
            "temperature",
            "COLD"
        ),
        "recommended_package": ai.get(
            "recommended_package",
            "STARTER"
        ),
        "customer_response": sales_reply,
        "next_action": ai.get(
            "next_action",
            ""
        )
    }


def generate_responses_for_new_leads(
    business_id
):

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *
            FROM leads
            WHERE business_id = ?
              AND status = 'new'
            ORDER BY created_at ASC
            """,
            (business_id,)
        ).fetchall()

    results = []

    for row in rows:

        try:

            result = generate_customer_response(
                row["id"],
                business_id
            )

            results.append(
                result
            )

        except Exception as error:

            print(
                "RESPONSE AGENT ERROR:",
                error
            )

    return results
