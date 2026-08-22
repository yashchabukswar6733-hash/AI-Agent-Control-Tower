from .database import get_db, new_id, now


def onboard_paid_client(
    payment_id,
    business_id
):

    with get_db() as db:

        payment = db.execute(
            """
            SELECT *
            FROM payments
            WHERE id = ?
              AND business_id = ?
            """,
            (
                payment_id,
                business_id
            )
        ).fetchone()

        if not payment:
            raise ValueError(
                "Payment not found."
            )

        payment = dict(payment)

        if payment["status"] != "paid":
            raise ValueError(
                "Client onboarding requires a verified paid payment."
            )

        proposal = None

        if payment.get("proposal_id"):

            proposal_row = db.execute(
                """
                SELECT *
                FROM proposals
                WHERE id = ?
                  AND business_id = ?
                """,
                (
                    payment["proposal_id"],
                    business_id
                )
            ).fetchone()

            if proposal_row:
                proposal = dict(proposal_row)

        client_id = payment.get(
            "client_id"
        )

        if client_id:

            existing = db.execute(
                """
                SELECT *
                FROM clients
                WHERE id = ?
                  AND business_id = ?
                """,
                (
                    client_id,
                    business_id
                )
            ).fetchone()

            if existing:

                return {
                    "created": False,
                    "client": dict(existing)
                }

        client_id = new_id()
        created_at = now()

        client_name = payment.get(
            "client_name",
            ""
        )

        company = payment.get(
            "company",
            ""
        )

        if proposal:

            if not client_name:
                client_name = proposal.get(
                    "client_name",
                    ""
                )

            if not company:
                company = proposal.get(
                    "company",
                    ""
                )

        db.execute(
            """
            INSERT INTO clients
            (
                id,
                name,
                company,
                email,
                phone,
                status,
                created_at,
                updated_at,
                business_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                client_name,
                company,
                "",
                "",
                "onboarding",
                created_at,
                created_at,
                business_id
            )
        )

        db.execute(
            """
            UPDATE payments
            SET client_id = ?,
                updated_at = ?
            WHERE id = ?
              AND business_id = ?
            """,
            (
                client_id,
                created_at,
                payment_id,
                business_id
            )
        )

        onboarding_id = new_id()

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS client_onboarding
            (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                business_id TEXT NOT NULL,
                payment_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        db.execute(
            """
            INSERT INTO client_onboarding
            (
                id,
                client_id,
                business_id,
                payment_id,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                onboarding_id,
                client_id,
                business_id,
                payment_id,
                "started",
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
                "client_onboarding_started",
                f"Onboarding created from paid payment {payment_id}",
                created_at
            )
        )

    return {
        "created": True,
        "client_id": client_id,
        "onboarding_id": onboarding_id,
        "status": "onboarding"
    }
