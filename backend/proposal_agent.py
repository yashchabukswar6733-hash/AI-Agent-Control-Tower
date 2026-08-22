import json

from .database import get_db
from .proposals import create_proposal


PACKAGE_PRICES = {
    "STARTER": {
        "setup_fee": 4999,
        "monthly_fee": 0,
        "service": "AI Business Automation - Starter",
    },
    "GROWTH": {
        "setup_fee": 14999,
        "monthly_fee": 0,
        "service": "AI Business Automation - Growth",
    },
}


def get_qualified_leads(
    business_id
):

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *
            FROM leads
            WHERE business_id = ?
              AND status = 'qualified'
            ORDER BY created_at ASC
            """,
            (
                business_id,
            )
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def get_existing_proposal(
    lead_id,
    business_id
):

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM proposals
            WHERE lead_id = ?
              AND business_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                lead_id,
                business_id
            )
        ).fetchone()

    return dict(row) if row else None


def get_ai_analysis(
    lead
):

    try:

        return json.loads(
            lead.get(
                "ai_analysis",
                "{}"
            )
        )

    except Exception:

        return {}


def build_description(
    lead,
    analysis,
    package
):

    problem = analysis.get(
        "business_problem",
        ""
    )

    reason = analysis.get(
        "reason",
        ""
    )

    if package == "GROWTH":

        features = (
            "Multiple AI workflows, "
            "lead automation, "
            "customer communication automation, "
            "and ongoing optimization."
        )

    else:

        features = (
            "One automation workflow, "
            "basic AI lead handling, "
            "and basic integration."
        )

    return (
        f"Recommended solution for "
        f"{lead.get('business', '') or 'your business'}.\n\n"
        f"Business requirement:\n"
        f"{lead.get('requirement', '')}\n\n"
        f"Identified problem:\n"
        f"{problem}\n\n"
        f"Recommended solution:\n"
        f"{features}\n\n"
        f"Why this package:\n"
        f"{reason}"
    )


def create_ai_proposal(
    lead,
    business_id
):

    lead_id = lead["id"]

    existing = get_existing_proposal(
        lead_id,
        business_id
    )

    if existing:

        return {
            "created": False,
            "already_exists": True,
            "proposal": existing
        }

    analysis = get_ai_analysis(
        lead
    )

    package = str(
        analysis.get(
            "recommended_package",
            "STARTER"
        )
    ).upper()

    if package not in PACKAGE_PRICES:

        package = "STARTER"

    pricing = PACKAGE_PRICES[
        package
    ]

    proposal = create_proposal(
        lead_id=lead_id,
        client_name=lead.get(
            "name",
            ""
        ),
        company=lead.get(
            "business",
            ""
        ),
        service=pricing["service"],
        setup_fee=pricing["setup_fee"],
        monthly_fee=pricing["monthly_fee"],
        description=build_description(
            lead,
            analysis,
            package
        ),
        business_id=business_id
    )

    return {
        "created": True,
        "already_exists": False,
        "package": package,
        "proposal": proposal
    }


def process_business(
    business_id
):

    leads = get_qualified_leads(
        business_id
    )

    results = []

    for lead in leads:

        try:

            result = create_ai_proposal(
                lead,
                business_id
            )

            if result.get("created"):

                results.append(
                    result
                )

        except Exception as error:

            print(
                "PROPOSAL AGENT ERROR:",
                error
            )

    return results
