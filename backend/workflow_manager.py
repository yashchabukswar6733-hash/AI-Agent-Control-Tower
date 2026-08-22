from .database import get_db, new_id, now


class WorkflowManager:

    def create_workflow(self, client_id, goal):

        workflow_id = new_id()
        created_at = now()

        with get_db() as db:

            client = db.execute(
                """
                SELECT id
                FROM clients
                WHERE id = ?
                """,
                (client_id,)
            ).fetchone()

            if not client:
                raise ValueError(
                    f"Client '{client_id}' not found"
                )

            db.execute(
                """
                INSERT INTO workflows
                (
                    id,
                    client_id,
                    goal,
                    status,
                    result,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow_id,
                    client_id,
                    goal,
                    "pending",
                    None,
                    created_at
                )
            )

            steps = [
                "research",
                "analysis",
                "report"
            ]

            for step_name in steps:

                db.execute(
                    """
                    INSERT INTO workflow_steps
                    (
                        workflow_id,
                        name,
                        status,
                        result
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        workflow_id,
                        step_name,
                        "pending",
                        None
                    )
                )

        return self.get_workflow(workflow_id)


    def get_workflow(self, workflow_id):

        with get_db() as db:

            workflow = db.execute(
                """
                SELECT *
                FROM workflows
                WHERE id = ?
                """,
                (workflow_id,)
            ).fetchone()

            if not workflow:
                return None

            steps = db.execute(
                """
                SELECT
                    id,
                    workflow_id,
                    name,
                    status,
                    result
                FROM workflow_steps
                WHERE workflow_id = ?
                ORDER BY id
                """,
                (workflow_id,)
            ).fetchall()

        result = dict(workflow)

        result["steps"] = [
            dict(step)
            for step in steps
        ]

        return result


    def list_workflows(self):

        with get_db() as db:

            workflows = db.execute(
                """
                SELECT *
                FROM workflows
                ORDER BY created_at DESC
                """
            ).fetchall()

            output = []

            for workflow in workflows:

                item = dict(workflow)

                steps = db.execute(
                    """
                    SELECT
                        id,
                        workflow_id,
                        name,
                        status,
                        result
                    FROM workflow_steps
                    WHERE workflow_id = ?
                    ORDER BY id
                    """,
                    (workflow["id"],)
                ).fetchall()

                item["steps"] = [
                    dict(step)
                    for step in steps
                ]

                output.append(item)

        return output


    def update_workflow_status(
        self,
        workflow_id,
        status,
        result=None
    ):

        workflow = self.get_workflow(workflow_id)

        if not workflow:
            return None

        allowed_statuses = {
            "pending",
            "running",
            "completed",
            "failed",
            "cancelled"
        }

        if status not in allowed_statuses:
            raise ValueError(
                f"Invalid workflow status: {status}"
            )

        with get_db() as db:

            db.execute(
                """
                UPDATE workflows
                SET
                    status = ?,
                    result = ?
                WHERE id = ?
                """,
                (
                    status,
                    result,
                    workflow_id
                )
            )

        return self.get_workflow(workflow_id)


    def update_step(
        self,
        workflow_id,
        step_name,
        status,
        result=None
    ):

        workflow = self.get_workflow(workflow_id)

        if not workflow:
            return None

        allowed_statuses = {
            "pending",
            "running",
            "completed",
            "failed",
            "skipped"
        }

        if status not in allowed_statuses:
            raise ValueError(
                f"Invalid step status: {status}"
            )

        with get_db() as db:

            step = db.execute(
                """
                SELECT id
                FROM workflow_steps
                WHERE workflow_id = ?
                AND name = ?
                """,
                (
                    workflow_id,
                    step_name
                )
            ).fetchone()

            if not step:
                return None

            db.execute(
                """
                UPDATE workflow_steps
                SET
                    status = ?,
                    result = ?
                WHERE workflow_id = ?
                AND name = ?
                """,
                (
                    status,
                    result,
                    workflow_id,
                    step_name
                )
            )

        return self.get_workflow(workflow_id)


workflow_manager = WorkflowManager()