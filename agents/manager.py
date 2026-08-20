from datetime import datetime


class AgentManager:
    def __init__(self):
        self.agents = {}

    def register_agent(self, name, role="general"):
        agent = {
            "name": name,
            "role": role,
            "status": "idle",
            "created_at": datetime.now().isoformat()
        }

        self.agents[name] = agent
        return agent

    def list_agents(self):
        return list(self.agents.values())

    def get_agent(self, name):
        return self.agents.get(name)

    def set_status(self, name, status):
        if name not in self.agents:
            return False

        self.agents[name]["status"] = status
        return True


agent_manager = AgentManager()