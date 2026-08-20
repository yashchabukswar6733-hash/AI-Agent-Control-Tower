from .database import get_db, new_id, now


# ============================================================
# CREATE PROPOSAL
# ============================================================

def create_proposal(
    lead_id,
    client_name,
    company,
    service,
    setup_fee,
    monthly_fee,
    description
):

    proposal_id = new_id()
    created_at = now()

    with get_db() as db:

        db.execute(
            """
            INSERT INTO proposals (
                id,
                lead_id,
                client_name,
                company,
                service,
                setup_fee,
                monthly_fee,
                description,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_id,
                lead_id,
                client_name,
                company,
                service,
                float(setup_fee),
                float(monthly_fee),
                description,
                "draft",
                created_at
            )
        )

    return get_proposal(proposal_id)


# ============================================================
# GET PROPOSAL
# ============================================================

def get_proposal(proposal_id):

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM proposals
            WHERE id = ?
            """,
            (proposal_id,)
        ).fetchone()

    if not row:
        return None

    return dict(row)


# ============================================================
# LIST PROPOSALS
# ============================================================

def list_proposals():

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *
            FROM proposals
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# UPDATE PROPOSAL
# ============================================================

def update_proposal(
    proposal_id,
    **updates
):

    allowed_fields = {
        "status",
        "setup_fee",
        "monthly_fee",
        "description"
    }

    clean_updates = {}

    for key, value in updates.items():

        if key in allowed_fields and value is not None:
            clean_updates[key] = value

    if not clean_updates:
        return get_proposal(proposal_id)

    with get_db() as db:

        existing = db.execute(
            """
            SELECT id
            FROM proposals
            WHERE id = ?
            """,
            (proposal_id,)
        ).fetchone()

        if not existing:
            return None

        fields = []
        values = []

        for key, value in clean_updates.items():

            fields.append(
                f"{key} = ?"
            )

            values.append(value)

        values.append(proposal_id)

        query = f"""
            UPDATE proposals
            SET {", ".join(fields)}
            WHERE id = ?
        """

        db.execute(
            query,
            values
        )

    return get_proposal(proposal_id)


# ============================================================
# MARK PROPOSAL AS SENT
# ============================================================

def send_proposal(proposal_id):

    return update_proposal(
        proposal_id,
        status="sent"
    )


# ============================================================
# MARK PROPOSAL AS ACCEPTED
# ============================================================

def accept_proposal(proposal_id):

    return update_proposal(
        proposal_id,
        status="accepted"
    )


# ============================================================
# MARK PROPOSAL AS REJECTED
# ============================================================

def reject_proposal(proposal_id):

    return update_proposal(
        proposal_id,
        status="rejected"
    )