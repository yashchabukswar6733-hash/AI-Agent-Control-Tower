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
                "Client onboarding requires a paid payment."
            )

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
                    "client": dict(existing),
                    "created": False
                }

        client_id = new_id()
        created_at = now()

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
                payment.get(
                    "client_name",
                    ""
                ),
                payment.get(
                    "company",
                    ""
                ),
                "",
                "",
                "active",
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
                "client_onboarded",
                "Client automatically onboarded after successful payment.",
                created_at
            )
        )

    return {
        "client_id": client_id,
        "payment_id": payment_id,
        "status": "active",
        "created": True
    }


def onboard_all_paid_clients(
    business_id
):

    with get_db() as db:

        payments = db.execute(
            """
            SELECT id
            FROM payments
            WHERE business_id = ?
              AND status = 'paid'
            ORDER BY created_at ASC
            """,
            (business_id,)
        ).fetchall()

    results = []

    for payment in payments:

        try:

            result = onboard_paid_client(
                payment["id"],
                business_id
            )

            results.append(
                result
            )

        except Exception as error:

            print(
                "ONBOARDING ERROR:",
                error
            )

    return results
