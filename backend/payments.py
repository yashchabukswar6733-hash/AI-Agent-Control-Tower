from datetime import datetime
import uuid

from .database import get_db


class PaymentManager:

    def create_payment(
        self,
        proposal_id,
        client_name,
        company,
        amount,
        payment_type="setup",
        description=""
    ):
        payment_id = uuid.uuid4().hex[:8]
        created_at = datetime.now().isoformat()

        with get_db() as db:
            db.execute(
                """
                INSERT INTO payments
                (
                    id,
                    proposal_id,
                    client_name,
                    company,
                    amount,
                    payment_type,
                    status,
                    notes,
                    created_at,
                    paid_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payment_id,
                    proposal_id,
                    client_name,
                    company,
                    float(amount),
                    payment_type,
                    "pending",
                    description,
                    created_at,
                    None
                )
            )

        return self.get_payment(payment_id)


    def get_payment(self, payment_id):

        with get_db() as db:
            row = db.execute(
                """
                SELECT *
                FROM payments
                WHERE id = ?
                """,
                (payment_id,)
            ).fetchone()

        return dict(row) if row else None


    def list_payments(self):

        with get_db() as db:
            rows = db.execute(
                """
                SELECT *
                FROM payments
                ORDER BY created_at DESC
                """
            ).fetchall()

        return [dict(row) for row in rows]


    def mark_paid(
        self,
        payment_id,
        payment_method=None,
        transaction_id=None
    ):

        payment = self.get_payment(payment_id)

        if not payment:
            return None

        # Prevent duplicate processing
        if payment["status"] == "paid":
            return payment

        paid_at = datetime.now().isoformat()

        with get_db() as db:

            # --------------------------------------------------
            # 1. MARK PAYMENT PAID
            # --------------------------------------------------

            db.execute(
                """
                UPDATE payments
                SET
                    status = 'paid',
                    payment_method = ?,
                    transaction_id = ?,
                    paid_at = ?
                WHERE id = ?
                """,
                (
                    payment_method,
                    transaction_id,
                    paid_at,
                    payment_id
                )
            )

            # --------------------------------------------------
            # 2. GET PROPOSAL
            # --------------------------------------------------

            proposal = None

            if payment["proposal_id"]:
                proposal = db.execute(
                    """
                    SELECT *
                    FROM proposals
                    WHERE id = ?
                    """,
                    (payment["proposal_id"],)
                ).fetchone()

            # --------------------------------------------------
            # 3. CREATE CLIENT AUTOMATICALLY
            # --------------------------------------------------

            client = db.execute(
                """
                SELECT *
                FROM clients
                WHERE name = ?
                AND company = ?
                """,
                (
                    payment["client_name"],
                    payment["company"]
                )
            ).fetchone()

            if client:

                client_id = client["id"]

            else:

                client_id = uuid.uuid4().hex[:8]

                db.execute(
                    """
                    INSERT INTO clients
                    (
                        id,
                        name,
                        company,
                        status,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        client_id,
                        payment["client_name"],
                        payment["company"],
                        "active",
                        paid_at
                    )
                )

            # --------------------------------------------------
            # 4. MARK SALES OPPORTUNITY AS WON
            # --------------------------------------------------

            if proposal:

                lead_id = proposal["lead_id"]

                sales = db.execute(
                    """
                    SELECT id
                    FROM sales_opportunities
                    WHERE lead_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (lead_id,)
                ).fetchone()

                if sales:

                    db.execute(
                        """
                        UPDATE sales_opportunities
                        SET
                            stage = 'won',
                            probability = 100,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            paid_at,
                            sales["id"]
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
                            "sales",
                            sales["id"],
                            "payment_confirmed_sales_won",
                            payment_id,
                            paid_at
                        )
                    )

            else:

                lead_id = None

            # --------------------------------------------------
            # 5. CREATE REVENUE RECORD
            # --------------------------------------------------

            existing_revenue = db.execute(
                """
                SELECT id
                FROM revenue
                WHERE client_id = ?
                AND payment_date = ?
                AND setup_fee = ?
                """,
                (
                    client_id,
                    paid_at,
                    float(payment["amount"])
                )
            ).fetchone()

            if not existing_revenue:

                revenue_id = uuid.uuid4().hex[:8]

                service = (
                    proposal["service"]
                    if proposal
                    else payment["notes"] or "Unknown Service"
                )

                setup_fee = (
                    float(proposal["setup_fee"])
                    if proposal
                    else float(payment["amount"])
                )

                monthly_fee = (
                    float(proposal["monthly_fee"])
                    if proposal
                    else 0
                )

                db.execute(
                    """
                    INSERT INTO revenue
                    (
                        id,
                        lead_id,
                        client_id,
                        service,
                        setup_fee,
                        monthly_fee,
                        status,
                        payment_date,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        revenue_id,
                        lead_id,
                        client_id,
                        service,
                        setup_fee,
                        monthly_fee,
                        "paid",
                        paid_at,
                        paid_at
                    )
                )

            # --------------------------------------------------
            # 6. LOG COMPLETE AUTOMATION
            # --------------------------------------------------

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
                    "payment_automation_completed",
                    "client_created_or_found; sales_won; revenue_recorded",
                    paid_at
                )
            )

        return self.get_payment(payment_id)


    def cancel_payment(self, payment_id):

        payment = self.get_payment(payment_id)

        if not payment:
            return None

        if payment["status"] == "paid":
            return payment

        with get_db() as db:
            db.execute(
                """
                UPDATE payments
                SET status = 'cancelled'
                WHERE id = ?
                """,
                (payment_id,)
            )

        return self.get_payment(payment_id)


payment_manager = PaymentManager()
