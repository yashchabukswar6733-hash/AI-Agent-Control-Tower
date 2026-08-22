from backend.tasks import task_manager
from agents.manager import agent_manager


class TaskExecutor:

    def execute(self, task_id):
        task = task_manager.get_task(task_id)

        if not task:
            return {
                "error": "Task not found"
            }

        agent_name = task["agent"]

        if not agent_manager.get_agent(agent_name):
            return {
                "error": "Agent not found"
            }

        # Mark task as running
        task_manager.update_status(task_id, "running")
        agent_manager.set_status(agent_name, "working")

        # Temporary execution result
        result = (
            f"Agent '{agent_name}' processed the task: "
            f"{task['description']}"
        )

        # Store result
        task["result"] = result
        task_manager.update_status(task_id, "completed")
        agent_manager.set_status(agent_name, "idle")

        return task


task_executor = TaskExecutor()