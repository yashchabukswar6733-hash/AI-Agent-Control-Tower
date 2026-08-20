from datetime import datetime
import uuid


class TaskManager:

    def __init__(self):
        self.tasks = {}

    def create_task(
        self,
        agent_name,
        description,
        client_id=None
    ):
        task_id = uuid.uuid4().hex[:8]

        task = {
            "id": task_id,
            "client_id": client_id,
            "agent": agent_name,
            "description": description,
            "status": "pending",
            "result": None,
            "created_at": datetime.now().isoformat()
        }

        self.tasks[task_id] = task

        return task

    def list_tasks(self):
        return list(self.tasks.values())

    def get_task(self, task_id):
        return self.tasks.get(task_id)

    def update_status(self, task_id, status):

        if task_id not in self.tasks:
            return False

        self.tasks[task_id]["status"] = status

        return True


task_manager = TaskManager()