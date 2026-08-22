from .database import get_db, new_id, now


class PaymentManager:

    def create_payment(
        self,
        proposal_id,
        client_name,
        company,
        amount,
        payment_type="setup",
        business_id=None,
        client_id=None
    ):

        payment_id = new_id()
        created_at = now()

        with get_db() as db:

            db.execute(
                """
                INSERT INTO payments
                (
                    id,
                    proposal_id,
                    client_id,
                    business_id,
                    client_name,
                    company,
                    amount,
                    payment_type,
                    status,
                    payment_date,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payment_id,
                    proposal_id,
                    client_id,
                    business_id,
                    client_name,
                    company,
                    float(amount),
                    payment_type,
                    "pending",
                    None,
                    created_at,
                    created_at
                )
            )

        return self.get_payment(
            payment_id,
            business_id
        )


    def get_payment(
        self,
        payment_id,
        business_id=None
    ):

        with get_db() as db:

            if business_id:

                row = db.execute(
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

            else:

                row = db.execute(
                    """
                    SELECT *
                    FROM payments
                    WHERE id = ?
                    """,
                    (payment_id,)
                ).fetchone()

        return dict(row) if row else None


    def list_payments(
        self,
        business_id=None
    ):

        with get_db() as db:

            if business_id:

                rows = db.execute(
                    """
                    SELECT *
                    FROM payments
                    WHERE business_id = ?
                    ORDER BY created_at DESC
                    """,
                    (business_id,)
                ).fetchall()

            else:

                rows = db.execute(
                    """
                    SELECT *
                    FROM payments
                    ORDER BY created_at DESC
                    """
                ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


    def mark_paid(
        self,
        payment_id,
        business_id=None
    ):

        with get_db() as db:

            if business_id:

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

            else:

                payment = db.execute(
                    """
                    SELECT *
                    FROM payments
                    WHERE id = ?
                    """,
                    (payment_id,)
                ).fetchone()

            if not payment:
                return None

            if payment["status"] == "paid":
                return dict(payment)

            paid_at = now()

            db.execute(
                """
                UPDATE payments
                SET status = ?,
                    payment_date = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    "paid",
                    paid_at,
                    paid_at,
                    payment_id
                )
            )

            # ------------------------------------------------
            # Synchronize the corresponding revenue record
            # ------------------------------------------------

            revenue = None

            if payment["proposal_id"]:

                revenue = db.execute(
                    """
                    SELECT *
                    FROM revenue
                    WHERE business_id = ?
                      AND lead_id = (
                          SELECT lead_id
                          FROM proposals
                          WHERE id = ?
                            AND business_id = ?
                      )
                      AND client_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (
                        payment["business_id"],
                        payment["proposal_id"],
                        payment["business_id"],
                        payment["client_id"]
                    )
                ).fetchone()

            if revenue:

                db.execute(
                    """
                    UPDATE revenue
                    SET status = ?,
                        payment_date = ?
                    WHERE id = ?
                      AND business_id = ?
                    """,
                    (
                        "paid",
                        paid_at,
                        revenue["id"],
                        business_id
                    )
                )

            # ------------------------------------------------
            # Record payment activity
            # ------------------------------------------------

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
                    "payment",
                    payment_id,
                    "payment_paid",
                    f"{payment['payment_type']} payment: {payment['amount']}",
                    paid_at
                )
            )

        return self.get_payment(
            payment_id,
            business_id
        )


    def cancel_payment(
        self,
        payment_id,
        business_id=None
    ):

        with get_db() as db:

            if business_id:

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

            else:

                payment = db.execute(
                    """
                    SELECT *
                    FROM payments
                    WHERE id = ?
                    """,
                    (payment_id,)
                ).fetchone()

            if not payment:
                return None

            updated_at = now()

            db.execute(
                """
                UPDATE payments
                SET status = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    "cancelled",
                    updated_at,
                    payment_id
                )
            )

        return self.get_payment(
            payment_id,
            business_id
        )


payment_manager = PaymentManager()
