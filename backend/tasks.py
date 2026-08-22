from .database import get_db, new_id, now


class TaskManager:

    def create_task(
        self,
        agent_name,
        description,
        client_id=None
    ):

        task_id = new_id()
        created_at = now()

        with get_db() as db:

            agent = db.execute(
                """
                SELECT id
                FROM agents
                WHERE id = ?
                """,
                (agent_name,)
            ).fetchone()

            if not agent:
                raise ValueError(
                    f"Agent '{agent_name}' not found"
                )

            db.execute(
                """
                INSERT INTO tasks
                (
                    id,
                    agent,
                    description,
                    status,
                    result,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    agent_name,
                    description,
                    "pending",
                    None,
                    created_at
                )
            )

        return self.get_task(task_id)


    def get_task(self, task_id):

        with get_db() as db:

            row = db.execute(
                """
                SELECT *
                FROM tasks
                WHERE id = ?
                """,
                (task_id,)
            ).fetchone()

        return dict(row) if row else None


    def list_tasks(self):

        with get_db() as db:

            rows = db.execute(
                """
                SELECT *
                FROM tasks
                ORDER BY created_at DESC
                """
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


    def update_status(
        self,
        task_id,
        status,
        result=None
    ):

        task = self.get_task(task_id)

        if not task:
            return None

        with get_db() as db:

            db.execute(
                """
                UPDATE tasks
                SET
                    status = ?,
                    result = ?
                WHERE id = ?
                """,
                (
                    status,
                    result,
                    task_id
                )
            )

        return self.get_task(task_id)


task_manager = TaskManager()