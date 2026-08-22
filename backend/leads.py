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

            columns = {
                row["name"]
                for row in db.execute(
                    "PRAGMA table_info(leads)"
                ).fetchall()
            }

            if "updated_at" in columns:

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

            else:

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
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

        lead = self.get_lead(lead_id)

        if not lead:
            return None

        with get_db() as db:

            columns = {
                row["name"]
                for row in db.execute(
                    "PRAGMA table_info(leads)"
                ).fetchall()
            }

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

            if "updated_at" in columns:
                updates.append("updated_at = ?")
                values.append(now())

            if not updates:
                return self.get_lead(lead_id)

            values.append(lead_id)

            db.execute(
                f"""
                UPDATE leads
                SET {", ".join(updates)}
                WHERE id = ?
                """,
                tuple(values)
            )

        return self.get_lead(lead_id)


lead_manager = LeadManager()