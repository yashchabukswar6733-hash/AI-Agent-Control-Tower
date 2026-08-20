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

            # Check which columns exist in the current database
            columns = {
                row["name"]
                for row in db.execute("PRAGMA table_info(leads)").fetchall()
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


lead_manager = LeadManager()