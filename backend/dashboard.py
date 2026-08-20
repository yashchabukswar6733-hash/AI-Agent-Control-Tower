from agents.manager import agent_manager
from backend.tasks import task_manager


def get_dashboard_data():

    agents = agent_manager.list_agents()
    tasks = task_manager.list_tasks()

    total_agents = len(agents)
    active_agents = len([
        agent for agent in agents
        if agent["status"] == "working"
    ])

    total_tasks = len(tasks)

    completed_tasks = len([
        task for task in tasks
        if task["status"] == "completed"
    ])

    running_tasks = len([
        task for task in tasks
        if task["status"] == "running"
    ])

    failed_tasks = len([
        task for task in tasks
        if task["status"] == "failed"
    ])

    return {
        "overview": {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "running_tasks": running_tasks,
            "failed_tasks": failed_tasks
        },

        "agents": agents,

        "recent_tasks": tasks[-10:]
    }