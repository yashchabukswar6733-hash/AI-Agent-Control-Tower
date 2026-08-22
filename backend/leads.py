import uuid

from .database import get_db, now


class LeadManager:

    def create_lead(
        self,
        business_id,
        name,
        phone,
        email="",
        business="",
        requirement=""
    ):
        lead_id = uuid.uuid4().hex[:8]
        created_at = now()

        with get_db() as db:

            db.execute(
                """
                INSERT INTO leads
                (
                    id,
                    name,
                    phone,
                    email,
                    business,
                    requirement,
                    status,
                    score,
                    ai_analysis,
                    follow_up,
                    created_at,
                    updated_at,
                    business_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead_id,
                    name,
                    phone,
                    email,
                    business,
                    requirement,
                    "new",
                    0,
                    "",
                    "",
                    created_at,
                    created_at,
                    business_id
                )
            )

        return self.get_lead(
            business_id,
            lead_id
        )


    def get_lead(
        self,
        business_id,
        lead_id
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

        if not row:
            return None

        return dict(row)


    def list_leads(
        self,
        business_id
    ):

        with get_db() as db:

            rows = db.execute(
                """
                SELECT *
                FROM leads
                WHERE business_id = ?
                ORDER BY created_at DESC
                """,
                (business_id,)
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


    def update_lead(
        self,
        business_id,
        lead_id,
        status=None,
        score=None,
        ai_analysis=None,
        follow_up=None
    ):

        lead = self.get_lead(
            business_id,
            lead_id
        )

        if not lead:
            return None

        updates = []
        values = []

        if status is not None:
            updates.append("status = ?")
            values.append(status)

        if score is not None:
            updates.append("score = ?")
            values.append(score)

        if ai_analysis is not None:
            updates.append("ai_analysis = ?")
            values.append(ai_analysis)

        if follow_up is not None:
            updates.append("follow_up = ?")
            values.append(follow_up)

        updates.append("updated_at = ?")
        values.append(now())

        values.extend([
            lead_id,
            business_id
        ])

        with get_db() as db:

            db.execute(
                f"""
                UPDATE leads
                SET {", ".join(updates)}
                WHERE id = ?
                  AND business_id = ?
                """,
                tuple(values)
            )

        return self.get_lead(
            business_id,
            lead_id
        )


lead_manager = LeadManager()
