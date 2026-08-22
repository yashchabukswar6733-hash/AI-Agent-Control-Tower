from .database import get_db
from .payments import PaymentManager


payment_manager = PaymentManager()


def get_business_proposals(
    business_id
):

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *
            FROM proposals
            WHERE business_id = ?
              AND status IN ('sent', 'accepted')
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


def payment_exists(
    proposal_id,
    business_id
):

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM payments
            WHERE proposal_id = ?
              AND business_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                proposal_id,
                business_id
            )
        ).fetchone()

    return dict(row) if row else None


def create_payment_for_proposal(
    proposal,
    business_id
):

    proposal_id = proposal["id"]

    existing = payment_exists(
        proposal_id,
        business_id
    )

    if existing:

        return {
            "created": False,
            "already_exists": True,
            "payment": existing
        }

    amount = float(
        proposal.get(
            "setup_fee",
            0
        )
    )

    if amount <= 0:

        raise ValueError(
            "Proposal setup fee must be greater than zero."
        )

    payment = payment_manager.create_payment(
        proposal_id=proposal_id,
        client_name=proposal.get(
            "client_name",
            ""
        ),
        company=proposal.get(
            "company",
            ""
        ),
        amount=amount,
        payment_type="setup",
        business_id=business_id
    )

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
                "proposal",
                proposal_id,
                "payment_created",
                f"Payment created for ₹{amount:g}",
                proposal.get(
                    "updated_at"
                )
            )
        )

    return {
        "created": True,
        "already_exists": False,
        "payment": payment
    }


def process_business(
    business_id
):

    proposals = get_business_proposals(
        business_id
    )

    results = []

    for proposal in proposals:

        try:

            result = create_payment_for_proposal(
                proposal,
                business_id
            )

            if result.get("created"):

                results.append(
                    result
                )

        except Exception as error:

            print(
                "PAYMENT AGENT ERROR:",
                error
            )

    return results
