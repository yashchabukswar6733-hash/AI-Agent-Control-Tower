import uuid

from .database import get_db, now


class LeadManager:

    def create_lead(
        self,
        name,
        phone,
        email="",
        business="",
        requirement=""
    ):
        lead_id = uuid.uuid4().hex[:8]
        created_at = now()

        with get_db() as db:

            # Make sure older databases have updated_at
            columns = db.execute(
                "PRAGMA table_info(leads)"
            ).fetchall()

            column_names = [column["name"] for column in columns]

            if "updated_at" not in column_names:
                db.execute(
                    "ALTER TABLE leads ADD COLUMN updated_at TEXT"
                )

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
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead_id,
                    name,
                    phone,
                    email,
                    business,
                    requirement,
                    "new",
                    None,
                    None,
                    None,
                    created_at,
                    created_at
                )
            )

        return self.get_lead(lead_id)

    def get_lead(self, lead_id):

        with get_db() as db:

            row = db.execute(
                """
                SELECT *
                FROM leads
                WHERE id = ?
                """,
                (lead_id,)
            ).fetchone()

        if not row:
            return None

        return dict(row)

    def list_leads(self):

        with get_db() as db:

            rows = db.execute(
                """
                SELECT *
                FROM leads
                ORDER BY created_at DESC
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def update_lead(
        self,
        lead_id,
        status=None,
        score=None,
        ai_analysis=None,
        follow_up=None
    ):

        with get_db() as db:

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

            if updates:
                updates.append("updated_at = ?")
                values.append(now())

                values.append(lead_id)

                db.execute(
                    f"""
                    UPDATE leads
                    SET {", ".join(updates)}
                    WHERE id = ?
                    """,
                    values
                )

        return self.get_lead(lead_id)


lead_manager = LeadManager()