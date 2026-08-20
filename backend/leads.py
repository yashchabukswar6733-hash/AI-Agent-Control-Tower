from datetime import datetime
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

    def update_lead(self, lead_id, **updates):

        allowed = {
            "name",
            "phone",
            "email",
            "business",
            "requirement",
            "status",
            "score",
            "ai_analysis",
            "follow_up"
        }

        clean_updates = {
            key: value
            for key, value in updates.items()
            if key in allowed
        }

        if not clean_updates:
            return self.get_lead(lead_id)

        clean_updates["updated_at"] = now()

        set_clause = ", ".join(
            f"{key} = ?"
            for key in clean_updates
        )

        values = list(clean_updates.values())
        values.append(lead_id)

        with get_db() as db:

            cursor = db.execute(
                f"""
                UPDATE leads
                SET {set_clause}
                WHERE id = ?
                """,
                values
            )

            if cursor.rowcount == 0:
                return None

        return self.get_lead(lead_id)


lead_manager = LeadManager()