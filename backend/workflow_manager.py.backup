from datetime import datetime
import uuid


class WorkflowManager:

    def __init__(self):
        self.workflows = {}

    def create_workflow(self, client_id, goal):

        workflow_id = uuid.uuid4().hex[:8]

        workflow = {
            "id": workflow_id,
            "client_id": client_id,
            "goal": goal,
            "status": "pending",
            "steps": [
                {
                    "name": "research",
                    "status": "pending",
                    "result": None
                },
                {
                    "name": "analysis",
                    "status": "pending",
                    "result": None
                },
                {
                    "name": "report",
                    "status": "pending",
                    "result": None
                }
            ],
            "result": None,
            "created_at": datetime.now().isoformat()
        }

        self.workflows[workflow_id] = workflow

        return workflow

    def list_workflows(self):
        return list(self.workflows.values())

    def get_workflow(self, workflow_id):
        return self.workflows.get(workflow_id)

    def update_workflow_status(
        self,
        workflow_id,
        status
    ):

        workflow = self.workflows.get(
            workflow_id
        )

        if not workflow:
            return False

        workflow["status"] = status

        return True

    def update_step(
        self,
        workflow_id,
        step_name,
        status,
        result=None
    ):

        workflow = self.workflows.get(
            workflow_id
        )

        if not workflow:
            return False

        for step in workflow["steps"]:

            if step["name"] == step_name:

                step["status"] = status
                step["result"] = result

                return True

        return False


workflow_manager = WorkflowManager()