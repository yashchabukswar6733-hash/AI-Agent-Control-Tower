from .database import get_db, new_id, now


class ClientManager:

    def create_client(self, name, company):

        client_id = new_id()
        created_at = now()

        with get_db() as db:

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
                    name,
                    company,
                    "active",
                    created_at
                )
            )

        return self.get_client(client_id)


    def get_client(self, client_id):

        with get_db() as db:

            row = db.execute(
                """
                SELECT *
                FROM clients
                WHERE id = ?
                """,
                (client_id,)
            ).fetchone()

        return dict(row) if row else None


    def list_clients(self):

        with get_db() as db:

            rows = db.execute(
                """
                SELECT *
                FROM clients
                ORDER BY created_at DESC
                """
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


    def update_status(self, client_id, status):

        client = self.get_client(client_id)

        if not client:
            return None

        allowed_statuses = {
            "active",
            "inactive",
            "onboarding",
            "paused",
            "completed"
        }

        if status not in allowed_statuses:
            raise ValueError(
                f"Invalid client status: {status}"
            )

        with get_db() as db:

            db.execute(
                """
                UPDATE clients
                SET status = ?
                WHERE id = ?
                """,
                (
                    status,
                    client_id
                )
            )

        return self.get_client(client_id)


    def delete_client(self, client_id):

        client = self.get_client(client_id)

        if not client:
            return False

        with get_db() as db:

            db.execute(
                """
                DELETE FROM clients
                WHERE id = ?
                """,
                (client_id,)
            )

        return True


client_manager = ClientManager()